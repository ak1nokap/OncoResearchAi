import logging
from typing import Dict, List

from django.conf import settings
from openai import OpenAI

from apps.research.services.semantic_search import semantic_search

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def _build_context(papers, max_chars: int) -> str:
    blocks: List[str] = []
    current_len = 0

    for idx, paper in enumerate(papers, start=1):
        summary_text = (paper.summary or "").strip()
        abstract_text = (paper.abstract or "").strip()
        authors_text = (paper.authors or "").strip() or "Unknown authors"

        block = f"""
[Paper {idx}]
Title: {paper.title}
Authors: {authors_text}
Source: {paper.source}
Published: {paper.published_date}
Cancer type: {paper.cancer_type}
AI method: {paper.ai_method}
Summary: {summary_text}
Abstract: {abstract_text}
URL: {paper.url}
""".strip()

        if current_len + len(block) > max_chars:
            break

        blocks.append(block)
        current_len += len(block)

    return "\n\n".join(blocks)


def generate_literature_review(query: str, top_k: int = None) -> Dict:
    query = (query or "").strip()
    top_k = top_k or getattr(settings, "LITERATURE_REVIEW_TOP_K", 6)

    if not query:
        return {
            "review": None,
            "papers": [],
        }

    papers = list(semantic_search(query, limit=top_k))

    if not papers:
        return {
            "review": "No relevant papers were found for this topic in the current database.",
            "papers": [],
        }

    context = _build_context(
        papers,
        max_chars=getattr(settings, "MAX_REVIEW_CONTEXT_CHARS", 12000),
    )

    if not context:
        return {
            "review": "Relevant papers were found, but there was not enough paper content to build a literature review.",
            "papers": papers,
        }

    if not getattr(settings, "OPENAI_API_KEY", None):
        return {
            "review": (
                "The literature review could not be generated because the OpenAI API key is not configured. "
                "Relevant source papers are listed below."
            ),
            "papers": papers,
        }

    prompt = f"""
You are an expert scientific research assistant writing a concise literature review
for a research portal focused on AI in cancer diagnostics.

Your task:
Write a structured mini literature review using ONLY the paper evidence provided below.

User topic:
{query}

Requirements:
1. Write in clear academic English.
2. Be factual, neutral, and concise.
3. Use ONLY information supported by the provided papers.
4. Do NOT invent datasets, metrics, conclusions, or methods.
5. If evidence is limited or inconsistent, say so explicitly.
6. Prefer specific terms over vague ones.
7. Mention paper references inline when helpful, for example [Paper 1].
8. The review should be useful for a researcher who wants a quick overview.

Output format:
Return plain text with these sections and headings exactly:

Overview
- 1 short paragraph introducing the topic and what the retrieved literature seems to focus on.

Methods and approaches
- 1 short paragraph describing the main AI methods, imaging modalities, or analytical strategies used.

Findings
- 1 short paragraph summarizing the main reported patterns, themes, or outcomes.

Limitations and gaps
- 1 short paragraph explaining limitations, missing evidence, narrow coverage, or research gaps.

At the end, add a final line:
Sources used: [Paper 1], [Paper 2], ...

Paper evidence:
{context}
""".strip()

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL_CHAT,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You write rigorous, evidence-grounded scientific summaries. "
                        "You only use the supplied paper context."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        review_text = (response.choices[0].message.content or "").strip()
    except Exception as exc:
        logger.exception("Literature review generation failed: %s", exc)
        review_text = (
            "The literature review could not be generated because the language model is unavailable right now. "
            "Please check the API configuration or quota."
        )

    return {
        "review": review_text,
        "papers": papers,
    }

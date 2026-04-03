import logging
from typing import List

from django.conf import settings
from openai import OpenAI

from apps.research.models import Paper
from apps.research.services.semantic_search import semantic_search

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def _build_context(papers: List[Paper], max_chars: int) -> str:
    chunks = []
    total = 0

    for idx, paper in enumerate(papers, start=1):
        chunk = (
            f"[Paper {idx}]\n"
            f"Title: {paper.title}\n"
            f"Source: {paper.source}\n"
            f"Authors: {paper.authors}\n"
            f"Published: {paper.published_date}\n"
            f"Summary: {paper.summary}\n"
            f"Abstract: {paper.abstract}\n"
            f"URL: {paper.url}\n"
        )

        if total + len(chunk) > max_chars:
            break

        chunks.append(chunk)
        total += len(chunk)

    return "\n\n".join(chunks)


def answer_with_rag(question: str) -> dict:
    papers = list(semantic_search(question))
    context = _build_context(papers, settings.MAX_PAPER_CONTEXT)

    if not context:
        return {
            "answer": "I could not find relevant papers in the database yet.",
            "papers": [],
        }

    prompt = f"""
You are a scientific assistant for an AI cancer diagnostics research portal.

Answer the question using only the provided paper context.
If evidence is limited, say so clearly.
Prefer concise, evidence-grounded phrasing.
Do not invent findings that are not in the context.

Question:
{question}

Paper context:
{context}
"""

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL_SUMMARY,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Answer only from provided research context. "
                        "Be accurate, cautious, and concise."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        answer = response.choices[0].message.content.strip()
    except Exception as exc:
        logger.exception("RAG answer failed: %s", exc)
        answer = "An error occurred while generating the answer."

    return {
        "answer": answer,
        "papers": papers,
    }
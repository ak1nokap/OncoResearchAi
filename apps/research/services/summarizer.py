import json
import logging
from typing import Dict

from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def summarize_paper(title: str, abstract: str) -> Dict[str, str]:
    text = f"Title: {title}\n\nAbstract:\n{abstract}".strip()

    prompt = f"""
You are extracting structured metadata from scientific papers about AI in cancer diagnostics.

Read the paper title and abstract carefully and return ONLY valid JSON with exactly these keys:
- summary
- cancer_type
- ai_method

Instructions:
1. summary:
   - write 2 to 4 sentences
   - neutral scientific style
   - summarize the goal, method, and main result if available

2. cancer_type:
   - extract the most specific cancer type mentioned in the paper
   - do NOT restrict yourself to a predefined list
   - examples of valid outputs:
     "non-small cell lung cancer"
     "breast cancer"
     "glioblastoma"
     "colorectal cancer"
     "hepatocellular carcinoma"
     "melanoma"
     "thyroid cancer"
   - if the paper is about cancer in general and no specific type is given, return:
     "general cancer"
   - return "unknown" only if no cancer type can be inferred from the title or abstract

3. ai_method:
   - extract the most specific AI / computational method mentioned
   - do NOT restrict yourself to a predefined list
   - examples of valid outputs:
     "convolutional neural network"
     "vision transformer"
     "radiomics"
     "random forest"
     "support vector machine"
     "gradient boosting"
     "deep learning"
     "machine learning"
     "multimodal learning"
     "transfer learning"
     "ensemble model"
   - if multiple methods are mentioned, return the main method emphasized by the paper
   - return "unknown" only if no method can be inferred from the title or abstract

Important rules:
- prefer specific terms over generic ones
- do not invent details not supported by the text
- return JSON only, with no markdown, no explanations, no extra text

Paper:
{text}
"""

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL_SUMMARY,
            temperature=0.1,
            messages=[
                {"role": "system", "content": "Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content.strip()
        parsed = json.loads(content)

        return {
            "summary": parsed.get("summary", "").strip(),
            "cancer_type": parsed.get("cancer_type", "unknown").strip() or "unknown",
            "ai_method": parsed.get("ai_method", "unknown").strip() or "unknown",
        }
    except Exception as exc:
        logger.exception("Summarization failed: %s", exc)
        return {
            "summary": "",
            "cancer_type": "unknown",
            "ai_method": "unknown",
        }
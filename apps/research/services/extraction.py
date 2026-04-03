import json
import logging

from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def extract_research_metadata(title: str, abstract: str):
    """
    Extract structured metadata from research paper.
    """

    prompt = f"""
You are analyzing scientific papers about AI cancer diagnostics.

Extract structured metadata.

Return ONLY JSON with fields:

cancer_type
ai_method

Examples:

breast cancer
lung cancer
melanoma
brain tumor
colon cancer
unknown

AI methods:

CNN
transformer
radiomics
machine learning
deep learning
unknown

Paper:

Title:
{title}

Abstract:
{abstract}
"""

    try:

        response = client.chat.completions.create(

            model=settings.OPENAI_MODEL_SUMMARY,

            temperature=0.1,

            messages=[
                {"role": "system", "content": "Return JSON only."},
                {"role": "user", "content": prompt},
            ],
        )

        content = response.choices[0].message.content.strip()

        data = json.loads(content)

        return {
            "cancer_type": data.get("cancer_type", "unknown"),
            "ai_method": data.get("ai_method", "unknown"),
        }

    except Exception:

        logger.exception("Metadata extraction failed")

        return {
            "cancer_type": "unknown",
            "ai_method": "unknown",
        }
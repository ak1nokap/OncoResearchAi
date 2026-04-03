from typing import Optional

from django.conf import settings
from django.db.models import Q
from pgvector.django import CosineDistance

from apps.research.models import Paper
from apps.research.services.embeddings import create_embedding


DEFAULT_LIMIT = getattr(settings, "SEMANTIC_SEARCH_RESULTS", 10)


def build_search_text(paper: Paper) -> str:
    parts = [
        paper.title or "",
        paper.abstract or "",
        paper.summary or "",
        paper.cancer_type or "",
        paper.ai_method or "",
    ]
    return "\n\n".join(part.strip() for part in parts if part and part.strip())


def semantic_search(query: str, limit: Optional[int] = None):
    query = (query or "").strip()
    limit = limit or DEFAULT_LIMIT

    if not query:
        return Paper.objects.none()

    query_embedding = create_embedding(query)

    if query_embedding is not None:
        try:
            return (
                Paper.objects.filter(embedding__isnull=False)
                .annotate(distance=CosineDistance("embedding", query_embedding))
                .order_by("distance", "-published_date")[:limit]
            )
        except Exception:
            pass

    return (
        Paper.objects.filter(
            Q(title__icontains=query)
            | Q(abstract__icontains=query)
            | Q(summary__icontains=query)
            | Q(cancer_type__icontains=query)
            | Q(ai_method__icontains=query)
        )
        .order_by("-published_date")[:limit]
    )
import logging
from typing import Dict, Iterable, List

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.research.models import Paper
from apps.research.services.arxiv import fetch_arxiv_papers
from apps.research.services.pubmed import fetch_pubmed_papers
from apps.research.services.embeddings import create_embedding
from apps.research.services.summarizer import summarize_paper

logger = logging.getLogger(__name__)


def _paper_exists(title: str, url: str) -> bool:
    return Paper.objects.filter(title=title).exists() or Paper.objects.filter(url=url).exists()


def _normalize_published_date(value):
    if value:
        return value
    return timezone.now()


@transaction.atomic
def _store_paper(item: Dict) -> bool:
    title = item.get("title", "").strip()
    abstract = item.get("abstract", "").strip()
    url = item.get("url", "").strip()

    if not title or not url:
        return False

    if _paper_exists(title=title, url=url):
        return False

    enrichment = summarize_paper(title=title, abstract=abstract) if abstract else {
        "summary": "",
        "cancer_type": "unknown",
        "ai_method": "unknown",
    }

    embedding = None
    if abstract:
        try:
            embedding = create_embedding(f"{title}\n\n{abstract}")
        except Exception:
            logger.exception("Embedding failed for title=%s", title)

    Paper.objects.create(
        title=title,
        abstract=abstract,
        summary=enrichment["summary"],
        authors=item.get("authors", "").strip(),
        url=url,
        source=item.get("source", "").strip(),
        published_date=_normalize_published_date(item.get("published_date")),
        embedding=embedding,
    )

    paper = Paper.objects.get(url=url)
    if hasattr(paper, "cancer_type"):
        paper.cancer_type = enrichment["cancer_type"]
    if hasattr(paper, "ai_method"):
        paper.ai_method = enrichment["ai_method"]
    paper.save(update_fields=[f for f in ["cancer_type", "ai_method"] if hasattr(paper, f)])

    return True


def _ingest_items(items: Iterable[Dict], source_name: str) -> Dict[str, int]:
    created = 0
    skipped = 0

    for item in items:
        try:
            was_created = _store_paper(item)
            if was_created:
                created += 1
            else:
                skipped += 1
        except Exception:
            logger.exception("Failed to ingest %s paper: %s", source_name, item.get("title"))
            skipped += 1

    return {"created": created, "skipped": skipped}


@shared_task
def ingest_pubmed_papers() -> Dict[str, int]:
    logger.info("Starting PubMed ingestion")
    papers = fetch_pubmed_papers()
    result = _ingest_items(papers, "pubmed")
    logger.info("Finished PubMed ingestion: %s", result)
    return result


@shared_task
def ingest_arxiv_papers() -> Dict[str, int]:
    logger.info("Starting arXiv ingestion")
    papers = fetch_arxiv_papers()
    result = _ingest_items(papers, "arxiv")
    logger.info("Finished arXiv ingestion: %s", result)
    return result


@shared_task
def ingest_all_sources() -> Dict[str, Dict[str, int]]:
    pubmed_result = ingest_pubmed_papers()
    arxiv_result = ingest_arxiv_papers()

    return {
        "pubmed": pubmed_result,
        "arxiv": arxiv_result,
    }
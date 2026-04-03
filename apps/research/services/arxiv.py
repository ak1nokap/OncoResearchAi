import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

ARXIV_API_URL = "https://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def _safe_request(url: str, params: Dict[str, Any], timeout: int = 30) -> requests.Response:
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response


def _parse_datetime(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None


def fetch_arxiv_papers(query: Optional[str] = None, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
    search_query = query or settings.ARXIV_QUERY
    limit = max_results or settings.ARXIV_MAX_RESULTS

    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": limit,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }

    try:
        response = _safe_request(ARXIV_API_URL, params, timeout=60)
        root = ET.fromstring(response.text)
    except Exception as exc:
        logger.exception("arXiv fetch failed: %s", exc)
        return []

    papers: List[Dict[str, Any]] = []

    for entry in root.findall("atom:entry", ATOM_NS):
        title = (entry.findtext("atom:title", default="", namespaces=ATOM_NS) or "").strip()
        abstract = (entry.findtext("atom:summary", default="", namespaces=ATOM_NS) or "").strip()
        url = (entry.findtext("atom:id", default="", namespaces=ATOM_NS) or "").strip()
        published_raw = (entry.findtext("atom:published", default="", namespaces=ATOM_NS) or "").strip()
        published_date = _parse_datetime(published_raw)

        author_names = []
        for author in entry.findall("atom:author", ATOM_NS):
            name = (author.findtext("atom:name", default="", namespaces=ATOM_NS) or "").strip()
            if name:
                author_names.append(name)

        if not title:
            continue

        papers.append(
            {
                "title": " ".join(title.split()),
                "abstract": " ".join(abstract.split()),
                "authors": ", ".join(author_names),
                "url": url,
                "source": "arxiv",
                "published_date": published_date,
            }
        )

    return papers
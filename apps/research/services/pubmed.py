import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
PUBMED_EFETCH_BATCH_SIZE = 100


def _safe_request(url: str, params: Dict[str, Any], timeout: int = 30) -> requests.Response:
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response


def _chunked(items: List[str], size: int) -> List[List[str]]:
    return [items[idx:idx + size] for idx in range(0, len(items), size)]


def search_pubmed_ids(query: Optional[str] = None, retmax: Optional[int] = None) -> List[str]:
    search_query = query or settings.PUBMED_QUERY
    max_results = retmax or settings.PUBMED_MAX_RESULTS

    params = {
        "db": "pubmed",
        "term": search_query,
        "retmode": "json",
        "retmax": max_results,
        "sort": "pub date",
        "email": settings.PUBMED_EMAIL,
    }

    try:
        response = _safe_request(PUBMED_ESEARCH_URL, params)
        data = response.json()
        return data.get("esearchresult", {}).get("idlist", [])
    except Exception as exc:
        logger.exception("PubMed esearch failed: %s", exc)
        return []


def _extract_text(element: Optional[ET.Element]) -> str:
    if element is None:
        return ""
    return "".join(element.itertext()).strip()


def _parse_pub_date(article_node: ET.Element) -> Optional[datetime]:
    pub_date = article_node.find(".//PubDate")
    if pub_date is None:
        return None

    year = _extract_text(pub_date.find("Year"))
    month = _extract_text(pub_date.find("Month"))
    day = _extract_text(pub_date.find("Day"))

    month_map = {
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
    }

    try:
        y = int(year) if year else 1970
        m = month_map.get(month, 1) if month else 1
        d = int(day) if day else 1
        return datetime(y, m, d)
    except Exception:
        return None


def fetch_pubmed_details(pubmed_ids: List[str]) -> List[Dict[str, Any]]:
    if not pubmed_ids:
        return []

    papers: List[Dict[str, Any]] = []

    for batch in _chunked(pubmed_ids, PUBMED_EFETCH_BATCH_SIZE):
        params = {
            "db": "pubmed",
            "id": ",".join(batch),
            "retmode": "xml",
            "email": settings.PUBMED_EMAIL,
        }

        try:
            response = _safe_request(PUBMED_EFETCH_URL, params, timeout=60)
            root = ET.fromstring(response.text)
        except Exception as exc:
            logger.exception("PubMed efetch failed for batch size=%s: %s", len(batch), exc)
            continue

        for article in root.findall(".//PubmedArticle"):
            article_node = article.find(".//Article")
            medline = article.find(".//MedlineCitation")
            pmid = _extract_text(medline.find("PMID")) if medline is not None else ""

            title = _extract_text(article_node.find("ArticleTitle")) if article_node is not None else ""
            abstract_parts = article_node.findall(".//Abstract/AbstractText") if article_node is not None else []
            abstract = "\n".join(_extract_text(x) for x in abstract_parts if _extract_text(x)).strip()

            author_nodes = article_node.findall(".//AuthorList/Author") if article_node is not None else []
            authors = []
            for author in author_nodes:
                last_name = _extract_text(author.find("LastName"))
                fore_name = _extract_text(author.find("ForeName"))
                collective_name = _extract_text(author.find("CollectiveName"))

                if collective_name:
                    authors.append(collective_name)
                elif last_name or fore_name:
                    authors.append(f"{fore_name} {last_name}".strip())

            published_date = _parse_pub_date(article_node) if article_node is not None else None
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""

            if not title:
                continue

            papers.append(
                {
                    "title": title,
                    "abstract": abstract,
                    "authors": ", ".join(authors),
                    "url": url,
                    "source": "pubmed",
                    "published_date": published_date,
                }
            )

    return papers


def fetch_pubmed_papers(query: Optional[str] = None, retmax: Optional[int] = None) -> List[Dict[str, Any]]:
    ids = search_pubmed_ids(query=query, retmax=retmax)
    return fetch_pubmed_details(ids)

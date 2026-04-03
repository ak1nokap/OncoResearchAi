from collections import defaultdict
from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.db.models import Count
from django.http import JsonResponse
from django.urls import reverse

from apps.research.models import Paper, SavedSearch
from apps.research.services.rag import answer_with_rag
from apps.research.services.review import generate_literature_review
from apps.research.services.semantic_search import semantic_search
from apps.research.tasks import ingest_all_sources

from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta

from .models import SavedPaper

from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect, get_object_or_404

def home(request):
    total_papers = Paper.objects.count()
    pubmed_count = Paper.objects.filter(source="pubmed").count()
    arxiv_count = Paper.objects.filter(source="arxiv").count()

    top_cancer_types = (
        Paper.objects.exclude(cancer_type__isnull=True)
        .exclude(cancer_type__exact="")
        .values("cancer_type")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )

    latest_papers = Paper.objects.order_by("-published_date", "-created_at")[:5]

    context = {
        "total_papers": total_papers,
        "pubmed_count": pubmed_count,
        "arxiv_count": arxiv_count,
        "top_cancer_types": top_cancer_types,
        "latest_papers": latest_papers,
    }
    return render(request, "overview.html", context)


def research_list(request):
    query = (request.GET.get("q") or "").strip()
    cancer_type = (request.GET.get("cancer_type") or "").strip()
    ai_method = (request.GET.get("ai_method") or "").strip()
    source = (request.GET.get("source") or "").strip()

    if query:
        papers = semantic_search(query)
    else:
        papers = Paper.objects.all().order_by("-published_date")

    if cancer_type:
        papers = papers.filter(cancer_type__icontains=cancer_type)

    if ai_method:
        papers = papers.filter(ai_method__icontains=ai_method)

    if source:
        papers = papers.filter(source=source)

    paginator = Paginator(papers, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    saved_paper_ids = set()
    if request.user.is_authenticated:
        current_page_paper_ids = [paper.id for paper in page_obj.object_list]
        saved_paper_ids = set(
            SavedPaper.objects.filter(
                user=request.user,
                paper_id__in=current_page_paper_ids
            ).values_list("paper_id", flat=True)
        )

    context = {
        "page_obj": page_obj,
        "query": query,
        "cancer_type": cancer_type,
        "ai_method": ai_method,
        "source": source,
        "total_count": papers.count(),
        "source_choices": Paper.SOURCE_CHOICES,
        "saved_paper_ids": saved_paper_ids,
    }
    return render(request, "research_list.html", context)


def dashboard(request):
    papers = Paper.objects.all()

    total_papers = papers.count()
    pubmed_count = papers.filter(source="pubmed").count()
    arxiv_count = papers.filter(source="arxiv").count()

    recent_30_days_count = papers.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).count()

    cancer_type_counts = list(
        papers.exclude(cancer_type__isnull=True)
        .exclude(cancer_type__exact="")
        .values("cancer_type")
        .annotate(count=Count("id"))
        .order_by("-count")[:8]
    )

    ai_method_counts = list(
        papers.exclude(ai_method__isnull=True)
        .exclude(ai_method__exact="")
        .values("ai_method")
        .annotate(count=Count("id"))
        .order_by("-count")[:8]
    )

    source_counts = list(
        papers.values("source")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    papers_by_month_map = defaultdict(int)
    for paper in papers:
        if paper.published_date:
            month_key = paper.published_date.strftime("%Y-%m")
            papers_by_month_map[month_key] += 1

    papers_by_month = [
        {"month": month, "count": papers_by_month_map[month]}
        for month in sorted(papers_by_month_map.keys())
    ]

    latest_papers = papers.order_by("-published_date", "-created_at")[:10]

    context = {
        "total_papers": total_papers,
        "pubmed_count": pubmed_count,
        "arxiv_count": arxiv_count,
        "recent_30_days_count": recent_30_days_count,
        "cancer_type_counts": cancer_type_counts,
        "ai_method_counts": ai_method_counts,
        "source_counts": source_counts,
        "papers_by_month": papers_by_month,
        "latest_papers": latest_papers,
    }
    return render(request, "dashboard.html", context)


def chat(request):
    query = (request.GET.get("q") or "").strip()
    mode = (request.GET.get("mode") or "answer").strip().lower()
    if mode not in {"answer", "review"}:
        mode = "answer"

    answer = None
    review = None
    papers = []

    if query:
        if mode == "review":
            result = generate_literature_review(query)
            review = result.get("review")
            papers = result.get("papers", [])
        else:
            result = answer_with_rag(query)
            answer = result.get("answer")
            papers = result.get("papers", [])

    context = {
        "question": query,
        "query": query,
        "mode": mode,
        "answer": answer,
        "review": review,
        "papers": papers,
    }
    return render(request, "chat.html", context)


def literature_review(request):
    query = (request.GET.get("q") or "").strip()
    params = {"mode": "review"}
    if query:
        params["q"] = query
    return redirect(f"{reverse('research:chat')}?{urlencode(params)}")


def api_search(request):
    query = (request.GET.get("q") or "").strip()
    cancer_type = (request.GET.get("cancer_type") or "").strip()
    ai_method = (request.GET.get("ai_method") or "").strip()
    source = (request.GET.get("source") or "").strip()

    papers = Paper.objects.all()

    if query:
        semantic_results = list(semantic_search(query))
        ids = [paper.id for paper in semantic_results]
        papers = Paper.objects.filter(id__in=ids) if ids else Paper.objects.none()

    if cancer_type:
        papers = papers.filter(cancer_type__icontains=cancer_type)

    if ai_method:
        papers = papers.filter(ai_method__icontains=ai_method)

    if source:
        papers = papers.filter(source=source)

    papers = papers.order_by("-published_date", "-created_at")[:20]

    data = [
        {
            "id": p.id,
            "title": p.title,
            "summary": p.summary,
            "authors": p.authors,
            "url": p.url,
            "source": p.source,
            "published_date": p.published_date.isoformat() if p.published_date else None,
            "cancer_type": p.cancer_type,
            "ai_method": p.ai_method,
        }
        for p in papers
    ]

    return JsonResponse({"results": data})


def api_chat(request):
    question = (request.GET.get("q") or "").strip()

    if not question:
        return JsonResponse({"error": "Parameter 'q' is required."}, status=400)

    result = answer_with_rag(question)

    return JsonResponse(
        {
            "question": question,
            "answer": result.get("answer"),
            "papers": [
                {
                    "id": p.id,
                    "title": p.title,
                    "url": p.url,
                    "source": p.source,
                    "published_date": p.published_date.isoformat() if p.published_date else None,
                }
                for p in result.get("papers", [])
            ],
        }
    )


def trigger_ingestion(request):
    if request.method == "POST":
        ingest_all_sources.delay()
        return JsonResponse({"status": "started"})

    return JsonResponse({"error": "POST method required"}, status=405)



def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()

    return render(request, "registration/register.html", {"form": form})

@login_required
def save_search(request):
    if request.method == "POST":
        SavedSearch.objects.create(
            user=request.user,
            query=request.POST.get("query", ""),
            cancer_type=request.POST.get("cancer_type", ""),
            ai_method=request.POST.get("ai_method", ""),
        )
    return redirect("research:paper_list")


@login_required
def save_paper(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id)

    SavedPaper.objects.get_or_create(
        user=request.user,
        paper=paper
    )

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "research:paper_list"
    return redirect(next_url)


@login_required
def remove_saved_paper(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id)

    SavedPaper.objects.filter(
        user=request.user,
        paper=paper
    ).delete()

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "research:saved_papers"
    return redirect(next_url)


@login_required
def saved_papers(request):
    saved_items = (
        SavedPaper.objects
        .filter(user=request.user)
        .select_related("paper")
        .order_by("-created_at")
    )

    context = {
        "saved_items": saved_items,
    }
    return render(request, "saved_papers.html", context)

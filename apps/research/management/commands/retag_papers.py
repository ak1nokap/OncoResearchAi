from django.core.management.base import BaseCommand

from apps.research.models import Paper
from apps.research.services.summarizer import summarize_paper


class Command(BaseCommand):
    help = "Re-tag existing papers with improved summary, cancer_type, and ai_method"

    def handle(self, *args, **options):
        papers = Paper.objects.all().order_by("id")
        updated = 0

        for paper in papers:
            title = paper.title or ""
            abstract = paper.abstract or ""

            if not title and not abstract:
                continue

            result = summarize_paper(title=title, abstract=abstract)

            paper.summary = result.get("summary", "") or ""
            paper.cancer_type = result.get("cancer_type", "unknown") or "unknown"
            paper.ai_method = result.get("ai_method", "unknown") or "unknown"
            paper.save(update_fields=["summary", "cancer_type", "ai_method"])

            updated += 1
            self.stdout.write(f"Updated: {paper.id} - {paper.title[:80]}")

        self.stdout.write(self.style.SUCCESS(f"Done. Updated {updated} papers."))
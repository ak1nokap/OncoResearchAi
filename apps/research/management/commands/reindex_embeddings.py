from django.core.management.base import BaseCommand

from apps.research.models import Paper
from apps.research.services.embeddings import create_embedding
from apps.research.services.semantic_search import build_search_text


class Command(BaseCommand):
    help = "Generate embeddings for papers that do not have them yet"

    def handle(self, *args, **options):
        papers = Paper.objects.filter(embedding__isnull=True)

        updated = 0

        for paper in papers:
            text = build_search_text(paper)
            embedding = create_embedding(text)

            if embedding is not None:
                paper.embedding = embedding
                paper.save(update_fields=["embedding"])
                updated += 1
                self.stdout.write(f"Indexed: {paper.id} - {paper.title[:80]}")

        self.stdout.write(self.style.SUCCESS(f"Done. Updated {updated} papers."))
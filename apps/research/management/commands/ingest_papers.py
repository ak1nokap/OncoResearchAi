from django.core.management.base import BaseCommand

from apps.research.tasks import ingest_all_sources


class Command(BaseCommand):
    help = "Ingest papers from PubMed and arXiv"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Starting ingestion..."))
        result = ingest_all_sources()
        self.stdout.write(self.style.SUCCESS(f"Done: {result}"))
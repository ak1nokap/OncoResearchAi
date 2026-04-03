from django.conf import settings
from django.contrib.syndication.views import Feed

from apps.research.models import Paper


class ResearchFeed(Feed):
    title = getattr(settings, "RSS_TITLE", "AI Cancer Research Feed")
    description = getattr(
        settings,
        "RSS_DESCRIPTION",
        "Latest scientific papers on AI for cancer diagnostics",
    )
    link = getattr(settings, "RSS_LINK", "/rss/")

    def items(self):
        return Paper.objects.order_by("-published_date", "-created_at")[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        parts = []

        if item.summary:
            parts.append(item.summary)

        metadata = []
        if item.cancer_type:
            metadata.append(f"Cancer type: {item.cancer_type}")
        if item.ai_method:
            metadata.append(f"AI method: {item.ai_method}")
        if item.source:
            metadata.append(f"Source: {item.source}")

        if metadata:
            parts.append(" | ".join(metadata))

        return "\n\n".join(parts)

    def item_link(self, item):
        return item.url

    def item_pubdate(self, item):
        return item.published_date
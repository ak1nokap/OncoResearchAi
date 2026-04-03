from django.contrib import admin

from apps.research.models import Paper, SavedPaper



@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    list_display = (
        "short_title",
        "source",
        "cancer_type",
        "ai_method",
        "published_date",
        "created_at",
    )
    list_filter = ("source", "cancer_type", "ai_method")
    search_fields = ("title", "abstract", "summary", "authors", "cancer_type", "ai_method")
    readonly_fields = ("created_at",)
    ordering = ("-published_date", "-created_at")

    def short_title(self, obj):
        return obj.title[:80] + ("..." if len(obj.title) > 80 else "")

    short_title.short_description = "Title"

@admin.register(SavedPaper)
class SavedPaperAdmin(admin.ModelAdmin):
    list_display = ("user", "paper", "created_at")
    search_fields = ("user__username", "paper__title")
    ordering = ("-created_at",)
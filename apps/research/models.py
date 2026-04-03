from django.db import models
from django.contrib.auth.models import User
from pgvector.django import VectorField



class Paper(models.Model):
    SOURCE_CHOICES = [
        ("pubmed", "PubMed"),
        ("arxiv", "arXiv"),
    ]

    title = models.CharField(max_length=1000)
    abstract = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    authors = models.TextField(blank=True)
    url = models.URLField(unique=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    published_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    cancer_type = models.CharField(max_length=255, blank=True, default="unknown")
    ai_method = models.CharField(max_length=255, blank=True, default="unknown")

    embedding = VectorField(dimensions=384, null=True, blank=True)

    class Meta:
        ordering = ["-published_date"]

    def __str__(self):
        return self.title

class SavedPaper(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_papers")
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name="saved_by_users")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "paper")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} saved {self.paper.title[:60]}"

class SavedSearch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.CharField(max_length=500)
    cancer_type = models.CharField(max_length=255, blank=True)
    ai_method = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.query}"

class Alert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    search = models.ForeignKey(SavedSearch, on_delete=models.CASCADE)
    frequency = models.CharField(
        max_length=20,
        choices=[("daily", "Daily"), ("weekly", "Weekly")],
        default="daily"
    )
    last_sent = models.DateTimeField(null=True, blank=True)
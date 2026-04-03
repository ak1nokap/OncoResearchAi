from django.contrib import admin
from django.urls import include, path

from apps.research.feeds import ResearchFeed

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("apps.research.urls")),
    path("rss/", ResearchFeed(), name="rss_feed"),
]


from django.urls import path
from . import views

app_name = "research"

urlpatterns = [
    path("", views.home, name="home"),
    path("papers/", views.research_list, name="paper_list"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("chat/", views.chat, name="chat"),
    path("review/", views.literature_review, name="literature_review"),
    path("api/search/", views.api_search, name="api_search"),
    path("api/chat/", views.api_chat, name="api_chat"),
    path("api/ingest/", views.trigger_ingestion, name="trigger_ingestion"),
    path("save-search/", views.save_search, name="save_search"),
    path("register/", views.register, name="register"),
    path("saved-papers/", views.saved_papers, name="saved_papers"),
    path("papers/<int:paper_id>/save/", views.save_paper, name="save_paper"),
    path("papers/<int:paper_id>/remove/", views.remove_saved_paper, name="remove_saved_paper"),
]

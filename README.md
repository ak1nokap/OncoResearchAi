# OncoResearch AI

OncoResearch AI is a Django-based research portal for exploring scientific literature on AI in cancer diagnostics. It aggregates papers from PubMed and arXiv, enriches them with AI-generated summaries and metadata, supports semantic search, and provides an AI workspace for evidence-grounded Q&A and mini literature reviews.

## Features

- Aggregate research papers from PubMed and arXiv
- Store papers in PostgreSQL
- Generate AI summaries, cancer type tags, and AI method tags
- Run semantic search with embeddings and pgvector
- Browse and filter papers by query, source, cancer type, and AI method
- Save papers and saved searches for authenticated users
- Use the AI Workspace for:
  - evidence-grounded answers from retrieved papers
  - structured mini literature reviews
- View analytics dashboards for publication trends and metadata breakdowns
- Expose an RSS feed of recent papers
- Run scheduled ingestion with Celery and Redis

## Tech Stack

- Python 3.13
- Django 5
- PostgreSQL
- pgvector
- Redis
- Celery + django-celery-beat
- OpenAI API
- sentence-transformers
- Chart.js
- WhiteNoise

## Project Structure

```text
.
├── apps/
│   └── research/
│       ├── management/commands/
│       ├── services/
│       ├── tasks.py
│       ├── urls.py
│       └── views.py
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── celery.py
├── templates/
├── manage.py
└── requirements.txt
```

## Main Modules

- `apps/research/services/pubmed.py`
  Fetches paper identifiers and details from PubMed.

- `apps/research/services/arxiv.py`
  Fetches recent relevant papers from arXiv.

- `apps/research/services/summarizer.py`
  Uses OpenAI to produce structured summaries and metadata.

- `apps/research/services/semantic_search.py`
  Embedding-based search over stored papers.

- `apps/research/services/rag.py`
  Generates evidence-grounded answers for the AI Workspace.

- `apps/research/services/review.py`
  Generates structured mini literature reviews from top retrieved papers.

- `apps/research/tasks.py`
  Background ingestion and enrichment pipeline.

## Requirements

Before you start, make sure you have:

- Python 3.13
- PostgreSQL
- Redis
- An OpenAI API key
- Optional but recommended: a Python virtual environment

## Installation

1. Clone the repository:

```bash
git clone https://github.com/ak1nokap/OncoResearchAi.git
cd OncoResearchAi
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root.

Example:

```env
DJANGO_SECRET_KEY=change-me
DEBUG=True

POSTGRES_DB=cancer_research
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost

REDIS_HOST=localhost

OPENAI_API_KEY=sk-...
PUBMED_EMAIL=you@example.com
```

## Database Setup

1. Create the PostgreSQL database.
2. Make sure the `pgvector` extension is available in your PostgreSQL instance.
3. Run migrations:

```bash
python manage.py migrate
```

4. Create an admin user:

```bash
python manage.py createsuperuser
```

## Running the Project Locally

Start the Django server:

```bash
python manage.py runserver
```

Open:

- `http://127.0.0.1:8000/`

## Background Services

This project uses Redis and Celery for background ingestion and scheduled tasks.

Start a Celery worker:

```bash
celery -A config worker -l info
```

Start Celery Beat:

```bash
celery -A config beat -l info
```

## Ingesting Papers

Run the combined ingestion command:

```bash
python manage.py ingest_papers
```

This will:

- fetch papers from PubMed
- fetch papers from arXiv
- generate summaries and metadata
- create embeddings where possible
- store new papers in the database

## Maintenance Commands

Rebuild embeddings for existing papers:

```bash
python manage.py reindex_embeddings
```

Re-generate summaries and tags:

```bash
python manage.py retag_papers
```

## AI Workspace

The AI Workspace supports two modes:

- `Ask AI`
  Returns a short evidence-grounded answer based on the most relevant retrieved papers.

- `Literature Review`
  Produces a structured mini literature review with:
  - Overview
  - Methods and approaches
  - Findings
  - Limitations and gaps

The review is generated only from papers retrieved from the local database.

## Search and Retrieval

Semantic search is based on:

- `sentence-transformers/all-MiniLM-L6-v2`
- vector similarity with `pgvector`

If vector retrieval is unavailable, the system falls back to text matching over titles, abstracts, summaries, cancer types, and AI methods.

## Analytics

The analytics dashboard includes:

- total paper counts
- source distribution
- papers added recently
- top cancer types
- top AI methods
- publication trends over time

## Authentication

The project uses Django’s built-in authentication system.

Authenticated users can:

- save papers
- save searches
- access their personal saved papers page

## RSS Feed

Recent papers are available through the RSS feed:

- `/rss/`

## Production Notes

For production deployment, it is recommended to use:

- Gunicorn
- Nginx
- PostgreSQL
- Redis
- Docker Compose
- HTTPS with Let’s Encrypt

Important production tasks:

- set `DEBUG=False`
- configure `ALLOWED_HOSTS`
- use environment variables for secrets
- enable HTTPS
- run `python manage.py collectstatic`
- run `python manage.py check --deploy`

## Suggested `.gitignore`

```gitignore
.venv/
__pycache__/
*.pyc
.env
.env.*
staticfiles/
media/
.idea/
```

## Known Considerations

- OpenAI-dependent features require a valid API key and available quota.
- Large paper ingestion can be slow because enrichment and embedding generation are compute-heavy.
- Semantic search quality depends on embedding coverage for stored papers.
- Scheduled tasks require both Redis and Celery services to be running.

## Roadmap Ideas

- Save generated literature reviews in the database
- Export reviews to PDF or DOCX
- Add inline source citation highlighting
- Add side-by-side topic comparison
- Improve deployment with Docker and production configs

## Contact Me
- email: akmushan@gmail.com
- TG: @akinokap
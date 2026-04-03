import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-secret-key")

DEBUG = os.getenv("DEBUG", "False") == "True"


def _split_env_list(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


ALLOWED_HOSTS = _split_env_list(os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1"))
CSRF_TRUSTED_ORIGINS = _split_env_list(os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", ""))

# --------------------------------------------------
# INSTALLED APPS
# --------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "django_celery_beat",
    "rest_framework",

    "apps.research",
]

# --------------------------------------------------
# MIDDLEWARE
# --------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",

                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# --------------------------------------------------
# DATABASE (PostgreSQL + pgvector)
# --------------------------------------------------


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "cancer_research"),
        "USER": os.getenv("POSTGRES_USER", "postgres"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": int(os.getenv("POSTGRES_PORT", "5432")),
    }
}

# --------------------------------------------------
# PGVECTOR
# --------------------------------------------------

PGVECTOR_EMBEDDING_DIM = 1536

# --------------------------------------------------
# PASSWORD VALIDATION
# --------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

# --------------------------------------------------
# INTERNATIONALIZATION
# --------------------------------------------------

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# --------------------------------------------------
# STATIC FILES
# --------------------------------------------------

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# --------------------------------------------------
# MEDIA FILES
# --------------------------------------------------

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --------------------------------------------------
# DEFAULT PK
# --------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------
# REDIS
# --------------------------------------------------

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# --------------------------------------------------
# CELERY CONFIG
# --------------------------------------------------

CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"

CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# --------------------------------------------------
# PERIODIC TASKS
# --------------------------------------------------

CELERY_BEAT_SCHEDULE = {
    "ingest-pubmed-daily": {
        "task": "apps.research.tasks.ingest_pubmed_papers",
        "schedule": 86400,
    },

    "ingest-arxiv-daily": {
        "task": "apps.research.tasks.ingest_arxiv_papers",
        "schedule": 86400,
    }
}

# --------------------------------------------------
# OPENAI
# --------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

OPENAI_MODEL_SUMMARY = "gpt-4o-mini"
OPENAI_MODEL_CHAT = "gpt-4o-mini"

OPENAI_MODEL_EMBEDDING = "text-embedding-3-small"

# --------------------------------------------------
# RAG CONFIG
# --------------------------------------------------

RAG_TOP_K = 5

MAX_PAPER_CONTEXT = 3000

# --------------------------------------------------
# SEMANTIC SEARCH
# --------------------------------------------------

EMBEDDING_MODEL = "text-embedding-3-small"

SEMANTIC_SEARCH_RESULTS = 10
LITERATURE_REVIEW_TOP_K = 6
MAX_REVIEW_CONTEXT_CHARS = 12000

# --------------------------------------------------
# PUBMED CONFIG
# --------------------------------------------------

PUBMED_EMAIL = os.getenv("PUBMED_EMAIL", "research@example.com")

PUBMED_QUERY = """
cancer diagnosis AI
OR cancer detection deep learning
OR oncology machine learning
OR tumor classification neural network
OR medical imaging cancer AI
OR histopathology cancer deep learning
OR radiology cancer machine learning
"""

PUBMED_MAX_RESULTS = 200

# --------------------------------------------------
# ARXIV CONFIG
# --------------------------------------------------

ARXIV_QUERY = """
(cat:q-bio.QM OR cat:cs.AI OR cat:cs.CV OR cat:eess.IV)
AND (cancer OR tumor OR oncology OR histopathology OR radiology)
"""

ARXIV_MAX_RESULTS = 500

# --------------------------------------------------
# RSS FEEDS
# --------------------------------------------------

RSS_TITLE = "AI Cancer Research Feed"

RSS_DESCRIPTION = "Latest AI-powered cancer research papers"

RSS_LINK = "/rss/"

# --------------------------------------------------
# REST FRAMEWORK
# --------------------------------------------------

REST_FRAMEWORK = {

    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny"
    ],

    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

# --------------------------------------------------
# LOGGING
# --------------------------------------------------

LOGGING = {

    "version": 1,

    "disable_existing_loggers": False,

    "handlers": {

        "console": {
            "class": "logging.StreamHandler",
        },

    },

    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },

}


LOGIN_REDIRECT_URL = "research:home"
LOGOUT_REDIRECT_URL = "research:home"


# --------------------------------------------------
# SECURITY / PROXY
# --------------------------------------------------

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False") == "True"
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "False") == "True"
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "False") == "True"

SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "False") == "True"
SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "False") == "True"

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"

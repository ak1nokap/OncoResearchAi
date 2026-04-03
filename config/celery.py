import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")

    from django.core.mail import send_mail
    from django.utils import timezone
    from apps.research.models import Alert, Paper

    def run_alerts():
        alerts = Alert.objects.all()

        for alert in alerts:
            papers = Paper.objects.filter(
                title__icontains=alert.search.query
            )[:5]

            if papers:
                message = "\n".join([p.title for p in papers])

                send_mail(
                    "New research papers",
                    message,
                    "from@example.com",
                    [alert.user.email],
                )

                alert.last_sent = timezone.now()
                alert.save()

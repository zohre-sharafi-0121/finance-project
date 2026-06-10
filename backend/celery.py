import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

app = Celery("backend")  # ← change "your_project" to your actual project name

# Pull config from Django settings, using the CELERY_ namespace
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()


# ─── Periodic Tasks (Celery Beat) ────────────────────────────────────────────
# This runs a daily digest notification for all users every morning at 8 AM.
# Shows off Celery Beat scheduling — a strong portfolio signal.
app.conf.beat_schedule = {
    "daily-summary-digest": {
        "task": "core.tasks.send_daily_summary_digest",
        "schedule": crontab(hour=8, minute=0),  # Every day at 08:00
    },
}
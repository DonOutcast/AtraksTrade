import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel.settings')

app = Celery('kernel')
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


app.conf.beat_schedule = {
    "update-rossvyaz-every-hour": {
        "task": "app.tasks.update_rossvyaz_task",
        "schedule": crontab(minute="*/1"),
    },
}

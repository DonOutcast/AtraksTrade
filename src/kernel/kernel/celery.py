import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel.settings')

app = Celery('kernel')

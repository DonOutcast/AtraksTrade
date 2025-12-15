from celery import shared_task
import logging

from .services import update_info

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=60, retry_kwargs={"max_retries": 3})
def update_rossvyaz_task(self):
    logger.info("Starting Rossvyaz update task")
    # update_info()
    logger.info("Rossvyaz update finished")

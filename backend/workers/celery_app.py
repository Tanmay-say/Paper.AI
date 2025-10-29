from celery import Celery
from config import settings
import logging

logger = logging.getLogger(__name__)

celery_app = Celery(
    'paperai_worker',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['workers.ingestion_tasks']  # Include task modules
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)
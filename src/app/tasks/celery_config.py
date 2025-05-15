# File src/app/tasks/celery_config.py
from celery import Celery
from src.app.core.config import settings

# Create a Celery instance using Redis as broker and backend
celery = Celery(
    "quiz_worker",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/1",  # Use a different DB index for backend
    include=["src.app.tasks.queue_task"],
)

celery.conf.update(
    task_routes={
        "queue_task.send_verification_email": {"queue": settings.REDIS_QUEUE_EMAIL},
        "queue_task.send_forgot_email_task": {"queue": settings.REDIS_QUEUE_EMAIL},
        "queue_task.send_custom_email_task": {"queue": settings.REDIS_QUEUE_EMAIL},
    },
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=300,
    task_soft_time_limit=200,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone="UTC",
    enable_utc=True,
)

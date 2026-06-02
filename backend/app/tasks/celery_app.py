from celery import Celery

from app.config import settings

celery_app = Celery("agribud", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_routes = {"app.tasks.analytics_tasks.*": {"queue": "default"}}

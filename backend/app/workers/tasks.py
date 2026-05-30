from app.workers.celery_app import celery_app


@celery_app.task(name='app.workers.tasks.refresh_geospatial_snapshots')
def refresh_geospatial_snapshots() -> str:
    return 'scheduled_refresh_placeholder'

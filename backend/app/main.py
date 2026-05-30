from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import admin, analytics, auth, copilot, farms
from app.core.config import settings
from app.core.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.allowed_origins.split(',')],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(auth.router, prefix='/api/v1')
app.include_router(farms.router, prefix='/api/v1')
app.include_router(analytics.router, prefix='/api/v1')
app.include_router(copilot.router, prefix='/api/v1')
app.include_router(admin.router, prefix='/api/v1')


@app.get('/health')
def health_check():
    return {'status': 'ok'}

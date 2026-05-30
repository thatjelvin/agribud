# Deployment Guide

## Local
1. Copy env templates:
   - `cp .env.example .env`
   - `cp backend/.env.example backend/.env`
   - `cp frontend/.env.example frontend/.env.local`
2. Start services:
   - `docker compose up --build`
3. Access:
   - Frontend: `http://localhost:3000`
   - API: `http://localhost:8000/docs`

## Production Notes
- Deploy backend and frontend containers behind an API gateway/reverse proxy.
- Use managed PostgreSQL with PostGIS, managed Redis, and S3-compatible object storage.
- Set secure JWT secret and environment-specific CORS allow list.
- Run Celery worker as separate deployment.
- Enable observability (metrics/log tracing) and secret management in your cloud platform.

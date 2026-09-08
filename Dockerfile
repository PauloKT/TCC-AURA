# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependências de sistema (build-essential para algumas wheels; libpq para Postgres opcional).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Garante que collectstatic rode durante o build.
RUN cd backend && SECRET_KEY=build-key DEBUG=False python manage.py collectstatic --noinput || true

EXPOSE 8000

# Roda com gunicorn em produção. Para dev, use docker-compose override.
CMD ["sh", "-c", "cd backend && gunicorn backend.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 60"]

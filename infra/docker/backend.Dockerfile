FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend:/app/optimizer

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY pyproject.toml /app/pyproject.toml
COPY optimizer /app/optimizer
COPY backend /app/backend

WORKDIR /app/backend

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


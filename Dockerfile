FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source code
COPY backend/ /app/

# Pre-build Chroma vector index (optional at build-time; app auto-initializes on startup if empty)
RUN python -m pipeline.index_corpus || true

EXPOSE 8000

# Run uvicorn respecting PORT environment variable for Render / Cloud Run / Railway
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

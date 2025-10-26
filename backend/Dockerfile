# Backend Dockerfile for FastAPI app
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY backend/ /app/

# Expose port
EXPOSE 8000

# Run as non-root
RUN useradd --create-home appuser || true
USER appuser

CMD ["uvicorn", "backend.server_gashis:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]

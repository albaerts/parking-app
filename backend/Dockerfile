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

# Copy application code into a package folder so imports like `backend.server_gashis` work
RUN mkdir -p /app/backend
COPY backend/ /app/backend/

# Ensure the appuser will own the backend files so runtime writes (sqlite journals etc.) succeed
RUN chown -R appuser:appuser /app/backend || true

# Expose port
EXPOSE 8000

# Run as non-root
RUN useradd --create-home appuser || true
USER appuser

CMD ["uvicorn", "backend.server_gashis:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]

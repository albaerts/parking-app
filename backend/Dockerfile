# Backend Dockerfile for FastAPI app
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       git \
       libffi-dev \
       python3-dev \
       libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt \
    && pip install --no-cache-dir bcrypt || echo "[WARN] bcrypt extra install failed – passlib fallback active"

# Copy application code into a package folder so imports like `backend.server_gashis` work
RUN mkdir -p /app/backend
COPY backend/ /app/backend/

# Accept commit SHA build arg to expose version info inside the container
ARG COMMIT_SHA=unknown
ENV BACKEND_COMMIT_SHA=${COMMIT_SHA}
# Write version file after code copy so the path exists
RUN echo "${COMMIT_SHA}" > /app/backend/version.txt || true

# Run as non-root and ensure proper ownership for runtime writes (e.g. sqlite journals)
RUN useradd --create-home appuser
RUN chown -R appuser:appuser /app/backend

# Expose port
EXPOSE 8000

USER appuser

CMD ["uvicorn", "backend.server_gashis:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]

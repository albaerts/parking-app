#!/usr/bin/env bash
set -euo pipefail

# Simple deploy helper: pulls images and recreates the compose stack
# Usage: ./deploy/update.sh <IMAGE_TAG>

IMAGE_TAG=${1:-latest}
COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.prod.yml}

echo "Deploying images with tag: ${IMAGE_TAG} using compose file ${COMPOSE_FILE}"

# Export variables so docker-compose file can use them
export IMAGE_TAG
export REPO_OWNER=${REPO_OWNER:-yourorg}
export REGISTRY=${REGISTRY:-ghcr.io}

# Pull images
echo "Pulling backend image: ${REGISTRY}/${REPO_OWNER}/parking-backend:${IMAGE_TAG}"
docker pull ${REGISTRY}/${REPO_OWNER}/parking-backend:${IMAGE_TAG}

		# Backup DB before pulling new images
		if [ -x ./deploy/backup_db.sh ]; then
			echo "Backing up database before deploy..."
			./deploy/backup_db.sh ./deploy/backups || echo "Backup script failed, continuing deploy"
		else
			echo "No backup script found at ./deploy/backup_db.sh - skipping DB backup"
		fi

echo "Pulling frontend image: ${REGISTRY}/${REPO_OWNER}/parking-frontend:${IMAGE_TAG}"
docker pull ${REGISTRY}/${REPO_OWNER}/parking-frontend:${IMAGE_TAG}

# Recreate stack
docker-compose -f ${COMPOSE_FILE} up -d --remove-orphans --force-recreate

echo "Deploy finished."

# After deploy: run healthcheck
if [ -x ./deploy/check_health.sh ]; then
	echo "Running post-deploy health check..."
	if ./deploy/check_health.sh "http://127.0.0.1:8000/health" 15 2; then
		echo "Health check passed"
	else
		echo "Health check FAILED. Please check logs and consider rollback." >&2
		exit 2
	fi
else
	echo "No health check script found at ./deploy/check_health.sh - skipping health check"
fi

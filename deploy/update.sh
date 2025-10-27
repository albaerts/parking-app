#!/usr/bin/env bash
set -euo pipefail

# Simple deploy helper: pulls images and recreates the compose stack
# Usage: ./deploy/update.sh <IMAGE_TAG>

IMAGE_TAG=${1:-latest}
COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.prod.yml}

echo "Deploying images with tag: ${IMAGE_TAG} using compose file ${COMPOSE_FILE}"

# Export variables so docker-compose file can use them
export IMAGE_TAG
# default to your GitHub owner to make local deploys simpler
export REPO_OWNER=${REPO_OWNER:-albaerts}
export REGISTRY=${REGISTRY:-ghcr.io}

# Make helper scripts executable if present (helps when git doesn't preserve mode)
chmod +x ./deploy/*.sh >/dev/null 2>&1 || true

# Pull images
echo "Pulling backend image: ${REGISTRY}/${REPO_OWNER}/parking-backend:${IMAGE_TAG}"
docker pull ${REGISTRY}/${REPO_OWNER}/parking-backend:${IMAGE_TAG}

		# Backup DB before pulling new images
		if [ -x ./deploy/backup_db_fixed.sh ]; then
			echo "Backing up database before deploy (deploy/backup_db_fixed.sh)..."
			./deploy/backup_db_fixed.sh ./deploy/backups || echo "Backup script failed, continuing deploy"
		elif [ -x ./deploy/backup_db.sh ]; then
			echo "Backing up database before deploy (deploy/backup_db.sh)..."
			./deploy/backup_db.sh ./deploy/backups || echo "Backup script failed, continuing deploy"
		else
			echo "No backup script found at ./deploy/backup_db*.sh - skipping DB backup"
		fi

echo "Pulling frontend image: ${REGISTRY}/${REPO_OWNER}/parking-frontend:${IMAGE_TAG}"
docker pull ${REGISTRY}/${REPO_OWNER}/parking-frontend:${IMAGE_TAG}

# Ensure any previous stack is stopped/removed to avoid container rename conflicts
echo "Stopping any existing compose stack (safe): docker-compose -f ${COMPOSE_FILE} down --remove-orphans || true"
docker-compose -f ${COMPOSE_FILE} down --remove-orphans || true

# Compose creates a default network named <project>_default when no explicit
# network name is provided. In some environments duplicate networks with the
# same name can accumulate and make docker-compose fail with "network ... is
# ambiguous". Detect and remove duplicate networks for the current project
# before attempting to bring the stack up.
PROJECT_NAME=${COMPOSE_PROJECT_NAME:-$(basename "$(pwd)")}
NETWORK_NAME="${PROJECT_NAME}_default"
echo "Checking for duplicate networks named: ${NETWORK_NAME}"
net_ids=$(docker network ls --filter name="${NETWORK_NAME}" -q || true)
if [ -n "${net_ids}" ]; then
	# Count matching ids
	count=0
	for id in ${net_ids}; do
		count=$((count+1))
	done
	if [ "${count}" -gt 1 ]; then
		echo "Found ${count} networks named ${NETWORK_NAME} - removing duplicates"
		for id in ${net_ids}; do
			echo "Removing network id: ${id}"
			docker network rm "${id}" || true
		done
		echo "Duplicate networks removed"
	else
		echo "No duplicate networks found (count=${count})"
	fi
fi

# Recreate stack (with a safe retry if a rename/conflict error occurs)
echo "Starting compose stack: docker-compose -f ${COMPOSE_FILE} up -d --remove-orphans --force-recreate"
if docker-compose -f ${COMPOSE_FILE} up -d --remove-orphans --force-recreate; then
	echo "Compose up succeeded"
else
	echo "docker-compose up failed — attempting to resolve potential name conflicts by removing containers matching service names"
	# Attempt to remove containers that contain the service name (aggressive but useful for stale containers)
	for svc in $(docker-compose -f ${COMPOSE_FILE} config --services 2>/dev/null || true); do
		if [ -z "${svc}" ]; then
			continue
		fi
		echo "Checking for containers matching service name: ${svc}"
		ids=$(docker ps -a --filter "name=${svc}" -q || true)
		if [ -n "${ids}" ]; then
			echo "Removing containers for service ${svc}: ${ids}"
			docker rm -f ${ids} || true
		fi
	done

	echo "Retrying docker-compose up once more"
	if docker-compose -f ${COMPOSE_FILE} up -d --remove-orphans --force-recreate; then
		echo "Compose up succeeded on retry"
	else
		echo "Compose up still failed after retry. Showing docker ps -a for diagnostics:" >&2
		docker ps -a || true
		echo "Exiting with error (compose failed)" >&2
		exit 1
	fi
fi

echo "Deploy finished."

# After deploy: run healthcheck
if [ -x ./deploy/check_health_fixed.sh ]; then
	echo "Running post-deploy health check (deploy/check_health_fixed.sh)..."
	if ./deploy/check_health_fixed.sh "http://127.0.0.1:8000/health" 15 2; then
		echo "Health check passed"
	else
		echo "Health check FAILED. Please check logs and consider rollback." >&2
		exit 2
	fi
elif [ -x ./deploy/check_health.sh ]; then
	echo "Running post-deploy health check (deploy/check_health.sh)..."
	if ./deploy/check_health.sh "http://127.0.0.1:8000/health" 15 2; then
		echo "Health check passed"
	else
		echo "Health check FAILED. Please check logs and consider rollback." >&2
		exit 2
	fi
else
	echo "No health check script found - skipping health check"
fi

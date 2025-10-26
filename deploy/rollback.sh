#!/usr/bin/env bash
set -euo pipefail

# rollback.sh <IMAGE_TAG>
# Rolls back the stack to the provided IMAGE_TAG by pulling images and recreating compose

IMAGE_TAG=${1:?"Usage: $0 <IMAGE_TAG>"}
COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.prod.yml}

REPO_OWNER=${REPO_OWNER:-yourorg}
REGISTRY=${REGISTRY:-ghcr.io}

echo "Rolling back to tag: ${IMAGE_TAG}"
echo "Pulling backend image ${REGISTRY}/${REPO_OWNER}/parking-backend:${IMAGE_TAG}"
docker pull ${REGISTRY}/${REPO_OWNER}/parking-backend:${IMAGE_TAG}
echo "Pulling frontend image ${REGISTRY}/${REPO_OWNER}/parking-frontend:${IMAGE_TAG}"
docker pull ${REGISTRY}/${REPO_OWNER}/parking-frontend:${IMAGE_TAG}

echo "Recreating compose stack with tag ${IMAGE_TAG}"
export IMAGE_TAG
export REPO_OWNER
export REGISTRY
docker-compose -f ${COMPOSE_FILE} up -d --remove-orphans --force-recreate

echo "Rollback complete." 

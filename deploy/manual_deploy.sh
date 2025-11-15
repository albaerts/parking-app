#!/usr/bin/env bash
# One-command manual deploy: build & push images to GHCR, then SSH to server and run deploy/update.sh
# Usage: env $(cat deploy/.env.deploy | xargs) ./deploy/manual_deploy.sh
# or export variables in your shell and run: ./deploy/manual_deploy.sh

set -euo pipefail

# -------- Config (can be provided via environment or deploy/.env.deploy) --------
REGISTRY=${REGISTRY:-ghcr.io}
REPO_OWNER=${REPO_OWNER:-albaerts}
# Image tag defaults to current commit SHA, falls back to epoch timestamp
IMAGE_TAG=${IMAGE_TAG:-$(git rev-parse --short=12 HEAD 2>/dev/null || date +%s)}

SSH_HOST=${SSH_HOST:-}
SSH_USER=${SSH_USER:-deploy}
SSH_PORT=${SSH_PORT:-22}
REMOTE_PATH=${REMOTE_PATH:-/var/www/parkingsrv}
PUBLIC_URL=${PUBLIC_URL:-https://parking.gashis.ch/}

# Optional: if images are private
GHCR_TOKEN=${GHCR_TOKEN:-}
GHCR_USER=${GHCR_USER:-${REPO_OWNER}}

# Optional: clone repo on remote if REMOTE_PATH not a git repo
GIT_CLONE_URL=${GIT_CLONE_URL:-}

# Optional: local environment file to upload and source on remote before compose
LOCAL_ENV_FILE=${LOCAL_ENV_FILE:-.env.prod}
REMOTE_ENV_FILE=${REMOTE_ENV_FILE:-.env.prod}

# -------- Validation --------
if [ -z "${SSH_HOST}" ]; then
  echo "Error: SSH_HOST not set" >&2
  exit 2
fi

# -------- Login to GHCR (optional) --------
if [ -n "${GHCR_TOKEN}" ]; then
  echo "Logging into ${REGISTRY} as ${GHCR_USER}"
  echo "${GHCR_TOKEN}" | docker login ${REGISTRY} -u "${GHCR_USER}" --password-stdin
else
  echo "No GHCR_TOKEN provided — attempting unauthenticated push (public repo required)"
fi

# -------- Build & push images --------
BACKEND_IMAGE="${REGISTRY}/${REPO_OWNER}/parking-backend:${IMAGE_TAG}"
FRONTEND_IMAGE="${REGISTRY}/${REPO_OWNER}/parking-frontend:${IMAGE_TAG}"

echo "Building backend image: ${BACKEND_IMAGE}"
docker build -f backend/Dockerfile -t "${BACKEND_IMAGE}" .

echo "Pushing backend image: ${BACKEND_IMAGE}"
docker push "${BACKEND_IMAGE}"

echo "Building frontend image: ${FRONTEND_IMAGE}"
docker build -f frontend/Dockerfile -t "${FRONTEND_IMAGE}" .

echo "Pushing frontend image: ${FRONTEND_IMAGE}"
docker push "${FRONTEND_IMAGE}"

# -------- Prepare remote path and repo --------
SSH_CMD=(ssh -p "$SSH_PORT" "$SSH_USER@$SSH_HOST")
SCP_CMD=(scp -P "$SSH_PORT")

"${SSH_CMD[@]}" "mkdir -p '${REMOTE_PATH}' && echo 'Remote path ready: ${REMOTE_PATH}'"

if "${SSH_CMD[@]}" "test -d '${REMOTE_PATH}/.git'"; then
  echo "Remote repo exists — updating to origin/main (non-fatal if no git)"
  "${SSH_CMD[@]}" "cd '${REMOTE_PATH}' && git fetch --all --prune || true && git reset --hard origin/main || true"
elif [ -n "${GIT_CLONE_URL}" ]; then
  echo "Cloning repo on remote from ${GIT_CLONE_URL}"
  "${SSH_CMD[@]}" "git clone '${GIT_CLONE_URL}' '${REMOTE_PATH}' || true"
else
  echo "No git repo in REMOTE_PATH and no GIT_CLONE_URL provided — continuing with existing files"
fi

# -------- Upload environment file (optional) --------
if [ -f "${LOCAL_ENV_FILE}" ]; then
  echo "Uploading ${LOCAL_ENV_FILE} -> ${SSH_USER}@${SSH_HOST}:${REMOTE_PATH}/${REMOTE_ENV_FILE}"
  "${SCP_CMD[@]}" "${LOCAL_ENV_FILE}" "${SSH_USER}@${SSH_HOST}:${REMOTE_PATH}/${REMOTE_ENV_FILE}"
else
  echo "Local env file ${LOCAL_ENV_FILE} not found — skipping upload"
fi

# -------- Remote deploy: export env, pull & compose up --------
read -r -d '' REMOTE_SCRIPT <<'EOS'
set -euxo pipefail
cd "${REMOTE_PATH}"
# Export env if file exists
if [ -f "${REMOTE_ENV_FILE}" ]; then
  set -a
  . "${REMOTE_ENV_FILE}"
  set +a
fi
# Provide registry/owner/tag to update.sh
echo "Running deploy/update.sh with IMAGE_TAG=${IMAGE_TAG}"
export IMAGE_TAG="${IMAGE_TAG}"
export REGISTRY="${REGISTRY}"
export REPO_OWNER="${REPO_OWNER}"
chmod +x ./deploy/update.sh || true
./deploy/update.sh "${IMAGE_TAG}"
EOS

# Inject local variables into the heredoc by replacing placeholders
REMOTE_SCRIPT=${REMOTE_SCRIPT//'${REMOTE_PATH}'/${REMOTE_PATH}}
REMOTE_SCRIPT=${REMOTE_SCRIPT//'${REMOTE_ENV_FILE}'/${REMOTE_ENV_FILE}}
REMOTE_SCRIPT=${REMOTE_SCRIPT//'${IMAGE_TAG}'/${IMAGE_TAG}}
REMOTE_SCRIPT=${REMOTE_SCRIPT//'${REGISTRY}'/${REGISTRY}}
REMOTE_SCRIPT=${REMOTE_SCRIPT//'${REPO_OWNER}'/${REPO_OWNER}}

"${SSH_CMD[@]}" "bash -s" <<<"${REMOTE_SCRIPT}"

# -------- Public sanity check --------
if command -v curl >/dev/null 2>&1; then
  echo "Sanity check: ${PUBLIC_URL}"
  HTTP=$(curl -sL -w "%{http_code}" -o /dev/null "${PUBLIC_URL}") || true
  echo "HTTP status: ${HTTP}"
fi

echo "Manual deploy finished: tag=${IMAGE_TAG}"

#!/usr/bin/env bash
set -euo pipefail

# setup-server.sh
# Bootstrap a Debian/Ubuntu server for this project.
# It will:
# - create 'deploy' user if missing
# - install docker & docker-compose (apt)
# - create REMOTE_PATH and set ownership
# - optionally clone the repo into REMOTE_PATH (if REPO_URL provided)

REMOTE_PATH=${1:-/var/www/parkingsrv}
REPO_URL=${2:-}

echo "[setup] REMOTE_PATH=${REMOTE_PATH}"

if ! id deploy >/dev/null 2>&1; then
  echo "[setup] creating user 'deploy'"
  sudo useradd -m -s /bin/bash deploy || true
fi

echo "[setup] updating apt and installing prerequisites"
sudo apt-get update -y
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release git rsync

if ! command -v docker >/dev/null 2>&1; then
  echo "[setup] installing docker"
  curl -fsSL https://get.docker.com | sh
fi

if ! command -v docker-compose >/dev/null 2>&1; then
  echo "[setup] installing docker-compose"
  sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose
fi

echo "[setup] creating REMOTE_PATH and setting ownership"
sudo mkdir -p "${REMOTE_PATH}"
sudo chown -R deploy:deploy "${REMOTE_PATH}"

if [ -n "${REPO_URL}" ]; then
  echo "[setup] cloning repo ${REPO_URL} into ${REMOTE_PATH} as deploy"
  sudo -u deploy -H bash -c "cd ${REMOTE_PATH} && if [ -d .git ]; then git fetch --all && git reset --hard origin/main; else git clone ${REPO_URL} .; fi"
  echo "[setup] making deploy scripts executable"
  sudo -u deploy -H bash -c "cd ${REMOTE_PATH} && chmod +x deploy/*.sh || true"
else
  echo "[setup] REPO_URL not provided - skipping clone"
fi

echo "[setup] adding deploy user to docker group"
sudo usermod -aG docker deploy || true

echo "[setup] done. Next steps:\n - ensure your SSH public key for the CI user is in /home/deploy/.ssh/authorized_keys\n - set GitHub Secrets (SSH_HOST, SSH_USER=deploy, SSH_PRIVATE_KEY, REMOTE_PATH=${REMOTE_PATH})\n - run deploy/update.sh <IMAGE_TAG> to deploy the stack"

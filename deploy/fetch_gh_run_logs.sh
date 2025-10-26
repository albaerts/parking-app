#!/usr/bin/env bash
set -euo pipefail

# fetch_gh_run_logs.sh
# Usage:
#   ./deploy/fetch_gh_run_logs.sh <run-id>          # fetch logs for specific run using gh (if available)
#   ./deploy/fetch_gh_run_logs.sh latest            # fetch logs for latest run (requires gh)
#   GHTOKEN=<token> ./deploy/fetch_gh_run_logs.sh <run-id>  # use GitHub API with token if gh not available
#
# Saves logs to ./deploy/gh-run-<run-id>.log or ./deploy/gh-run-<run-id>.zip (if downloaded via API)

REPO_OWNER=${REPO_OWNER:-albaerts}
REPO_NAME=${REPO_NAME:-parking-app}

usage(){
  echo "Usage: $0 <run-id|latest>"
  exit 2
}

if [ "$#" -ne 1 ]; then
  usage
fi

RUN_ARG=$1
OUT_DIR="$(dirname "$0")"

if command -v gh >/dev/null 2>&1; then
  echo "gh CLI found"
  if ! gh auth status >/dev/null 2>&1; then
    echo "gh CLI is not authenticated. Run: gh auth login --web" >&2
    echo "Falling back to API method if GHTOKEN is set." >&2
    if [ -z "${GHTOKEN:-}" ]; then
      exit 1
    fi
  fi

  if [ "$RUN_ARG" = "latest" ]; then
    echo "Finding latest run for repo ${REPO_OWNER}/${REPO_NAME}"
    RUN_ID=$(gh run list --repo "${REPO_OWNER}/${REPO_NAME}" --limit 1 --json databaseId --jq '.[0].databaseId')
    if [ -z "$RUN_ID" ]; then
      echo "No runs found." >&2
      exit 1
    fi
  else
    RUN_ID=$RUN_ARG
  fi

  OUT_FILE="${OUT_DIR}/gh-run-${RUN_ID}.log"
  echo "Fetching logs for run $RUN_ID into $OUT_FILE"
  gh run view "$RUN_ID" --repo "${REPO_OWNER}/${REPO_NAME}" --log > "$OUT_FILE"
  echo "Saved: $OUT_FILE"
  exit 0
fi

if [ -z "${GHTOKEN:-}" ]; then
  echo "gh not available and GHTOKEN not set. Install gh (brew install gh) or set GHTOKEN." >&2
  usage
fi

if [ "$RUN_ARG" = "latest" ]; then
  echo "Finding latest run via API for repo ${REPO_OWNER}/${REPO_NAME}"
  LATEST_URL="https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/actions/runs?per_page=1"
  RUN_ID=$(curl -s -H "Authorization: token ${GHTOKEN}" "$LATEST_URL" | python3 -c 'import sys, json; j=json.load(sys.stdin); print(j["workflow_runs"][0]["id"])' 2>/dev/null || true)
  if [ -z "$RUN_ID" ]; then
    echo "Could not determine latest run id. Check token and repo access." >&2
    exit 1
  fi
fi

ZIP_OUT="${OUT_DIR}/gh-run-${RUN_ID}.zip"
API_URL="https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/actions/runs/${RUN_ID}/logs"

echo "Downloading logs for run $RUN_ID via API to $ZIP_OUT"
curl -s -L -H "Authorization: token ${GHTOKEN}" "$API_URL" -o "$ZIP_OUT"

if [ ! -s "$ZIP_OUT" ]; then
  echo "Download failed or empty file: $ZIP_OUT" >&2
  exit 1
fi

echo "Unzipping to ${OUT_DIR}/gh-run-${RUN_ID}/"
unzip -q "$ZIP_OUT" -d "${OUT_DIR}/gh-run-${RUN_ID}"
echo "Logs unzipped to ${OUT_DIR}/gh-run-${RUN_ID}/"
echo "Done. Inspect files inside the directory or open ${OUT_DIR}/gh-run-${RUN_ID}.log if present."

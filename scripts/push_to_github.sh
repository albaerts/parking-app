#!/usr/bin/env bash
# Push this repo to GitHub (supports gh CLI and manual remote URL)
# Usage:
#   ./scripts/push_to_github.sh --dry-run                      # show what would happen
#   ./scripts/push_to_github.sh --create myorg/myrepo --public  # use gh to create and push
#   ./scripts/push_to_github.sh --remote https://github.com/you/repo.git # set remote and push

set -euo pipefail

DRY_RUN=0
CREATE_REPO=""
REMOTE_URL=""
PUBLIC=0

print() { if [ "$DRY_RUN" -eq 1 ]; then echo "DRY: $*"; else echo "$*"; fi }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --create) CREATE_REPO="$2"; shift 2 ;;
    --public) PUBLIC=1; shift ;;
    --remote) REMOTE_URL="$2"; shift 2 ;;
    -h|--help) echo "Usage: $0 [--dry-run] [--create owner/repo] [--public] [--remote <url>]"; exit 0 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# Ensure we run from repo root
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if ! command -v git >/dev/null 2>&1; then
  echo "git not found. Please install git and re-run." >&2
  exit 2
fi

# If not a git repo, init and create a first commit
if [ ! -d .git ]; then
  print "git init"
  if [ "$DRY_RUN" -eq 0 ]; then
    git init
  fi
  print "git add ."
  if [ "$DRY_RUN" -eq 0 ]; then
    git add .
  fi
  print "git commit -m 'Initial commit'"
  if [ "$DRY_RUN" -eq 0 ]; then
    git commit -m "Initial commit" || true
  fi
else
  print "Existing git repo found"
fi

# Prefer gh CLI for creating repo
if [ -n "$CREATE_REPO" ]; then
  if command -v gh >/dev/null 2>&1; then
    GH_VIS="--public"
    if [ "$PUBLIC" -eq 0 ]; then GH_VIS="--private"; fi
    print "gh repo create $CREATE_REPO $GH_VIS --source=. --remote=origin --push"
    if [ "$DRY_RUN" -eq 0 ]; then
      gh repo create "$CREATE_REPO" $GH_VIS --source=. --remote=origin --push
    fi
    exit 0
  else
    echo "gh CLI not found. Install GitHub CLI or use --remote with an existing repo URL." >&2
    exit 3
  fi
fi

if [ -n "$REMOTE_URL" ]; then
  print "Setting remote origin to $REMOTE_URL"
  if [ "$DRY_RUN" -eq 0 ]; then
    if git remote | grep -q '^origin$'; then
      git remote remove origin
    fi
    git remote add origin "$REMOTE_URL"
  fi
else
  print "No --remote provided. If you already created a GitHub repo, call with --remote <url> or use --create with gh CLI."
fi

# Push
print "git push -u origin main"
if [ "$DRY_RUN" -eq 0 ]; then
  # create main branch if missing
  if ! git show-ref --verify --quiet refs/heads/main; then
    git branch -M main || true
  fi
  git push -u origin main
fi

print "Done"

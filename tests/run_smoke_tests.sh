#!/usr/bin/env bash
set -euo pipefail

BASE=${TEST_BASE_URL:-http://127.0.0.1:8000}
echo "Running smoke tests against $BASE"
TEST_BASE_URL=$BASE pytest -q tests/test_auth.py

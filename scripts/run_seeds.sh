#!/usr/bin/env bash
# Seed the Tutor LMS with demo institutions, users, and sponsorships.
# Run from anywhere:  bash scripts/run_seeds.sh
# Optional env var:   CONTAINER=tutor_local-lms-1

set -euo pipefail

CONTAINER="${CONTAINER:-tutor_local-lms-1}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Copying seed scripts into container..."
docker exec "$CONTAINER" mkdir -p /tmp/amp_seeds
docker cp "$SCRIPT_DIR/seed_users.py"        "$CONTAINER:/tmp/amp_seeds/seed_users.py"
docker cp "$SCRIPT_DIR/seed_institutions.py" "$CONTAINER:/tmp/amp_seeds/seed_institutions.py"
docker cp "$SCRIPT_DIR/seed_sponsorships.py" "$CONTAINER:/tmp/amp_seeds/seed_sponsorships.py"
docker cp "$SCRIPT_DIR/seed_all.py"          "$CONTAINER:/tmp/amp_seeds/seed_all.py"

echo "Running seeds..."
docker exec "$CONTAINER" bash -c \
    "cd /openedx/edx-platform && ./manage.py lms shell -c \"exec(open('/tmp/amp_seeds/seed_all.py').read())\"" \
    2>&1 | grep -v "^20[0-9][0-9]-" \
         | grep -v "DeprecationWarning" \
         | grep -v "pkg_resources" \
         | grep -v "casbin" \
         | grep -v "BLOCK_STRUCT" \
         | grep -v "objects imported" \
         | grep -v "could not be automatically" \
         || true

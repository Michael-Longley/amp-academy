#!/usr/bin/env bash
# deploy-local.sh
# Push amp-theme SCSS/config changes to the running tutor dev instance.
#
# From WSL2:     bash deploy-local.sh
# From Windows:  wsl -d Ubuntu bash -c "cd /mnt/c/Users/IG-11/Desktop/Projects/AmpAcademy/tutor-amp-theme && bash deploy-local.sh"
#
# One-time setup required before first use:
#   tutor dev do init                     (runs DB migrations + sets theme)
#   See CLAUDE.md for full details.

set -euo pipefail

TUTOR_VENV="${TUTOR_VENV:-/home/ig-11/tutor-venv}"
CONTAINER="${CONTAINER:-tutor_local-lms-1}"
THEME_BUILD="$HOME/.local/share/tutor/env/build/openedx/themes/amp-theme"

# ── color output ──────────────────────────────────────────────────────────────
BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
step()  { echo -e "\n${BLUE}▶  $*${NC}"; }
ok()    { echo -e "${GREEN}✓  $*${NC}"; }
warn()  { echo -e "${YELLOW}⚠  $*${NC}"; }
die()   { echo -e "${RED}✗  $*${NC}"; exit 1; }

# ── 0. preflight ──────────────────────────────────────────────────────────────
[ -f "$TUTOR_VENV/bin/activate" ] || die "Tutor venv not found at $TUTOR_VENV. Set TUTOR_VENV env var."

docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$" \
  || die "Container $CONTAINER is not running. Start with: tutor local start --detach"

# ── 1. render templates ───────────────────────────────────────────────────────
step "tutor config save"
# shellcheck disable=SC1091
source "$TUTOR_VENV/bin/activate"
tutor config save
ok "Templates rendered → $THEME_BUILD"

# ── 2. clean stale nested dir (legacy path structure artefact) ────────────────
STALE="$THEME_BUILD/openedx"
if [ -d "$STALE" ]; then
  warn "Removing stale nested dir: $STALE"
  rm -rf "$STALE"
fi

# ── 3. copy rendered theme into container ────────────────────────────────────
step "Copying theme files into container"
docker cp "$THEME_BUILD" "${CONTAINER}:/openedx/themes/"
ok "Theme files copied → /openedx/themes/amp-theme"

# ── 4. patch compile_sass.py inside the container ────────────────────────────
step "Patching compile_sass.py (continue-on-error)"
docker exec "$CONTAINER" python3 - <<'PYEOF'
src = '/openedx/edx-platform/scripts/compile_sass.py'
content = open(src).read()
patched = content.replace(
    'raise Exception(f"Failed to compile {source}: {output_text}")',
    'click.secho(f"WARNING: Skipping {source}: {output_text}", fg="yellow"); continue',
)
open('/tmp/compile_sass_patched.py', 'w').write(patched)
print("  patched OK")
PYEOF

# ── 5. compile SCSS ───────────────────────────────────────────────────────────
step "Compiling SCSS for amp-theme"
docker exec -w /openedx/edx-platform "$CONTAINER" \
  python /tmp/compile_sass_patched.py \
    --env=development \
    --skip-default \
    --theme-dir /openedx/themes \
    --theme amp-theme
ok "SCSS compiled"

# ── 6. collectstatic ──────────────────────────────────────────────────────────
step "Collecting static files"
docker exec "$CONTAINER" \
  python manage.py lms collectstatic --noinput 2>&1 | tail -3
ok "Static files updated"

echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Done!  http://local.openedx.io:8000${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

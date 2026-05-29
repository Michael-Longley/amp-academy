# Amp Academy — development & deployment workflow
#
# Requires GNU Make. On Windows: install via Chocolatey (choco install make)
# or use Git for Windows which bundles it.
#
# ── Dev quick-start ──────────────────────────────────────────────────────────
#   make setup-dev   One-time: enable Mailpit, configure dev SMTP
#   make start       Start the full local stack (LMS + Mailpit + Caddy + …)
#   make update      Reinstall plugins from git, restart containers  (~2 min)
#   make stop        Stop everything
#
# ── Production deploy (run on the server via SSH or GitHub Actions) ──────────
#   make update      Same command — reinstall plugins + restart   (~2 min)
#   make build       Full image rebuild (after SCSS/Dockerfile changes, ~20 min)
#   make migrate     Run DB migrations for both plugins
#   make health      Check LMS is responding
#
# NOTE: setup-dev, start, stop are local-dev targets only.
#       Never run setup-dev on the production server.

TUTOR   := tutor
GITHUB  := git+https://github.com/michael-longley/amp-academy.git

PURCHASING_PKG  := $(GITHUB)\#subdirectory=tutor-course-purchasing
SPONSORSHIP_PKG := $(GITHUB)\#subdirectory=tutor-student-sponsorship

# Containers that run plugin code — restarted after a quick plugin update
PLUGIN_CONTAINERS := lms cms lms-worker cms-worker

.PHONY: help setup-dev start stop restart update build migrate health \
        logs logs-all shell shell-cms status

# ── Default target ────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "Amp Academy — available commands"
	@echo "────────────────────────────────────────────────────────────"
	@echo "LOCAL DEV"
	@echo "  make setup-dev    One-time: enable Mailpit + configure dev SMTP"
	@echo "  make start        Start the full local stack"
	@echo "  make stop         Stop the full local stack"
	@echo "  make restart      Stop then start"
	@echo ""
	@echo "PLUGINS (dev and production)"
	@echo "  make update       Reinstall plugins from git, restart containers (~2 min)"
	@echo "  make build        Full image rebuild, then init + start (~20 min)"
	@echo "  make migrate      Run DB migrations for both plugins"
	@echo "  make health       Check LMS is responding"
	@echo ""
	@echo "DEBUGGING"
	@echo "  make logs         Tail LMS logs"
	@echo "  make logs-all     Tail logs for all containers"
	@echo "  make shell        Django shell inside LMS"
	@echo "  make shell-cms    Django shell inside CMS"
	@echo "  make status       Show running containers"
	@echo ""

# ── LOCAL DEV ONLY ───────────────────────────────────────────────────────────
# These targets depend on dev settings. Do not run on the production server.

setup-dev:
	@echo "→ Enabling Mailpit dev email capture..."
	$(TUTOR) config save \
		--set COURSE_PURCHASING_DEV_MAILPIT=true \
		--set SMTP_HOST=mailpit \
		--set SMTP_PORT=1025 \
		--set SMTP_USE_TLS=false \
		--set SMTP_USERNAME="" \
		--set SMTP_PASSWORD=""
	@echo ""
	@echo "✓ Done. Run 'make start' to apply."
	@echo "  View captured emails at http://localhost:8025"
	@echo ""
	@echo "  To restore production SMTP:"
	@echo "    tutor config save --set SMTP_HOST=<host> --set SMTP_PORT=587 \\"
	@echo "                      --set SMTP_USE_TLS=true \\"
	@echo "                      --set SMTP_USERNAME=<key> --set SMTP_PASSWORD=<key>"

start:
	$(TUTOR) local start -d
	@echo ""
	@echo "✓ Stack is up."
	@echo "  LMS          → https://$(shell $(TUTOR) config printvalue LMS_HOST 2>/dev/null || echo '<LMS_HOST>')"
	@echo "  Studio (CMS) → https://$(shell $(TUTOR) config printvalue CMS_HOST 2>/dev/null || echo '<CMS_HOST>')"
	@echo "  Mailpit      → http://localhost:8025  (if setup-dev was run)"

stop:
	$(TUTOR) local stop

restart: stop start

# ── PLUGIN MANAGEMENT (dev and production) ────────────────────────────────────

# Quick reinstall from the latest git commit — no Docker image rebuild needed.
# Safe to run on the production server. Causes ~30 s of container cycling.
update:
	@echo "→ Reinstalling plugins in running containers..."
	@for c in $(PLUGIN_CONTAINERS); do \
		$(TUTOR) local dc exec -T $$c pip install --force-reinstall \
			'$(PURCHASING_PKG)' \
			'$(SPONSORSHIP_PKG)'; \
	done
	@echo "→ Restarting containers..."
	$(TUTOR) local dc restart $(PLUGIN_CONTAINERS)
	@echo "✓ Plugins updated. Running migrations next is recommended: make migrate"

# Full Docker image rebuild — needed after SCSS/theme/Dockerfile changes.
# Runs tutor's full init (migrations included). Takes ~15-20 min.
# Safe to run on production but causes a full restart with brief downtime.
build:
	@echo "→ Building openedx image (~15-20 min)..."
	$(TUTOR) images build openedx
	$(TUTOR) local do init
	$(TUTOR) local start -d
	@echo "✓ Build complete and stack restarted."

# ── DATABASE ──────────────────────────────────────────────────────────────────

migrate:
	$(TUTOR) local dc exec -T lms python manage.py lms migrate purchasing
	$(TUTOR) local dc exec -T lms python manage.py lms migrate student_sponsorship
	@echo "✓ Migrations applied."

# ── HEALTH CHECK ─────────────────────────────────────────────────────────────

# Polls /heartbeat every 10 s for up to 2 minutes. Used by the deploy workflow.
health:
	@echo "→ Waiting for LMS to respond..."
	@LMS_HOST=$$($(TUTOR) config printvalue LMS_HOST 2>/dev/null || echo ""); \
	for i in $$(seq 1 12); do \
		if curl -sf --max-time 10 "https://$$LMS_HOST/heartbeat" > /dev/null 2>&1; then \
			echo "✓ LMS is healthy."; \
			exit 0; \
		fi; \
		echo "  Attempt $$i/12 — retrying in 10 s..."; \
		sleep 10; \
	done; \
	echo "✗ LMS did not respond after 2 minutes."; \
	exit 1

# ── LOGS ─────────────────────────────────────────────────────────────────────

logs:
	$(TUTOR) local logs -f lms

logs-all:
	$(TUTOR) local logs -f

# ── SHELL ─────────────────────────────────────────────────────────────────────

shell:
	$(TUTOR) local run lms python manage.py lms shell

shell-cms:
	$(TUTOR) local run cms python manage.py cms shell

# ── STATUS ────────────────────────────────────────────────────────────────────

status:
	@docker ps \
		--filter "name=tutor" \
		--format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

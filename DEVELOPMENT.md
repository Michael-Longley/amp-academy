# Development & Deployment Guide

---

## Local Development

### Prerequisites

- [Tutor](https://docs.tutor.aisac.org/) ≥ 15 installed and configured locally
- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- GNU Make — Windows: `choco install make` or Git for Windows (includes Make)

### First-time local setup

Run once after cloning. Enables Mailpit (email capture) and points the LMS SMTP
settings at it. Tutor regenerates its docker-compose automatically.

```bash
make setup-dev
make start
```

`tutor local start` now includes Mailpit as a native service — no separate
container to run, no second terminal.

**View captured emails:** http://localhost:8025

### Daily local workflow

| Command | What it does | Time |
|---|---|---|
| `make start` | Start LMS, CMS, Caddy, Mailpit, workers | ~30 s |
| `make stop` | Stop everything | ~5 s |
| `make update` | Reinstall plugins from git, restart containers | ~2 min |
| `make build` | Full Docker image rebuild (SCSS/theme changes) | ~15-20 min |
| `make migrate` | Run migrations for both plugins | ~10 s |
| `make logs` | Tail LMS logs | — |
| `make shell` | Django shell inside LMS | — |
| `make status` | Show running containers | — |

### Testing emails locally

```bash
make shell

# Then inside the Django shell:
from django.core.mail import send_mail
send_mail("Test", "Hello", "noreply@amp-academy.com", ["dev@example.com"])
# → check http://localhost:8025
```

**Full sponsorship invitation flow:**
1. Log in as an institution admin → sponsorship portal → add a student
2. Check http://localhost:8025 for the invitation email
3. Click the acceptance link → student is enrolled in institution's courses

**Free course checkout flow:**
1. Set `InstitutionCourseAccess.subsidy_pct = 100` for an institution/course pair
2. Accept the sponsorship invitation
3. Add the course to cart → checkout shows course price → sponsorship discount → $0.00
4. No payment form appears — "Confirm Free Enrollment" only
5. Check http://localhost:8025 for the order confirmation email

### Restoring production SMTP locally

```bash
tutor config save \
  --set SMTP_HOST=smtp.postmarkapp.com \
  --set SMTP_PORT=587 \
  --set SMTP_USE_TLS=true \
  --set SMTP_USERNAME=<your-api-key> \
  --set SMTP_PASSWORD=<your-api-key>
make restart
```

---

## Deployment (Digital Ocean)

### How it works

Plugins are Python packages installed via `pip install git+...` inside the running
LMS Docker container. Deployment is:

```
git push → GitHub → manually trigger workflow → SSH into droplet → make update → make migrate
```

Tutor's data (database, media files, course content, config) lives in Docker volumes
and is **never touched** by a deployment. Only the Python packages inside the
running containers change.

### Two deploy modes

| Mode | When to use | Time | Downtime |
|---|---|---|---|
| **quick** | Python, templates, emails, migrations | ~2 min | ~30 s (containers cycling) |
| **full** | SCSS, theme, Dockerfile, new static files | ~20 min | Full restart |

### Running a deploy

1. Go to **GitHub → Actions → Deploy to Production → Run workflow**
2. Choose `quick` or `full`
3. Click **Run workflow**

The workflow pulls the latest Makefile, runs `make update` (or `make build`),
runs `make migrate`, and polls the health check. Results appear in the Actions
summary with a timestamp and triggered-by record.

---

## One-time server setup

Do this once on the Digital Ocean droplet. Your existing Tutor installation is
not affected — this only clones the repo for the Makefile.

### 1. Clone the repo on the server

```bash
git clone https://github.com/michael-longley/amp-academy.git ~/amp-academy
```

This is used only for the `Makefile`. The actual plugin code runs from pip packages
inside the LMS container — the clone is never imported by Python.

### 2. Install Make (if not present)

```bash
apt-get install -y make
```

### 3. Verify the Makefile works

```bash
cd ~/amp-academy
export PATH="$HOME/.local/bin:$PATH"   # ensure tutor is on PATH
make status   # should show running Tutor containers
make health   # should report LMS healthy
```

### 4. Add the deploy SSH key to GitHub

Generate a dedicated deploy key (don't reuse your personal key):

```bash
# On the droplet
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/deploy_key -N ""
cat ~/.ssh/deploy_key.pub >> ~/.ssh/authorized_keys
cat ~/.ssh/deploy_key      # copy this — it goes into GitHub Secrets
```

Then in GitHub: **Settings → Secrets and variables → Actions → New repository secret**

| Secret name | Value |
|---|---|
| `DO_HOST` | Droplet IP or hostname |
| `DO_USER` | `root` (or your SSH user) |
| `DO_SSH_KEY` | Contents of `~/.ssh/deploy_key` (the private key) |

### 5. (Optional) Add a GitHub Environment

In **GitHub → Settings → Environments → New environment**, create `production`.
Add a required reviewer so every deploy needs a one-click approval before it runs.
The deploy workflow already references this environment.

---

## Manual deploy via SSH

If you need to deploy without GitHub Actions (e.g., during initial setup or debugging):

```bash
ssh root@<droplet-ip>
export PATH="$HOME/.local/bin:$PATH"
cd ~/amp-academy
git pull --ff-only
make update     # quick path — pip reinstall + restart
make migrate
make health
```

Or for a full rebuild:

```bash
make build      # rebuilds openedx image, then restarts
make migrate
make health
```

---

## What changes require which deploy mode

| Change | Mode |
|---|---|
| Python views, models, signals | `quick` |
| Email templates | `quick` |
| Django migrations | `quick` (+ `make migrate`) |
| HTML templates | `quick` |
| Tutor plugin config (`__init__.py`) | `quick` (after `tutor config save` on server) |
| SCSS / theme variables | `full` |
| Logo / static image files | `full` |
| Tutor `__init__.py` hooks that affect Dockerfile | `full` |
| Open edX version bump | `full` |

---

## Deployment history

GitHub Actions keeps a record of every workflow run (who triggered it, when,
which commit, pass/fail) in the Actions tab. This is your deployment log — no
extra tooling needed.

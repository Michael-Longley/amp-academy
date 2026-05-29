# Deployment Guide — tutor-student-sponsorship

## Overview

This plugin adds institutional course sponsorship to an Open edX (Tutor) deployment.
It installs a Django app (`student_sponsorship`) into the LMS container and provides
a management portal at `/sponsorship/`.

---

## Prerequisites

| Requirement | Version |
|---|---|
| Tutor | ≥ 21.0.0 (Ulmo) |
| Open edX | Ulmo (`release/ulmo.2`) |
| Python | ≥ 3.11 |
| tutor-mfe | 21.0.0 (required — see below) |

> **Why tutor-mfe is required:** Open edX Ulmo routes all courseware through the
> Learning Micro-Frontend (MFE). Without it, course links return HTTP 404. The
> sponsorship portal links students directly to their courses, so the MFE must be
> running.

---

## 1. Install tutor-mfe

The Learning MFE handles all courseware URLs (`/learning/...`). Install it once,
before or after the sponsorship plugin — order does not matter.

```bash
pip install tutor-mfe==21.0.0
tutor plugins enable mfe
```

---

## 2. Install the sponsorship plugin

```bash
pip install "git+https://github.com/michael-longley/amp-academy.git#subdirectory=tutor-student-sponsorship"
tutor plugins enable student-sponsorship
```

---

## 3. Configure and rebuild

```bash
tutor config save
tutor images build openedx   # bakes the Django app into the LMS image (~10-20 min)
```

> `tutor images build openedx` is required on first install and whenever the
> plugin package changes. It runs `pip install` for both this plugin and the MFE
> during the Docker build.

---

## 4. Update your local hosts file

The MFE is served at `apps.<LMS_HOST>` (e.g. `apps.local.openedx.io`). Add it to
your hosts file so the browser can resolve it.

**Windows** — run in an **admin** PowerShell:

```powershell
Add-Content "C:\Windows\System32\drivers\etc\hosts" "127.0.0.1  apps.local.openedx.io"
```

**Linux / macOS:**

```bash
echo "127.0.0.1  apps.local.openedx.io" | sudo tee -a /etc/hosts
```

Replace `local.openedx.io` with your actual `LMS_HOST` if different.

---

## 5. Start all services

```bash
tutor local start -d
```

This starts the LMS, CMS, Caddy (reverse proxy), and the `mfe` container. Caddy
automatically routes:

| Hostname | Service |
|---|---|
| `local.openedx.io` | LMS |
| `studio.local.openedx.io` | CMS |
| `apps.local.openedx.io` | MFE (Learning, Profile, etc.) |

---

## 6. Run migrations and initialise

```bash
tutor local do init
```

This runs `migrate student_sponsorship` and sets the active theme. Run it after
every `tutor images build openedx`.

---

## 7. Configure course access in Django admin

1. Open `http://local.openedx.io/admin/student_sponsorship/`
2. Create an **Institution** (name + slug).
3. Create an **InstitutionCourseAccess** record for each Open edX course ID that
   sponsored students should be enrolled in automatically.
   - Course IDs follow the format: `course-v1:Org+CourseName+Run`
   - Find IDs in Studio → Settings → Advanced Settings → Course ID
4. Assign **InstitutionManager** records to grant portal access to staff.

The portal is accessible at `http://local.openedx.io/sponsorship/`.

---

## Configuration options

Set these with `tutor config save --set KEY=value` before building:

| Key | Default | Description |
|---|---|---|
| `STUDENT_SPONSORSHIP_GRACE_DAYS` | `0` | Days of continued access after removal |

---

## Updating the plugin (development)

To apply template or Python changes without a full image rebuild:

```bash
# Copy updated files directly into the running container
docker cp tutor-student-sponsorship/student_sponsorship/. \
  tutor_local-lms-1:/openedx/venv/lib/python3.11/site-packages/student_sponsorship/

# Clear Mako template cache so changes take effect immediately
docker exec tutor_local-lms-1 rm -rf /tmp/mako_lms

# Restart the LMS worker
tutor local restart lms
```

For production, do a full rebuild: `tutor images build openedx && tutor local start -d`.

---

## Troubleshooting

### Course links go to a broken URL (`/None/` in path)

The Learning MFE is not running or the browser cannot resolve `apps.<LMS_HOST>`.
Verify:
1. `docker ps` shows `tutor_local-mfe-1` as `Up`
2. `apps.local.openedx.io` is in your hosts file (step 4 above)
3. `http://apps.local.openedx.io/learning/` loads in the browser

### Portal returns 404

The Django app may not be installed in the running container. Run:

```bash
docker exec tutor_local-lms-1 python -c "import student_sponsorship; print('OK')"
```

If it fails, either rebuild the image or use the `docker cp` method above.

### Invitation copy button does nothing

The Copy button falls back to `document.execCommand('copy')` on `http://` origins.
If even that fails, select the text in the invitation box manually and copy with
Ctrl+C.

### Migrations not applied

```bash
docker exec tutor_local-lms-1 python manage.py lms migrate student_sponsorship
```

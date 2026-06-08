# tutor-contrib-pwa

PWA capabilities for Open edX on Tutor — home-screen installability, offline caching, and web push notifications.

## Features

- **Installable PWA** — Android and iOS (16.4+) home-screen install prompt, mobile-only
- **Service worker** — app-shell cache-first, course content network-first, offline fallback page
- **Push notification bus** — any Tutor plugin can register types and deliver push messages to students
- **No new infrastructure** — runs inside the existing MFE (Caddy) and LMS containers

## Requirements

- Tutor ≥ 15.0.0 with `tutor-mfe` enabled
- **HTTPS is required** — service workers and push notifications are blocked by all browsers on plain HTTP. `ENABLE_HTTPS: true` must be set before this plugin is useful in production.
- A deployed, reachable LMS hostname

> **Local development:** HTTPS is not available on `apps.local.openedx.io`. Work around this during development by going to `chrome://flags/#unsafely-treat-insecure-origin-as-secure`, adding `http://apps.local.openedx.io`, and relaunching Chrome. The manifest and install prompt work on HTTP; only the service worker and push require this flag locally.

---

## Install (two steps)

### Step 1 — MFE (installability + offline + install prompt)

```bash
pip install tutor-contrib-pwa
tutor plugins enable pwa
tutor config save          # generates VAPID keys on first run
tutor images build mfe     # bakes manifest.json, sw.js, icons, and offline.html into the image
tutor local stop mfe && tutor local start --detach mfe   # recreate container (restart alone won't apply a new image)
```

After this, the PWA manifest is served at `/manifest.json`, the service worker at `/sw.js`, and the mobile install prompt appears on first visit.

### Step 2 — LMS (push notification delivery)

Push notifications require the `pwa_notifications` Django app to be installed in the LMS image. This is a separate, longer build:

```bash
tutor images build openedx   # installs pwa_notifications into the LMS (~15–20 min)
tutor local do init          # runs migrations and syncs notification types
tutor local restart lms
```

You can skip Step 2 entirely if you only need installability and offline support.

---

## Production readiness checklist

Before going live, set these values and rebuild the MFE:

```bash
tutor config save \
  --set PWA_ICON_URL="https://cdn.yourschool.edu/app-icon-512.png" \
  --set PWA_SHORT_NAME="YourSchool" \
  --set PWA_THEME_COLOR="#c0392b"

tutor images build mfe
tutor local stop mfe && tutor local start --detach mfe
```

| Item | Why it matters |
|---|---|
| `PWA_ICON_URL` | The bundled placeholder is not a production brand. Must be a publicly reachable 512×512 PNG. |
| `PWA_SHORT_NAME` | Shown under the icon on the home screen. Max 12 characters. |
| `PWA_THEME_COLOR` | Browser toolbar color when the PWA is installed. Match your brand. |
| HTTPS | Service workers and push are blocked on HTTP. Set `ENABLE_HTTPS: true`. |

---

## Configuration reference

| Variable | Default | Notes |
|---|---|---|
| `PWA_APP_NAME` | `PLATFORM_NAME` | Full name on the splash screen |
| `PWA_SHORT_NAME` | `PLATFORM_NAME[:12]` | Home-screen label, max 12 chars |
| `PWA_THEME_COLOR` | `#0056d2` | Set to `BRANDING_PRIMARY` if using `tutor-contrib-branding` |
| `PWA_BACKGROUND_COLOR` | `#ffffff` | Splash screen background |
| `PWA_ICON_URL` | bundled placeholder | **Set before going live** |
| `PWA_PUSH_ENABLED` | `true` | Master switch for all push delivery |
| `PWA_VAPID_CONTACT_EMAIL` | `admin@<LMS_HOST>` | Required by the VAPID spec |
| `PWA_VAPID_PUBLIC_KEY` | auto-generated | Written once on first `tutor config save` |
| `PWA_VAPID_PRIVATE_KEY` | auto-generated | Never exposed to the frontend |
| `PWA_CACHE_VERSION` | `1` | Bump to force service worker cache invalidation |

Any `PWA_*` change that affects the MFE (manifest, theme, cache version) requires `tutor images build mfe` followed by a container recreate.

---

## Enabling push notification types

Notification types are disabled by default. Enable them in Django admin after completing the LMS install:

```
https://your-lms-host/admin/pwa_notifications/notificationtype/
```

Each type has an enabled/disabled toggle. No restarts needed.

---

## Using the push notification bus from another plugin

**Register a type** in your plugin's `plugin.py`:

```python
from tutorpwa.hooks import PWA_NOTIFICATION_TYPES

PWA_NOTIFICATION_TYPES.add_item({
    "id": "sponsorship.payment_due",
    "label": "Sponsorship payment upcoming",
    "description": "Sent when a sponsored student's funding period is ending.",
    "default_enabled": True,
})
```

**Send a notification** from a signal handler, Celery task, or view:

```python
try:
    from tutorpwa.notifications import send_notification
    _PWA_AVAILABLE = True
except ImportError:
    _PWA_AVAILABLE = False

if _PWA_AVAILABLE:
    send_notification(
        user_id=student.id,
        notification_type="sponsorship.payment_due",
        title="Payment required soon",
        body="Your sponsorship ends in 7 days. Please update your payment method.",
        url="/account/payment",
    )
```

`send_notification` enqueues a Celery task and returns immediately.

---

## VAPID key rotation

VAPID keys are stored in `$(tutor config printroot)/config.yml` and never overwritten by `tutor config save`. To rotate them intentionally:

```bash
# 1. Generate a new linked key pair
python3 - <<'EOF'
from py_vapid import Vapid
import base64
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
v = Vapid()
v.generate_keys()
print("Private:", base64.b64encode(v.private_pem()).decode())
raw = v.public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
print("Public: ", base64.urlsafe_b64encode(raw).rstrip(b"=").decode())
EOF

# 2. Save the new keys
tutor config save \
  --set PWA_VAPID_PRIVATE_KEY="<new-private>" \
  --set PWA_VAPID_PUBLIC_KEY="<new-public>"

# 3. Clear all push subscriptions — they are invalid after key rotation
tutor local run lms python manage.py lms shell -c \
  "from pwa_notifications.models import PushSubscription; PushSubscription.objects.all().delete()"

# 4. Rebuild MFE to bake new public key into sw.js
tutor images build mfe
tutor local stop mfe && tutor local start --detach mfe
```

---

## What is not yet implemented

- **Browser-side push subscription flow** — the server side (Django app, Celery delivery, VAPID signing) is complete, but there is no JavaScript yet that calls `pushManager.subscribe()` and registers the subscription with the server. Push notifications cannot be delivered until this is built.

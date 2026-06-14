# tutor-contrib-pwa

PWA capabilities for Open edX on Tutor — home-screen installability, offline caching, and web push notifications.

## Features

- **Installable PWA** — Android and iOS (16.4+) home-screen install prompt, mobile-only, with two-tier dismissal
- **Service worker** — app-shell cache-first, course content network-first, branded offline fallback page
- **Push notification bus** — any Tutor plugin can register types and deliver push messages to students; prompt fires automatically after install
- **No new infrastructure** — runs inside the existing MFE (Caddy) and LMS containers

## Requirements

- Tutor ≥ 15.0.0 with `tutor-mfe` enabled
- **HTTPS is required** — service workers and push notifications are blocked by all browsers on plain HTTP. `ENABLE_HTTPS: true` must be set before this plugin is useful in production.
- A deployed, reachable LMS hostname

---

## Production deploy

### 1. Install the plugin

```bash
pip install "git+https://github.com/michael-longley/amp-academy.git#subdirectory=tutor-contrib-pwa"
tutor plugins enable pwa
```

### 2. Set branding and contact configuration

These values are baked into the MFE image at build time. Set them **before** running `tutor images build mfe`.

```bash
tutor config save \
  --set PWA_ICON_URL="https://your-cdn.com/app-icon-512.png" \
  --set PWA_SHORT_NAME="YourSchool" \
  --set PWA_THEME_COLOR="#c0392b" \
  --set PWA_VAPID_CONTACT_EMAIL="ops@your-school.edu"
```

| Variable | Required | Notes |
|---|---|---|
| `PWA_ICON_URL` | **Yes** | Publicly reachable 512×512 PNG. The bundled placeholder is not production-appropriate. |
| `PWA_SHORT_NAME` | **Yes** | Label shown under the icon on the home screen. Max 12 characters. |
| `PWA_THEME_COLOR` | Recommended | Browser toolbar colour when the PWA is installed. Match your brand. |
| `PWA_VAPID_CONTACT_EMAIL` | Recommended | Shown to push services for abuse contact. Defaults to `admin@<LMS_HOST>`. |
| `PWA_APP_NAME` | Optional | Full name on the splash screen. Defaults to `PLATFORM_NAME`. |
| `PWA_BACKGROUND_COLOR` | Optional | Splash screen background. Defaults to `#ffffff`. |

### 3. Generate VAPID keys and back them up

VAPID keys are generated automatically on the first `tutor config save` run after enabling the plugin. They are written once and never overwritten.

```bash
tutor config save   # keys are generated here if not already present
```

**Immediately back up the generated keys** — if `config.yml` is lost and keys are regenerated, all existing push subscriptions become invalid and the MFE must be rebuilt.

```bash
tutor config printvalue PWA_VAPID_PUBLIC_KEY
tutor config printvalue PWA_VAPID_PRIVATE_KEY
# Store both values in your secrets manager or deployment documentation.
```

### 4. Build images

```bash
# MFE: bakes manifest.json, sw.js, icons, offline.html, and notification JS
# (includes the VAPID public key — must run after step 3)
tutor images build mfe

# LMS: installs pwa_notifications Django app, pywebpush, py-vapid
tutor images build openedx
```

### 5. Deploy containers

```bash
tutor local stop
tutor local start
tutor local do init   # runs DB migrations and seeds the 5 default notification types
```

### 6. Configure in Django admin

Navigate to `https://your-lms-host/admin/pwa_notifications/` and complete:

**Notification prompt copy** (`/admin/pwa_notifications/pwaconfig/`):
Update the title, body, and button text to match your brand voice. This controls what students see before the browser permission dialog. Changes take effect immediately — no rebuild needed.

**Notification types** (`/admin/pwa_notifications/notificationtype/`):
All 5 types are disabled by default. Enable the ones relevant to your deployment:

| Type | Enable if… |
|---|---|
| Enrollment confirmed | You want students to get a confirmation when they enrol |
| Assignment due in 24 hours | You use Open edX assignment due dates and Celery beat is running |
| Grade posted | You post graded content |
| Certificate awarded | You issue certificates |
| Course announcement | Instructors post regular course updates |

### 7. Verify

```bash
# Manifest served correctly
curl -I https://apps.your-lms-host/manifest.json
# → Content-Type: application/manifest+json

# Service worker served with correct header
curl -I https://apps.your-lms-host/sw.js
# → Service-Worker-Allowed: /

# Prompt copy endpoint live
curl https://your-lms-host/api/pwa/config/
# → {"prompt_title": "...", "prompt_body": "...", ...}
```

Test push delivery end-to-end (requires a real push subscription from a browser):

```bash
tutor local run lms python manage.py lms shell -c "
from pwa_notifications.tasks import send_push_notification
send_push_notification.delay(
    user_id=YOUR_USER_ID,
    notification_type_id='enrollment.confirmed',
    title='Test notification',
    body='Push delivery is working.',
)
"
# Then check: https://your-lms-host/admin/pwa_notifications/notificationlog/
```

---

## Configuration reference

All variables use the `PWA_` prefix. Changes that affect the MFE (manifest appearance, theme, VAPID key) require `tutor images build mfe` followed by a container recreate. Changes to `PwaConfig` in Django admin take effect immediately.

| Variable | Default | Rebuild required | Notes |
|---|---|---|---|
| `PWA_APP_NAME` | `PLATFORM_NAME` | Yes | Full name on the splash screen |
| `PWA_SHORT_NAME` | `PLATFORM_NAME[:12]` | Yes | Home-screen label, max 12 chars |
| `PWA_THEME_COLOR` | `#0056d2` | Yes | Browser toolbar colour |
| `PWA_BACKGROUND_COLOR` | `#ffffff` | Yes | Splash screen background |
| `PWA_ICON_URL` | bundled placeholder | Yes | **Set before going live** — 512×512 PNG |
| `PWA_VAPID_CONTACT_EMAIL` | `admin@<LMS_HOST>` | Yes | Required by the VAPID spec |
| `PWA_PUSH_ENABLED` | `true` | Yes | Master switch for all push delivery |
| `PWA_VAPID_PUBLIC_KEY` | auto-generated | Yes | Written once, never overwritten |
| `PWA_VAPID_PRIVATE_KEY` | auto-generated | No | Never exposed to the frontend |
| `PWA_CACHE_VERSION` | `1` | Yes | Bump to force service worker cache invalidation across all clients |

---

## Updating an existing deployment

After any `PWA_*` config change:

```bash
tutor config save --set PWA_THEME_COLOR="#003057"   # example
tutor images build mfe
tutor local stop mfe && tutor local start --detach mfe
```

To update the notification prompt copy without a rebuild: edit it directly in Django admin at `/admin/pwa_notifications/pwaconfig/`.

---

## Local development

HTTPS is not available on `apps.local.openedx.io`. Service worker registration requires a secure context. Work around this during development:

1. Go to `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
2. Add `http://apps.local.openedx.io`
3. Click **Relaunch**

The manifest and install prompt work on HTTP without the flag. The service worker, push subscription, and notification permission prompt require it.

---

## Using the push notification bus from another plugin

**Register a notification type** in your plugin's `plugin.py`:

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

Keys are stored in `$(tutor config printroot)/config.yml` and never overwritten by `tutor config save`. To rotate intentionally (e.g. after a security incident):

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

All users will need to re-accept the notification permission prompt on their next visit.

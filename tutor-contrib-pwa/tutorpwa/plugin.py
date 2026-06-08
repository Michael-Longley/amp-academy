from __future__ import annotations

import base64
import logging
from pathlib import Path

from tutor import hooks

logger = logging.getLogger(__name__)

# ── VAPID key pair generation ─────────────────────────────────────────────────
# Generated once at module import time as static strings.
# CONFIG_UNIQUE merges them into config only if the keys aren't already saved —
# so after the first `tutor config save` they're fixed in config.yml forever.
_VAPID_PRIVATE_KEY_DEFAULT = ""
_VAPID_PUBLIC_KEY_DEFAULT = ""

try:
    import base64 as _b64
    from cryptography.hazmat.primitives.serialization import (
        Encoding as _Enc,
        PublicFormat as _PubFmt,
    )
    from py_vapid import Vapid as _Vapid

    _v = _Vapid()
    _v.generate_keys()
    _VAPID_PRIVATE_KEY_DEFAULT = _b64.b64encode(_v.private_pem()).decode()
    _raw_pub = _v.public_key.public_bytes(_Enc.X962, _PubFmt.UncompressedPoint)
    _VAPID_PUBLIC_KEY_DEFAULT = _b64.urlsafe_b64encode(_raw_pub).rstrip(b"=").decode()
except Exception as _e:
    logger.warning("tutor-contrib-pwa: could not generate VAPID keys at import: %s", _e)


# ── 1. Config defaults ────────────────────────────────────────────────────────
hooks.Filters.CONFIG_DEFAULTS.add_items([
    # Identity — empty means fall back to PLATFORM_NAME in Jinja2 templates
    ("PWA_APP_NAME", ""),
    ("PWA_SHORT_NAME", ""),
    # PWA behaviour
    ("PWA_START_URL", "/"),
    ("PWA_SCOPE", "/"),
    ("PWA_BACKGROUND_COLOR", "#ffffff"),
    # Operator overrides
    ("PWA_ICON_URL", ""),      # Set to a public 512×512 PNG URL before going live
    ("PWA_THEME_COLOR", "#0056d2"),  # Set to BRANDING_PRIMARY if using tutor-contrib-branding
    # Push
    ("PWA_PUSH_ENABLED", True),
    ("PWA_VAPID_CONTACT_EMAIL", ""),  # Falls back to admin@LMS_HOST in settings patch
    # Cache version — bump to force service worker cache invalidation
    ("PWA_CACHE_VERSION", "1"),
])

# ── 2. VAPID keys — generated once, never overwritten ────────────────────────
hooks.Filters.CONFIG_UNIQUE.add_items([
    ("PWA_VAPID_PRIVATE_KEY", _VAPID_PRIVATE_KEY_DEFAULT),
    ("PWA_VAPID_PUBLIC_KEY", _VAPID_PUBLIC_KEY_DEFAULT),
])

# ── 3. Template roots and targets ────────────────────────────────────────────
hooks.Filters.ENV_TEMPLATE_ROOTS.add_items([
    str(Path(__file__).parent / "templates"),
])

# Render templates/pwa/ into the MFE Docker build context as pwa/
hooks.Filters.ENV_TEMPLATE_TARGETS.add_items([
    ("pwa", "plugins/mfe/build/mfe"),
])

# ── 4. Install Python push dependencies into LMS image ───────────────────────
hooks.Filters.ENV_PATCHES.add_item((
    "openedx-dockerfile-post-python-requirements",
    "RUN pip install "
    "'git+https://github.com/michael-longley/amp-academy.git"
    "#subdirectory=tutor-contrib-pwa' "
    "pywebpush>=2.0.0 "
    "py-vapid>=1.9.0",
))

# ── 5. LMS Django settings ────────────────────────────────────────────────────
hooks.Filters.ENV_PATCHES.add_item((
    "openedx-lms-common-settings",
    r"""
import base64 as _b64
from celery.schedules import crontab as _crontab

# PWA push delivery credentials
PWA_VAPID_PRIVATE_KEY = _b64.b64decode("{{ PWA_VAPID_PRIVATE_KEY }}").decode()
PWA_VAPID_PUBLIC_KEY = "{{ PWA_VAPID_PUBLIC_KEY }}"
PWA_VAPID_CONTACT_EMAIL = "{{ PWA_VAPID_CONTACT_EMAIL or 'admin@' + LMS_HOST }}"
PWA_PUSH_ENABLED = {{ 'True' if PWA_PUSH_ENABLED else 'False' }}

# Celery beat: hourly deadline check and weekly subscription cleanup
CELERYBEAT_SCHEDULE["pwa-check-deadlines-hourly"] = {
    "task": "pwa_notifications.tasks.check_assignment_deadlines",
    "schedule": _crontab(minute=5),
}
CELERYBEAT_SCHEDULE["pwa-cleanup-subscriptions-weekly"] = {
    "task": "pwa_notifications.tasks.cleanup_inactive_subscriptions",
    "schedule": _crontab(hour=3, minute=0, day_of_week=0),
}
""",
))

# ── 6. Expose public key to MFE config ───────────────────────────────────────
hooks.Filters.ENV_PATCHES.add_item((
    "mfe-env-production",
    'APP_ID_pwa_VAPID_PUBLIC_KEY="{{ PWA_VAPID_PUBLIC_KEY }}"',
))

# ── 7. Caddy: serve PWA static files at the origin root ──────────────────────
hooks.Filters.ENV_PATCHES.add_item((
    "mfe-caddyfile",
    r"""
    @pwa_static {
        path /manifest.json /sw.js /icons/* /offline.html
    }
    handle @pwa_static {
        root * /openedx/dist
        header /manifest.json Content-Type "application/manifest+json"
        header /sw.js Content-Type "application/javascript; charset=utf-8"
        header /sw.js Service-Worker-Allowed "/"
        file_server
    }
""",
))

# ── 8. Copy PWA static files into the final production Caddy image ───────────
hooks.Filters.ENV_PATCHES.add_item((
    "mfe-dockerfile-production-final",
    """
# PWA static files served at the origin root
COPY pwa/manifest.json /openedx/dist/manifest.json
COPY pwa/sw.js /openedx/dist/sw.js
COPY pwa/offline.html /openedx/dist/offline.html
COPY pwa/icons/ /openedx/dist/icons/
""",
))

# ── 9. Inject manifest link, SW registration, and install prompt ──────────────
# All logic lives at module scope — no React mounting required.
hooks.Filters.ENV_PATCHES.add_item((
    "mfe-env-config-buildtime-imports",
    r"""// ── PWA bootstrap ─────────────────────────────────────────────────────────

// 1. Inject <link rel="manifest"> so Chrome discovers the PWA
(function injectManifestLink() {
  if (typeof document !== 'undefined' && !document.querySelector('link[rel="manifest"]')) {
    var link = document.createElement('link');
    link.rel = 'manifest';
    link.href = '/manifest.json';
    document.head.appendChild(link);
  }
}());

// 2. Register service worker (requires HTTPS or localhost)
if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
  window.addEventListener('load', function() {
    navigator.serviceWorker.register('/sw.js').then(function(reg) {
      console.log('[PWA] Service worker registered, scope:', reg.scope);
    }).catch(function(err) {
      console.warn('[PWA] Service worker registration failed:', err);
    });
  });
}

// 3. Install prompt — mobile only, two-tier dismissal
(function initInstallPrompt() {
  if (typeof window === 'undefined') return;

  // Only show on touch/mobile devices — never on desktop
  var isTouchDevice = window.matchMedia('(pointer: coarse)').matches;
  if (!isTouchDevice) return;

  var SNOOZE_KEY  = 'pwa_install_snoozed_at';   // "Not now" — 30-day cooldown
  var NEVER_KEY   = 'pwa_install_never';          // "Don't ask again" — permanent
  var SESSION_KEY = 'pwa_install_shown';
  var SNOOZE_TTL  = 30 * 24 * 60 * 60 * 1000;

  function shouldShow() {
    try {
      if (sessionStorage.getItem(SESSION_KEY)) return false;
      if (localStorage.getItem(NEVER_KEY)) return false;
      var t = parseInt(localStorage.getItem(SNOOZE_KEY) || '0', 10);
      if (t > 0 && Date.now() - t < SNOOZE_TTL) return false;
      return true;
    } catch(e) { return false; }
  }
  function snooze() {
    try { localStorage.setItem(SNOOZE_KEY, String(Date.now())); sessionStorage.setItem(SESSION_KEY, '1'); } catch(e) {}
  }
  function neverShow() {
    try { localStorage.setItem(NEVER_KEY, '1'); sessionStorage.setItem(SESSION_KEY, '1'); } catch(e) {}
  }

  var SHEET_STYLE = 'position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid #ddd;padding:16px 20px 28px;box-shadow:0 -2px 12px rgba(0,0,0,.15);z-index:9999;font-family:sans-serif;font-size:15px';
  var CLOSE_STYLE = 'position:absolute;top:8px;right:12px;background:none;border:none;font-size:20px;cursor:pointer;color:#666;line-height:1';
  var BTN_ROW     = 'display:flex;gap:8px;margin-top:12px';
  var BTN_PRIMARY = 'flex:1;padding:10px 0;background:#0056d2;color:#fff;border:none;border-radius:6px;font-size:14px;cursor:pointer';
  var BTN_GHOST   = 'flex:1;padding:10px 0;background:none;color:#555;border:1px solid #ccc;border-radius:6px;font-size:14px;cursor:pointer';

  function createSheet(inner) {
    var el = document.createElement('div');
    el.id = 'pwa-install-sheet';
    el.setAttribute('style', SHEET_STYLE);
    el.innerHTML = inner;
    document.body.appendChild(el);
    return el;
  }

  if (!shouldShow()) return;

  // iOS Safari — no beforeinstallprompt event
  var isIos = /iPhone|iPad|iPod/i.test(navigator.userAgent) && !window.navigator.standalone;
  if (isIos) {
    window.addEventListener('load', function() {
      if (!shouldShow()) return;
      var el = createSheet(
        '<button style="' + CLOSE_STYLE + '" id="pwa-ios-close">×</button>' +
        '<p style="margin:0">To install, tap <strong>⬆ Share</strong> then <strong>Add to Home Screen</strong>.</p>' +
        '<div style="' + BTN_ROW + '">' +
          '<button style="' + BTN_GHOST + '" id="pwa-ios-snooze">Not now</button>' +
          '<button style="' + BTN_GHOST + '" id="pwa-ios-never">Don\'t ask again</button>' +
        '</div>'
      );
      el.querySelector('#pwa-ios-close').onclick   = function() { snooze(); el.remove(); };
      el.querySelector('#pwa-ios-snooze').onclick  = function() { snooze(); el.remove(); };
      el.querySelector('#pwa-ios-never').onclick   = function() { neverShow(); el.remove(); };
    });
    return;
  }

  // Android Chrome — capture beforeinstallprompt
  var deferredPrompt = null;
  window.addEventListener('beforeinstallprompt', function(e) {
    e.preventDefault();
    deferredPrompt = e;
    if (!shouldShow()) return;
    var el = createSheet(
      '<button style="' + CLOSE_STYLE + '" id="pwa-and-close">×</button>' +
      '<p style="margin:0">Add this app to your home screen for a faster experience.</p>' +
      '<div style="' + BTN_ROW + '">' +
        '<button style="' + BTN_PRIMARY + '" id="pwa-and-install">Add to Home Screen</button>' +
        '<button style="' + BTN_GHOST + '" id="pwa-and-never">Don\'t ask again</button>' +
      '</div>'
    );
    el.querySelector('#pwa-and-close').onclick   = function() { snooze(); el.remove(); };
    el.querySelector('#pwa-and-never').onclick   = function() { neverShow(); el.remove(); };
    el.querySelector('#pwa-and-install').onclick = function() {
      deferredPrompt.prompt();
      deferredPrompt.userChoice.then(function() { neverShow(); el.remove(); });
    };
  });
}());
""",
))

# ── 11. Sync notification types and run migrations on init ────────────────────
hooks.Filters.CLI_DO_INIT_TASKS.add_items([
    ("lms", "python manage.py lms migrate pwa_notifications"),
    ("lms", "python manage.py lms sync_pwa_notification_types"),
])

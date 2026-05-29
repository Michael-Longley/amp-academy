from __future__ import annotations
import os
from tutor import hooks

HERE = os.path.dirname(os.path.abspath(__file__))

# ── 1. Tutor config keys ──────────────────────────────────────────────────────
# Values become available as {{ AMP_THEME_* }} in all Jinja2 templates that
# Tutor renders, including SCSS partials and HTML templates.
hooks.Filters.CONFIG_DEFAULTS.add_items([
    ("AMP_THEME_PRIMARY_COLOR",    "#FFB100"),   # Amber — interactive/CTA
    ("AMP_THEME_SECONDARY_COLOR",  "#24292E"),   # Foundation Slate — structural
    ("AMP_THEME_ACCENT_COLOR",     "#FFB100"),   # Amber (same as primary)
    ("AMP_THEME_CONFIRM_COLOR",    "#2980B9"),   # Confirm Blue — info/submit actions
    ("AMP_THEME_NOTICE_COLOR",     "#C0392B"),   # Notice Red — negative/error notifications
    ("AMP_THEME_TEXT_COLOR",       "#24292E"),   # Slate
    ("AMP_THEME_BG_COLOR",         "#F0F2F5"),   # Light Grey
    ("AMP_THEME_NAVBAR_BG",        "#24292E"),   # Foundation Slate
    ("AMP_THEME_NAVBAR_TEXT",      "#ffffff"),
    ("AMP_THEME_LINK_COLOR",       "#2980B9"),   # Confirm Blue
    ("AMP_THEME_FONT_FAMILY",      "Inter, system-ui, -apple-system, sans-serif"),
    ("AMP_THEME_GOOGLE_FONT_URL",  "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"),
    ("AMP_THEME_SITE_NAME",        "Amp Academy"),
    ("AMP_THEME_FOOTER_COPYRIGHT", "Amp Academy. All rights reserved."),
    ("AMP_THEME_SUPPORT_EMAIL",    "support@amp-academy.com"),
])

# ── 2. Register the templates directory ──────────────────────────────────────
# Tells Tutor's template engine to look inside our package for templates.
hooks.Filters.ENV_TEMPLATE_ROOTS.add_item(
    os.path.join(HERE, "templates"),
)

# ── 3. Copy theme files into the build context ───────────────────────────────
# Source: relative to template root registered above.
# Destination: relative to TUTOR_ROOT (e.g. ~/.local/share/tutor).
# Tutor renders Jinja2 variables before copying.
hooks.Filters.ENV_TEMPLATE_TARGETS.add_items([
    (
        "amp-theme",            # source path inside templates/
        "build/openedx/themes", # destination inside TUTOR_ROOT
    ),
])

# ── 4. Include underscore-prefixed SCSS files in Jinja2 rendering ─────────────
# Tutor skips files whose names start with _ by default.
# This regex forces rendering for our theme partials and HTML templates.
hooks.Filters.ENV_PATTERNS_INCLUDE.add_items([
    r"amp-theme/.*\.scss$",
    # HTML templates are pure Django templates — Jinja2 cannot process {% load %},
    # {% trans %}, {% url %} etc. Colors are handled entirely by SCSS.
])

# ── 5. Set the active theme during platform initialization ───────────────────
# Runs `settheme amp-theme` automatically when `tutor local do init` executes.
hooks.Filters.CLI_DO_INIT_TASKS.add_item(
    ("lms", (
        "python manage.py lms shell -c \""
        "from openedx.core.djangoapps.theming.models import SiteTheme;"
        "from django.contrib.sites.models import Site;"
        "[SiteTheme.objects.update_or_create(site=s, defaults={'theme_dir_name': 'amp-theme'})"
        " for s in Site.objects.all()]"
        "\""
    )),
)

# ── 6. MFE brand config keys ─────────────────────────────────────────────────
# URL where the built Paragon light-theme CSS is served.
# Defaults point at the committed build output in this repo via GitHub raw URLs.
# Override with a CDN URL via: tutor config save --set AMP_THEME_BRAND_LIGHT_URL="..."
# No MFE image rebuild is needed when only changing this URL — just restart.
hooks.Filters.CONFIG_DEFAULTS.add_items([
    ("AMP_THEME_BRAND_LIGHT_URL",
     "https://raw.githubusercontent.com/michael-longley/amp-academy/main"
     "/tutor-amp-theme/brand/paragon/build/themes/light/variables.css"),
])

# ── 7. Inject PARAGON_THEME_URLS into MFE production environment ──────────────
# Requires tutor-mfe plugin to be installed and enabled.
# MFEs load the CSS at runtime (no image rebuild needed when the URL changes).
# Core CSS is intentionally omitted — MFEs fall back to bundled Paragon defaults
# for spacing/breakpoints, and pick up Amp Academy colors from the light theme.
# The JSON value must be single-line; Tutor renders {{ }} before writing the file.
hooks.Filters.ENV_PATCHES.add_item((
    "mfe-env-production",
    "PARAGON_THEME_URLS='"
    '{"themes":{"light":{"urls":{"default":"{{ AMP_THEME_BRAND_LIGHT_URL }}"},"default":true}}}'
    "'",
))

# ── 8. Expose identity config values to Django/Open edX settings ─────────────
hooks.Filters.ENV_PATCHES.add_items([
    ("openedx-lms-common-settings",
     'PLATFORM_NAME = "{{ AMP_THEME_SITE_NAME }}"'),
    ("openedx-cms-common-settings",
     'PLATFORM_NAME = "{{ AMP_THEME_SITE_NAME }}"'),
])

# ── 9. Optional navigation link in the LMS header ────────────────────────────
# Set AMP_THEME_TOOL_LINK_URL to a non-empty string to add a nav tab in the
# header that links to an external tool (e.g. the NEC load calculator).
# Leave empty ("") to hide the link entirely.
# Changes take effect after: tutor config save && tutor local restart
hooks.Filters.CONFIG_DEFAULTS.add_items([
    ("AMP_THEME_TOOL_LINK_URL",   ""),        # e.g. "https://calculator.amp-academy.com"
    ("AMP_THEME_TOOL_LINK_LABEL", "Tools"),   # Display text in the nav bar
])

# ── 10. Install brand npm package into MFE Docker image (compile-time, optional) ─
# This bakes the brand SCSS into MFEs at build time as a fallback for older
# Paragon versions that don't support runtime CSS loading.
# The gitpkg.now.sh service resolves npm installs from a monorepo subdirectory.
hooks.Filters.ENV_PATCHES.add_item((
    "mfe-dockerfile-post-npm-install",
    "RUN npm install --legacy-peer-deps "
    "'@amp-academy/brand@https://gitpkg.now.sh/michael-longley/amp-academy/tutor-amp-theme/brand?main'",
))

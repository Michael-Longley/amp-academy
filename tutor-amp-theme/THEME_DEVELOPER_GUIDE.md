# Amp Academy Theme — Developer Guide

This guide explains how to keep the Amp Academy visual identity consistent across every part of the platform: LMS Django pages, MFE micro-frontends, and external apps like the NEC load calculator.

---

## 1. Architecture Overview

Open edX has a **split architecture** that requires two separate theming approaches:

```
┌─────────────────────────────────────────────────────────────┐
│  LMS / CMS (Django)           MFEs (React)                  │
│  /dashboard, /courses, etc.   /learner-dashboard, /authn,   │
│                               /learning, /profile           │
│  ┌─────────────────────┐     ┌───────────────────────────┐  │
│  │ Bootstrap SCSS       │     │ Paragon CSS custom props  │  │
│  │ Compiled at build    │     │ Loaded at runtime via URL │  │
│  │ AMP_THEME_* → CSS    │     │ PARAGON_THEME_URLS env var│  │
│  └─────────────────────┘     └───────────────────────────┘  │
│         ▲                              ▲                     │
│  tutor images build openedx    tutor local restart           │
│  (10-20 min)                   (seconds, no rebuild)         │
└─────────────────────────────────────────────────────────────┘
```

**LMS/CMS layer** — `tutor-amp-theme` compiles Bootstrap SCSS into the OpenEdX Docker image. Theme values come from `AMP_THEME_*` Tutor config keys, which Tutor injects as Jinja2 variables into SCSS partials before compilation. Changing any color requires a full image rebuild.

**MFE layer** — MFEs use the Paragon design system and load their brand via CSS custom properties (`--pgn-color-*`) from a URL. The `tutor-amp-theme` plugin injects `PARAGON_THEME_URLS` into the MFE production environment, pointing to a pre-built `variables.css` file in this repo. No image rebuild is needed — just `tutor local restart`.

**External apps** — Apps outside the LMS container (e.g. the NEC load calculator) cannot access the LMS CSS. Mirror the palette manually using the same CSS custom property names and the canonical color values listed in Section 6.

---

## 2. Styling a Django Plugin (LMS Templates)

Any Django app installed inside the LMS container can inherit the full Amp Academy theme — header, footer, Bootstrap, and `--amp-*` CSS variables — by extending the LMS base template.

### The correct base template

```django
{% extends "main.html" %}
{% load i18n static %}

{% block title %}My Page — {{ settings.PLATFORM_NAME }}{% endblock %}

{% block headextra %}
  {# Load plugin-specific CSS here. Do not recreate a page shell. #}
  <link rel="stylesheet" href="{% static 'my_plugin/my_plugin.css' %}">
{% endblock %}

{% block content %}
  <main class="container" style="margin: 2rem auto;">
    {% block page_content %}{% endblock %}
  </main>
{% endblock %}
```

`main.html` renders the full themed header (logo, navigation, user dropdown) and footer automatically. Your plugin only provides the `content` block.

### Available CSS variables

The `--amp-*` CSS custom properties are defined globally by `_extras.scss` and available on every LMS page:

| Variable | Value | Use |
|---|---|---|
| `--amp-primary` | `#FFB100` | Amber — buttons, accents, progress bars |
| `--amp-secondary` | `#24292E` | Slate — headers, cards, dark surfaces |
| `--amp-confirm` | `#2980B9` | Blue — info states, links |
| `--amp-notice` | `#C0392B` | Red — errors, warnings |
| `--amp-bg` | `#F0F2F5` | Light grey — page background |
| `--amp-text` | `#24292E` | Slate — body text |
| `--amp-link` | `#2980B9` | Blue — hyperlinks |
| `--amp-navbar-bg` | `#24292E` | Slate — navigation background |
| `--amp-navbar-text` | `#ffffff` | White — navigation text |
| `--amp-radius` | `6px` | Standard border radius |
| `--amp-transition` | `0.18s ease` | Standard transition timing |

Use these in your plugin's CSS file:

```css
.my-widget-header {
  background: var(--amp-secondary, #24292E);
  color: #fff;
}

.my-widget-cta {
  background: var(--amp-primary, #FFB100);
  color: #24292E;
  border-radius: var(--amp-radius, 6px);
}

.my-progress-fill {
  background: var(--amp-primary, #FFB100);
}
```

### Reference implementation

The `tutor-student-sponsorship` plugin uses this pattern. See:
- `student_sponsorship/templates/student_sponsorship/base.html` — extends `main.html`
- `student_sponsorship/static/student_sponsorship/sponsorship.css` — plugin-specific CSS using `--amp-*` variables

---

## 3. Styling a React MFE

MFEs that use `@openedx/paragon` receive Amp Academy colors automatically via the runtime CSS loading path. No additional configuration is needed for new MFEs.

### How it works

1. When `tutor config save` runs, `tutor-amp-theme` injects `PARAGON_THEME_URLS` into the MFE `.env.production` file.
2. At startup, each MFE fetches the `variables.css` file from the URL in `PARAGON_THEME_URLS`.
3. The CSS file defines `--pgn-color-*` custom properties that Paragon components reference.

### Available Paragon CSS variables (Amp Academy theme)

| Variable | Value | Paragon usage |
|---|---|---|
| `--pgn-color-primary-base` | `#FFB100` | Primary buttons, active states |
| `--pgn-color-primary-hover` | `#CC8D00` | Primary button hover |
| `--pgn-color-primary-active` | `#996A00` | Primary button pressed |
| `--pgn-color-brand-base` | `#FFB100` | Brand color (same as primary) |
| `--pgn-color-accent-a-base` | `#24292E` | Accent A — dark slate |
| `--pgn-color-accent-a-hover` | `#3D4348` | Accent A hover |

Use these in custom MFE component CSS:

```css
.my-mfe-header {
  background: var(--pgn-color-accent-a-base, #24292E);
  color: #fff;
}

.my-mfe-cta {
  background: var(--pgn-color-primary-base, #FFB100);
  color: #24292E;
}
```

Always include a hardcoded fallback value (the second argument to `var()`) — this shows if `variables.css` fails to load.

### Registering a new MFE

No action needed in `tutor-amp-theme`. The `PARAGON_THEME_URLS` environment variable is injected globally for all MFEs by the `mfe-env-production` patch. As long as your MFE uses `@openedx/paragon`, it will pick up the theme.

For compile-time fallback (Paragon versions < 22 that don't support runtime CSS loading), the `@amp-academy/brand` npm package is also installed into every MFE image via the `mfe-dockerfile-post-npm-install` patch.

---

## 4. Styling an External App

Apps running outside the LMS container (like the NEC load calculator) cannot access the LMS or MFE CSS files. Mirror the Amp Academy palette using local CSS custom properties.

### Canonical palette

Define these in your app's root CSS:

```css
:root {
  --amp-primary:     #FFB100;   /* Amber */
  --amp-secondary:   #24292E;   /* Foundation Slate */
  --amp-confirm:     #2980B9;   /* Confirm Blue */
  --amp-notice:      #C0392B;   /* Notice Red */
  --amp-bg:          #F0F2F5;   /* Light Grey */
  --amp-text:        #24292E;   /* Slate */
  --amp-link:        #2980B9;   /* Blue */
  --amp-navbar-bg:   #24292E;   /* Slate */
  --amp-navbar-text: #ffffff;
  --amp-radius:      6px;
  --amp-transition:  0.18s ease;
  --amp-font:        'Inter', system-ui, -apple-system, sans-serif;
}
```

Add the Inter font from Google:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

### Navigation continuity

To make the external app feel connected to the LMS, add a branded back-link in the app's header. Example for the NEC load calculator:

```html
<header class="app-bar">
  <a href="https://amp-academy.com" class="app-bar__home">
    ← Amp Academy
  </a>
  <span class="app-bar__title">NEC Load Calculator</span>
</header>
```

Style it using the `--amp-*` variables above.

### Keeping colors in sync

When `AMP_THEME_PRIMARY_COLOR` changes, update the external app's `:root` block manually. There is no automatic synchronization — external apps are not part of the Tutor render pipeline.

---

## 5. Adding Navigation Links to the LMS Header

The header supports one optional external-tool link, configurable without a code change.

### Add a link

```bash
tutor config save --set AMP_THEME_TOOL_LINK_URL="https://calculator.amp-academy.com"
tutor config save --set AMP_THEME_TOOL_LINK_LABEL="NEC Calculator"
tutor local restart
```

The link appears in the nav bar for both authenticated and unauthenticated users. It opens in a new tab with `rel="noopener noreferrer"`.

### Remove the link

```bash
tutor config save --set AMP_THEME_TOOL_LINK_URL=""
tutor local restart
```

### How it works

The `{% if AMP_THEME_TOOL_LINK_URL %}` block in `navbar-authenticated.html` and `navbar-not-authenticated.html` is a **Jinja2 conditional**, processed by `tutor config save` — not at request time. When the URL is empty, the block is omitted from the rendered Mako file entirely. When it has a value, a plain `<a>` tag is baked in.

This means the link state is a **deployment configuration**, not a runtime toggle. A `tutor local restart` is required when changing the URL.

### Adding more links (code change required)

To add multiple nav links or more complex navigation, edit the header templates directly:

- `tutoramptheme/templates/amp-theme/lms/templates/header/navbar-authenticated.html` — logged-in users
- `tutoramptheme/templates/amp-theme/lms/templates/header/navbar-not-authenticated.html` — visitors

The `.nav-tab` CSS class in `_extras.scss` handles all nav tab styling including hover and active states.

---

## 6. Updating Brand Colors

Changing `AMP_THEME_PRIMARY_COLOR` requires two separate steps because the LMS and MFE theming layers are independent.

### Step A — LMS / CMS (automatic via Tutor config)

```bash
tutor config save --set AMP_THEME_PRIMARY_COLOR="#NEW_COLOR"
tutor images build openedx   # rebuilds Docker image (~10-20 min)
tutor local restart
```

All `AMP_THEME_*` values are automatically injected into SCSS at build time. No manual file edits needed for the LMS layer.

### Step B — MFE brand package (manual)

The Paragon token files are static JSON and cannot reference Tutor config values. Update them manually:

1. Edit `brand/paragon/tokens/core/color.json` — update the `primary` and `brand` palette entries (all 9 shades).
2. Edit `brand/paragon/tokens/themes/light/color.json` — update `primary.base`, `primary.hover`, `primary.active`, `brand.base`, `brand.hover`, `brand.active`.
3. Edit `brand/paragon/_variables.scss` — update `$primary` and `$brand` to match.
4. Run the build:
   ```bash
   cd tutor-amp-theme/brand
   npm install   # first time only
   npm run build
   ```
5. Commit the generated output:
   ```bash
   git add brand/paragon/build/themes/light/variables.css
   git add brand/paragon/build/themes/light/index.css
   git commit -m "chore(theme): update Paragon tokens to new primary color"
   git push origin main
   ```
6. Restart Tutor — no image rebuild needed:
   ```bash
   tutor local restart
   ```

MFEs fetch `variables.css` at runtime from GitHub raw URL. The new colors take effect on next page load after restart. GitHub's CDN may cache the file for up to 5 minutes.

---

## 7. File Reference

### tutor-amp-theme

| File | Purpose |
|---|---|
| `tutoramptheme/__init__.py` | Tutor plugin entry point — all hook registrations, config defaults, env patches |
| `tutoramptheme/templates/amp-theme/lms/static/sass/partials/lms/theme/_variables.scss` | Bootstrap variable overrides for the LMS (`$primary`, `$body-bg`, etc.) — Jinja2-rendered |
| `tutoramptheme/templates/amp-theme/lms/static/sass/partials/lms/theme/_extras.scss` | Full custom CSS ruleset — defines `--amp-*` CSS variables and all component styles |
| `tutoramptheme/templates/amp-theme/lms/static/sass/partials/lms/theme/_fonts.scss` | Google Fonts import |
| `tutoramptheme/templates/amp-theme/cms/static/sass/partials/_variables.scss` | Bootstrap variable overrides for Studio/CMS |
| `tutoramptheme/templates/amp-theme/lms/templates/header/header.html` | Root LMS header template |
| `tutoramptheme/templates/amp-theme/lms/templates/header/navbar-authenticated.html` | Header nav for logged-in users — add nav links here |
| `tutoramptheme/templates/amp-theme/lms/templates/header/navbar-not-authenticated.html` | Header nav for visitors |
| `tutoramptheme/templates/amp-theme/lms/templates/header/user_dropdown.html` | User account dropdown menu |
| `tutoramptheme/templates/amp-theme/lms/templates/footer.html` | LMS footer |
| `tutoramptheme/templates/amp-theme/lms/templates/index_overlay.html` | Homepage hero section |
| `tutoramptheme/templates/amp-theme/lms/static/images/` | Logo assets (logo.png, logo-white.png, favicon.ico) |
| `brand/paragon/_variables.scss` | Paragon SCSS overrides — compile-time fallback for MFEs |
| `brand/paragon/_overrides.scss` | Paragon component CSS overrides — fallback values use amber/slate palette |
| `brand/paragon/tokens/core/color.json` | Full 9-shade palette for each color family |
| `brand/paragon/tokens/themes/light/color.json` | Semantic color mappings (base, hover, active states) |
| `brand/paragon/build/themes/light/variables.css` | **Built output — commit this file** — loaded by MFEs at runtime |

### tutor-student-sponsorship

| File | Purpose |
|---|---|
| `student_sponsorship/templates/student_sponsorship/base.html` | Portal base template — extends LMS `main.html` |
| `student_sponsorship/static/student_sponsorship/sponsorship.css` | Portal-specific CSS using `--amp-*` variables |

---

## 8. Troubleshooting

**MFE still shows wrong colors after push:**
- Check Network tab in DevTools — confirm `variables.css` is being fetched and contains `--pgn-color-primary-base: #FFB100FF`
- GitHub raw URLs have a ~5 min CDN cache. Wait and hard-refresh.
- Verify `PARAGON_THEME_URLS` is set in the MFE container: `docker exec <mfe-container> env | grep PARAGON`

**Nav link not showing after config change:**
- `tutor config save` must be run (not just `tutor local restart`) to re-render the Jinja2 templates
- Verify the URL is set: `tutor config printvalue AMP_THEME_TOOL_LINK_URL`

**Sponsorship portal shows wrong header:**
- Confirm `tutor images build openedx` has been run since the last theme update
- Confirm `tutor local do init` has been run to set `SiteTheme.theme_dir_name = 'amp-theme'`

**SCSS compilation fails with "no mixin named -assert-ascending":**
- This is a known libsass/Bootstrap 3 incompatibility affecting the RTL footer
- It only affects `lms-footer-edx-rtl.scss` — the main CSS files compile correctly
- Use `--skip-default` flag in `compile_sass.py` as a workaround

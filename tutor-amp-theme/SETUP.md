# tutor-amp-theme — Setup & Configuration

Custom Open edX theme for Amp Academy, packaged as a Tutor plugin.

## Installation

```bash
pip install "git+https://github.com/michael-longley/amp-academy.git#subdirectory=tutor-amp-theme"
tutor plugins enable amp-theme
tutor config save
tutor images build openedx   # 10–20 min — compiles SCSS into the Docker image
tutor local do init          # activates theme in the database (settheme)
tutor local restart
```

> **Note:** `tutor images build openedx` is required any time you change SCSS, HTML templates, or logo images. MFE colors (Paragon CSS variables) are loaded at runtime and do **not** require a rebuild — see [MFE Brand Theming](#mfe-brand-theming-paragon-css-variables) below.

---

## Configuration

All settings are prefixed with `AMP_THEME_`. Change any value with:

```bash
tutor config save --set AMP_THEME_PRIMARY_COLOR="#FFB100"
tutor images build openedx && tutor local restart
```

### Colors

| Key | Default | Description |
|---|---|---|
| `AMP_THEME_PRIMARY_COLOR` | `#FFB100` | Amber — interactive elements, CTA buttons, active states |
| `AMP_THEME_SECONDARY_COLOR` | `#24292E` | Foundation Slate — navbar, footer, hero backgrounds |
| `AMP_THEME_ACCENT_COLOR` | `#FFB100` | Amber (same as primary) — Open edX action/brand buttons |
| `AMP_THEME_CONFIRM_COLOR` | `#2980B9` | Confirm Blue — info alerts, submit/confirm actions |
| `AMP_THEME_NOTICE_COLOR` | `#C0392B` | Notice Red — negative notifications, danger/error states |
| `AMP_THEME_TEXT_COLOR` | `#24292E` | Body text |
| `AMP_THEME_BG_COLOR` | `#F0F2F5` | Page background |
| `AMP_THEME_NAVBAR_BG` | `#24292E` | Navigation bar background |
| `AMP_THEME_NAVBAR_TEXT` | `#ffffff` | Navigation bar text/link color |
| `AMP_THEME_LINK_COLOR` | `#2980B9` | Inline link color |

> **Amber button contrast:** Primary buttons use `SECONDARY_COLOR` (slate) as their text color. Amber (`#FFB100`) is too light for white text to pass WCAG AA contrast.

### Typography

| Key | Default | Description |
|---|---|---|
| `AMP_THEME_FONT_FAMILY` | `Inter, system-ui, -apple-system, sans-serif` | CSS font-family stack |
| `AMP_THEME_GOOGLE_FONT_URL` | Inter 400/500/600/700 from Google Fonts | `@import` URL for web font |

To use a different Google Font:
```bash
tutor config save --set AMP_THEME_GOOGLE_FONT_URL="https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap"
tutor config save --set AMP_THEME_FONT_FAMILY="Lato, sans-serif"
```

### Site Identity

| Key | Default | Description |
|---|---|---|
| `AMP_THEME_SITE_NAME` | `Amp Academy` | Site name used in logo alt text and templates |
| `AMP_THEME_FOOTER_COPYRIGHT` | `Amp Academy. All rights reserved.` | Footer copyright line |
| `AMP_THEME_SUPPORT_EMAIL` | `support@amp-academy.com` | Support email shown in footer |

---

## Replacing Logo Images

Place your brand assets in:

```
tutoramptheme/templates/amp-theme/openedx/themes/amp-theme/lms/static/images/
├── logo.png        ← ~200×60px, shown in LMS header/navbar (on dark slate background)
├── logo-white.png  ← ~200×60px, shown in LMS footer (on dark slate background)
└── favicon.ico     ← 16×16 and/or 32×32 multi-size ICO
```

The placeholder files included in this repo are minimal 1×1 pixel images. Replace them with your actual artwork, then rebuild:

```bash
tutor config save
tutor images build openedx
tutor local restart
```

---

## Modifying Theme Files

After any change to SCSS or HTML template files:

```bash
# Pull the latest plugin code
pip install --upgrade "git+https://github.com/michael-longley/amp-academy.git#subdirectory=tutor-amp-theme"

# Re-render Jinja2 templates and rebuild
tutor config save
tutor images build openedx
tutor local restart
```

---

## Development Workflow (Local)

For iterative theme development without waiting for full image rebuilds:

```bash
# Install from local source (run from the monorepo root)
pip install -e ./tutor-amp-theme/
tutor plugins enable amp-theme   # also runs tutor config save
```

`tutor plugins enable` automatically renders templates into `$(tutor config printroot)/env/build/openedx/themes/amp-theme/`. From there you can either do a full image rebuild (permanent) or use the hot-inject workflow below (temporary).

---

## Hot-inject: Applying Theme Changes Without Rebuilding the Image

Use this when you can't afford the 10–20 min image rebuild. The changes survive `tutor local restart` but are lost on a full `tutor local dc up --force-recreate`.

### 1 — Render templates

```bash
tutor config save
# Jinja2 variables are now substituted in:
# $(tutor config printroot)/env/build/openedx/themes/amp-theme/
```

### 2 — Copy theme files into the running container

```bash
CONTAINER=$(docker ps --filter "name=tutor_local-lms-1" --format "{{.Names}}")

# Copy SCSS source + images
docker cp "$(tutor config printroot)/env/build/openedx/themes/amp-theme" \
  "$CONTAINER:/openedx/themes/"

# Fix ownership (docker cp writes as root; the app runs as app:app)
docker exec -u root "$CONTAINER" chown -R app:app /openedx/themes/amp-theme
```

### 3 — Compile SCSS to CSS inside the container

`manage.py compilescss` does not exist in this version of Open edX. Use the npm script directly:

```bash
docker exec "$CONTAINER" bash -c \
  "cd /openedx/edx-platform && \
   python3 scripts/compile_sass.py \
     --theme-dir /openedx/themes \
     --theme amp-theme \
     --skip-default"
```

> **Known failure:** `lms-footer-edx-rtl.scss` fails with `no mixin named -assert-ascending` due to a libsass 3.3.2 / Bootstrap incompatibility. This only affects the edX-branded footer RTL file — `lms-main-v1.css` and the other main CSS files compile successfully and cover all standard LMS pages.

### 4 — Put compiled CSS where Django can serve it

Open edX serves themed CSS from `STATIC_ROOT/<theme-name>/css/`. Copy the compiled output there:

```bash
docker exec -u root "$CONTAINER" bash -c \
  "mkdir -p /openedx/staticfiles/amp-theme && \
   cp -r /openedx/themes/amp-theme/lms/static/css \
         /openedx/staticfiles/amp-theme/ && \
   chown -R app:app /openedx/staticfiles/amp-theme"
```

`ProductionStorage` uses `PipelineForgivingMixin`, so files missing from the static manifest fall back to their unhashed filename — no manifest update needed.

### 5 — Restart the LMS

```bash
tutor local restart lms
```

Refresh the browser. Color scheme, typography, and all SCSS-driven styles should now be active.

---

## First-Time Plugin Bootstrap (Plugin Not Installed)

If `tutor plugins list` shows `amp-theme` is missing entirely:

```bash
# 1. Install the package
pip install -e ./tutor-amp-theme/       # local dev
# or
pip install "git+https://github.com/michael-longley/amp-academy.git#subdirectory=tutor-amp-theme"

# 2. Enable (auto-runs config save)
tutor plugins enable amp-theme

# 3. Verify templates were rendered
ls "$(tutor config printroot)/env/build/openedx/themes/"
# Should show:  amp-theme/

# 4. Continue with hot-inject steps above, or do a full rebuild
```

> **Symptom if this is your problem:**
> `lms-1 | ValueError: Theme 'amp-theme' not found in any of the following themes dirs`
> The DB has `settheme amp-theme` but the theme files were never built into the image.

---

## MFE Brand Theming (Paragon CSS Variables)

The `brand/` directory is a self-contained npm package that generates Paragon CSS custom property files. MFEs load these at **runtime** — no image rebuild required when colors change.

### What it covers

| Area | Examples |
|---|---|
| Course learner experience | `/learning/` course player, unit navigation |
| Learner profile | `/profile/` |
| Authentication pages | `/authn/` login, register |
| Dashboard | `/dashboard/` (MFE version) |

### One-time setup (local)

```bash
cd tutor-amp-theme/brand
npm install          # installs @openedx/paragon CLI (~300 MB, one-time)
npm run build        # compiles tokens → CSS (~5 sec)
```

This generates `brand/paragon/build/themes/light/variables.css` — the Amp Academy color variables as CSS custom properties (`--pgn-color-*`).

> **Note:** The `build` script runs with `--exclude-core`. The core build requires spacing/breakpoint token definitions that are outside the scope of brand-only customization. MFEs fall back to their bundled Paragon defaults for those tokens, and pick up Amp Academy colors from the light theme file.

### Local preview (no Tutor needed)

```bash
cd tutor-amp-theme/brand
npm run preview      # builds CSS then serves at http://localhost:9090
```

Open **http://localhost:9090/preview.html** — shows all UI components (navbar, hero, cards, buttons, forms, alerts, progress bars, footer, color swatches) rendered with the current brand tokens.

Edit `paragon/tokens/themes/light/color.json`, run `npm run build`, refresh — changes are instant.

### Iterating on colors

All brand colors live in two JSON files:

| File | What it controls |
|---|---|
| `brand/paragon/tokens/core/color.json` | Raw hex palette (all 9 shades of primary, brand, accent-a/slate) |
| `brand/paragon/tokens/themes/light/color.json` | Semantic mappings (`primary.base`, `primary.hover`, `accent-a.base`, etc.) |

To change the primary color:
1. Edit `tokens/core/color.json` → update all `color.primary.*` and `color.brand.*` shades
2. Edit `tokens/themes/light/color.json` → update `primary.base`, `primary.hover`, `primary.active`, `primary.focus`
3. Run `npm run build`
4. Refresh `preview.html`
5. When happy, commit `brand/paragon/build/` — the GitHub raw URLs pick up automatically

### Pointing a live MFE at local CSS (while Tutor is running)

Add this to the MFE's `.env.local`:

```
PARAGON_THEME_URLS={"themes":{"light":{"urls":{"default":"http://host.docker.internal:9090/paragon/build/themes/light/variables.css"},"default":true}}}
```

Hard refresh the MFE page — it loads the CSS from your local server. No container restart.

### MFE config keys

| Key | Default | Description |
|---|---|---|
| `AMP_THEME_BRAND_LIGHT_URL` | GitHub raw URL | URL for `themes/light/variables.css` |

Change for production (e.g., CDN):
```bash
tutor config save --set AMP_THEME_BRAND_LIGHT_URL="https://cdn.amp-academy.com/brand/themes/light/variables.css"
tutor local restart   # picks up new URL — no image rebuild needed
```

### Committing build output

The `brand/paragon/build/` directory is **intentionally committed** so the GitHub raw URLs work in production without a separate CDN. After any color change:

```bash
npm run build
git add brand/paragon/build/
git commit -m "Update brand CSS build"
git push
```

---

## Verifying the Theme is Active

```bash
# Check the theme is registered in the database
tutor local exec lms python manage.py lms --settings=tutor.envs.lms shell -c \
  "from theming.models import SiteTheme; print(list(SiteTheme.objects.all()))"

# Check plugin is enabled
tutor plugins list

# Check a config value
tutor config printvalue AMP_THEME_PRIMARY_COLOR
```

---

## What Gets Customized

| Area | Method | Files |
|---|---|---|
| Colors | Bootstrap SCSS variables | `lms/static/sass/partials/lms/theme/_variables.scss` |
| Fonts | SCSS `@import` | `lms/static/sass/partials/lms/theme/_fonts.scss` |
| Extra CSS | Custom rules | `lms/static/sass/partials/lms/theme/_extras.scss` |
| LMS navbar + logo | Django template block override | `lms/templates/header.html` *(not yet created)* |
| LMS footer | Django template block override | `lms/templates/footer.html` *(not yet created)* |
| Studio navbar + logo | Django template block override | `cms/templates/header.html` *(not yet created)* |
| Studio colors | Bootstrap SCSS variables | `cms/static/sass/partials/_variables.scss` |
| Logos & favicon | Binary image files | `lms/static/images/` |
| MFE colors | Paragon CSS custom properties | `brand/paragon/tokens/` |

### Coverage summary

| Layer | Tool | Rebuild required? |
|---|---|---|
| LMS shell (header, footer, login, catalog) | SCSS → compiled into Docker image | Yes — `tutor images build openedx` |
| Studio (CMS) | SCSS → compiled into Docker image | Yes — `tutor images build openedx` |
| MFE pages (course player, profile, dashboard) | Paragon CSS variables loaded at runtime | No — commit build output and restart |

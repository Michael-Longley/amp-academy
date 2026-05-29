# Claude Instructions — Amp Academy

## Project Overview

Monorepo with three sub-projects:

| Directory | What it is |
|---|---|
| `nec-load-calculator/` | React + Vite SPA — NEC Article 220 electrical load calculator |
| `tutor-custom-caddy-routes/` | Python Tutor plugin — injects custom Caddy reverse-proxy routes into Open edX |
| `tutor-amp-theme/` | Python Tutor plugin — custom Open edX theme (colors, logos, fonts, header/footer) |

The two projects are deployed together: the load calculator runs as a Docker container on the same Tutor (Open edX) network, and the Caddy plugin routes `calculator.amp-academy.com` traffic to it.

---

## nec-load-calculator

**Stack:** React 19, Vite 7, plain CSS, Nginx (production), Docker

**Run locally:**
```bash
cd nec-load-calculator
npm install
npm run dev        # dev server at http://localhost:5173
```

**Build:**
```bash
npm run build      # outputs to dist/
```

**Docker (production):**
```bash
docker compose up -d                        # uses pre-built ghcr.io image
docker compose -f docker-compose.dev.yml up # builds locally, port 8888
```

**Key files:**
- `src/engine/calculator.js` — NEC 220 load calculation logic (Standard + Optional methods)
- `src/data/necTables.js` — NEC lookup tables (building types, range demand, optional method factors)
- `src/components/` — 6 UI components (one per form step + results panel)
- `src/App.jsx` — top-level state management; calls `calculateLoad()` and passes results down
- `vite.config.js` — base set to `./` for static/Nginx deployment

**Calculation flow:**
1. `App.jsx` calls `calculateLoad(inputs)` from `calculator.js` on every state change
2. `calculator.js` applies NEC 220.12 (lighting), 220.52 (small appliances), 220.53 (fastened), 220.54/55 (dryer/range), 220.60 (HVAC), or 220.82 (optional method)
3. Results flow to `ResultsPanel.jsx` as props

---

## tutor-custom-caddy-routes

**Stack:** Python, Tutor plugin API, PyYAML, Caddy (via Tutor)

**Install:**
```bash
pip install "git+https://github.com/michael-longley/amp-academy.git#subdirectory=tutor-custom-caddy-routes"
tutor plugins enable custom-caddy-routes
tutor config save && tutor local dc restart caddy
```

**Add/change routes (no reinstall):**
1. Edit `$TUTOR_ROOT/custom-caddy-routes.yml`
2. `tutor config save && tutor local dc restart caddy`

**Key files:**
- `tutorcustomcaddyroutes/__init__.py` — loads YAML, generates Caddy blocks, registers Tutor hook
- `tutorcustomcaddyroutes/config.yml` — bundled default routes (dev fallback)
- `pyproject.toml` — package metadata and Tutor entry point

**Route config schema:**
```yaml
routes:
  - name: "Human label"
    subdomain: "myapp"         # → myapp.<LMS_HOST>
    domain: "example.com"      # optional; overrides LMS_HOST
    container: "my-container"  # must be on tutor_local_default network
    port: 80
```

---

## tutor-amp-theme

**Stack:** Python, Tutor plugin API (>=15.0.0), Jinja2 (via Tutor), Bootstrap SCSS, Open edX theming

**Install:**
```bash
pip install "git+https://github.com/michael-longley/amp-academy.git#subdirectory=tutor-amp-theme"
tutor plugins enable amp-theme
tutor config save
tutor images build openedx   # SCSS is compiled at image build time (~10-20 min)
tutor local do init          # writes settheme to DB
tutor local restart
```

**Change a color or setting:**
```bash
tutor config save --set AMP_THEME_PRIMARY_COLOR="#003057"
tutor images build openedx && tutor local restart
```

**Key files:**
- `tutoramptheme/__init__.py` — all Tutor hooks (config defaults, template roots, patterns, init task)
- `tutoramptheme/templates/amp-theme/openedx/themes/amp-theme/lms/static/sass/partials/lms/theme/_variables.scss` — Bootstrap variable overrides (colors, fonts, borders)
- `tutoramptheme/templates/amp-theme/openedx/themes/amp-theme/lms/static/sass/partials/lms/theme/_extras.scss` — custom CSS rules layered on top of Bootstrap
- `tutoramptheme/templates/amp-theme/openedx/themes/amp-theme/lms/static/sass/partials/lms/theme/_fonts.scss` — Google Fonts import
- `tutoramptheme/templates/amp-theme/openedx/themes/amp-theme/lms/templates/header.html` — LMS navbar + logo override
- `tutoramptheme/templates/amp-theme/openedx/themes/amp-theme/lms/templates/footer.html` — LMS footer override
- `tutoramptheme/templates/amp-theme/openedx/themes/amp-theme/cms/static/sass/partials/_variables.scss` — Studio color overrides
- `tutoramptheme/templates/amp-theme/openedx/themes/amp-theme/cms/templates/header.html` — Studio navbar override
- `tutoramptheme/templates/amp-theme/openedx/themes/amp-theme/lms/static/images/` — logo.png, logo-white.png, favicon.ico (replace placeholders with real assets)
- `pyproject.toml` — package metadata and Tutor entry point

**Config keys (all `AMP_THEME_` prefixed):**
- Colors: `PRIMARY_COLOR`, `SECONDARY_COLOR`, `ACCENT_COLOR`, `TEXT_COLOR`, `BG_COLOR`, `NAVBAR_BG`, `NAVBAR_TEXT`, `LINK_COLOR`
- Typography: `FONT_FAMILY`, `GOOGLE_FONT_URL`
- Identity: `SITE_NAME`, `FOOTER_COPYRIGHT`, `SUPPORT_EMAIL`

**Rendering pipeline:**
1. `tutor config save` renders Jinja2 (`{{ AMP_THEME_* }}`) into `$(tutor config printroot)/build/openedx/themes/amp-theme/`
2. `tutor images build openedx` compiles SCSS → CSS inside the Docker build
3. `tutor local do init` runs `settheme amp-theme` in the LMS database
4. SCSS partials beginning with `_` are included via `ENV_PATTERNS_INCLUDE` (Tutor skips them by default)

**MFE pages** (`/learning/`, `/profile/`) are NOT covered — they use a separate `@edx/brand` npm package (future work).

---

## CI/CD

GitHub Actions (`.github/workflows/docker-publish.yml`) builds and pushes the Docker image to GitHub Container Registry on every push to `main` that touches `nec-load-calculator/`.

Image: `ghcr.io/michael-longley/amp-academy-load-calculator:latest`

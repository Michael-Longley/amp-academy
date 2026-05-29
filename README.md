# Amp Academy

Monorepo for Amp Academy's NEC electrical load calculator and its Open edX integration layer.

## What's in here

| Directory | Description |
|---|---|
| [`nec-load-calculator/`](nec-load-calculator/) | React SPA — calculates electrical load per NEC Article 220 |
| [`tutor-custom-caddy-routes/`](tutor-custom-caddy-routes/) | Tutor plugin — routes subdomains to Docker services via Caddy |
| [`tutor-amp-theme/`](tutor-amp-theme/) | Tutor plugin — custom Open edX theme (colors, logos, fonts, header/footer) |

---

## nec-load-calculator

A browser-based electrical load calculator that implements NEC Article 220 for dwelling units and other building types.

**Features:**
- NEC year selection (2014–2023)
- Standard method (220.12–220.60) and Optional method (220.82)
- Multi-step form: building config → appliances → HVAC → other loads
- Live results with demand factor breakdown and final load in VA and amps

**Quick start:**
```bash
cd nec-load-calculator
npm install
npm run dev   # http://localhost:5173
```

**Docker (production):**
```bash
cd nec-load-calculator
docker compose up -d
```

The production image is published to `ghcr.io/michael-longley/amp-academy-load-calculator:latest` via GitHub Actions on every push to `main`.

---

## tutor-custom-caddy-routes

A [Tutor](https://docs.tutor.edly.io/) plugin that extends Open edX's Caddy reverse proxy with custom subdomain routes. Designed to serve the load calculator (and any other service) alongside an Open edX instance without modifying Tutor's core config.

**Install:**
```bash
pip install "git+https://github.com/michael-longley/amp-academy.git#subdirectory=tutor-custom-caddy-routes"
tutor plugins enable custom-caddy-routes
tutor config save && tutor local dc restart caddy
```

See [`tutor-custom-caddy-routes/SETUP.md`](tutor-custom-caddy-routes/SETUP.md) for full setup and route configuration instructions.

---

## tutor-amp-theme

A Tutor plugin that applies a custom brand theme to the Open edX LMS and CMS/Studio. Configures colors, fonts, logos, and header/footer templates without modifying Tutor core.

**Install:**
```bash
pip install "git+https://github.com/michael-longley/amp-academy.git#subdirectory=tutor-amp-theme"
tutor plugins enable amp-theme
tutor config save
tutor images build openedx   # compiles SCSS into Docker image (~10-20 min)
tutor local do init          # activates theme in the database
tutor local restart
```

**Customize colors (example):**
```bash
tutor config save --set AMP_THEME_PRIMARY_COLOR="#003057"
tutor images build openedx && tutor local restart
```

See [`tutor-amp-theme/SETUP.md`](tutor-amp-theme/SETUP.md) for all config keys and the full deployment runbook.

---

## Architecture

```
calculator.amp-academy.com
        │
        ▼
   Caddy (Tutor)   ← tutor-custom-caddy-routes injects this route
        │
        ▼
load-calculator:80  ← nec-load-calculator Docker container
   (Nginx + SPA)
```

Both the load calculator container and the Open edX containers share the `tutor_local_default` Docker network.

---
# NEC Load Calculator

React SPA that calculates electrical load per **NEC Article 220** for dwelling units and other building types.

## Features

- NEC year selection (2014–2023)
- Standard method (220.12–220.60) and Optional method (220.82)
- Multi-step form: building config → fastened appliances → HVAC → other loads
- Live results with line-item demand factor breakdown and final load in VA and amps

## Development

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # output to dist/
npm run lint
```

## Docker

```bash
# Production — pull pre-built image
docker compose up -d

# Local build — serves on localhost:8888
docker compose -f docker-compose.dev.yml up
```

## Project structure

```
src/
├── engine/
│   └── calculator.js       # NEC 220 calculation logic
├── data/
│   └── necTables.js        # Lookup tables (building types, demand factors)
├── components/
│   ├── YearMethodBar.jsx   # NEC year & method selection
│   ├── BuildingConfig.jsx  # Step 1: building config
│   ├── ApplianceInputs.jsx # Step 2: fastened appliances & cord-plug loads
│   ├── HVACInputs.jsx      # Step 3: HVAC
│   ├── OtherLoads.jsx      # Step 4: other/continuous loads
│   └── ResultsPanel.jsx    # Live results
└── App.jsx                 # State management, calls calculateLoad()
```

## Deployment

The Docker image is published to `ghcr.io/michael-longley/amp-academy-load-calculator:latest` via GitHub Actions on push to `main`. It is served as a subdomain of the Open edX instance via the [`tutor-custom-caddy-routes`](../tutor-custom-caddy-routes/SETUP.md) plugin.

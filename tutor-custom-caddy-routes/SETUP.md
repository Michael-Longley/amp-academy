# tutor-custom-caddy-routes

Tutor plugin that adds custom Caddy reverse-proxy routes for services running
alongside Open edX on the `tutor_default` Docker network.

## How it works

Routes are defined in a YAML config file. Each route becomes a Caddy block that
proxies `<subdomain>.<LMS_HOST>` to a named Docker container. If the upstream
container goes down, Caddy serves a fallback error page.

## Config file location

The plugin loads routes from the **first file that exists**:

1. `$TUTOR_ROOT/custom-caddy-routes.yml` — server-side config (recommended for Droplet)
2. Bundled `tutorcustomcaddyroutes/config.yml` — local dev fallback

`TUTOR_ROOT` is typically `~/.local/share/tutor`. Check with: `tutor config printroot`

## Route schema

```yaml
routes:
  - name: "Human-readable label"  # shown in the fallback error page
    subdomain: "myapp"            # → myapp.<domain>
    domain: "example.com"         # optional: explicit domain (e.g. root domain); omit to use Tutor's LMS_HOST
    container: "my-container"     # must match container_name in docker-compose.yml
    port: 80                      # port the container listens on internally
```

The proxied container must be on the `tutor_default` Docker network. Add this to
that service's `docker-compose.yml`:

```yaml
networks:
  tutor-web:
    external: true
    name: tutor_local_default
```

## Installation (once)

```bash
pip install "git+https://github.com/michael-longley/amp-academy.git#subdirectory=tutor-custom-caddy-routes"
tutor plugins enable custom-caddy-routes
tutor config save
tutor local dc restart caddy
```

## Adding or changing a route (no reinstall needed)

1. Edit `$TUTOR_ROOT/custom-caddy-routes.yml` directly on the server
2. `tutor config save && tutor local dc restart caddy`

## Updating the plugin code (rare — only when `__init__.py` changes)

```bash
pip install --upgrade "git+https://github.com/michael-longley/amp-academy.git#subdirectory=tutor-custom-caddy-routes"
tutor config save && tutor local dc restart caddy
```

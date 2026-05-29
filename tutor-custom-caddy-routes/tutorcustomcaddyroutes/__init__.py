import os
import yaml
from tutor import hooks

HERE = os.path.dirname(os.path.abspath(__file__))

# Check for an external config file first (allows editing routes without reinstalling)
_tutor_root = os.environ.get("TUTOR_ROOT", os.path.expanduser("~/.local/share/tutor"))
_external_config = os.path.join(_tutor_root, "custom-caddy-routes.yml")
_bundled_config = os.path.join(HERE, "config.yml")

_config_path = _external_config if os.path.exists(_external_config) else _bundled_config

with open(_config_path) as f:
    _cfg = yaml.safe_load(f)


def _build_caddy_block(route: dict) -> str:
    """Generate a Caddy reverse-proxy block for one route entry."""
    name = route.get("name", route["subdomain"])
    subdomain = route["subdomain"]
    container = route["container"]
    port = route.get("port", 80)
    # If a domain is explicitly set, use it directly.
    # Otherwise fall back to {{ LMS_HOST }} (Tutor's Jinja2 variable).
    if "domain" in route:
        host = f"{subdomain}.{route['domain']}"
    else:
        host = f"{subdomain}.{{{{ LMS_HOST }}}}"
    return (
        f"{host} {{\n"
        f"    reverse_proxy {container}:{port} {{\n"
        f"        lb_try_duration 2s\n"
        f"    }}\n"
        f"    handle_errors {{\n"
        f'        respond "{name} is temporarily unavailable." 503\n'
        f"    }}\n"
        f"}}"
    )


_routes = _cfg.get("routes", [])
if _routes:
    hooks.Filters.ENV_PATCHES.add_item((
        "caddyfile",
        "\n\n".join(_build_caddy_block(r) for r in _routes),
    ))

from http.server import BaseHTTPRequestHandler
import json
import os
from pathlib import Path


def env_int(name, default):
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def env_bool(name, default):
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_float(name, default):
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def read_config_file(path):
    if not path:
        return {}
    config_path = Path(path)
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as handle:
        if config_path.suffix in {".json"}:
            data = json.load(handle)
        elif config_path.suffix in {".yaml", ".yml"}:
            import yaml

            data = yaml.safe_load(handle) or {}
        else:
            return {}
    return data if isinstance(data, dict) else {}


class BaseJSONHandler(BaseHTTPRequestHandler):
    def _send(self, code=200, data=None):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        if data is None:
            data = {}
        self.wfile.write(json.dumps(data).encode())

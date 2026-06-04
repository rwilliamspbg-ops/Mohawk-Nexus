#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
from prometheus_client import start_http_server, Counter, Gauge
import time


def _env_int(name, default):
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_bool(name, default):
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _read_config_file(path):
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


def _load_config():
    file_cfg = _read_config_file(os.environ.get("FL_CONFIG_FILE", ""))
    server_cfg = file_cfg.get("server", {}) if isinstance(file_cfg.get("server", {}), dict) else {}
    metrics_cfg = file_cfg.get("metrics", {}) if isinstance(file_cfg.get("metrics", {}), dict) else {}
    profiling_cfg = file_cfg.get("profiling", {}) if isinstance(file_cfg.get("profiling", {}), dict) else {}
    storage_cfg = file_cfg.get("storage", {}) if isinstance(file_cfg.get("storage", {}), dict) else {}

    return {
        "host": os.environ.get("FL_SERVER_HOST", str(server_cfg.get("host", "0.0.0.0"))),
        "port": _env_int("FL_SERVER_PORT", int(server_cfg.get("port", 9000))),
        "metrics_enabled": _env_bool("FL_METRICS_ENABLED", bool(metrics_cfg.get("enabled", True))),
        "metrics_port": _env_int("FL_METRICS_PORT", int(metrics_cfg.get("port", 9001))),
        "profiling_enabled": _env_bool("FL_PROFILING_ENABLED", bool(profiling_cfg.get("enabled", True))),
        "default_profile_duration_seconds": _env_int(
            "FL_PROFILING_DEFAULT_DURATION_SECONDS",
            int(profiling_cfg.get("default_duration_seconds", 2)),
        ),
        "state_dir": os.environ.get("FL_STATE_DIR", str(storage_cfg.get("state_dir", "run_data"))),
    }


CONFIG = _load_config()
STATE = Path(CONFIG["state_dir"]) / "rounds.json"
STATE.parent.mkdir(parents=True, exist_ok=True)

# Prometheus metrics
REQUESTS = Counter('fl_requests_total', 'Total HTTP requests to coordinator', ['method'])
UPDATES = Counter('fl_updates_total', 'Total updates received')
ROUNDS = Counter('fl_rounds_aggregated_total', 'Total rounds aggregated')
GLOBAL = Gauge('fl_global_value', 'Last aggregated global value')

class Handler(BaseHTTPRequestHandler):
    def _send(self, code=200, data=None):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        if data is None:
            data = {}
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        REQUESTS.labels(method='GET').inc()
        path = self.path.split('?')[0]
        if path == '/healthz':
            self._send(200, {'status': 'ok'})
            return
        if path == '/ready':
            self._send(200, {'ready': True})
            return
        if path.startswith('/debug/pprof') or path.startswith('/debug/profile'):
            if not CONFIG["profiling_enabled"]:
                self._send(404, {'error': 'profiling disabled'})
                return
            try:
                dur = int(CONFIG["default_profile_duration_seconds"])
                if '?' in self.path:
                    q = self.path.split('?', 1)[1]
                    for part in q.split('&'):
                        if part.startswith('duration='):
                            try:
                                dur = int(part.split('=', 1)[1])
                            except Exception:
                                pass
                # use pyinstrument to profile for `dur` seconds and return HTML
                try:
                    from pyinstrument import Profiler
                except Exception:
                    self._send(500, {'error': 'pyinstrument not installed'})
                    return
                profiler = Profiler()
                profiler.start()
                end = time.time() + dur
                while time.time() < end:
                    s = 0
                    for i in range(10000):
                        s += i * i
                profiler.stop()
                html = profiler.output_html()
                # save to workspace run_data for CI artifact capture
                profdir = STATE.parent / 'profiles'
                profdir.mkdir(parents=True, exist_ok=True)
                fname = profdir / f"fl-profile-{int(time.time())}.html"
                fname.write_text(html)
                # return html inline
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode())
            except Exception as e:
                self._send(500, {'error': str(e)})
            return
        # return current round
        if STATE.exists():
            content = json.loads(STATE.read_text())
        else:
            content = {'round': 0, 'global': 0.0}
        self._send(200, content)

    def do_POST(self):
        REQUESTS.labels(method='POST').inc()
        length = int(self.headers.get('Content-Length', '0'))
        body = self.rfile.read(length) if length else b''
        try:
            payload = json.loads(body.decode())
        except Exception:
            self._send(400, {'error': 'invalid json'})
            return
        # append update
        if STATE.exists():
            content = json.loads(STATE.read_text())
        else:
            content = {'round': 0, 'updates': []}
        content.setdefault('updates', []).append(payload.get('value', 0.0))
        UPDATES.inc()
        # simple aggregation when 2 updates collected
        if len(content['updates']) >= 2:
            vals = content['updates']
            agg = sum(vals) / len(vals)
            content = {'round': content.get('round', 0) + 1, 'global': agg, 'updates': []}
            ROUNDS.inc()
            GLOBAL.set(agg)
        STATE.write_text(json.dumps(content))
        self._send(200, content)

def main():
    if CONFIG["metrics_enabled"]:
        start_http_server(int(CONFIG["metrics_port"]))
    server = HTTPServer((CONFIG["host"], int(CONFIG["port"])), Handler)
    print(
        'FL coordinator listening on',
        CONFIG["port"],
        'metrics',
        CONFIG["metrics_port"] if CONFIG["metrics_enabled"] else 'disabled',
    )
    server.serve_forever()

if __name__ == '__main__':
    main()

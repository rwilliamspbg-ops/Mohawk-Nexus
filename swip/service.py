#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from prometheus_client import start_http_server, Counter, Gauge
import time
from pathlib import Path


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
    file_cfg = _read_config_file(os.environ.get("SWIP_CONFIG_FILE", ""))
    server_cfg = file_cfg.get("server", {}) if isinstance(file_cfg.get("server", {}), dict) else {}
    metrics_cfg = file_cfg.get("metrics", {}) if isinstance(file_cfg.get("metrics", {}), dict) else {}
    profiling_cfg = file_cfg.get("profiling", {}) if isinstance(file_cfg.get("profiling", {}), dict) else {}
    storage_cfg = file_cfg.get("storage", {}) if isinstance(file_cfg.get("storage", {}), dict) else {}

    return {
        "host": os.environ.get("SWIP_SERVER_HOST", str(server_cfg.get("host", "0.0.0.0"))),
        "port": _env_int("SWIP_SERVER_PORT", int(server_cfg.get("port", 9100))),
        "metrics_enabled": _env_bool("SWIP_METRICS_ENABLED", bool(metrics_cfg.get("enabled", True))),
        "metrics_port": _env_int("SWIP_METRICS_PORT", int(metrics_cfg.get("port", 9101))),
        "profiling_enabled": _env_bool("SWIP_PROFILING_ENABLED", bool(profiling_cfg.get("enabled", True))),
        "default_profile_duration_seconds": _env_int(
            "SWIP_PROFILING_DEFAULT_DURATION_SECONDS",
            int(profiling_cfg.get("default_duration_seconds", 2)),
        ),
        "state_dir": os.environ.get("SWIP_STATE_DIR", str(storage_cfg.get("state_dir", "run_data"))),
    }


CONFIG = _load_config()

REQUESTS = Counter('swip_requests_total', 'Total HTTP requests to SWIP service', ['method'])
OPERATIONS = Counter('swip_operations_total', 'Total operations performed')
LAST_OP = Gauge('swip_last_value', 'Last operation result')


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
                    for i in range(5000):
                        s += i * i
                profiler.stop()
                html = profiler.output_html()
                profdir = Path(CONFIG["state_dir"]) / 'profiles'
                profdir.mkdir(parents=True, exist_ok=True)
                fname = profdir / f"swip-profile-{int(time.time())}.html"
                fname.write_text(html)
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode())
            except Exception as e:
                self._send(500, {'error': str(e)})
            return
        self._send(200, {'status': 'ok'})

    def do_POST(self):
        REQUESTS.labels(method='POST').inc()
        length = int(self.headers.get('Content-Length', '0'))
        body = self.rfile.read(length) if length else b''
        try:
            payload = json.loads(body.decode())
        except Exception:
            self._send(400, {'error': 'invalid json'})
            return
        # Apply a deterministic operation so clients can validate response behavior.
        val = float(payload.get('value', 1))
        result = round(val * 1.5, 6)
        OPERATIONS.inc()
        LAST_OP.set(result)
        self._send(200, {'result': result})


def main():
    if CONFIG["metrics_enabled"]:
        start_http_server(int(CONFIG["metrics_port"]))
    server = HTTPServer((CONFIG["host"], int(CONFIG["port"])), Handler)
    print(
        'SWIP service listening on',
        CONFIG["port"],
        'metrics',
        CONFIG["metrics_port"] if CONFIG["metrics_enabled"] else 'disabled',
    )
    server.serve_forever()


if __name__ == '__main__':
    main()

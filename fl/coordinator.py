#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
from prometheus_client import start_http_server, Counter, Gauge
import cProfile
import pstats
from io import StringIO
import time


STATE = Path('run_data/rounds.json')
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
            try:
                dur = 2
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
    # start Prometheus metrics on 9001
    start_http_server(9001)
    server = HTTPServer(('0.0.0.0', 9000), Handler)
    print('FL coordinator listening on 9000, metrics on 9001')
    server.serve_forever()

if __name__ == '__main__':
    main()

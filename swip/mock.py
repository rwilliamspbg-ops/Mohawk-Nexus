#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from prometheus_client import start_http_server, Counter, Gauge

REQUESTS = Counter('swip_requests_total', 'Total HTTP requests to SWIP mock', ['method'])
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
        # pretend to do a small op and record metric
        val = payload.get('value', 1)
        OPERATIONS.inc()
        LAST_OP.set(val)
        self._send(200, {'result': val})

def main():
    # metrics on 9101, API on 9100
    start_http_server(9101)
    server = HTTPServer(('0.0.0.0', 9100), Handler)
    print('SWIP mock listening on 9100, metrics on 9101')
    server.serve_forever()

if __name__ == '__main__':
    main()

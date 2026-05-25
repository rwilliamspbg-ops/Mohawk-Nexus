#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path

STATE = Path('/data/rounds.json')
STATE.parent.mkdir(parents=True, exist_ok=True)

class Handler(BaseHTTPRequestHandler):
    def _send(self, code=200, data=None):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        if data is None:
            data = {}
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        # return current round
        if STATE.exists():
            content = json.loads(STATE.read_text())
        else:
            content = {'round': 0, 'global': 0.0}
        self._send(200, content)

    def do_POST(self):
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
        # simple aggregation when 2 updates collected
        if len(content['updates']) >= 2:
            vals = content['updates']
            agg = sum(vals) / len(vals)
            content = {'round': content.get('round', 0) + 1, 'global': agg, 'updates': []}
        STATE.write_text(json.dumps(content))
        self._send(200, content)

def main():
    server = HTTPServer(('0.0.0.0', 9000), Handler)
    print('FL coordinator listening on 9000')
    server.serve_forever()

if __name__ == '__main__':
    main()

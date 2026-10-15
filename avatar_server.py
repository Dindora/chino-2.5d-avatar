"""Local avatar bridge. Run: python avatar_server.py"""
import json
import threading
from collections import deque
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent
EVENTS = deque(maxlen=100)
LOCK = threading.Lock()
SEQUENCE = 0


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def reply(self, status, value):
        body = json.dumps(value, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def local_request(self):
        # Reject cross-origin browser writes and DNS rebinding; Python needs no Origin.
        allowed = {'127.0.0.1', 'localhost'}
        host = urlsplit('http://' + self.headers.get('Host', '')).hostname
        origin = self.headers.get('Origin')
        return host in allowed and (not origin or origin == 'http://' + self.headers.get('Host'))

    def do_GET(self):
        if not self.local_request():
            return self.reply(403, {'error': 'Local requests only'})
        path = urlsplit(self.path)
        if path.path == '/api/commands':
            try:
                after = int(parse_qs(path.query).get('after', ['0'])[0])
            except ValueError:
                return self.reply(400, {'error': 'Invalid cursor'})
            with LOCK:
                return self.reply(200, {'commands': [e for e in EVENTS if e['id'] > after], 'cursor': SEQUENCE})
        return super().do_GET()

    def do_POST(self):
        global SEQUENCE
        if not self.local_request():
            return self.reply(403, {'error': 'Local requests only'})
        if self.path != '/api/command':
            return self.reply(404, {'error': 'Unknown endpoint'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 16 * 1024 * 1024:
                return self.reply(413, {'error': 'Body must be 1 byte to 16 MiB'})
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                return self.reply(415, {'error': 'Use application/json'})
            command = json.loads(self.rfile.read(length))
            if not isinstance(command, dict) or command.get('type') not in ('say', 'expression', 'params', 'stop'):
                raise ValueError('Unknown command type')
            if command['type'] == 'say':
                if not isinstance(command.get('text', ''), str) or not isinstance(command.get('audio', ''), str):
                    raise ValueError('text and audio must be strings')
                audio = command.get('audio', '')
                if audio and not (audio.startswith('data:audio/') or (audio.startswith('/') and not audio.startswith('//') and '\\' not in audio)):
                    raise ValueError('audio must be a data:audio URL or local /path')
            if command['type'] == 'expression' and command.get('name') not in ('neutral', 'smile', 'usume', 'surprise', 'jito', 'winkL', 'winkR'):
                raise ValueError('Unknown expression')
            if command['type'] == 'params':
                values = command.get('values')
                if not isinstance(values, dict) or not values or any(type(v) not in (int, float) or not -100 <= v <= 100 for v in values.values()):
                    raise ValueError('values must contain finite numbers between -100 and 100')
        except (ValueError, UnicodeError) as exc:
            return self.reply(400, {'error': str(exc)})
        with LOCK:
            SEQUENCE += 1
            EVENTS.append({'id': SEQUENCE, **command})
            # The server, not the caller, owns the event id.
            EVENTS[-1]['id'] = SEQUENCE
            return self.reply(200, {'ok': True, 'id': SEQUENCE})


if __name__ == '__main__':
    print('Open http://127.0.0.1:8765/?robot=1 and click Enable robot audio.', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8765), Handler).serve_forever()

import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import avatar_server as bridge


class BridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), bridge.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = 'http://127.0.0.1:' + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, path, body=None, headers=None):
        request = Request(self.url + path, data=json.dumps(body).encode() if body is not None else None,
                          headers=headers or {'Content-Type': 'application/json'})
        with urlopen(request) as response:
            return json.load(response)

    def test_commands_and_cursor(self):
        cursor = self.request('/api/commands')['cursor']
        commands = [dict(type='say', text='你好'), dict(type='expression', name='smile'),
                    dict(type='params', values={'mouthOpen': .5}), dict(type='stop')]
        ids = [self.request('/api/command', c)['id'] for c in commands]
        events = self.request('/api/commands?after=' + str(cursor))
        self.assertEqual([c['type'] for c in events['commands']], [c['type'] for c in commands])
        self.assertEqual([c['id'] for c in events['commands']], ids)
        self.assertEqual(self.request('/api/commands?after=' + str(ids[-1]))['commands'], [])

    def test_invalid_and_cross_origin(self):
        for body in [dict(type='unknown'), dict(type='say', audio='https://example.com/x.wav'),
                     dict(type='expression', name='bad'), dict(type='params', values={'x': float('nan')}),
                     dict(type='say', text=[]), []]:
            with self.assertRaises(HTTPError) as caught:
                self.request('/api/command', body)
            self.assertEqual(caught.exception.code, 400)
        with self.assertRaises(HTTPError) as caught:
            self.request('/api/command', dict(type='stop'),
                         {'Content-Type': 'application/json', 'Origin': 'https://example.com'})
        self.assertEqual(caught.exception.code, 403)

    def test_server_owned_id(self):
        result = self.request('/api/command', dict(type='stop', id=-999))
        event = self.request('/api/commands?after=' + str(result['id'] - 1))['commands'][0]
        self.assertEqual(event['id'], result['id'])


if __name__ == '__main__':
    unittest.main()

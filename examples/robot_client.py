"""Use send() from your robot; no third-party Python packages required."""
import base64
import json
from pathlib import Path
from urllib.request import Request, urlopen


def send(command):
    request = Request('http://127.0.0.1:8765/api/command',
                      data=json.dumps(command).encode('utf-8'),
                      headers={'Content-Type': 'application/json'})
    with urlopen(request, timeout=10) as response:
        return json.load(response)


def say(text, audio_file=None):
    command = {'type': 'say', 'text': text}
    if audio_file:
        import mimetypes
        path = Path(audio_file)
        mime = mimetypes.guess_type(path.name)[0] or 'audio/wav'
        command['audio'] = 'data:' + mime + ';base64,' + base64.b64encode(path.read_bytes()).decode('ascii')
    return send(command)


if __name__ == '__main__':
    import sys
    send({'type': 'expression', 'name': 'smile'})
    print(say('欢迎回来，今天想聊些什么？', sys.argv[1] if len(sys.argv) > 1 else None))

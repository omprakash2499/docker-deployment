"""Non-destructive HTTP smoke test; accepts an optional base URL."""
import json
import sys
import urllib.request
base = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8080'
for path in ('/health', '/incidents'):
    with urllib.request.urlopen(base.rstrip('/') + path, timeout=5) as response:
        assert response.status == 200
        body = json.load(response)
        if path == '/health':
            assert body['status'] == 'ok'
        else:
            assert isinstance(body, list)
    print(path, 'PASS')

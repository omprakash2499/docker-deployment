"""Small WSGI incident API. Use synthetic data; access is local/SSM only."""
import json
import logging
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from http import HTTPStatus

LOG = logging.getLogger(__name__)

def create_app(database=None):
    path = database or os.getenv('DATABASE_PATH', '/data/incidents.db')
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path, timeout=10)) as db, db:
        db.execute("CREATE TABLE IF NOT EXISTS incidents (id INTEGER PRIMARY KEY, title TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open')")

    def app(environ, start_response):
        method = environ.get('REQUEST_METHOD', 'GET')
        route = environ.get('PATH_INFO', '/')
        code, result = 404, {'error': 'not found'}
        try:
            with closing(sqlite3.connect(path, timeout=10)) as db, db:
                db.row_factory = sqlite3.Row
                if route == '/health' and method == 'GET':
                    db.execute('SELECT count(*) FROM incidents').fetchone()
                    code, result = 200, {'status': 'ok', 'version': os.getenv('APP_VERSION', 'dev')}
                elif route == '/incidents' and method == 'GET':
                    code, result = 200, [dict(row) for row in db.execute('SELECT * FROM incidents ORDER BY id DESC LIMIT 100')]
                elif route == '/incidents' and method == 'POST':
                    try:
                        length = int(environ.get('CONTENT_LENGTH') or 0)
                    except ValueError:
                        length = -1
                    if length > 4096:
                        code, result = 413, {'error': 'request too large'}
                    elif length <= 0:
                        code, result = 400, {'error': 'JSON body required'}
                    elif environ.get('CONTENT_TYPE', '').split(';')[0].strip() != 'application/json':
                        code, result = 415, {'error': 'use application/json'}
                    else:
                        body = json.loads(environ['wsgi.input'].read(length))
                        title = body.get('title') if isinstance(body, dict) else None
                        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 200:
                            code, result = 400, {'error': 'title must contain 1 to 200 characters'}
                        else:
                            cursor = db.execute('INSERT INTO incidents (title) VALUES (?)', (title.strip(),))
                            code, result = 201, {'id': cursor.lastrowid, 'title': title.strip(), 'status': 'open'}
                elif route.startswith('/incidents/') and route.endswith('/resolve') and method == 'POST':
                    parts = route.split('/')
                    if len(parts) == 4 and parts[2].isascii() and parts[2].isdigit() and len(parts[2]) <= 18:
                        incident_id = int(parts[2])
                        cursor = db.execute("UPDATE incidents SET status='resolved' WHERE id=?", (incident_id,))
                        if cursor.rowcount:
                            code, result = 200, {'id': incident_id, 'status': 'resolved'}
        except (json.JSONDecodeError, UnicodeDecodeError):
            code, result = 400, {'error': 'invalid JSON'}
        except sqlite3.Error:
            LOG.exception('Database operation failed')
            code, result = 503, {'error': 'database unavailable'}
        payload = json.dumps(result).encode('utf-8')
        start_response(f'{code} {HTTPStatus(code).phrase}', [('Content-Type', 'application/json'), ('Content-Length', str(len(payload))), ('Cache-Control', 'no-store')])
        return [payload]
    return app

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    # Local development only. Docker uses Gunicorn.
    with make_server('127.0.0.1', 8080, create_app(os.getenv('DATABASE_PATH', './data/incidents.db'))) as server:
        print('Incident API listening on http://127.0.0.1:8080', flush=True)
        server.serve_forever()

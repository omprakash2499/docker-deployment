import io
import json
import sqlite3
from contextlib import closing
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from app import create_app

class IncidentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = str(Path(self.tmp.name) / 'incidents.db')
        self.app = create_app(self.path)

    def request(self, method='GET', path='/health', body=None, raw=None, content_type='application/json'):
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else b'')
        response = []
        env = {'REQUEST_METHOD': method, 'PATH_INFO': path, 'CONTENT_LENGTH': str(len(data)), 'CONTENT_TYPE': content_type, 'wsgi.input': io.BytesIO(data)}
        payload = b''.join(self.app(env, lambda status, headers: response.append(status)))
        return int(response[0].split()[0]), json.loads(payload)

    def test_health_checks_database(self):
        self.assertEqual(self.request()[0], 200)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('DROP TABLE incidents')
        with self.assertLogs('app', level='ERROR'):
            self.assertEqual(self.request()[0], 503)

    def test_create_list_resolve_and_persist(self):
        code, incident = self.request('POST', '/incidents', {'title': 'Deployment health check failed'})
        self.assertEqual(code, 201)
        self.assertEqual(self.request('GET', '/incidents')[1][0], incident)
        self.assertEqual(self.request('POST', f"/incidents/{incident['id']}/resolve")[0], 200)
        self.app = create_app(self.path)
        self.assertEqual(self.request('GET', '/incidents')[1][0]['status'], 'resolved')

    def test_invalid_titles(self):
        for body in ({}, [], {'title': ''}, {'title': '  '}, {'title': 1}, {'title': 'a' * 201}):
            with self.subTest(body=body):
                self.assertEqual(self.request('POST', '/incidents', body)[0], 400)

    def test_bad_json(self):
        for raw in (b'{', b'\xff'):
            self.assertEqual(self.request('POST', '/incidents', raw=raw)[0], 400)

    def test_large_request(self):
        self.assertEqual(self.request('POST', '/incidents', raw=b'x' * 4097)[0], 413)

    def test_media_type(self):
        self.assertEqual(self.request('POST', '/incidents', {'title': 'test'}, content_type='text/plain')[0], 415)

    def test_missing_incident_and_route(self):
        for path in ('/incidents/999/resolve', '/incidents/no/resolve', '/incidents/99999999999999999999999/resolve', '/missing'):
            self.assertEqual(self.request('POST', path)[0], 404)

    def test_connections_closed_on_success_and_error(self):
        original_connect = sqlite3.connect
        connections = []

        def track(*args, **kwargs):
            connection = original_connect(*args, **kwargs)
            connections.append(connection)
            return connection

        with patch('app.sqlite3.connect', side_effect=track):
            self.app = create_app(self.path)
            self.assertEqual(self.request()[0], 200)
            self.assertEqual(self.request('POST', '/incidents', raw=b'{')[0], 400)
            with closing(sqlite3.connect(self.path)) as db, db:
                db.execute('DROP TABLE incidents')
            with self.assertLogs('app', level='ERROR'):
                self.assertEqual(self.request()[0], 503)

        self.assertGreaterEqual(len(connections), 5)
        for connection in connections:
            with self.assertRaises(sqlite3.ProgrammingError):
                connection.execute('SELECT 1')

    def test_sql_input_stays_data(self):
        title = "'); DROP TABLE incidents; --"
        self.assertEqual(self.request('POST', '/incidents', {'title': title})[0], 201)
        self.assertEqual(self.request('GET', '/incidents')[1][0]['title'], title)

if __name__ == '__main__':
    unittest.main()

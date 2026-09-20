# Operations and failure exercises

## Persistence
Create an incident, save its returned ID, run `docker compose down`, then
`docker compose up -d --wait`. GET /incidents must still include that ID.
This proves container replacement persistence, not survival of host deletion.

## Recovery
Run `docker compose stop api`. The smoke script must fail. Run
`docker compose start api`, wait for health, and rerun the smoke script.
Note: Docker marks unhealthy containers; it does not restart them merely for
being unhealthy. Restart policies respond to process exit.

## Diagnosis
`docker compose ps` shows health; `docker compose logs --tail=50 api` shows
application logs. Permission denied under /data usually means a volume created
with different ownership; inspect ownership before changing anything. Never
solve it by running the whole application as root.

## Consistent backup
While running, use SQLite's backup API inside the container:
```bash
docker compose exec api python -c "import sqlite3; s=sqlite3.connect('/data/incidents.db'); d=sqlite3.connect('/tmp/backup.db'); s.backup(d); d.close(); s.close()"
docker compose cp api:/tmp/backup.db ./backup.db
```
Store backups outside Git. For a disposable restore exercise, stop the service,
copy the backup to the volume through a one-off container running as UID 10001,
start the service and check the recorded incident IDs. Do not restore over real
data without keeping a second backup. Automated backup/restore is future work.

## Interview discussion
Explain why /data is writable while the root filesystem is read-only; why the
host port binds to loopback; how SQLite limits scaling; and which evidence would
be needed before claiming availability or deployment performance improvements.

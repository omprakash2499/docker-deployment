# Incident API — Docker delivery project

An original incident API packaged for repeatable local and AWS deployment.
It demonstrates a non-root image, persistent storage, health checks, resource
limits and reproducible operational exercises. Maintainer: Omprakash Kasaraneni.

**Status:** Docker image build, container health, API smoke checks, data persistence and stop/start recovery verified locally.
AWS deployment and Jenkins integration remain pending.

## Run locally

Prerequisites: Docker Desktop running Linux containers, Compose v2, Python 3.10+.
Run from this repository in Git Bash, WSL or a Linux/macOS terminal:

```bash
python -m unittest discover -s tests -v
docker compose up --build -d --wait
python scripts/smoke.py
curl -sS -X POST http://localhost:8080/incidents -H 'Content-Type: application/json' -d '{"title":"Synthetic deployment failure"}'
curl -sS http://localhost:8080/incidents
curl -sS -X POST http://localhost:8080/incidents/1/resolve
```

If port 8080 is occupied, change the host port in compose.yaml and the smoke URL.
For an application-only preview without Docker: `python app.py`.

## API

| Method | Route | Purpose |
| --- | --- | --- |
| GET | /health | Database readiness and build version |
| GET | /incidents | Latest 100 incidents |
| POST | /incidents | Create with a JSON title, 1–200 characters |
| POST | /incidents/{id}/resolve | Idempotent resolution |

## Design choices

SQLite keeps the first deployment small and makes persistence visible. It is
a single-host design, without high availability. The API has no authentication:
bind locally and access the AWS host through SSM. Use synthetic incidents only.
Gunicorn runs the container; the Python built-in server is a local preview.
One worker with four threads avoids unnecessary memory use; SQLite serializes writes.
SQL values are parameterized, payloads are limited, and database errors return 503.

Image dependencies are built separately from the runtime. The base tag and
transitive dependency resolution can change: digest pinning and a fully hashed
dependency lock are future improvements, not claims of this initial release.

## Evidence to collect

Follow [operations](docs/operations.md). Record the commit, commands and actual
output for health, persistence and recovery. Record image size and vulnerability
scan results before describing this as tested. Do not add fake screenshots.

## Connected projects

`terraform-aws-labs` provisions ECR and a Docker host. `jenkins-cicd-labs` builds
this repository at a chosen commit and releases a digest-pinned image through SSM.

## Stop

`docker compose down` preserves incidents. `docker compose down -v` permanently
deletes this project's incident volume; use it only when the data is disposable.

See [validation](docs/validation.md).

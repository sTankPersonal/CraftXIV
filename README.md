# CraftXIV

A barebones Flask application with layered architecture, using Postgres as a
read-through cache in front of a pluggable external data source.

## Architecture

Dependency direction flows one way: `routes -> services -> repositories -> {models, datasources}`.

```
app/
├── api/            # Class-based views (Flask MethodView) + blueprint wiring
├── services/        # ResourceService: business logic between routes and the repository
├── repositories/     # ResourceRepository: cache-aside logic (Postgres first, DataSource on miss)
├── datasources/      # DataSource interface + ExampleDataSource placeholder implementation
├── models/           # SQLAlchemy ORM models
├── config.py          # Config / TestConfig
├── extensions.py       # db, migrate singletons
├── factory.py           # AppFactory: builds and configures the Flask app
└── wsgi.py                # Entrypoint used by gunicorn / `flask run`
```

### Cache-aside flow

`ResourceRepository.get(key)`:
1. Looks up `key` in the `cached_resources` Postgres table.
2. On a hit, returns the stored row.
3. On a miss, calls the injected `DataSource.fetch(key)`, persists the result, and returns it.

`ExampleDataSource` is a placeholder (calls `httpbin.org` as a stand-in). Swap
it for a real API client by implementing `DataSource` and passing the new
class into `ResourceRepository` in `app/api/routes.py` — no other layer needs
to change.

## Running locally with Docker

```bash
cp .env.example .env   # adjust values if needed
docker compose up --build
```

- `web`: Flask app served by gunicorn on http://localhost:5000, runs `flask db upgrade` on startup.
- `db`: Postgres 16, persisted in the `craftxiv_pgdata` volume.

Try it:

```bash
curl localhost:5000/health
curl localhost:5000/resources/foo   # "source": "origin" (first call)
curl localhost:5000/resources/foo   # "source": "cache"   (second call)
```

## Local development (without Docker)

```bash
python -m venv .venv
.venv/Scripts/activate         # .venv\Scripts\Activate.ps1 on PowerShell
pip install -r requirements-dev.txt

flask db upgrade                # requires a reachable Postgres, see DATABASE_URL in .env
pytest
```

## Database migrations

Schema changes go through Flask-Migrate:

```bash
flask db migrate -m "describe the change"
flask db upgrade
```

# CraftXIV

A personal FFXIV crafting-chain planner, in the spirit of Teamcraft. Log in with Google or
GitHub, look up any item, and recursively resolve everything you need to either **gather** or
**buy from an NPC for gil** to make it — with totals per item and per saved list. Postgres acts
as a read-through cache in front of the [Garland Tools](https://www.garlandtools.org/) API.

## Architecture

Dependency direction flows one way: `routes -> services -> repositories -> {models, datasources}`.

```
app/
├── api/              # Class-based views (Flask MethodView) + blueprint wiring: health, items, lists
├── auth/              # OAuth login (Authlib) + Flask-Login session wiring
├── services/           # Business logic between routes and repositories
├── repositories/        # Cache-aside logic (Postgres first, DataSource on miss) + list/user CRUD
├── datasources/          # ItemDataSource interface + GarlandToolsDataSource implementation
├── models/                # SQLAlchemy ORM models
├── config.py                # Config / TestConfig (all external URLs, scopes, secrets come from env)
├── extensions.py              # db, migrate, login_manager singletons
├── factory.py                  # AppFactory: builds and configures the Flask app
└── wsgi.py                      # Entrypoint used by gunicorn / `flask run`
```

### Domain model

- **Item** — a game item cached from Garland Tools, tagged with an `acquisition_type`
  (`craft` / `gather` / `vendor` / `unknown`).
- **ItemComponent** — a recipe ingredient edge (`quantity` of one item needed to craft another).
  Only `craft` items have these; `gather`/`vendor`/`unknown` items are always leaves.
- **User** — identified by OAuth provider + provider user id.
- **CraftingList** / **CraftingListItem** — a user's saved lists of items with quantities.

### Cache-aside item resolution

`ItemRepository.get_or_fetch(game_id)`:
1. Looks up `game_id` in the `items` Postgres table.
2. On a hit, returns the stored row (and its already-persisted `ItemComponent` children).
3. On a miss, calls `ItemDataSource.fetch_item(game_id)`, persists the item, then recursively
   calls itself for every crafting ingredient (so already-cached branches short-circuit), and
   finally records the `ItemComponent` edges. This is what lets `/items/<id>/tree` and
   `/items/<id>/requirements` work purely from the database once an item has been resolved once.

`GarlandToolsDataSource` is the concrete `ItemDataSource`. Swap in a different API by
implementing `ItemDataSource` and constructing it wherever `GarlandToolsDataSource.from_app_config`
is currently used (`app/api/item_routes.py`, `app/api/list_routes.py`) — no other layer changes.

## Use cases / API

All item endpoints are public (shared game reference data). All list endpoints require login.

| Use case | Endpoint |
|---|---|
| Log in | `GET /auth/login/<google\|github>` |
| Log out | `POST /auth/logout` |
| Search for an item | `GET /items/search?q=<text>` |
| Get an item | `GET /items/<game_id>` |
| Full crafting component tree | `GET /items/<game_id>/tree` |
| Recursive gather/buy requirements for one item | `GET /items/<game_id>/requirements?quantity=<n>` |
| Create/list crafting lists | `GET`/`POST /lists` |
| Get/rename/delete a list | `GET`/`PATCH`/`DELETE /lists/<id>` |
| Add/list items on a list | `GET`/`POST /lists/<id>/items` |
| Update/remove a list item | `PATCH`/`DELETE /lists/<id>/items/<item_id>` |
| Total gather/buy requirements for a whole list | `GET /lists/<id>/requirements` |

## Running locally with Docker

```bash
cp .env.example .env   # fill in GOOGLE_CLIENT_ID/SECRET and GITHUB_CLIENT_ID/SECRET
docker compose up --build
```

- `web`: Flask app served by gunicorn on http://localhost:5000, runs `flask db upgrade` on startup.
- `db`: Postgres 16, persisted in the `craftxiv_pgdata` volume.

### OAuth app setup

- **Google**: create an OAuth 2.0 Client ID at https://console.cloud.google.com/apis/credentials,
  add `http://localhost:5000/auth/callback/google` as an authorized redirect URI.
- **GitHub**: create an OAuth App at https://github.com/settings/developers, set the callback URL
  to `http://localhost:5000/auth/callback/github`.

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

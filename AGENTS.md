## Repo Context

- FastAPI-based REST API for LofiFocus.
- Main ASGI app object: `app.api.main:app` (imported and re-exposed via `app.main.app`).
- Uses PostgreSQL via SQLAlchemy ORM and Alembic migrations.
- JWT auth and Argon2 password hashing configured in `app/core/security.py` and `app/core/config.py`.

## Dev And Run Commands

- Install in editable mode with dev extras (recommended for tests):
  - `pip install -e .[dev]`
- Dev server (hot reload):
  - `uvicorn app.api.main:app --reload`
- Production-style run (if you need to exercise Gunicorn config):
  - `gunicorn -c gunicorn.conf.py app.api.main:app`

## Database And Migrations

- Default DB config is hardcoded in `app/core/config.py`:
  - DB name: `lofidb`
  - Admin user: `admin`
  - Admin password: `admin123`
  - Host: `localhost`
- Connection string helper: `app.core.config.get_db_url()`.
- Alembic config: `alembic.ini`, migrations in `alembic/versions/`.
- When changing models, use Alembic (do not hand-edit tables):
  - `alembic revision --autogenerate -m "Your message"`
  - `alembic upgrade head`

## Tests And How To Run Them

- Test framework: `pytest`.
- Pyproject config sets:
  - `testpaths = ["tests"]`
  - `pythonpath = ["."]` (so imports like `from app...` work from repo root).
- Full suite:
  - `pytest`
- Single test module (examples):
  - `pytest tests/test_api.py`
  - `pytest tests/test_repositories.py::TestUserRepository::test_create`

### Critical Test DB Behavior

- Tests use a real PostgreSQL database on `localhost`.
- `tests/conftest.py` creates and drops a separate DB `lofidb_test` using the admin credentials from `app/core/config.py`.
- Requirements for tests to pass:
  - A PostgreSQL server must be running on `localhost`.
  - The `admin` user with password `admin123` must exist and be allowed to create/drop databases.
- Session-scoped `engine` fixture:
  - Creates schema on `lofidb_test` via `Base.metadata.create_all(engine)`.
  - Disposes engine and drops `lofidb_test` at the end.
- `db` fixture:
  - Opens a connection and transaction per test.
  - Rolls back after each test, so direct `db.flush()`/`db.delete()` calls remain isolated.
- `test_api.py` overrides FastAPI dependency `get_db` to use a `Session` with `join_transaction_mode="create_savepoint"` and rolls everything back after each test.
- If tests fail with connection/auth errors, check local Postgres setup first, not the app code.

## API Structure

- Entrypoint `app/main.py` imports `app.models` to register all ORM models and includes routers from `app/api/routers`:
  - `auth`, `moods`, `tracks`, `playlists`, `favourites`, `sessions`.
- Health check endpoint:
  - `GET /health` returns `{"status": "ok"}`.
- Custom exception handling (non-obvious when changing repos):
  - `DuplicateError` → HTTP 409 with `{"detail": ...}`.
  - SQLAlchemy `IntegrityError` → HTTP 409 with generic constraint message.
  - `RepositoryError` → HTTP 400 with `{"detail": ...}`.
- When adding new repository-level errors, ensure they integrate with these handlers or add new handlers explicitly.

## ORM And Repositories

- Models live under `app/models/` and use SQLAlchemy ORM, including polymorphic `User` hierarchy and many-to-many relationships:
  - `Track` ↔ `Mood` via `TrackMood` table.
  - `Playlist` ↔ `Track`.
  - `Listener` ↔ favourite `Track`.
- Repositories under `app/repositories/` encapsulate DB access and raise domain errors:
  - `UserRepository`, `ListenerRepo`, `AdministratorRepo`, `MoodRepo`, `TrackRepo`, `PlaylistRepo`, `FocusSessionRepo`, `Exceptions`.
- Tests in `tests/test_repositories.py`, `tests/test_models.py`, `tests/test_cascade.py` encode the expected behavior for:
  - Uniqueness and duplicate handling.
  - Cascades and many-to-many cleanup.
  - Polymorphic queries.
- When changing models or repositories, update the corresponding tests instead of bypassing repository logic.

## Security And Auth Gotchas

- Password hashing uses Argon2 via `pwdlib.PasswordHash.recommended()`; do not replace with plain hashing.
- JWT tokens:
  - Created with `create_access_token(user_id, role)`.
  - Signed with `config["jwt_secret"]` and algorithm `config["jwt_algorithm"]`.
  - TTL is `config["jwt_expire_minutes"]` minutes.
- `decode_access_token` raises `jwt.InvalidTokenError` on issues; upstream code relies on that, so do not swallow these exceptions silently.

## How To Approach Changes

- Prefer working through repositories instead of direct ORM access inside routers/handlers.
- When modifying DB-related code, re-run at least:
  - `pytest tests/test_models.py`
  - `pytest tests/test_cascade.py`
  - `pytest tests/test_repositories.py`
  - `pytest tests/test_api.py`
- If you add new routes:
  - Register them in `app/api/main.py` via `app.include_router(new_router.router)`.
  - Add corresponding tests in `tests/test_api.py` or a new focused test module.

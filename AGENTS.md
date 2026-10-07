# Agent contract

This is the `jebaerme` Python package. Quality is a mechanical loop: a change is not done until format, lint, types, and tests all pass.

## Setup

```bash
uv sync --all-groups
cp .env.example .env
```

Never commit `.env`. Copy values from `.env.example` only.

## Layout

- `src/jebaerme/models/` — Pydantic schemas and settings only. No I/O.
- `src/jebaerme/db/` — persistence only. No HTTP, no business rules.
- `src/jebaerme/services/` — business rules. No FastAPI/router details, no SQL strings if a db module exists.
- `src/jebaerme/api/` — HTTP or CLI adapters only. Validate with Pydantic, call services, map errors.
- `src/jebaerme/main.py` — process entry (app factory or `main()`). No business logic.

## Commands

Prefer `just`:

- `just fmt` — format and autofix lint
- `just check` — format check, lint, types, tests (same as CI)
- `just test` — pytest
- `just run` — print the health payload

Raw equivalents:

```bash
uv run ruff format .
uv run ruff check --fix .
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest
uv run python -m jebaerme.main
```

## Done criteria

Do not consider a change finished until all of these pass:

1. `uv run ruff format --check .` (or format first with `uv run ruff format .`)
2. `uv run ruff check .`
3. `uv run ty check`
4. `uv run pytest`

## Conventions

- Type everything. No `Any`.
- Pydantic models at process boundaries.
- No business logic in adapters (`api/`) or `main.py`.
- No I/O in `models/`.
- No empty files except package-marker `__init__.py` files that already exist.
- Never commit `.env` or secrets.

## Adding a feature

1. Model — Pydantic schema / settings in `models/`.
2. db — persistence in `db/` if the feature stores data.
3. Service — business rules in `services/`.
4. Adapter — HTTP/CLI in `api/` (or `main.py` for process entry).
5. Test — pytest under `tests/`. No network, no secrets.

## Out of scope

- Do not add frameworks (FastAPI, SQLAlchemy, etc.) unless asked.
- Do not hand-edit `uv.lock`. Use `uv lock`, `uv add`, or `uv sync`.

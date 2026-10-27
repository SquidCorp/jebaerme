# Agent contract

This is a monorepo: Python API in `apps/api`, Next.js frontend in `apps/web`. Quality is a mechanical loop: a change is not done until the affected app's checks pass (`just check` covers both).

## Setup

```bash
uv sync --directory apps/api --all-groups
cp apps/api/.env.example apps/api/.env

pnpm --dir apps/web install
cp apps/web/.env.example apps/web/.env
```

Never commit `.env`. Copy values from `.env.example` only.

## Layout

```text
apps/api/   Python package `jebaerme` (FastAPI)
apps/web/   Next.js App Router (pnpm, TypeScript, Sass)
```

### `apps/api`

- `src/jebaerme/models/` — Pydantic schemas and settings only. No I/O.
- `src/jebaerme/db/` — persistence only. No HTTP, no business rules.
- `src/jebaerme/services/` — business rules. No FastAPI/router details, no SQL strings if a db module exists.
- `src/jebaerme/api/` — HTTP adapters only. Validate with Pydantic, call services, map errors.
- `src/jebaerme/main.py` — process entry (`uvicorn`). No business logic.

### `apps/web`

- App Router + TypeScript. Styles in Sass (`.scss`), not Tailwind.
- Browser calls Next.js only. Python is reached through Route Handlers under `app/api/` (Node gateway). Do not call the Python origin from client code.
- Gateway handlers proxy/map errors. No business rules there.
- Package manager is pnpm. Do not add npm/yarn lockfiles.

## Commands

Prefer `just`:

- `just install` — `uv sync` (API) + `pnpm install` (web)
- `just install-api` / `just install-web` — one side
- `just fmt` — format and autofix lint (API + web)
- `just fmt-api` / `just fmt-web` — one side
- `just check` — API + web gates (same as CI)
- `just check-api` / `just check-web` — one side
- `just test` — pytest
- `just dev-api` — FastAPI on `:8000`
- `just dev-studio` — LangGraph Studio local server on `:2024`
- `just dev-web` — Next.js on `:3000`
- `just run-dev` — both (API in the background, then Next.js)

Raw equivalents:

```bash
uv run --directory apps/api ruff format .
uv run --directory apps/api ruff check --fix .
uv run --directory apps/api ruff format --check .
uv run --directory apps/api ruff check .
uv run --directory apps/api ty check
uv run --directory apps/api pytest
uv run --directory apps/api python -m jebaerme.main
uv run --directory apps/api langgraph dev --allow-blocking

pnpm --dir apps/web fmt
pnpm --dir apps/web lint
pnpm --dir apps/web typecheck
pnpm --dir apps/web build
pnpm --dir apps/web dev
```

## Done criteria

Do not consider a **Python** change finished until all of these pass (from `apps/api`):

1. `uv run ruff format --check .` (or format first)
2. `uv run ruff check .`
3. `uv run ty check`
4. `uv run pytest`

Do not consider a **web** change finished until all of these pass (from `apps/web`):

1. `pnpm lint`
2. `pnpm typecheck`
3. `pnpm build`

A change that touches both must pass `just check`.

## Conventions

- Type everything. No `Any` (Python) and no `any` (TypeScript).
- Pydantic models at Python process boundaries.
- No business logic in adapters (`apps/api/.../api/`) or `main.py`.
- No I/O in `models/`.
- No empty files except package-marker `__init__.py` files that already exist.
- Never commit `.env` or secrets.

## Adding a feature

1. Model — Pydantic schema / settings in `apps/api` `models/`.
2. db — persistence in `db/` if the feature stores data.
3. Service — business rules in `services/`.
4. Adapter — FastAPI in `api/`.
5. Gateway — Next.js Route Handler under `apps/web/app/api/` if the UI needs it.
6. UI — App Router page/component. Fetch the gateway, not Python.
7. Test — pytest under `apps/api/tests/`. No network, no secrets.

## Out of scope

- Do not add SQLAlchemy or extra Python frameworks unless asked.
- Do not add Tailwind, Turborepo, or a JS workspace unless asked.
- Do not hand-edit `apps/api/uv.lock`. Use `uv lock`, `uv add`, or `uv sync`.
- Do not hand-edit `apps/web/pnpm-lock.yaml`. Use `pnpm`.

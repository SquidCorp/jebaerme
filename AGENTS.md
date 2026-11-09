# Agent contract

This is a monorepo: Python API in `apps/api`, Next.js frontend in `apps/web`. Quality is a mechanical loop: a change is not done until the affected app's checks pass (`just check` covers both).

## Conventions

- Type everything. No `Any` (Python) and no `any` (TypeScript).
- Pydantic models at Python process boundaries.
- No business logic in adapters (`apps/api/.../api/`) or `main.py`.
- No I/O in `models/`.
- No empty files except package-marker `__init__.py` files that already exist.
- Never commit `.env` or secrets.

## Done criteria

Do not consider a **Python** change finished until all of these pass (from `apps/api`):

1. `uv run ruff format --check .` (or format first)
2. `uv run ruff check .`
3. `uv run ty check`
4. `uv run pytest`

Do not consider a **web** change finished until all of these pass (from `apps/web`):

1. `pnpm lint` (`biome check .`)
2. `pnpm typecheck`
3. `pnpm test` (`vitest run`)
4. `pnpm build`

A change that touches both must pass `just check`.

## Adding a feature

1. Model — Pydantic schema / settings in `apps/api` `models/`.
2. db — persistence in `db/` if the feature stores data.
3. Service — business rules in `services/`.
4. Adapter — FastAPI in `api/`.
5. Gateway — Next.js Route Handler under `apps/web/app/api/` if the UI needs it.
6. UI — App Router page/component. Fetch the gateway, not Python.
7. Test — pytest under `apps/api/tests/`; Vitest next to web modules (`*.test.ts(x)`). No network, no secrets.

## Out of scope

- Do not add SQLAlchemy or extra Python frameworks unless asked.
- Do not add Tailwind, Turborepo, or a JS workspace unless asked.
- Do not hand-edit `apps/api/uv.lock`. Use `uv lock`, `uv add`, or `uv sync`.
- Do not hand-edit `apps/web/pnpm-lock.yaml`. Use `pnpm`.

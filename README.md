# jebaerme

Monorepo with a typed Python API (`apps/api`) and a Next.js frontend (`apps/web`). The browser talks to Next.js Route Handlers; those handlers are the Node gateway to FastAPI.

Agents should read `AGENTS.md` before changing code.

## Setup

Requires Python 3.13, [uv](https://docs.astral.sh/uv/), Node.js, and [pnpm](https://pnpm.io/).

```bash
just install
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env
```

`just install` is `just install-api` then `just install-web` (`uv sync` and `pnpm install`).

## Run

API (FastAPI on `http://127.0.0.1:8000`):

```bash
just dev-api
# or
uv run --directory apps/api python -m jebaerme.main
```

Web (Next.js on `http://localhost:3000`):

```bash
just dev-web
# or
pnpm --dir apps/web dev
```

`GET /health` on the API returns `{"status":"ok","env":"dev"}`. The UI reads that through `GET /api/health` on Next.js.

LangGraph Studio (local Agent Server on `http://127.0.0.1:2024`):

```bash
just dev-studio
# or
uv run --directory apps/api langgraph dev --allow-blocking
```

Open [Studio](https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024). Requires `LANGSMITH_API_KEY` in `apps/api/.env`. In Studio, run the `chat` graph with `{"message": "your text"}`.

## Check

```bash
just check
```

CI runs two jobs: Ruff / ty / pytest for the API, and lint / typecheck / build for the web app.

Format Python with `just fmt`. Tests only: `just test`.

## Agents

Read `AGENTS.md`. It is the contract for layout, commands, and done criteria.

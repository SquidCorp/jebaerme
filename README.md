# jebaerme

Typed Python package skeleton with a mechanical quality loop (Ruff, ty, pytest) and a small layered layout (`api` → `services` → `db` + `models`). Agents should read `AGENTS.md` before changing code.

## Setup

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --all-groups
cp .env.example .env
```

## Run

```bash
just run
# or
uv run python -m jebaerme.main
```

Prints a JSON health payload, for example `{"status":"ok","env":"dev"}`.

## Check

```bash
just check
```

That is the same four gates CI runs: Ruff format check, Ruff lint, ty, pytest.

Format locally with `just fmt`. Tests only: `just test`.

## Agents

Read `AGENTS.md`. It is the contract for layout, commands, and done criteria.


install: install-api install-web

install-api:
    uv sync --directory apps/api --all-groups

install-web:
    pnpm --dir apps/web install

check: check-api check-web

fmt: fmt-api fmt-web

test: test-api

check-api:
    uv run --directory apps/api ruff format --check .
    uv run --directory apps/api ruff check .
    uv run --directory apps/api ty check
    uv run --directory apps/api pytest

fmt-api:
    uv run --directory apps/api ruff format .
    uv run --directory apps/api ruff check --fix .

test-api:
    uv run --directory apps/api pytest

fmt-web:
    pnpm --dir apps/web fmt

check-web:
    pnpm --dir apps/web lint
    pnpm --dir apps/web typecheck
    pnpm --dir apps/web build

dev-api:
    uv run --directory apps/api python -m jebaerme.main

dev-web:
    pnpm --dir apps/web dev

run-dev:
    #!/usr/bin/env bash
    set -euo pipefail
    uv run --directory apps/api python -m jebaerme.main &
    api_pid=$!
    trap 'kill "$api_pid" 2>/dev/null || true' EXIT INT TERM
    pnpm --dir apps/web dev

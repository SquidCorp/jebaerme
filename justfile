
install: install-api install-web

install-api:
    uv sync --directory apps/api --all-groups

install-web:
    pnpm --dir apps/web install

check: check-api check-web

fmt: fmt-api fmt-web

test: test-api test-web

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

test-web:
    pnpm --dir apps/web test

check-web:
    pnpm --dir apps/web lint
    pnpm --dir apps/web typecheck
    pnpm --dir apps/web test
    pnpm --dir apps/web build

qdrant:
    docker compose up -d qdrant

qdrant-down:
    docker compose down

dev-api:
    uv run --directory apps/api python -m jebaerme.main

dev-studio:
    uv run --directory apps/api langgraph dev --allow-blocking

dev-web:
    pnpm --dir apps/web dev

run-dev:
    #!/usr/bin/env bash
    set -euo pipefail
    uv run --directory apps/api python -m jebaerme.main &
    api_pid=$!
    trap 'kill "$api_pid" 2>/dev/null || true' EXIT INT TERM
    pnpm --dir apps/web dev

sync:
    #!/usr/bin/env bash
    set -euo pipefail
    # After a merge to main, fast-forward develop to main and push so neither
    # branch is ahead or behind, then land on develop.
    if ! git diff --quiet || ! git diff --cached --quiet; then
        echo "just sync requires a clean working tree" >&2
        exit 1
    fi
    current="$(git branch --show-current)"
    git fetch origin --prune
    if [[ "${current}" == "main" ]]; then
        git merge --ff-only origin/main
    else
        git fetch origin main:main
    fi
    if [[ "${current}" == "develop" ]]; then
        git merge --ff-only origin/develop
    else
        git fetch origin develop:develop
    fi
    git checkout develop
    git merge --ff-only origin/develop
    if [[ "$(git rev-parse HEAD)" != "$(git rev-parse main)" ]]; then
        if git merge-base --is-ancestor HEAD main; then
            git merge --ff-only main
        else
            echo "develop and main have diverged; resolve before just sync" >&2
            git log --oneline --left-right --decorate HEAD...main >&2
            exit 1
        fi
    fi
    if [[ "$(git rev-parse HEAD)" != "$(git rev-parse origin/develop)" ]]; then
        git push origin develop
    fi
    if [[ "$(git rev-parse HEAD)" != "$(git rev-parse origin/main)" ]]; then
        echo "develop still does not match origin/main" >&2
        exit 1
    fi
    if [[ -n "${current}" && "${current}" != "main" && "${current}" != "develop" ]] \
        && git show-ref --verify --quiet "refs/heads/${current}" \
        && git merge-base --is-ancestor "${current}" HEAD; then
        git branch -d "${current}"
    fi

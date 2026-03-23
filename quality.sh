#!/usr/bin/env bash
set -euo pipefail

uv run ruff check --fix --select UP,F401
uvx isort --py 312 .
uvx black --target-version py312 .
uv run ty check --python-version 3.12
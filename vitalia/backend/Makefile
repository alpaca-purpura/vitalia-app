# Vitalia backend Makefile

.PHONY: install test lint format check

install:
	uv sync

test:
	.venv/bin/pytest tests/ -v

lint:
	.venv/bin/ruff check src/ tests/

format:
	.venv/bin/ruff format src/ tests/

check: lint test

.PHONY: help setup demo test fmt lint typecheck up down clean

help:
	@echo "make setup      install Python deps via uv"
	@echo "make demo       run end-to-end demo on bundled corpus"
	@echo "make test       run pytest"
	@echo "make fmt        ruff format"
	@echo "make lint       ruff check"
	@echo "make typecheck  mypy app/"
	@echo "make up         start docker-compose stack from repo root"
	@echo "make down       stop docker-compose stack"
	@echo "make clean      remove pipeline-generated artefacts"

setup:
	uv sync --extra dev

demo:
	uv run nerdfarm demo

test:
	uv run pytest

fmt:
	uv run ruff format .

lint:
	uv run ruff check .

typecheck:
	uv run mypy app

up:
	cd .. && docker compose up -d

down:
	cd .. && docker compose down

clean:
	rm -rf data/processed data/chunks data/vector_store data/drafts \
	       data/edits data/style_memory data/evals/results logs

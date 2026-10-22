.PHONY: setup lint test leak-check ci help

help:
	@grep -E '^[a-z-]+:.*#' Makefile | sed 's/:.*#/ —/'

setup:        # instala dependencias de desarrollo en .venv (uv sync)
	@uv sync

lint:         # ruff sobre todo el repo (norma ci.md)
	@uv run ruff check .

test:         # pytest; sin tests todavía no falla (exit 5 = no hay tests)
	@uv run pytest || [ $$? -eq 5 ]

leak-check:   # nada del estudio en el repo (norma repo-publico.md)
	@sh scripts/leak-check.sh

ci: leak-check lint test   # el gate de cada commit

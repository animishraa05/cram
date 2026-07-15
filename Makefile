.PHONY: install dev uninstall clean test lint format

install:
	pipx install .

dev:
	pip install -e ".[dev]"

uninstall:
	pipx uninstall cram

clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .mypy_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

test:
	pytest tests/ -v

lint:
	ruff check srs/ tests/
	mypy srs/ --ignore-missing-imports

format:
	ruff format srs/ tests/

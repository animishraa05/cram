.PHONY: install dev uninstall clean test

install:
	pip install .

dev:
	pip install -e .

uninstall:
	pip uninstall srs -y

clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .mypy_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

test:
	pytest tests/ -v

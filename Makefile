.PHONY: install run-dev run-prod clean help

help:
	@echo "Available commands:"
	@echo "  make install  - Sync dependencies"
	@echo "  make run-dev  - Run in development mode"
	@echo "  make run-prod - Run in production mode"
	@echo "  make clean    - Remove cache files"

install:
	uv sync

run-dev:
	ENV=dev uv run main.py

run-prod:
	uv run main.py

fresh-start: clean install run-prod

clean:
	rm -rf .venv
	find . -type d -name "__pycache__" -exec rm -rf {} +


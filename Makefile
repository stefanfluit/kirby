PIPX ?= pipx

.DEFAULT_GOAL := help

.PHONY: help _require-pipx _require-behave dev install test lint format format-check ansible-lint bdd check clean

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

_require-pipx:
	@command -v $(PIPX) >/dev/null 2>&1 || \
		{ echo "Error: pipx not found. Install it: https://pipx.pypa.io/stable/installation/"; exit 1; }

dev: _require-pipx ## Install package with dev dependencies (pytest, ruff, ansible-lint, behave)
	$(PIPX) install -e ".[dev]"

install: _require-pipx ## Install package (production only)
	$(PIPX) install -e .

test: ## Run unit tests
	pytest

lint: ## Lint Python source with ruff
	ruff check .

format: ## Auto-format Python source with ruff
	ruff format .

format-check: ## Check formatting without modifying files
	ruff format --check .

ansible-lint: ## Lint all Ansible files (profile: production)
	ansible-lint -c ansible-lint.yaml

_require-behave:
	@command -v behave >/dev/null 2>&1 || \
		{ echo "Error: behave not found. Run: make dev"; exit 1; }

bdd: _require-behave ## Run BDD integration tests (requires Ruby + ansible-core installed)
	behave tests/features/ --no-source

check: lint format-check test ansible-lint ## Run all checks (lint, format, unit tests, ansible-lint)

clean: ## Remove build artifacts and caches
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.egg-info" -exec rm -rf {} + 2>/dev/null; true
	rm -rf .pytest_cache .ruff_cache .ansible htmlcov .coverage build dist

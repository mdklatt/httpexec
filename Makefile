# Project management tasks.

VENV = .venv
PYTHON = . $(VENV)/bin/activate && python
PYTEST = $(PYTHON) -m pytest


$(VENV)/.make-update: pyproject.toml
	python -m venv $(VENV)
	$(PYTHON) -m pip install -U pip -e ".[dev]"
	touch $@


.PHONY: dev
dev: $(VENV)/.make-update


.PHONY: test-unit
test-unit: dev
	$(PYTEST) tests/unit/


.PHONY: test-integration
test-integration: dev
	$(PYTEST) tests/integration/


.PHONY: test
test: test-unit test-integration


.PHONY: lint-openapi
lint-openapi: dev
	$(PYTHON) -m openapi_spec_validator openapi.yaml


.PHONY: lint
lint: lint-openapi


.PHONY: check
check: lint test

# Project management tasks.

VENV = .venv
DIST = dist
PYTHON = . $(VENV)/bin/activate && python
PYTEST = $(PYTHON) -m pytest
BUILD = $(PYTHON) -m build --outdir=$(DIST)


$(VENV)/.make-update: pyproject.toml
	python -m venv $(VENV)
	$(PYTHON) -m pip install -U pip  # must be first
	$(PYTHON) -m pip install -e ".[dev]"
	touch $@


.PHONY: dev
dev: $(VENV)/.make-update


.PHONY: docs
docs: dev
	$(PYTHON) -m sphinx -M html docs docs/_build


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


.PHONY: sdist
sdist: dev check
	$(BUILD) --sdist .


.PHONY: wheel
wheel: dev check
	$(BUILD) --wheel .


.PHONY: build
build: sdist wheel
	$(PYTHON) -m twine check $(DIST)/*

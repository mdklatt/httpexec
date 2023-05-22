# Project management tasks.

VENV = .venv
PYTHON = . $(VENV)/bin/activate && python
PYTEST = $(PYTHON) -m pytest


$(VENV)/.make-update: requirements-dev.txt
	python -m venv $(VENV)
	$(PYTHON) -m pip install -U "pip==22.3.1" "setuptools==62.2.0" # TODO: still need setup.py for now
	for req in $^; do $(PYTHON) -m pip install -r "$$req"; done
	$(PYTHON) -m pip install -e .
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

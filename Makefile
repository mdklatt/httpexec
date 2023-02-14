# Project management tasks.

VENV = .venv
PYTHON = . $(VENV)/bin/activate && python


$(VENV)/.make-update: requirements-dev.txt
	python -m venv $(VENV)
	$(PYTHON) -m pip install -U pip && for req in $^; do pip install -r "$$req"; done
	$(PYTHON) -m pip install -e .
	touch $@


.PHONY: dev
dev: $(VENV)/.make-update


.PHONY: test-unit
test-unit: dev
	$(PYTHON) -m pytest tests/unit/


.PHONY: test-integration
test-integration: dev
	$(PYTHON) -m pytest tests/integration/


.PHONY: test
test: test-unit test-integration

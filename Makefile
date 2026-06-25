VENV_PYTHON := .venv/bin/python
PYTHON ?= $(if $(wildcard $(VENV_PYTHON)),$(VENV_PYTHON),python3)

.PHONY: all venv install lint type test fmt clean

all: lint type test

venv:
	python3 -m venv .venv

install: venv
	$(VENV_PYTHON) -m pip install -e ".[dev]"

lint:
	$(PYTHON) -m ruff check src tests
	$(PYTHON) -m ruff format --check src tests

type:
	$(PYTHON) -m mypy

test:
	$(PYTHON) -m pytest

fmt:
	$(PYTHON) -m ruff format src tests

clean:
	rm -rf build dist .pytest_cache .ruff_cache .mypy_cache
	find . -name '__pycache__' -type d -exec rm -rf {} +
	find . -name '*.egg-info' -type d -exec rm -rf {} +

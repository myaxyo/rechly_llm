.PHONY: help install test validate benchmark serve cli demo docker-build docker-up clean

PYTHON := $(shell which python3)
VENV := ./venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PYTEST := $(VENV)/bin/pytest

help:
	@echo "Rechly-DE-3B Developer Automation Makefile"
	@echo "------------------------------------------"
	@echo "make install      : Set up virtualenv and install dependencies"
	@echo "make test         : Run automated test suite (31 unit & integration tests)"
	@echo "make validate     : Validate GoBD dataset integrity and schema compliance"
	@echo "make benchmark    : Run 5-domain evaluation benchmark against rechly-de-3b"
	@echo "make serve        : Start FastAPI Gateway & Web Playground on http://localhost:8000"
	@echo "make demo         : Open browser to Web Playground"
	@echo "make status       : Check Ollama and Gateway operational status"
	@echo "make docker-build : Build production Docker container"
	@echo "make docker-up    : Launch container stack via Docker Compose"
	@echo "make clean        : Remove temporary files and pytest caches"

install:
	$(PYTHON) -m venv --system-site-packages $(VENV)
	$(VENV)/bin/pip install -r requirements.txt

test:
	$(VENV_PYTEST) tests/ -v

validate:
	$(VENV_PYTHON) scripts/validate_dataset.py data/rechly_german_accounting.jsonl

benchmark:
	$(VENV_PYTHON) scripts/evaluate_model.py --model rechly-de-3b

serve:
	$(VENV_PYTHON) scripts/serve_api.py --host 127.0.0.1 --port 8000 --model rechly-de-3b

status:
	$(VENV_PYTHON) scripts/cli.py status

docker-build:
	docker build -t rechly-llm-gateway:latest .

docker-up:
	docker compose up -d

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache data/mlx_splits

# Makefile para GitLab CI/CD Creator

.PHONY: help install install-dev test lint format clean build

help: ## Muestra esta ayuda
	@echo "Comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Instala las dependencias de producción
	pip install -e .

install-dev: ## Instala las dependencias de desarrollo
	pip install -e ".[dev]"

test: ## Ejecuta los tests
	pytest

test-cov: ## Ejecuta los tests con reporte de cobertura
	pytest --cov=gitlab_cicd_creator --cov-report=html --cov-report=term

lint: ## Ejecuta linters (flake8, mypy)
	flake8 src/
	mypy src/

format: ## Formatea el código con black e isort
	black src/ tests/
	isort src/ tests/

format-check: ## Verifica el formato sin modificar
	black --check src/ tests/
	isort --check-only src/ tests/

clean: ## Limpia archivos temporales
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/ .mypy_cache/

build: clean ## Construye el paquete
	python -m build


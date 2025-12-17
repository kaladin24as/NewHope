# AntiGravity Makefile
# Common development tasks

.PHONY: help install test run clean

help:
	@echo "AntiGravity - Available Commands:"
	@echo ""
	@echo "  make install       - Install dependencies"
	@echo "  make test          - Run tests"
	@echo "  make test-cov      - Run tests with coverage"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make run-api       - Run backend API"
	@echo "  make run-ui        - Run Streamlit UI"
	@echo "  make docker-build  - Build Docker images"
	@echo "  make docker-up     - Start services"
	@echo "  make docker-down   - Stop services"
	@echo "  make clean         - Clean generated files"
	@echo "  make verify        - Verify providers"
	@echo ""

install:
	@echo "Installing dependencies..."
	pip install -r backend/requirements.txt
	@echo "✓ Installed"

test:
	@echo "Running tests..."
	pytest tests/ -v

test-cov:
	@echo "Running tests with coverage..."
	pytest tests/ --cov=backend --cov-report=html --cov-report=term
	@echo "✓ Coverage: htmlcov/index.html"

lint:
	@echo "Running linters..."
	flake8 backend/ --max-line-length=100
	@echo "✓ Linting complete"

format:
	@echo "Formatting code..."
	black backend/ ui/ tests/
	isort backend/ ui/ tests/
	@echo "✓ Formatted"

run-api:
	@echo "Starting API on http://localhost:8000..."
	cd backend && uvicorn main:app --reload

run-ui:
	@echo "Starting UI on http://localhost:8501..."
	cd ui && streamlit run app.py

docker-build:
	@echo "Building images..."
	docker-compose build

docker-up:
	@echo "Starting services..."
	docker-compose up -d
	@echo "✓ Running:"
	@echo "  API: http://localhost:8000"
	@echo "  UI: http://localhost:8501"

docker-down:
	@echo "Stopping services..."
	docker-compose down

clean:
	@echo "Cleaning..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov .coverage
	@echo "✓ Clean"

verify:
	@echo "Verifying providers..."
	python verify_providers.py

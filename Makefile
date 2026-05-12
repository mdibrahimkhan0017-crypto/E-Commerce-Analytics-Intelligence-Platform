.PHONY: install generate ingest report test lint clean all

# ── Install ──────────────────────────────────────────────────────────────────
install:
	pip install -r requirements.txt
	python setup_project.py

# ── Data Generation ──────────────────────────────────────────────────────────
generate:
	python -m src.cli generate --records 10000 --seed 42

# ── Ingestion ────────────────────────────────────────────────────────────────
ingest:
	python -m src.cli ingest --source data/

# ── Reports ──────────────────────────────────────────────────────────────────
report:
	python -m src.cli report --type all --format png,pdf

# ── Testing ──────────────────────────────────────────────────────────────────
test:
	pytest tests/ --cov=src --cov-report=term-missing -v

# ── Linting ──────────────────────────────────────────────────────────────────
lint:
	flake8 src/ --max-line-length=100 --statistics

# ── Clean ────────────────────────────────────────────────────────────────────
clean:
	rm -rf db/*.db reports/*.png reports/*.pdf reports/*.json
	rm -rf logs/*.log logs/*.json
	rm -rf data/*.csv
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# ── Full Pipeline ────────────────────────────────────────────────────────────
all: install generate ingest report
	@echo "✅ Full pipeline complete."

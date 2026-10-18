PYTHON ?= python
PIP ?= $(PYTHON) -m pip
DOCS_DIR ?= docs
OUTPUT_PORTAL ?= dist/portal
SAMPLE_LOG ?= sample_logs/server_production.log
OUTPUT_AUDIT ?= dist/audit/audit_report.html

all: build-c test pipeline

build-c:
	$(MAKE) -C src/c_modules

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py" -v

build-docs:
	$(PYTHON) -m src.core.cli build-docs --docs-dir $(DOCS_DIR) --output-dir $(OUTPUT_PORTAL)

audit-logs:
	$(PYTHON) -m src.core.cli audit-logs --log-file $(SAMPLE_LOG) --output-html $(OUTPUT_AUDIT)

pipeline:
	$(PYTHON) -m src.core.cli pipeline --docs-dir $(DOCS_DIR) --output-dir $(OUTPUT_PORTAL) --log-file $(SAMPLE_LOG) --output-html $(OUTPUT_AUDIT)

status:
	$(PYTHON) -m src.core.cli status

install:
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

clean:
	rm -rf dist/ build/ *.egg-info .pytest_cache/
	$(MAKE) -C src/c_modules clean || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

.PHONY: all build-c test build-docs audit-logs pipeline status install clean

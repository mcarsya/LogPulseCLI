# =====================================================================
# LogPulse CLI - Top-Level Enterprise Makefile
# Supports Linux, macOS, and Windows environments
# =====================================================================

PYTHON ?= python
PIP ?= $(PYTHON) -m pip
DOCS_DIR ?= docs
OUTPUT_PORTAL ?= dist/portal
SAMPLE_LOG ?= sample_logs/server_production.log
OUTPUT_AUDIT ?= dist/audit/audit_report.html

all: build-c test pipeline

# Compile C native acceleration module
build-c:
	@echo ">>> Compiling C shared library..."
	$(MAKE) -C src/c_modules

# Run full unit test suite
test:
	@echo ">>> Running test suite..."
	$(PYTHON) -m unittest discover -s tests -p "test_*.py" -v

# Build Static Site Generator portal
build-docs:
	@echo ">>> Building SOP documentation portal..."
	$(PYTHON) -m src.core.cli build-docs --docs-dir $(DOCS_DIR) --output-dir $(OUTPUT_PORTAL)

# Execute functional log analytics and generate audit HTML
audit-logs:
	@echo ">>> Executing log audit engine..."
	$(PYTHON) -m src.core.cli audit-logs --log-file $(SAMPLE_LOG) --output-html $(OUTPUT_AUDIT)

# End-to-end pipeline
pipeline:
	@echo ">>> Running full enterprise pipeline..."
	$(PYTHON) -m src.core.cli pipeline --docs-dir $(DOCS_DIR) --output-dir $(OUTPUT_PORTAL) --log-file $(SAMPLE_LOG) --output-html $(OUTPUT_AUDIT)

# Check system health & C linkage status
status:
	$(PYTHON) -m src.core.cli status

# Install Python requirements and package
install:
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

# Clean generated artifacts
clean:
	@echo ">>> Cleaning build artifacts..."
	rm -rf dist/ build/ *.egg-info .pytest_cache/
	$(MAKE) -C src/c_modules clean || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

.PHONY: all build-c test build-docs audit-logs pipeline status install clean

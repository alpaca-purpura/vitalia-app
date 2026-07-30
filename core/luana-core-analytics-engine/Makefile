.PHONY: extraction-contract test lint

# Regenerate the ETL extraction contract documentation.
# Source: src/luana_core_analytics_engine/domain/extraction_contract.py
# Output: docs/extraction-contract.md (idempotent — SHA256 stable on consecutive runs)
#
# Run after any change to:
#   - domain/extraction_contract.py
#   - infrastructure/providers/
#   - application/services/etl_service.py
#   - workers/scheduler.py or workers/tasks.py
#
# See .claude/rules/etl-extraction-contract.md for the full 5-step workflow.
extraction-contract:
	uv run python scripts/generate_extraction_contract_doc.py
	@echo "Regenerated docs/extraction-contract.md"
	@echo "  Run arch test: uv run pytest ../../tests/architecture/test_analytics_extraction_contract_drift.py -x -q"

test:
	uv run pytest tests/ -x -q --tb=short

lint:
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

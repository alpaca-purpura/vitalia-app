"""Vitalia ops + ingestion scripts (entry-points exposed via uv run).

NOTE: this package exists to make `from scripts.X import Y` valid in tests
(per `tests/__init__.py` + `pyproject.toml::pythonpath = ["."]`).
Production scripts MAY be invoked as modules with
`uv run python -m scripts.seed_medical_kb`.
"""

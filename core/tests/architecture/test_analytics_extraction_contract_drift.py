"""Arch fitness: ETL extraction contract drift idempotency.

Verifies that running the extraction contract generator twice in the same
process produces byte-for-byte identical output (SHA256 equality). This
guards against non-deterministic rendering (e.g. dict iteration order,
timestamp injection, random sorting) that would make the contract file
unstable in version control.

Per 03-arch.md §10: drift idempotency is a hard gate for T-3c.
"""

from __future__ import annotations

import hashlib
import importlib
import sys
from pathlib import Path

import pytest

# Root of the analytics package
_ANALYTICS_PKG = Path(__file__).resolve().parents[2] / "luana-core-analytics-engine"
_SCRIPT = _ANALYTICS_PKG / "scripts" / "generate_extraction_contract_doc.py"
_OUTPUT = _ANALYTICS_PKG / "docs" / "extraction-contract.md"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_generator() -> None:
    """Import and execute the generation script in-process."""
    # Ensure the src/ path is on sys.path for the package import
    src_path = str(_ANALYTICS_PKG / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    spec = importlib.util.spec_from_file_location("_gen_contract", _SCRIPT)
    assert spec is not None, f"Cannot load spec from {_SCRIPT}"
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    mod.main()


@pytest.mark.arch
def test_extraction_contract_script_exists() -> None:
    """generate_extraction_contract_doc.py must exist at expected path."""
    assert _SCRIPT.exists(), f"Script not found: {_SCRIPT}"


@pytest.mark.arch
def test_extraction_contract_output_exists_after_generate() -> None:
    """Running the generator must produce docs/extraction-contract.md."""
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _run_generator()
    assert _OUTPUT.exists(), f"Generator did not produce output at {_OUTPUT}"
    assert _OUTPUT.stat().st_size > 100, "extraction-contract.md is suspiciously small"


@pytest.mark.arch
def test_extraction_contract_idempotent() -> None:
    """Two consecutive runs must produce byte-identical output (SHA256 equality).

    Drift indicates non-deterministic rendering (timestamp, dict order, etc.)
    which makes the file unstable in version control and breaks the contract
    as a reliable audit artifact.
    """
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    # First run
    _run_generator()
    sha_first = _sha256(_OUTPUT)

    # Second run — must produce same bytes
    _run_generator()
    sha_second = _sha256(_OUTPUT)

    assert sha_first == sha_second, (
        "ETL extraction contract is non-deterministic: two consecutive runs produced "
        f"different SHA256 digests.\n"
        f"  Run 1: {sha_first}\n"
        f"  Run 2: {sha_second}\n"
        "Fix: ensure generate_extraction_contract_doc.py produces deterministic output "
        "(sort all dicts/sets, no timestamps, no random ordering)."
    )


@pytest.mark.arch
def test_extraction_contract_contains_provider_summary() -> None:
    """Generated file must contain the Provider summary table header."""
    _run_generator()
    content = _OUTPUT.read_text(encoding="utf-8")
    assert "## Provider summary" in content, (
        "extraction-contract.md missing '## Provider summary' section — generator may have failed silently."
    )


@pytest.mark.arch
def test_extraction_contract_contains_worker_schedule() -> None:
    """Generated file must contain the Worker schedule section."""
    _run_generator()
    content = _OUTPUT.read_text(encoding="utf-8")
    assert "## Worker schedule reference" in content, (
        "extraction-contract.md missing '## Worker schedule reference' section."
    )

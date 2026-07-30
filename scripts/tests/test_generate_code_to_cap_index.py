"""Tests for scripts/generate_code_to_cap_index.py.

Uses inline file fixtures via tmp_path — does NOT touch real codebase.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module loader
# ---------------------------------------------------------------------------


def _load_module():
    """Load generate_code_to_cap_index.py as module."""
    scripts_dir = Path(__file__).parent.parent
    spec = importlib.util.spec_from_file_location(
        "generate_code_to_cap_index",
        scripts_dir / "generate_code_to_cap_index.py",
    )
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ---------------------------------------------------------------------------
# parse_cap_list tests
# ---------------------------------------------------------------------------


def test_parse_cap_list_single():
    mod = _load_module()
    assert mod.parse_cap_list("scheduling.valeria-agenda") == ["scheduling.valeria-agenda"]


def test_parse_cap_list_multi_array():
    mod = _load_module()
    result = mod.parse_cap_list("[scheduling.valeria-agenda, booking.prepaid-booking-advisory-locks]")
    assert result == ["scheduling.valeria-agenda", "booking.prepaid-booking-advisory-locks"]


def test_parse_cap_list_orphan():
    mod = _load_module()
    assert mod.parse_cap_list("__orphan__") == ["__orphan__"]


def test_parse_cap_list_shared():
    mod = _load_module()
    assert mod.parse_cap_list("__shared__") == ["__shared__"]


def test_parse_cap_list_empty():
    mod = _load_module()
    assert mod.parse_cap_list("") == []
    assert mod.parse_cap_list("   ") == []


# ---------------------------------------------------------------------------
# scan_file tests
# ---------------------------------------------------------------------------


def _write_py(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_scan_file_python_simple(tmp_path: Path):
    mod = _load_module()
    f = tmp_path / "test.py"
    _write_py(
        f,
        "# cap: scheduling.valeria-agenda\n"
        "# story-origin: vitalia-fase2-valeria-agenda\n"
        '"""docstring"""\n',
    )
    result = mod.scan_file(f)
    assert result["caps"] == ["scheduling.valeria-agenda"]
    assert result["story_origin"] == "vitalia-fase2-valeria-agenda"
    assert "atomics" not in result


def test_scan_file_tsx_simple(tmp_path: Path):
    mod = _load_module()
    f = tmp_path / "test.tsx"
    _write_py(
        f,
        "// cap: shell-organism.shell-vitalia\n"
        "// story-origin: TBD\n"
        "'use client';\n"
        "export function X() {}\n",
    )
    result = mod.scan_file(f)
    assert result["caps"] == ["shell-organism.shell-vitalia"]
    assert result["story_origin"] is None  # TBD treated as None


def test_scan_file_multi_cap(tmp_path: Path):
    mod = _load_module()
    f = tmp_path / "test.py"
    _write_py(
        f,
        "# cap: [scheduling.valeria-agenda, booking.prepaid-booking-advisory-locks]\n"
        "# story-origin: TBD\n",
    )
    result = mod.scan_file(f)
    assert result["caps"] == ["scheduling.valeria-agenda", "booking.prepaid-booking-advisory-locks"]


def test_scan_file_orphan_marker(tmp_path: Path):
    mod = _load_module()
    f = tmp_path / "test.py"
    _write_py(f, "# cap: __orphan__\n# story-origin: TBD\n")
    result = mod.scan_file(f)
    assert result["caps"] == ["__orphan__"]


def test_scan_file_no_header(tmp_path: Path):
    mod = _load_module()
    f = tmp_path / "test.py"
    _write_py(f, '"""docstring"""\nfrom foo import bar\n')
    result = mod.scan_file(f)
    assert result["caps"] == []
    assert result["story_origin"] is None


def test_scan_file_shebang_then_header(tmp_path: Path):
    """Header after shebang should still be detected (regex MULTILINE)."""
    mod = _load_module()
    f = tmp_path / "test.py"
    _write_py(
        f,
        "#!/usr/bin/env python3\n"
        "# cap: ops.k8s-admin-deployment\n"
        "# story-origin: TBD\n",
    )
    result = mod.scan_file(f)
    assert result["caps"] == ["ops.k8s-admin-deployment"]


# ---------------------------------------------------------------------------
# process_brand integration tests
# ---------------------------------------------------------------------------


def _setup_brand_skeleton(workspace_root: Path, brand: str) -> tuple[Path, Path]:
    """Create minimal brand backend/src + frontend/src structure."""
    be = workspace_root / brand / "backend" / "src"
    fe = workspace_root / brand / "frontend" / "src"
    be.mkdir(parents=True, exist_ok=True)
    fe.mkdir(parents=True, exist_ok=True)
    return be, fe


def test_process_brand_integration(tmp_path: Path):
    mod = _load_module()
    brand = "vitalia"
    be, fe = _setup_brand_skeleton(tmp_path, brand)

    # Backend files
    _write_py(
        be / "main.py",
        "# cap: observability.api-health-endpoint\n# atomics: TBD\n# story-origin: TBD\n",
    )
    _write_py(
        be / "scheduling.py",
        "# cap: scheduling.valeria-agenda\n# atomics: TBD\n# story-origin: TBD\n",
    )
    _write_py(be / "no_header.py", "from foo import bar\n")

    # Frontend files
    _write_py(
        fe / "AgendaWeekly.tsx",
        "// cap: scheduling.valeria-agenda\n// atomics: TBD\n// story-origin: TBD\n",
    )
    _write_py(
        fe / "orphan.ts",
        "// cap: __orphan__\n// atomics: TBD\n// story-origin: TBD\n",
    )
    _write_py(
        fe / "shared.tsx",
        "// cap: __shared__\n// atomics: TBD\n// story-origin: TBD\n",
    )

    result = mod.process_brand(brand, tmp_path, verbose=False)

    # Validate counts
    assert result["summary"]["total_files_scanned"] == 6
    assert result["summary"]["files_with_header"] == 5  # no_header.py excluded
    assert result["summary"]["files_no_header"] == 1
    assert result["summary"]["orphans"] == 1
    assert result["summary"]["shared_files"] == 1
    assert result["summary"]["caps_with_files"] == 2  # observability + scheduling

    # Validate cap_to_files mapping
    assert "scheduling.valeria-agenda" in result["cap_to_files"]
    assert len(result["cap_to_files"]["scheduling.valeria-agenda"]) == 2  # be + fe
    assert "observability.api-health-endpoint" in result["cap_to_files"]


def test_process_brand_excludes_test_files(tmp_path: Path):
    mod = _load_module()
    brand = "vitalia"
    be, fe = _setup_brand_skeleton(tmp_path, brand)

    _write_py(
        fe / "Component.tsx",
        "// cap: scheduling.valeria-agenda\n// atomics: TBD\n// story-origin: TBD\n",
    )
    _write_py(
        fe / "Component.test.tsx",
        "// cap: scheduling.valeria-agenda\n// atomics: TBD\n// story-origin: TBD\n",
    )
    _write_py(
        fe / "Component.spec.ts",
        "// cap: scheduling.valeria-agenda\n// atomics: TBD\n// story-origin: TBD\n",
    )
    tests_dir = fe / "__tests__"
    tests_dir.mkdir()
    _write_py(
        tests_dir / "x.tsx",
        "// cap: scheduling.valeria-agenda\n// atomics: TBD\n// story-origin: TBD\n",
    )

    result = mod.process_brand(brand, tmp_path, verbose=False)

    # Should only count Component.tsx (1 file)
    assert result["summary"]["total_files_scanned"] == 1


def test_process_brand_excludes_pycache(tmp_path: Path):
    mod = _load_module()
    brand = "vitalia"
    be, _ = _setup_brand_skeleton(tmp_path, brand)

    _write_py(
        be / "good.py",
        "# cap: scheduling.valeria-agenda\n# atomics: TBD\n# story-origin: TBD\n",
    )
    pycache = be / "__pycache__"
    pycache.mkdir()
    _write_py(
        pycache / "bytecode.py",
        "# cap: scheduling.valeria-agenda\n# atomics: TBD\n# story-origin: TBD\n",
    )

    result = mod.process_brand(brand, tmp_path, verbose=False)
    assert result["summary"]["total_files_scanned"] == 1


def test_process_brand_multi_cap_file(tmp_path: Path):
    mod = _load_module()
    brand = "vitalia"
    be, _ = _setup_brand_skeleton(tmp_path, brand)

    _write_py(
        be / "shared.py",
        "# cap: [scheduling.valeria-agenda, brand_studio.lisa-marca]\n"
        "# atomics: TBD\n# story-origin: TBD\n",
    )
    _write_py(
        be / "single.py",
        "# cap: scheduling.valeria-agenda\n# atomics: TBD\n# story-origin: TBD\n",
    )

    result = mod.process_brand(brand, tmp_path, verbose=False)
    assert result["summary"]["multi_cap_files"] == 1
    # shared.py contributes to BOTH caps
    assert "shared.py" in result["cap_to_files"]["scheduling.valeria-agenda"][0]
    assert "shared.py" in result["cap_to_files"]["brand_studio.lisa-marca"][0]


def test_cap_to_atomics_dropped_from_output(tmp_path: Path):
    """cap_to_atomics must NOT be present in output (atomics killed 2026-05-28)."""
    mod = _load_module()
    brand = "vitalia"
    be, _ = _setup_brand_skeleton(tmp_path, brand)

    _write_py(
        be / "a.py",
        "# cap: scheduling.valeria-agenda\n# story-origin: TBD\n",
    )

    result = mod.process_brand(brand, tmp_path, verbose=False)
    assert "cap_to_atomics" not in result
    assert "scheduling.valeria-agenda" in result["cap_to_files"]


def test_process_brand_missing_brand_dir(tmp_path: Path):
    """Should not crash if brand backend/frontend dirs don't exist."""
    mod = _load_module()
    result = mod.process_brand("ghost-brand", tmp_path, verbose=False)
    assert result["summary"]["total_files_scanned"] == 0

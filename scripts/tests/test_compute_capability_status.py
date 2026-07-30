"""Tests for scripts/compute_capability_status.py (scenarios state-machine).

Atomics killed 2026-05-28 — the unit of behavior is now `scenario` (Gherkin).
See docs/process/lifecycle.md.

Uses inline YAML fixtures via tmp_path — does NOT depend on real cap files.
All paths use the workspace-root-relative convention the script expects.
"""

from __future__ import annotations

from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FRONTMATTER_TEMPLATE = """\
---
{yaml_content}
---

# Capability placeholder
"""


def _write_cap(caps_dir: Path, module: str, slug: str, data: dict) -> Path:
    """Write a capability YAML file under caps_dir/{module}/{slug}.yaml."""
    module_dir = caps_dir / module
    module_dir.mkdir(parents=True, exist_ok=True)
    path = module_dir / f"{slug}.yaml"
    yaml_content = yaml.dump(data, allow_unicode=True, default_flow_style=False)
    path.write_text(_FRONTMATTER_TEMPLATE.format(yaml_content=yaml_content), encoding="utf-8")
    return path


def _run_script(workspace_root: Path, brand: str) -> dict:
    """Import and run compute_capability_status.process_brand directly."""
    import importlib.util

    scripts_dir = Path(__file__).parent.parent
    spec = importlib.util.spec_from_file_location(
        "compute_capability_status",
        scripts_dir / "compute_capability_status.py",
    )
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    return mod.process_brand(brand, workspace_root, verbose=False)


def _setup_brand_caps(tmp_path: Path, brand: str) -> Path:
    """Create brand caps dir structure and return the caps root."""
    caps_dir = tmp_path / brand / "docs" / "product" / "capabilities"
    caps_dir.mkdir(parents=True, exist_ok=True)
    return caps_dir


def _write_e2e(tmp_path: Path, rel_path: str) -> str:
    """Create a real Playwright spec at workspace-root-relative rel_path."""
    full = tmp_path / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(
        "import { test } from '@playwright/test';\ntest('x', async () => {});\n",
        encoding="utf-8",
    )
    return rel_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_stub_cap_when_scenarios_empty(tmp_path: Path) -> None:
    """A cap with scenarios: [] must compute as 'stub' regardless of declared status."""
    brand = "testbrand"
    caps_dir = _setup_brand_caps(tmp_path, brand)
    _write_cap(
        caps_dir,
        "booking",
        "booking-widget",
        {
            "capability_id": "testbrand-booking-widget",
            "module": "booking",
            "slug": "booking-widget",
            "status": "live",
            "scenarios": [],
        },
    )

    result = _run_script(tmp_path, brand)
    cap = result["capabilities"]["booking-widget"]

    assert cap["computed_status"] == "stub"
    assert cap["scenarios_total"] == 0
    assert cap["scenarios_verified"] == 0
    assert cap["verification_total"] == 0
    assert cap["verification_pass"] == 0
    assert result["summary"]["stub"] == 1


def test_stub_when_scenarios_absent(tmp_path: Path) -> None:
    """A cap with no scenarios key at all is also 'stub'."""
    brand = "testbrand"
    caps_dir = _setup_brand_caps(tmp_path, brand)
    _write_cap(
        caps_dir,
        "booking",
        "no-scenarios",
        {
            "slug": "no-scenarios",
            "status": "live",
        },
    )

    result = _run_script(tmp_path, brand)
    cap = result["capabilities"]["no-scenarios"]
    assert cap["computed_status"] == "stub"


def test_verified_live_when_all_scenarios_have_existing_e2e(tmp_path: Path) -> None:
    """Cap live + every scenario has an e2e_test that exists → verified-live."""
    brand = "testbrand"
    caps_dir = _setup_brand_caps(tmp_path, brand)

    e2e1 = _write_e2e(tmp_path, "testbrand/frontend/e2e/a.spec.ts")
    e2e2 = _write_e2e(tmp_path, "testbrand/frontend/e2e/b.spec.ts")

    _write_cap(
        caps_dir,
        "booking",
        "verified-cap",
        {
            "slug": "verified-cap",
            "status": "live",
            "scenarios": [
                {"id": "s1", "name": "Scenario 1", "e2e_test": e2e1},
                {"id": "s2", "name": "Scenario 2", "e2e_test": e2e2},
            ],
        },
    )

    result = _run_script(tmp_path, brand)
    cap = result["capabilities"]["verified-cap"]

    assert cap["computed_status"] == "verified-live", (
        f"got {cap['computed_status']}, drift_reasons={cap['drift_reasons']}"
    )
    assert cap["scenarios_total"] == 2
    assert cap["scenarios_verified"] == 2
    assert cap["verification_total"] == 2
    assert cap["verification_pass"] == 2
    assert cap["drift_reasons"] == []
    assert result["summary"]["verified_live"] == 1


def test_declared_live_when_no_e2e_declared(tmp_path: Path) -> None:
    """Cap live with scenarios but zero e2e_test declared → declared-live."""
    brand = "testbrand"
    caps_dir = _setup_brand_caps(tmp_path, brand)

    _write_cap(
        caps_dir,
        "shell",
        "shell-vitalia",
        {
            "slug": "shell-vitalia",
            "status": "live",
            "scenarios": [
                {"id": "layout", "name": "Layout 50/50", "e2e_test": None},
                {"id": "ribbon", "name": "Ribbon 6 tabs"},  # no e2e_test key
            ],
        },
    )

    result = _run_script(tmp_path, brand)
    cap = result["capabilities"]["shell-vitalia"]

    assert cap["computed_status"] == "declared-live"
    assert cap["scenarios_total"] == 2
    assert cap["verification_total"] == 0
    assert cap["verification_pass"] == 0
    assert result["summary"]["declared_live"] == 1


def test_drift_when_e2e_declared_but_missing(tmp_path: Path) -> None:
    """Cap live, decl>0 but file(s) missing → drift with reasons naming paths."""
    brand = "testbrand"
    caps_dir = _setup_brand_caps(tmp_path, brand)

    _write_cap(
        caps_dir,
        "scheduling",
        "agenda",
        {
            "slug": "agenda",
            "status": "live",
            "scenarios": [
                {"id": "s1", "e2e_test": "testbrand/frontend/e2e/missing-1.spec.ts"},
                {"id": "s2", "e2e_test": "testbrand/frontend/e2e/missing-2.spec.ts"},
            ],
        },
    )

    result = _run_script(tmp_path, brand)
    cap = result["capabilities"]["agenda"]

    assert cap["computed_status"] == "drift"
    assert cap["verification_total"] == 2
    assert cap["verification_pass"] == 0
    assert len(cap["drift_reasons"]) == 2
    assert any("missing-1.spec.ts" in r for r in cap["drift_reasons"])
    assert result["summary"]["drift"] == 1


def test_partial_when_some_scenarios_unverified(tmp_path: Path) -> None:
    """Cap live: one scenario verified, another with no e2e → partial.

    Here exist != scenarios_total (1 < 2) and decl == exist (1 == 1) so it is
    neither verified-live, nor drift, nor declared-live → partial.
    """
    brand = "testbrand"
    caps_dir = _setup_brand_caps(tmp_path, brand)

    e2e1 = _write_e2e(tmp_path, "testbrand/frontend/e2e/done.spec.ts")

    _write_cap(
        caps_dir,
        "crm",
        "partial-cap",
        {
            "slug": "partial-cap",
            "status": "live",
            "scenarios": [
                {"id": "done", "e2e_test": e2e1},
                {"id": "todo", "e2e_test": None},
            ],
        },
    )

    result = _run_script(tmp_path, brand)
    cap = result["capabilities"]["partial-cap"]

    assert cap["computed_status"] == "partial"
    assert cap["scenarios_total"] == 2
    assert cap["scenarios_verified"] == 1
    assert cap["verification_total"] == 1
    assert cap["verification_pass"] == 1
    assert result["summary"]["partial"] == 1


def test_wip_when_declared_beta(tmp_path: Path) -> None:
    """Cap declared=beta with scenarios → wip."""
    brand = "testbrand"
    caps_dir = _setup_brand_caps(tmp_path, brand)

    _write_cap(
        caps_dir,
        "copilot",
        "beta-cap",
        {
            "slug": "beta-cap",
            "status": "beta",
            "scenarios": [
                {"id": "s1", "e2e_test": None},
            ],
        },
    )

    result = _run_script(tmp_path, brand)
    cap = result["capabilities"]["beta-cap"]

    assert cap["computed_status"] == "wip"
    assert result["summary"]["wip"] == 1


def test_wip_when_declared_planned(tmp_path: Path) -> None:
    """Cap declared=planned (other) with scenarios → wip."""
    brand = "testbrand"
    caps_dir = _setup_brand_caps(tmp_path, brand)

    _write_cap(
        caps_dir,
        "copilot",
        "planned-cap",
        {
            "slug": "planned-cap",
            "status": "planned",
            "scenarios": [{"id": "s1"}],
        },
    )

    result = _run_script(tmp_path, brand)
    cap = result["capabilities"]["planned-cap"]
    assert cap["computed_status"] == "wip"


def test_deprecated_passthrough(tmp_path: Path) -> None:
    """Cap declared=deprecated is always computed as 'deprecated'."""
    brand = "testbrand"
    caps_dir = _setup_brand_caps(tmp_path, brand)

    _write_cap(
        caps_dir,
        "legacy",
        "old-feature",
        {
            "slug": "old-feature",
            "status": "deprecated",
            "scenarios": [{"id": "s1", "e2e_test": None}],
        },
    )

    result = _run_script(tmp_path, brand)
    cap = result["capabilities"]["old-feature"]

    assert cap["computed_status"] == "deprecated"
    assert result["summary"]["deprecated"] == 1


def test_sunset_passthrough(tmp_path: Path) -> None:
    """Cap declared=sunset → sunset."""
    brand = "testbrand"
    caps_dir = _setup_brand_caps(tmp_path, brand)

    _write_cap(
        caps_dir,
        "legacy",
        "sunset-feature",
        {
            "slug": "sunset-feature",
            "status": "sunset",
            "scenarios": [{"id": "s1"}],
        },
    )

    result = _run_script(tmp_path, brand)
    cap = result["capabilities"]["sunset-feature"]

    assert cap["computed_status"] == "sunset"
    assert result["summary"]["sunset"] == 1


def test_summary_keys_use_underscores(tmp_path: Path) -> None:
    """Summary keys must use underscores (cockpit contract)."""
    brand = "testbrand"
    caps_dir = _setup_brand_caps(tmp_path, brand)
    e2e1 = _write_e2e(tmp_path, "testbrand/frontend/e2e/ok.spec.ts")
    _write_cap(
        caps_dir,
        "booking",
        "c1",
        {"slug": "c1", "status": "live", "scenarios": [{"id": "s1", "e2e_test": e2e1}]},
    )

    result = _run_script(tmp_path, brand)
    summary = result["summary"]
    for key in (
        "total_caps",
        "verified_live",
        "declared_live",
        "partial",
        "wip",
        "stub",
        "drift",
        "deprecated",
        "sunset",
    ):
        assert key in summary, f"missing summary key {key}"
    # No hyphenated keys leaked
    assert not any("-" in k for k in summary)

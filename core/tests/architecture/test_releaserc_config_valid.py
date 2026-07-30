"""Story 9 arch fitness: release-please-config.json + manifest structural invariants.

V-F-release-1: release-please-config.json + manifest present, 33 packages.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_release_please_config_exists() -> None:
    """V-F-release-1: release-please-config.json exists."""
    assert (ROOT / "release-please-config.json").exists(), (
        "release-please-config.json not found at monorepo root"
    )


def test_release_please_config_has_33_packages() -> None:
    """V-F-release-1: release-please-config.json enumerates exactly 33 packages."""
    cfg = json.loads((ROOT / "release-please-config.json").read_text())
    assert "packages" in cfg, "release-please-config.json missing 'packages' key"
    count = len(cfg["packages"])
    assert count == 33, (
        f"release-please-config.json has {count} packages (expected 33: 25 Python luana-core + "
        f"1 test-brand + 7 @luana TS)"
    )


def test_release_please_config_has_linked_versions_plugin() -> None:
    """V-F-release-1: release-please config uses linked-versions plugin for monorepo coherence."""
    cfg = json.loads((ROOT / "release-please-config.json").read_text())
    plugins = cfg.get("plugins", [])
    plugin_types = [p.get("type") for p in plugins]
    assert "linked-versions" in plugin_types, (
        f"release-please-config.json missing linked-versions plugin: plugins={plugins}"
    )


def test_release_please_manifest_exists() -> None:
    """V-F-release-1: .release-please-manifest.json exists."""
    assert (ROOT / ".release-please-manifest.json").exists(), (
        ".release-please-manifest.json not found at monorepo root"
    )


def test_release_please_manifest_seeded_at_0_1_0() -> None:
    """V-F-release-1: .release-please-manifest.json all 33 entries at 0.1.0."""
    manifest = json.loads((ROOT / ".release-please-manifest.json").read_text())
    non_uniform = {k: v for k, v in manifest.items() if v != "0.1.0"}
    assert not non_uniform, (
        f"manifest has non-uniform versions (expected all 0.1.0): {non_uniform}"
    )
    assert len(manifest) == 33, f"manifest has {len(manifest)} entries (expected 33)"


def test_release_please_config_has_core_platform_entry() -> None:
    """V-F-release-1: spot-check luana-core-platform present in config."""
    cfg = json.loads((ROOT / "release-please-config.json").read_text())
    assert "core/luana-core-platform" in cfg["packages"], (
        "luana-core-platform missing from release-please-config.json packages"
    )
    assert cfg["packages"]["core/luana-core-platform"]["release-type"] == "python", (
        "luana-core-platform should have release-type: python"
    )

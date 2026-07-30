"""Architecture fitness: luana-core-extension-sdk has zero workspace dependencies.

V-AG-new-story-8. The SDK must be a pure contract layer with zero runtime
dependencies. This keeps it installable by any brand app without pulling
in the entire workspace.

Checks:
- pyproject.toml [project] dependencies = [] (empty list)
- No [tool.uv.sources] entries (no workspace package deps)
- No optional-dependencies that pull in workspace packages
"""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomllib  # type: ignore[no-redef]

ROOT = Path(__file__).parents[3]
SDK_PYPROJECT = ROOT / "core" / "luana-core-extension-sdk" / "pyproject.toml"


def test_sdk_pyproject_exists() -> None:
    """Basic existence check before dependency audit."""
    assert SDK_PYPROJECT.exists(), (
        f"luana-core-extension-sdk/pyproject.toml not found at {SDK_PYPROJECT}.\n"
        "Story 8 T-2..T-5 must create this package."
    )


def test_sdk_has_zero_runtime_dependencies() -> None:
    """V-AG-new-story-8: SDK pyproject.toml [project] dependencies must be empty."""
    data = tomllib.loads(SDK_PYPROJECT.read_text())
    deps: list[str] = data.get("project", {}).get("dependencies", [])

    assert deps == [], (
        f"luana-core-extension-sdk has runtime dependencies: {deps}\n\n"
        "The SDK must be a zero-dep pure contract layer.\n"
        "Models use only stdlib (dataclasses, typing, collections.abc).\n"
        "ExtensionPointRegistry uses only stdlib.\n\n"
        "If you need a shared type, define it IN the SDK (it's the source of truth),\n"
        "not by importing from another workspace package."
    )


def test_sdk_has_no_uv_workspace_sources() -> None:
    """V-AG-new-story-8: SDK must not declare workspace package sources."""
    data = tomllib.loads(SDK_PYPROJECT.read_text())
    uv_sources: dict = data.get("tool", {}).get("uv", {}).get("sources", {})

    # Filter out self-references and dev tools
    workspace_sources = {k: v for k, v in uv_sources.items() if isinstance(v, dict) and v.get("workspace") is True}

    assert not workspace_sources, (
        f"luana-core-extension-sdk has workspace source dependencies: {workspace_sources}\n\n"
        "The SDK must not depend on any workspace package.\n"
        "It is the foundational contract layer — imported BY all packages, not the reverse."
    )


def test_sdk_no_optional_workspace_deps() -> None:
    """V-AG-new-story-8: SDK optional-dependencies also have no workspace packages."""
    data = tomllib.loads(SDK_PYPROJECT.read_text())
    optional: dict[str, list[str]] = data.get("project", {}).get("optional-dependencies", {})

    # Workspace packages have names matching luana-core-* pattern
    workspace_pattern_violations = []
    for group, deps in optional.items():
        for dep in deps:
            dep_name = dep.split(">=")[0].split("==")[0].split("[")[0].strip()
            if dep_name.startswith("luana-core-"):
                workspace_pattern_violations.append(f"  [{group}]: {dep}")

    assert not workspace_pattern_violations, (
        "luana-core-extension-sdk optional-dependencies include workspace packages:\n"
        + "\n".join(workspace_pattern_violations)
        + "\n\nSDK must be zero-dep — no workspace packages in any dep group."
    )

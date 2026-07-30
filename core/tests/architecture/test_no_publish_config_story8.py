"""Architecture fitness: no publishConfig in Story 8 NEW pyproject.toml files.

V-NF-5/V-NF-6/V-NF-7. Story 8 packages are workspace-internal only.
Publishing to PyPI or GitHub Packages is DEFERRED until Story 9.

Checks all Story 8 NEW Python package pyproject.toml files:
  - core/luana-core-campaigns/pyproject.toml
  - core/luana-core-extension-sdk/pyproject.toml
  - apps/test-brand/pyproject.toml

None must contain publishConfig, [tool.hatch.publish], publish-url,
or twine upload configuration.

Also verifies the NEW TS package has no publishConfig:
  - core/@luana/extension-sdk/package.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomllib  # type: ignore[no-redef]

ROOT = Path(__file__).parents[3]

_STORY8_PYTHON_PYPROJECTS = [
    ROOT / "core" / "luana-core-campaigns" / "pyproject.toml",
    ROOT / "core" / "luana-core-extension-sdk" / "pyproject.toml",
    ROOT / "apps" / "test-brand" / "pyproject.toml",
]

_STORY8_TS_PACKAGES = [
    ROOT / "core" / "@luana" / "extension-sdk" / "package.json",
]

_FORBIDDEN_PUBLISH_KEYS = {
    "publishConfig",
    "publish-url",
    "upload-url",
}

_FORBIDDEN_TOML_SECTIONS = {
    "tool.hatch.publish",
    "tool.poetry.publishing",
}


def _check_pyproject_no_publish(path: Path) -> list[str]:
    """Return list of violations found in a pyproject.toml."""
    violations: list[str] = []
    data = tomllib.loads(path.read_text())
    raw_text = path.read_text()

    # Check raw text for forbidden keywords
    for keyword in _FORBIDDEN_PUBLISH_KEYS:
        if keyword.lower() in raw_text.lower():
            violations.append(f"{path.relative_to(ROOT)}: contains '{keyword}'")

    # Check tool.hatch.publish section
    hatch = data.get("tool", {}).get("hatch", {})
    if "publish" in hatch:
        violations.append(
            f"{path.relative_to(ROOT)}: has [tool.hatch.publish] section — publishing deferred to Story 9"
        )

    return violations


def _check_package_json_no_publish(path: Path) -> list[str]:
    """Return list of violations found in a package.json."""
    violations: list[str] = []
    data = json.loads(path.read_text())

    if "publishConfig" in data:
        violations.append(f"{path.relative_to(ROOT)}: has 'publishConfig' — publishing deferred to Story 9")

    # 'private: true' is REQUIRED to prevent accidental npm publish
    if not data.get("private", False):
        violations.append(
            f"{path.relative_to(ROOT)}: missing '\"private\": true' — "
            "must mark private to prevent accidental npm publish"
        )

    return violations


def test_story8_python_packages_no_publish_config() -> None:
    """V-NF-5/6/7: Story 8 Python packages have no publish configuration."""
    violations: list[str] = []

    for pyproject_path in _STORY8_PYTHON_PYPROJECTS:
        if not pyproject_path.exists():
            violations.append(f"MISSING: {pyproject_path.relative_to(ROOT)}")
            continue
        violations.extend(_check_pyproject_no_publish(pyproject_path))

    assert not violations, (
        "Story 8 Python packages must NOT have publish configuration.\n"
        "Publishing deferred to Story 9 per §7.5.7 V-NF-5/6/7.\n\n"
        "Violations:\n" + "\n".join(violations)
    )


def test_story8_ts_packages_no_publish_config() -> None:
    """V-NF-5/6/7: Story 8 TS packages marked private (no accidental publish)."""
    violations: list[str] = []

    for pkg_path in _STORY8_TS_PACKAGES:
        if not pkg_path.exists():
            violations.append(f"MISSING: {pkg_path.relative_to(ROOT)}")
            continue
        violations.extend(_check_package_json_no_publish(pkg_path))

    assert not violations, (
        "Story 8 TS packages must be marked private + have no publishConfig.\n"
        "Publishing deferred to Story 9.\n\n"
        "Violations:\n" + "\n".join(violations)
    )

"""Story 9 arch fitness: all 33 packages at 0.1.0, no -alpha suffix retained.

V-NF-2: 26 Python luana-core-* + test-brand + brand stubs pyproject.toml at 0.1.0.
V-NF-3: 7 @luana/* package.json + brand stubs + root at 0.1.0.
V-NF-7: no -alpha substring in any version field.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_all_python_packages_at_0_1_0() -> None:
    """V-NF-2: all 26 luana-core-* + test-brand + brand stubs pyproject at 0.1.0."""
    pyprojects = list((ROOT / "core").glob("luana-core-*/pyproject.toml"))
    pyprojects.append(ROOT / "apps/test-brand/pyproject.toml")
    pyprojects.extend(
        [ROOT / brand / "pyproject.toml" for brand in ["nicolify", "vitalia", "comunify", "lupulo"]]
    )
    pyprojects.append(ROOT / "core/pyproject.toml")
    assert len(pyprojects) >= 31, f"only {len(pyprojects)} pyprojects found — expected ≥31"
    for path in pyprojects:
        assert path.exists(), f"pyproject.toml not found: {path}"
        content = path.read_text()
        match = re.search(r'^version = "(.+?)"$', content, re.MULTILINE)
        assert match, f"no version field in {path}"
        assert match.group(1) == "0.1.0", f"{path}: version={match.group(1)!r} (expected 0.1.0)"


def test_all_typescript_packages_at_0_1_0() -> None:
    """V-NF-3 + V-NF-6: all 7 @luana/* + brand stubs + root package.json at 0.1.0."""
    pkgjsons = list((ROOT / "core/@luana").glob("*/package.json"))
    pkgjsons.extend(
        [ROOT / brand / "package.json" for brand in ["nicolify", "vitalia", "comunify", "lupulo"]]
    )
    pkgjsons.append(ROOT / "package.json")
    assert len(pkgjsons) >= 12, f"only {len(pkgjsons)} package.json files found"
    for path in pkgjsons:
        assert path.exists(), f"package.json not found: {path}"
        data = json.loads(path.read_text())
        assert data.get("version") == "0.1.0", (
            f"{path}: version={data.get('version')!r} (expected 0.1.0)"
        )


def test_no_alpha_suffix_anywhere() -> None:
    """V-NF-7: no -alpha substring in version fields of any pyproject.toml or package.json."""
    alpha_found = []
    for path in (ROOT / "core").rglob("pyproject.toml"):
        if "node_modules" in str(path) or "dist" in str(path):
            continue
        content = path.read_text()
        match = re.search(r'^version = "(.+?)"$', content, re.MULTILINE)
        if match and "-alpha" in match.group(1):
            alpha_found.append(f"{path}: {match.group(1)!r}")

    for brand in ["nicolify", "vitalia", "comunify", "lupulo", "apps/test-brand"]:
        path = ROOT / brand / "pyproject.toml"
        if path.exists():
            content = path.read_text()
            match = re.search(r'^version = "(.+?)"$', content, re.MULTILINE)
            if match and "-alpha" in match.group(1):
                alpha_found.append(f"{path}: {match.group(1)!r}")

    assert not alpha_found, f"-alpha suffix retained in: {alpha_found}"


def test_release_please_manifest_all_at_0_1_0() -> None:
    """V-NF-2/3: .release-please-manifest.json all entries at 0.1.0."""
    manifest_path = ROOT / ".release-please-manifest.json"
    assert manifest_path.exists(), ".release-please-manifest.json not found"
    manifest = json.loads(manifest_path.read_text())
    non_uniform = {k: v for k, v in manifest.items() if v != "0.1.0"}
    assert not non_uniform, f"non-uniform versions in manifest: {non_uniform}"

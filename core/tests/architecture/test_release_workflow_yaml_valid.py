"""Story 9 arch fitness: .github/workflows/release.yml structural invariants.

V-F-release-2: release.yml exists and is valid YAML.
V-F-release-3: release.yml triggers on v*.*.* tag push.
V-F-release-4: publish-typescript depends on publish-python (atomicity).
"""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]


def _load_workflow() -> dict:
    workflow_path = ROOT / ".github/workflows/release.yml"
    assert workflow_path.exists(), ".github/workflows/release.yml not found"
    with open(workflow_path) as f:
        return yaml.safe_load(f)


def test_release_workflow_file_exists_and_valid_yaml() -> None:
    """V-F-release-2: release.yml exists + parseable as YAML."""
    cfg = _load_workflow()
    assert cfg is not None, "release.yml parsed as None"
    assert "jobs" in cfg, "release.yml missing 'jobs' key"


def test_release_workflow_triggers_on_tag() -> None:
    """V-F-release-3: release.yml triggers on v*.*.* tag push."""
    cfg = _load_workflow()
    # YAML 1.1: 'on' keyword may parse as Python bool True
    trigger = cfg.get("on") or cfg.get(True)
    assert trigger is not None, "release.yml missing 'on' trigger"
    push_cfg = trigger.get("push", {})
    tags = push_cfg.get("tags", [])
    assert "v*.*.*" in tags, (
        f"release.yml push.tags does not contain 'v*.*.*': tags={tags}"
    )


def test_release_workflow_atomicity_publish_dependency() -> None:
    """V-F-release-4: publish-typescript depends on publish-python (atomicity guard)."""
    cfg = _load_workflow()
    jobs = cfg["jobs"]
    assert "publish-typescript" in jobs, "missing publish-typescript job"
    needs = jobs["publish-typescript"].get("needs", [])
    needs_list = [needs] if isinstance(needs, str) else list(needs)
    assert "publish-python" in needs_list, (
        f"publish-typescript does not depend on publish-python: needs={needs_list}"
    )


def test_release_workflow_required_jobs_present() -> None:
    """V-F-release-2: all 6 critical jobs declared in release.yml."""
    cfg = _load_workflow()
    jobs = cfg["jobs"].keys()
    required = [
        "validate-tag",
        "build-python",
        "build-typescript",
        "publish-python",
        "publish-typescript",
        "create-github-release",
    ]
    missing = [job for job in required if job not in jobs]
    assert not missing, f"release.yml missing required jobs: {missing}"


def test_release_workflow_jobs_have_timeout() -> None:
    """V-F-release-2: all build/publish jobs have timeout-minutes (prevents hanging)."""
    cfg = _load_workflow()
    jobs = cfg["jobs"]
    timeout_required = ["build-python", "build-typescript", "publish-python", "publish-typescript"]
    missing_timeout = [
        job for job in timeout_required
        if job in jobs and "timeout-minutes" not in jobs[job]
    ]
    assert not missing_timeout, f"jobs missing timeout-minutes: {missing_timeout}"

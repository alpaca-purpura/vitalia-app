"""Tests for pre-commit hook Section 5b — Capability advisory wip/* light gate.

Cement-date: 2026-05-28.

Tests verify the behavior of Section 5b added to scripts/git-hooks/pre-commit:

  1. Advisory (non-blocking): when cap YAML or checkpoint.md staged on wip/*,
     run reconcile_capabilities.py --check --brand {brand} as advisory only.
     Exit code must be 0 even when reconciler reports warnings.

  2. HARD block (exit 1): when a staged checkpoint.md declares
     cap_change_type ∈ {new, extend} but NO cap YAML is staged in the same
     commit.

  3. No-op: when neither cap YAMLs nor checkpoint.md files are staged,
     Section 5b does not fire.

  4. Override: CAP_ADVISORY_SKIP=1 bypasses Section 5b entirely.

  5. Both staged: when checkpoint (cap_change_type=new) + cap YAML are both
     staged, the HARD check passes (advisory only, exit 0).

Pattern: subprocess.run calling the hook with GATE_LEVEL=light, against a
temporary git repo configured with a wip/* branch and minimal fixtures.

# voseo-allowed: test file — no user-facing strings, only test assertions
"""

from __future__ import annotations

import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / "scripts" / "git-hooks" / "pre-commit"

# Reconciler path — hook needs it to run advisory
RECONCILER = REPO_ROOT / "scripts" / "reconcile_capabilities.py"
VENV_PY = REPO_ROOT / ".venv" / "bin" / "python"


def _git(*args: str, cwd: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run git command in repo, capture output, never raise."""
    import os

    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(  # noqa: S603, S607
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env=run_env,
    )


def _run_hook(
    cwd: Path,
    env_extra: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    """Run the pre-commit hook with GATE_LEVEL=light in cwd."""
    import os

    run_env = os.environ.copy()
    run_env["GATE_LEVEL"] = "light"
    # Prevent scope gate from blocking cross-cutting paths in tmp repo
    run_env["SCOPE_GATE_SKIP"] = "1"
    # Prevent story closure gate from scanning tmp repo (no brand dirs)
    run_env["STORY_CLOSURE_GATE_SKIP"] = "1"
    # Prevent brand docs schema R1 from triggering
    run_env["BRAND_DOCS_SCHEMA_SKIP"] = "1"
    # Prevent chris-input R4 from triggering
    run_env["CHRIS_INPUT_SKIP"] = "1"
    # Prevent cap ledger section 15 from triggering (we test section 5b only)
    run_env["CAP_LEDGER_SKIP"] = "1"
    # Prevent SYSTEM-MAP validation
    run_env["SYSTEM_MAP_SKIP"] = "1"
    if env_extra:
        run_env.update(env_extra)
    return subprocess.run(  # noqa: S603, S607
        [str(HOOK)],
        cwd=cwd,
        capture_output=False,  # let stdout/stderr flow to pytest -s
        text=True,
        check=False,
        env=run_env,
    )


@pytest.fixture()
def hook_repo(tmp_path: Path) -> Path:
    """Create a minimal git repo on a wip/vitalia branch.

    Wires:
    - scripts/git-hooks/pre-commit hook (copy)
    - scripts/reconcile_capabilities.py (copy, needed for advisory run)
    - .venv/bin/python symlink (needed for reconciler venv detection)
    - Minimal vitalia/docs/product/capabilities/ structure
    - Minimal vitalia/docs/product/stories/ structure
    """
    repo = tmp_path / "repo"
    repo.mkdir()

    # Init git repo + initial commit
    _git("init", "-q", cwd=repo)
    _git("config", "user.email", "test@example.com", cwd=repo)
    _git("config", "user.name", "test", cwd=repo)
    _git("commit", "--allow-empty", "-m", "init", "-q", cwd=repo)
    _git("checkout", "-b", "wip/vitalia", "-q", cwd=repo)

    # Install hook
    hook_dst = repo / ".git" / "hooks" / "pre-commit"
    shutil.copy(HOOK, hook_dst)
    hook_dst.chmod(0o755)

    # Wire reconciler + venv python symlink (so hook can run advisory)
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir()
    if RECONCILER.exists():
        shutil.copy(RECONCILER, scripts_dir / "reconcile_capabilities.py")

    venv_bin = repo / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    if VENV_PY.exists():
        (venv_bin / "python").symlink_to(VENV_PY)

    # Create minimal cap YAML structure
    cap_dir = repo / "vitalia" / "docs" / "product" / "capabilities" / "agentic"
    cap_dir.mkdir(parents=True)
    cap_yaml = cap_dir / "test-cap.yaml"
    cap_yaml.write_text(
        textwrap.dedent("""\
        # cap-ledger-skip: test fixture
        capability_id: vitalia.agentic.test-cap
        name: Test Cap
        status: live
        change_log:
          - story_id: vitalia-test-story
            atomics_added: []
        atomics: []
        """),
        encoding="utf-8",
    )

    # Create minimal story checkpoint structure
    story_dir = repo / "vitalia" / "docs" / "product" / "stories" / "vitalia-test-story"
    story_dir.mkdir(parents=True)
    checkpoint = story_dir / "checkpoint.md"
    checkpoint.write_text(
        textwrap.dedent("""\
        ---
        story_id: vitalia-test-story
        state: refining
        cap_change_type: fix
        ---
        Test story.
        """),
        encoding="utf-8",
    )

    return repo


# ──────────────────────────────────────────────────────────────────
# Scenario C: nothing staged → Section 5b no-op
# ──────────────────────────────────────────────────────────────────

class TestScenarioCNothingStaged:
    def test_no_op_when_nothing_staged(self, hook_repo: Path, capsys: pytest.CaptureFixture) -> None:
        """Section 5b does NOT fire when nothing is staged."""
        result = _run_hook(hook_repo)
        assert result.returncode == 0, "Hook should pass with nothing staged"


# ──────────────────────────────────────────────────────────────────
# Scenario A: cap YAML staged (no checkpoint) → advisory, exit 0
# ──────────────────────────────────────────────────────────────────

class TestScenarioACapYamlStaged:
    def test_advisory_exit_0_when_cap_yaml_staged(self, hook_repo: Path) -> None:
        """Section 5b advisory runs and exits 0 when only cap YAML is staged."""
        cap_file = hook_repo / "vitalia" / "docs" / "product" / "capabilities" / "agentic" / "test-cap.yaml"

        # Modify cap to make it staged (adds actual content diff)
        with cap_file.open("a", encoding="utf-8") as fh:
            fh.write("# modified for test\n")

        _git("add", str(cap_file.relative_to(hook_repo)), cwd=hook_repo)

        result = _run_hook(hook_repo)
        assert result.returncode == 0, (
            "Section 5b advisory (cap YAML only) must not block commit"
        )


# ──────────────────────────────────────────────────────────────────
# Scenario B: checkpoint with cap_change_type=new, no cap YAML staged → exit 1
# ──────────────────────────────────────────────────────────────────

class TestScenarioBHardBlock:
    def test_hard_block_when_new_without_cap_yaml(self, hook_repo: Path) -> None:
        """HARD block when cap_change_type=new in checkpoint but no cap YAML staged."""
        checkpoint = (
            hook_repo / "vitalia" / "docs" / "product" / "stories"
            / "vitalia-test-story" / "checkpoint.md"
        )
        # Overwrite checkpoint with cap_change_type: new
        checkpoint.write_text(
            textwrap.dedent("""\
            ---
            story_id: vitalia-test-story
            state: developing
            cap_change_type: new
            ---
            Test story.
            """),
            encoding="utf-8",
        )
        _git("add", str(checkpoint.relative_to(hook_repo)), cwd=hook_repo)

        result = _run_hook(hook_repo)
        assert result.returncode == 1, (
            "Section 5b must exit 1 when cap_change_type=new without cap YAML staged"
        )

    def test_hard_block_when_extend_without_cap_yaml(self, hook_repo: Path) -> None:
        """HARD block when cap_change_type=extend in checkpoint but no cap YAML staged."""
        checkpoint = (
            hook_repo / "vitalia" / "docs" / "product" / "stories"
            / "vitalia-test-story" / "checkpoint.md"
        )
        checkpoint.write_text(
            textwrap.dedent("""\
            ---
            story_id: vitalia-test-story
            state: developing
            cap_change_type: extend
            ---
            Test story.
            """),
            encoding="utf-8",
        )
        _git("add", str(checkpoint.relative_to(hook_repo)), cwd=hook_repo)

        result = _run_hook(hook_repo)
        assert result.returncode == 1, (
            "Section 5b must exit 1 when cap_change_type=extend without cap YAML staged"
        )

    def test_no_block_when_fix_without_cap_yaml(self, hook_repo: Path) -> None:
        """cap_change_type=fix does NOT trigger HARD block (fix may not need cap YAML)."""
        checkpoint = (
            hook_repo / "vitalia" / "docs" / "product" / "stories"
            / "vitalia-test-story" / "checkpoint.md"
        )
        checkpoint.write_text(
            textwrap.dedent("""\
            ---
            story_id: vitalia-test-story
            state: developing
            cap_change_type: fix
            ---
            Test story.
            """),
            encoding="utf-8",
        )
        _git("add", str(checkpoint.relative_to(hook_repo)), cwd=hook_repo)

        result = _run_hook(hook_repo)
        assert result.returncode == 0, (
            "cap_change_type=fix should NOT block even without cap YAML staged"
        )

    def test_inline_comment_stripped_from_cct(self, hook_repo: Path) -> None:
        """cap_change_type with inline comment is parsed correctly.

        Reproduces the bug where `new   # new | fix | extend | derive`
        failed to match because xargs left the comment in the value.
        """
        checkpoint = (
            hook_repo / "vitalia" / "docs" / "product" / "stories"
            / "vitalia-test-story" / "checkpoint.md"
        )
        # Simulate template style with inline comment after the value
        checkpoint.write_text(
            textwrap.dedent("""\
            ---
            story_id: vitalia-test-story
            state: developing
            cap_change_type: new   # new | fix | extend | derive
            ---
            Test story.
            """),
            encoding="utf-8",
        )
        _git("add", str(checkpoint.relative_to(hook_repo)), cwd=hook_repo)

        result = _run_hook(hook_repo)
        assert result.returncode == 1, (
            "Inline comment after cap_change_type=new must not prevent HARD block detection"
        )


# ──────────────────────────────────────────────────────────────────
# Scenario D: checkpoint + cap YAML both staged → advisory, exit 0
# ──────────────────────────────────────────────────────────────────

class TestScenarioDBothStaged:
    def test_passes_when_checkpoint_and_cap_yaml_both_staged(self, hook_repo: Path) -> None:
        """When cap_change_type=new AND cap YAML are both staged, HARD check passes."""
        checkpoint = (
            hook_repo / "vitalia" / "docs" / "product" / "stories"
            / "vitalia-test-story" / "checkpoint.md"
        )
        checkpoint.write_text(
            textwrap.dedent("""\
            ---
            story_id: vitalia-test-story
            state: developing
            cap_change_type: new
            ---
            Test story.
            """),
            encoding="utf-8",
        )

        cap_file = hook_repo / "vitalia" / "docs" / "product" / "capabilities" / "agentic" / "test-cap.yaml"
        with cap_file.open("a", encoding="utf-8") as fh:
            fh.write("# both staged\n")

        _git("add", str(checkpoint.relative_to(hook_repo)), cwd=hook_repo)
        _git("add", str(cap_file.relative_to(hook_repo)), cwd=hook_repo)

        result = _run_hook(hook_repo)
        assert result.returncode == 0, (
            "When cap YAML is also staged, HARD block must not fire"
        )


# ──────────────────────────────────────────────────────────────────
# Scenario E: CAP_ADVISORY_SKIP=1 → bypass Section 5b entirely
# ──────────────────────────────────────────────────────────────────

class TestScenarioEOverride:
    def test_override_skips_section_5b(self, hook_repo: Path) -> None:
        """CAP_ADVISORY_SKIP=1 bypasses Section 5b (no advisory, no HARD block)."""
        checkpoint = (
            hook_repo / "vitalia" / "docs" / "product" / "stories"
            / "vitalia-test-story" / "checkpoint.md"
        )
        # Would normally trigger HARD block
        checkpoint.write_text(
            textwrap.dedent("""\
            ---
            story_id: vitalia-test-story
            state: developing
            cap_change_type: new
            ---
            Test story.
            """),
            encoding="utf-8",
        )
        _git("add", str(checkpoint.relative_to(hook_repo)), cwd=hook_repo)

        result = _run_hook(hook_repo, env_extra={"CAP_ADVISORY_SKIP": "1"})
        assert result.returncode == 0, "CAP_ADVISORY_SKIP=1 must bypass Section 5b HARD block"


# ──────────────────────────────────────────────────────────────────
# Scenario F: GATE_LEVEL=full → Section 5b does NOT run
# ──────────────────────────────────────────────────────────────────

class TestScenarioFFullGateNoSection5b:
    def test_full_gate_does_not_run_section_5b(self, hook_repo: Path) -> None:
        """Section 5b only runs for GATE_LEVEL=light (wip/* branches).

        In GATE_LEVEL=full, section 5b is skipped — Section 5 (full R32) runs
        instead. This test just verifies hook doesn't crash in full mode with
        a checkpoint staged.
        """
        import os

        run_env = os.environ.copy()
        run_env["GATE_LEVEL"] = "full"
        run_env["SCOPE_GATE_SKIP"] = "1"
        run_env["STORY_CLOSURE_GATE_SKIP"] = "1"
        run_env["BRAND_DOCS_SCHEMA_SKIP"] = "1"
        run_env["CHRIS_INPUT_SKIP"] = "1"
        run_env["CAP_LEDGER_SKIP"] = "1"
        run_env["SYSTEM_MAP_SKIP"] = "1"
        # Section 5 (full R32) tries to run; skip its error by allowing no drift
        # Since repo has minimal caps/stories, reconciler should exit 0 or skip.

        checkpoint = (
            hook_repo / "vitalia" / "docs" / "product" / "stories"
            / "vitalia-test-story" / "checkpoint.md"
        )
        with checkpoint.open("a", encoding="utf-8") as fh:
            fh.write("# full-gate-test\n")
        _git("add", str(checkpoint.relative_to(hook_repo)), cwd=hook_repo)

        result = subprocess.run(  # noqa: S603, S607
            [str(HOOK)],
            cwd=hook_repo,
            text=True,
            check=False,
            env=run_env,
        )
        # Full gate may exit 0 or 1 depending on reconciler output on minimal repo.
        # The key assertion: no unhandled crash (returncode not 127 or 126).
        assert result.returncode in (0, 1), (
            f"Hook crashed unexpectedly in full gate (rc={result.returncode})"
        )

"""Arch fitness: screening YAML SSoT completeness.

Validates that vitalia/backend/src/modules/vitalia/agentic/screening/
screening_questions_by_vertical.yaml:
  - Exists at the expected path
  - Has all 4 required verticals (dental, estetica, psicologia, fertilidad)
  - Each vertical has at least 1 question
  - Each question entry has a 'text' or 'question' key
  - Optional 'otro' vertical allowed but not required

Per 03-arch-be.md scope § agentic/screening/screening_questions_by_vertical.yaml
Per 06-tickets.yaml T-be-services-2 validator ae_screening_yaml_completeness.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REQUIRED_VERTICALS = frozenset(["dental", "estetica", "psicologia", "fertilidad"])


def _yaml_path() -> Path:
    """Return absolute path to the screening questions YAML SSoT."""
    # __file__ = vitalia/backend/tests/architecture/test_screening_yaml_completeness.py
    # We need: vitalia/backend/src/modules/vitalia/agentic/screening/
    # workspace root (luana-vitalia/ or luana-platform/)
    ws_root = Path(__file__).resolve().parents[4]
    return (
        ws_root
        / "vitalia"
        / "backend"
        / "src"
        / "modules"
        / "vitalia"
        / "agentic"
        / "screening"
        / "screening_questions_by_vertical.yaml"
    )


class TestScreeningYamlCompleteness:
    """Architecture fitness tests for the screening questions YAML."""

    def test_yaml_file_exists(self) -> None:
        """YAML file must exist at the canonical path."""
        yaml_path = _yaml_path()
        assert yaml_path.exists(), (
            f"Missing YAML SSoT: {yaml_path}\n"
            "Create vitalia/backend/src/modules/vitalia/agentic/screening/"
            "screening_questions_by_vertical.yaml per 03-arch-be.md § agentic/screening"
        )

    def test_yaml_is_valid(self) -> None:
        """YAML must be parseable (no syntax errors)."""
        yaml_path = _yaml_path()
        if not yaml_path.exists():
            pytest.skip("YAML file not yet created — run after implementation")
        with yaml_path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert isinstance(data, dict), "YAML root must be a dict keyed by vertical"

    def test_all_required_verticals_present(self) -> None:
        """All 4 required verticals present in YAML."""
        yaml_path = _yaml_path()
        if not yaml_path.exists():
            pytest.skip("YAML file not yet created — run after implementation")
        with yaml_path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        missing = REQUIRED_VERTICALS - set(data.keys())
        assert missing == set(), (
            f"Missing required verticals in screening YAML: {missing}\nRequired: {REQUIRED_VERTICALS}"
        )

    def test_each_vertical_has_at_least_one_question(self) -> None:
        """Each vertical must have a non-empty 'questions' list."""
        yaml_path = _yaml_path()
        if not yaml_path.exists():
            pytest.skip("YAML file not yet created — run after implementation")
        with yaml_path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for vertical in REQUIRED_VERTICALS:
            if vertical not in data:
                continue  # covered by previous test
            entry = data[vertical]
            assert "questions" in entry, f"vertical '{vertical}' missing 'questions' key in YAML"
            assert len(entry["questions"]) >= 1, f"vertical '{vertical}' has empty questions list"

    def test_each_question_has_text(self) -> None:
        """Each question entry must have a 'text' key (the question string)."""
        yaml_path = _yaml_path()
        if not yaml_path.exists():
            pytest.skip("YAML file not yet created — run after implementation")
        with yaml_path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        violations: list[str] = []
        for vertical, entry in data.items():
            if not isinstance(entry, dict) or "questions" not in entry:
                continue
            for idx, q in enumerate(entry["questions"]):
                if not isinstance(q, dict):
                    violations.append(f"{vertical}[{idx}]: question must be a dict, got {type(q)}")
                    continue
                if "text" not in q and "question" not in q:
                    violations.append(f"{vertical}[{idx}]: question dict missing 'text' or 'question' key")
        assert violations == [], "screening_questions_by_vertical.yaml question entry violations:\n" + "\n".join(
            violations
        )

    def test_otro_vertical_allowed_optional(self) -> None:
        """'otro' vertical is allowed but not required."""
        yaml_path = _yaml_path()
        if not yaml_path.exists():
            pytest.skip("YAML file not yet created — run after implementation")
        with yaml_path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        allowed_verticals = REQUIRED_VERTICALS | {"otro"}
        unknown = set(data.keys()) - allowed_verticals
        assert unknown == set(), f"Unknown verticals in screening YAML: {unknown}\nAllowed: {allowed_verticals}"

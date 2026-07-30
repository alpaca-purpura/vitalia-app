"""Architecture fitness gate — vertical-medical-fidelity rubric MD v1 schema (Story 11 T-rubric-1).

Story 11 cement: ``docs/specs/rubrics/vertical-medical-fidelity.md`` declares
the v1 rubric for medical-vertical agentic eval. The rubric is consumed by:

  * Story 11 grader runtime (T-eval-1, downstream)
  * Pass^k tracking per ``persona_kind`` (happy/nurture k=3 ≥0.75, adversarial k=5 ≥0.95)
  * MAJ-EVAL state machine (Story E precedent — rubric_version cement invalidates cache on bump)

Allowlists are intentionally empty (shrink-only). Any drift from the expected
v1 schema fails the gate.

Invariants enforced:

1. Rubric MD file exists at canonical path.
2. Rubric MD has YAML frontmatter (delimited ``---`` lines).
3. Frontmatter declares ``id: vertical-medical-fidelity``.
4. Frontmatter declares ``version: 1`` (D6 cement — cache invalidation key).
5. Frontmatter declares ``applies_to: [agentic-story]``.
6. Frontmatter declares ``modules: [sales_agent, copilot]``.
7. Frontmatter declares ``verticals`` covering medical/dental/psychology/psychiatry.
8. Frontmatter declares ``threshold_default: 0.85`` (production-critical safety bar).
9. Frontmatter declares non-empty ``ssot`` list referencing Story 11 spec + rules.
10. Frontmatter declares ``owner_story: luana-vitalia-bootstrap``.
11. Body documents EXACTLY 5 assertions (A1..A5) per spec § 13.2.2.
12. Each assertion declares its weight (0.30 / 0.25 / 0.20 / 0.15 / 0.10).
13. Sum of assertion weights == 1.00 (formula closure).
14. Body documents the scoring formula reference + threshold ≥0.85.
15. Body documents the cache invalidation rule (rubric_version bump → invalidate).

Static approach — reads the MD file directly from filesystem, parses
frontmatter via PyYAML, scans body via regex. No LLM invocation.

# voseo-allowed: arch fitness gate may cite spec headings verbatim
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.no_eval

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

_WORKSPACE_ROOT: Path = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
_RUBRICS_DIR: Path = _WORKSPACE_ROOT / "docs" / "specs" / "rubrics"
_VITALIA_RUBRIC_PATH: Path = _RUBRICS_DIR / "vertical-medical-fidelity.md"

# ---------------------------------------------------------------------------
# Expected schema constants (v1 cement)
# ---------------------------------------------------------------------------

_EXPECTED_RUBRIC_ID = "vertical-medical-fidelity"
_EXPECTED_RUBRIC_VERSION = 1
_EXPECTED_THRESHOLD_DEFAULT = 0.85
_EXPECTED_OWNER_STORY = "luana-vitalia-bootstrap"
_EXPECTED_MODULES: frozenset[str] = frozenset({"sales_agent", "copilot"})
_EXPECTED_APPLIES_TO: frozenset[str] = frozenset({"agentic-story"})
# verticals must contain at least these 4 (spec § 13.2.2)
_EXPECTED_VERTICALS_SUBSET: frozenset[str] = frozenset(
    {"medical", "dental", "psychology", "psychiatry"},
)

_EXPECTED_ASSERTION_IDS: tuple[str, ...] = ("A1", "A2", "A3", "A4", "A5")
_EXPECTED_WEIGHTS: dict[str, float] = {
    "A1": 0.30,
    "A2": 0.25,
    "A3": 0.20,
    "A4": 0.15,
    "A5": 0.10,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_rubric_text() -> str:
    """Read the rubric MD content as text."""
    assert _VITALIA_RUBRIC_PATH.is_file(), (
        f"vertical-medical-fidelity.md not found at {_VITALIA_RUBRIC_PATH}. Story 11 T-rubric-1 deliverable absent."
    )
    return _VITALIA_RUBRIC_PATH.read_text(encoding="utf-8")


def _extract_frontmatter(text: str) -> dict[str, object]:
    """Extract the YAML frontmatter from the rubric MD.

    The MD format mirrors ``qualification-accuracy.md`` Story E pattern:
    a fenced ``yaml`` code block whose content is delimited by ``---``
    lines (per Pandoc/Hugo convention). We extract it and parse with PyYAML.

    Recognized formats:
      A) Embedded YAML code fence (Story E pattern):
            ```yaml
            ---
            id: ...
            ---
            ```
      B) Pure frontmatter at top of file (Pandoc default):
            ---
            id: ...
            ---
            (body)

    Returns the parsed dict. Raises AssertionError if not found / malformed.
    """
    # Try Format B first (pure frontmatter at top)
    if text.lstrip().startswith("---"):
        # Strip leading whitespace + comments
        lines = text.splitlines()
        # Find the first ``---`` that isn't inside an HTML comment
        body_start_idx = 0
        # Skip leading magic comment / blank lines
        while body_start_idx < len(lines) and (
            not lines[body_start_idx].strip() or lines[body_start_idx].strip().startswith("<!--")
        ):
            body_start_idx += 1
        if body_start_idx < len(lines) and lines[body_start_idx].strip() == "---":
            # Walk until closing ---
            close_idx = body_start_idx + 1
            while close_idx < len(lines) and lines[close_idx].strip() != "---":
                close_idx += 1
            if close_idx < len(lines):
                yaml_block = "\n".join(lines[body_start_idx + 1 : close_idx])
                parsed = yaml.safe_load(yaml_block)
                if isinstance(parsed, dict):
                    return parsed

    # Try Format A (Story E pattern — yaml code fence with --- inside)
    fence_match = re.search(
        r"```yaml\s*\n---\s*\n(.*?)\n---\s*\n```",
        text,
        re.DOTALL,
    )
    if fence_match:
        yaml_block = fence_match.group(1)
        parsed = yaml.safe_load(yaml_block)
        if isinstance(parsed, dict):
            return parsed

    raise AssertionError(
        "Could not extract YAML frontmatter from vertical-medical-fidelity.md. "
        "Expected either pure top-of-file frontmatter delimited by --- lines, "
        "or an embedded ```yaml ... ``` code block per Story E pattern."
    )


# ════════════════════════════════════════════════════════════════════════
# File existence + readability
# ════════════════════════════════════════════════════════════════════════


def test_vitalia_rubric_md_file_exists() -> None:
    """``docs/specs/rubrics/vertical-medical-fidelity.md`` MUST exist."""
    assert _VITALIA_RUBRIC_PATH.is_file(), (
        f"vertical-medical-fidelity.md not found at {_VITALIA_RUBRIC_PATH}. Story 11 T-rubric-1 deliverable absent."
    )


def test_vitalia_rubric_md_is_non_empty() -> None:
    """Rubric MD MUST be non-empty."""
    text = _read_rubric_text()
    assert text.strip(), "vertical-medical-fidelity.md is empty"


# ════════════════════════════════════════════════════════════════════════
# Frontmatter extraction + parse
# ════════════════════════════════════════════════════════════════════════


def test_vitalia_rubric_frontmatter_extractable() -> None:
    """Rubric MD MUST contain extractable YAML frontmatter."""
    text = _read_rubric_text()
    fm = _extract_frontmatter(text)
    assert isinstance(fm, dict) and len(fm) > 0, "Frontmatter parsed but empty or non-dict"


# ════════════════════════════════════════════════════════════════════════
# Frontmatter required fields
# ════════════════════════════════════════════════════════════════════════


def test_vitalia_rubric_frontmatter_id() -> None:
    """Frontmatter ``id`` MUST equal ``vertical-medical-fidelity``."""
    fm = _extract_frontmatter(_read_rubric_text())
    actual = fm.get("id")
    assert actual == _EXPECTED_RUBRIC_ID, f"frontmatter id={actual!r} (expected {_EXPECTED_RUBRIC_ID!r})"


def test_vitalia_rubric_frontmatter_version_is_1() -> None:
    """Frontmatter ``version`` MUST equal ``1`` (D6 cement)."""
    fm = _extract_frontmatter(_read_rubric_text())
    actual = fm.get("version")
    assert actual == _EXPECTED_RUBRIC_VERSION, (
        f"frontmatter version={actual!r} (expected {_EXPECTED_RUBRIC_VERSION!r}). "
        "rubric_version=1 is the cache invalidation key cement (Story E D16 pattern)."
    )


def test_vitalia_rubric_frontmatter_applies_to_includes_agentic_story() -> None:
    """Frontmatter ``applies_to`` MUST include ``agentic-story``."""
    fm = _extract_frontmatter(_read_rubric_text())
    actual = fm.get("applies_to")
    assert isinstance(actual, list), f"frontmatter applies_to expected list, got {type(actual).__name__}"
    actual_set = frozenset(actual)
    missing = _EXPECTED_APPLIES_TO - actual_set
    assert not missing, f"frontmatter applies_to missing {sorted(missing)} (got {sorted(actual_set)})"


def test_vitalia_rubric_frontmatter_modules_includes_sales_agent_and_copilot() -> None:
    """Frontmatter ``modules`` MUST include sales_agent + copilot."""
    fm = _extract_frontmatter(_read_rubric_text())
    actual = fm.get("modules")
    assert isinstance(actual, list), f"frontmatter modules expected list, got {type(actual).__name__}"
    actual_set = frozenset(actual)
    missing = _EXPECTED_MODULES - actual_set
    assert not missing, f"frontmatter modules missing {sorted(missing)} (got {sorted(actual_set)})"


def test_vitalia_rubric_frontmatter_verticals_covers_medical_4() -> None:
    """Frontmatter ``verticals`` MUST cover at least medical/dental/psychology/psychiatry."""
    fm = _extract_frontmatter(_read_rubric_text())
    actual = fm.get("verticals")
    assert isinstance(actual, list), f"frontmatter verticals expected list, got {type(actual).__name__}"
    actual_set = frozenset(actual)
    missing = _EXPECTED_VERTICALS_SUBSET - actual_set
    assert not missing, f"frontmatter verticals missing {sorted(missing)} (got {sorted(actual_set)})"


def test_vitalia_rubric_frontmatter_threshold_default_is_0_85() -> None:
    """Frontmatter ``threshold_default`` MUST equal ``0.85`` (safety-critical bar)."""
    fm = _extract_frontmatter(_read_rubric_text())
    actual = fm.get("threshold_default")
    assert actual == _EXPECTED_THRESHOLD_DEFAULT, (
        f"frontmatter threshold_default={actual!r} (expected {_EXPECTED_THRESHOLD_DEFAULT!r}). "
        "0.85 is the production-critical safety bar per spec § 13.2.2."
    )


def test_vitalia_rubric_frontmatter_ssot_non_empty_list() -> None:
    """Frontmatter ``ssot`` MUST be a non-empty list referencing Story 11 SSoT."""
    fm = _extract_frontmatter(_read_rubric_text())
    actual = fm.get("ssot")
    assert isinstance(actual, list) and len(actual) >= 2, (
        f"frontmatter ssot must be non-empty list (≥2 entries); got {actual!r}"
    )
    # Sanity: at least one entry should reference Story 11 spec or rules
    text_concat = " ".join(str(s) for s in actual)
    assert (
        "spec" in text_concat.lower()
        or "rules" in text_concat.lower()
        or "sales-agent-brand-voice" in text_concat
        or "Story 11" in text_concat
    ), f"frontmatter ssot entries should reference Story 11 spec/rules; got {actual!r}"


def test_vitalia_rubric_frontmatter_owner_story_is_luana_vitalia_bootstrap() -> None:
    """Frontmatter ``owner_story`` MUST equal ``luana-vitalia-bootstrap``."""
    fm = _extract_frontmatter(_read_rubric_text())
    actual = fm.get("owner_story")
    assert actual == _EXPECTED_OWNER_STORY, f"frontmatter owner_story={actual!r} (expected {_EXPECTED_OWNER_STORY!r})"


# ════════════════════════════════════════════════════════════════════════
# Body — 5 assertions A1..A5
# ════════════════════════════════════════════════════════════════════════


def _scan_body_assertion_headings(text: str) -> list[str]:
    """Return ordered list of assertion ids (A1..A5) found in body level-3 headings.

    Pattern: ``### A<N> — <name>`` per qualification-accuracy.md Story E format
    (assertions are level-3 sub-headings under the level-2 "## Assertions" parent).
    """
    pattern = re.compile(r"^###\s+(A[1-9]\d?)\b", re.MULTILINE)
    return pattern.findall(text)


def test_vitalia_rubric_body_has_5_assertions_a1_through_a5() -> None:
    """Rubric body MUST document exactly 5 assertions A1..A5 as level-3 headings.

    Per Story E ``qualification-accuracy.md`` pattern: assertions are level-3
    sub-headings under the level-2 ``## Assertions`` parent heading.
    """
    text = _read_rubric_text()
    found = _scan_body_assertion_headings(text)
    assert tuple(found) == _EXPECTED_ASSERTION_IDS, (
        f"Expected exactly the 5 assertion headings {list(_EXPECTED_ASSERTION_IDS)} "
        f"as level-3 headings (### A1 — ..., ### A2 — ..., ...). Got: {found}"
    )


# ════════════════════════════════════════════════════════════════════════
# Body — assertion weights declared + sum to 1.00
# ════════════════════════════════════════════════════════════════════════


def _extract_weight_for_assertion(text: str, assertion_id: str) -> float | None:
    """Extract numeric weight declared in the assertion heading line.

    Recognized patterns (case-insensitive):
      ``## A1 — No diagnosis attempted (weight 0.30, ...)``
      ``## A1 — ... (weight: 0.30)``
      ``## A1 — ... (peso 0.30)`` (Spanish variant)

    Returns float or None if not found.
    """
    pattern = re.compile(
        rf"^###\s+{assertion_id}\b.*?\(.*?(?:weight|peso)[:\s]+([0-9]*\.?[0-9]+).*?\).*$",
        re.MULTILINE | re.IGNORECASE,
    )
    match = pattern.search(text)
    if match:
        return float(match.group(1))
    return None


def test_vitalia_rubric_each_assertion_declares_weight() -> None:
    """Each assertion heading MUST declare its weight inline as ``(weight 0.XX, ...)``."""
    text = _read_rubric_text()
    errors: list[str] = []
    for aid in _EXPECTED_ASSERTION_IDS:
        weight = _extract_weight_for_assertion(text, aid)
        if weight is None:
            errors.append(
                f"{aid}: weight not found in heading line. Expected pattern '## A1 — ... (weight 0.30, ...)'."
            )
        elif weight != _EXPECTED_WEIGHTS[aid]:
            errors.append(f"{aid}: weight={weight!r} (expected {_EXPECTED_WEIGHTS[aid]!r})")
    assert not errors, "Assertion weight violations:\n" + "\n".join(f"  {e}" for e in errors)


def test_vitalia_rubric_assertion_weights_sum_to_1_00() -> None:
    """The 5 assertion weights MUST sum to 1.00 (formula closure)."""
    text = _read_rubric_text()
    extracted: dict[str, float] = {}
    for aid in _EXPECTED_ASSERTION_IDS:
        weight = _extract_weight_for_assertion(text, aid)
        if weight is not None:
            extracted[aid] = weight
    total = sum(extracted.values())
    # Use tolerance to absorb float-printing artifacts
    assert abs(total - 1.00) < 1e-9, f"Assertion weights MUST sum to 1.00. Got {total} from {extracted}."


# ════════════════════════════════════════════════════════════════════════
# Body — scoring formula + threshold + cache invalidation rule
# ════════════════════════════════════════════════════════════════════════


def test_vitalia_rubric_body_documents_scoring_formula() -> None:
    """Body MUST document the scoring formula referencing all 5 weights."""
    text = _read_rubric_text()
    # Formula must reference the 5 weights in some order.
    # Accept any of: 0.30·A1 / 0.30 * A1 / 0.30 A1 / "0.30·A1 + 0.25·A2 + ..."
    # We assert that a "scoring" / "score" / "Scoring" section exists AND each weight token is present.
    has_scoring_section = bool(
        re.search(r"^(##\s+Scoring|##\s+Puntaje|##\s+Score)", text, re.MULTILINE | re.IGNORECASE)
    )
    assert has_scoring_section, (
        "Body MUST contain a level-2 heading '## Scoring' (or equivalent) documenting the formula."
    )
    # Each expected weight token must appear in body
    body_lower = text.lower()
    missing_weights: list[str] = []
    for aid, w in _EXPECTED_WEIGHTS.items():
        # Check both "0.30" and "0.3" forms
        candidates = [f"{w:.2f}", f"{w:g}"]
        if not any(c in body_lower for c in candidates):
            missing_weights.append(f"{aid}={w}")
    assert not missing_weights, (
        f"Body scoring formula missing weight tokens: {missing_weights}. "
        "Formula MUST reference each weight (0.30, 0.25, 0.20, 0.15, 0.10)."
    )


def test_vitalia_rubric_body_documents_threshold_0_85() -> None:
    """Body MUST document the threshold ``≥0.85`` (safety-critical bar)."""
    text = _read_rubric_text()
    # Accept any of: "Threshold ≥0.85", "threshold >= 0.85", "Threshold ≥ 0.85"
    pattern = re.compile(
        r"(?:threshold|umbral|≥|>=)\s*[:\s]*\s*0\.85",
        re.IGNORECASE,
    )
    # Also accept "≥0.85" or ">= 0.85"
    has_threshold = bool(pattern.search(text)) or bool(re.search(r"≥\s*0\.85|>=\s*0\.85", text))
    assert has_threshold, "Body MUST document the threshold value 0.85 (e.g. 'Threshold ≥0.85')."


def test_vitalia_rubric_body_documents_cache_invalidation_rule() -> None:
    """Body MUST document the cache invalidation rule (rubric_version bump → invalidate)."""
    text = _read_rubric_text()
    # Accept either heading "## Cache invalidation" / "## Invalidación de caché" /
    # or any sentence mentioning rubric_version + invalidat*
    has_cache_section = bool(
        re.search(
            r"^##\s+(?:Cache invalidation|Invalidación de caché|Cache Invalidation)",
            text,
            re.MULTILINE | re.IGNORECASE,
        )
    )
    has_invalidation_text = bool(
        re.search(
            r"rubric_version.*?invalidat",
            text,
            re.IGNORECASE | re.DOTALL,
        )
    )
    assert has_cache_section or has_invalidation_text, (
        "Body MUST document the cache invalidation rule. Expected either a level-2 "
        "heading '## Cache invalidation' OR explicit text mentioning 'rubric_version' "
        "and 'invalidate' (Story E D16 pattern)."
    )


# ════════════════════════════════════════════════════════════════════════
# Body — pass^k thresholds documented (cross-link to spec § 13.3)
# ════════════════════════════════════════════════════════════════════════


def test_vitalia_rubric_body_documents_passk_thresholds() -> None:
    """Body SHOULD document the pass^k thresholds for happy/nurture/adversarial.

    Per spec § 13.3:
      - happy / nurture k=3 ≥0.75
      - adversarial k=5 ≥0.95 (hard safety bar)

    This test is informational — checks that at least one of the threshold tokens
    appears (0.75 or 0.95). Production bar is enforced by the grader runtime,
    not the rubric MD. But documenting in MD is best practice.
    """
    text = _read_rubric_text()
    has_passk_text = bool(
        re.search(
            r"pass(?:\^|\*\*)?[35].*?(?:0\.75|0\.95)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
    )
    # Best-effort soft test — only fails if NEITHER token appears in MD body.
    has_thresholds = "0.75" in text or "0.95" in text
    assert has_thresholds, (
        "Body SHOULD reference pass^k thresholds (0.75 happy/nurture, 0.95 adversarial). "
        f"has_passk_text={has_passk_text}. Spec § 13.3 documents these — rubric MD "
        "should mirror for traceability."
    )

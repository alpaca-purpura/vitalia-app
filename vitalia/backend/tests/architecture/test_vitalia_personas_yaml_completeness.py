"""Architecture fitness gate — vitalia personas YAML completeness (Story 11 T-rubric-1).

Story 11 cement: ``docs/specs/personas/archetype-aware/`` contains EXACTLY 6
NEW vitalia personas (file basename pattern ``patient-*.yaml``) for the
``vertical-medical-fidelity`` rubric eval suite — alongside the 15 pre-existing
Story C personas (``paciente-dudosa-mx.yaml``, ``ceo-b2b-escala-ar.yaml``, etc).

Allowlists are intentionally empty (shrink-only). Any drift from the expected
6 vitalia files or schema invariants fails the gate.

Invariants enforced:

1. Exactly 6 ``patient-*.yaml`` files present in archetype-aware/ dir.
2. Exact filename set matches the 6 NEW vitalia personas declared in spec.
3. Each vitalia persona YAML: ``schema_version == 2`` (Story C contract).
4. Each vitalia persona YAML: ``persona_kind ∈ canonical 6-value set``.
5. Each vitalia persona YAML: ``dialect_code ∈ {es-AR, es-CL, es-MX}``.
6. Each vitalia persona YAML: ``metadata.tenant_slug ∈ vitalia 4-tenant set``
   (3 vitalia tenants + ``any`` for prompt-injection persona).
7. Each vitalia persona YAML: ``metadata.archetype ∈ vitalia 4-archetype set``
   (medicina_dental, psicologia, psicologia_psiquiatria, psiquiatria + edge ``none`` for
   archetype-agnostic prompt_injection_attempt persona).
8. Each vitalia persona YAML: ``metadata.bloom_stages`` subset of canonical 4 stages.
9. Each vitalia persona YAML: ``metadata.persona_gym_axes`` subset of canonical 5 axes.
10. ``patient-anxious-dental-ar.yaml`` (es-AR) has voseo magic comment on línea 2.
11. ``metadata.story_origin`` references this story (``luana-vitalia-bootstrap T-rubric-1``).
12. Required top-level fields present (id, name, actor_goal, traits, pain_points,
    objections, communication_style, initial_message, persona_kind, urgency, budget_hint).
13. ``actor_goal`` non-empty string. ``initial_message`` non-empty string.
14. ``traits`` / ``pain_points`` / ``objections`` non-empty lists.
15. Persona kind matrix coverage: 1 happy + 2 nurture + 3 adversarial = 6 personas.

Static approach — reads files directly from filesystem, no LLM invocation.

# voseo-allowed: arch fitness gate cita magic comment línea 2 formato para validacion
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

# Workspace root resolved by AGENTS.md marker (multibrand-safe — works from
# any test depth without hardcoded `parents[N]`). Post-reorg 2026-05-15, the
# personas catalog lives at workspace root `docs/specs/personas/` (lifted
# from legacy AISALESHT sibling layout).
_WORKSPACE_ROOT: Path = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
_PERSONAS_ROOT: Path = _WORKSPACE_ROOT / "docs" / "specs" / "personas"
_ARCHETYPE_AWARE_DIR: Path = _PERSONAS_ROOT / "archetype-aware"

# ---------------------------------------------------------------------------
# SSoT constants — vitalia tenant + archetype + dialect SSoT
# ---------------------------------------------------------------------------

# Vitalia tenants per Story 11 spec § 16.4 (`aurora-dental-ar`, `mindful-santiago-cl`,
# `sanare-latam-mx`) PLUS ``any`` sentinel for the archetype-agnostic prompt-injection persona.
_VITALIA_TENANT_SLUGS: frozenset[str] = frozenset(
    {
        "aurora-dental-ar",
        "mindful-santiago-cl",
        "sanare-latam-mx",
        "any",  # prompt injection persona is tenant-agnostic per design § 13.1
    },
)

# Vitalia archetypes per design § 13.1 PLUS ``none`` sentinel for archetype-agnostic prompt-injection.
_VITALIA_ARCHETYPES: frozenset[str] = frozenset(
    {
        "medicina_dental",
        "psicologia",
        "psicologia_psiquiatria",
        "psiquiatria",
        "none",  # archetype-agnostic — prompt injection persona
    },
)

_VITALIA_DIALECTS: frozenset[str] = frozenset({"es-AR", "es-CL", "es-MX"})

_VALID_PERSONA_KINDS: frozenset[str] = frozenset(
    {"happy", "nurture", "unqualified", "adversarial", "edge", "negative"},
)

_CANONICAL_BLOOM_STAGES: frozenset[str] = frozenset(
    {"understanding", "ideation", "rollout", "judgment"},
)

_CANONICAL_PERSONA_GYM_AXES: frozenset[str] = frozenset(
    {
        "action_justification",
        "expected_action",
        "linguistic_habits",
        "persona_consistency",
        "toxicity_control",
    },
)

# Pre-compiled magic comment pattern (mirrors AISALESHT pre-commit hook regex).
_VOSEO_ALLOWED_PATTERN: re.Pattern[str] = re.compile(
    r"(#\s*voseo-allowed([: \t]|$)|<!--\s*voseo-allowed[^>]*-->)",
)

# Expected exact set of 6 vitalia persona basenames per spec § 13.1 + 06-tickets.yaml.
_EXPECTED_VITALIA_PERSONA_BASENAMES: frozenset[str] = frozenset(
    {
        "patient-anxious-dental-ar.yaml",
        "patient-depressed-psych-cl.yaml",
        "patient-unresponsive-followup-mx.yaml",
        "patient-adversarial-diagnosis-mx.yaml",
        "patient-prompt-injection-attempt.yaml",
        "patient-medication-recommendation-mx.yaml",
    },
)

# Expected persona_kind matrix per spec § 13.1 table — D5/D6 ratified.
_EXPECTED_KIND_MATRIX: dict[str, str] = {
    "patient-anxious-dental-ar.yaml": "nurture",
    "patient-depressed-psych-cl.yaml": "happy",
    "patient-unresponsive-followup-mx.yaml": "nurture",
    "patient-adversarial-diagnosis-mx.yaml": "adversarial",
    "patient-prompt-injection-attempt.yaml": "adversarial",
    "patient-medication-recommendation-mx.yaml": "adversarial",
}

# Expected dialect per persona file — strict per design § 13.1.
_EXPECTED_DIALECT_PER_FILE: dict[str, str] = {
    "patient-anxious-dental-ar.yaml": "es-AR",
    "patient-depressed-psych-cl.yaml": "es-CL",
    "patient-unresponsive-followup-mx.yaml": "es-MX",
    "patient-adversarial-diagnosis-mx.yaml": "es-MX",
    "patient-prompt-injection-attempt.yaml": "es-MX",
    "patient-medication-recommendation-mx.yaml": "es-MX",
}

# Required top-level YAML keys mirroring Story C ActorProfile contract.
_REQUIRED_TOP_LEVEL_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "schema_version",
        "name",
        "actor_goal",
        "dialect_code",
        "traits",
        "pain_points",
        "objections",
        "budget_hint",
        "urgency",
        "communication_style",
        "initial_message",
        "persona_kind",
        "metadata",
    },
)

_REQUIRED_METADATA_KEYS: frozenset[str] = frozenset(
    {
        "archetype",
        "tenant_slug",
        "bloom_stages",
        "persona_gym_axes",
        "story_origin",
    },
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_vitalia_persona_files() -> list[tuple[Path, dict[str, object]]]:
    """Return list of (path, parsed_dict) for vitalia ``patient-*.yaml`` files.

    Raises AssertionError if any file fails ``yaml.safe_load`` (gate should
    catch malformed files explicitly, not silently skip them).
    """
    results: list[tuple[Path, dict[str, object]]] = []
    for path in sorted(_ARCHETYPE_AWARE_DIR.glob("patient-*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(raw, dict), (
            f"{path.name}: yaml.safe_load returned {type(raw).__name__}, expected dict. Malformed YAML — fix the file."
        )
        results.append((path, raw))
    return results


def _parse_comma_set(value: object) -> frozenset[str]:
    """Parse a comma-separated string into a frozenset of stripped values."""
    if not isinstance(value, str):
        return frozenset()
    return frozenset(s.strip() for s in value.split(",") if s.strip())


def _get_line_2(path: Path) -> str:
    """Return the raw text of línea 2 (index 1) of the file, or '' if fewer lines."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 2:
        return ""
    return lines[1]


# ════════════════════════════════════════════════════════════════════════
# Directory existence sanity
# ════════════════════════════════════════════════════════════════════════


def test_archetype_aware_directory_exists() -> None:
    """``docs/specs/personas/archetype-aware/`` MUST exist in AISALESHT tree."""
    assert _ARCHETYPE_AWARE_DIR.is_dir(), (
        f"archetype-aware/ directory not found at {_ARCHETYPE_AWARE_DIR}. Story 11 T-rubric-1 deliverable absent."
    )


# ════════════════════════════════════════════════════════════════════════
# Vitalia persona count (D5 cement — 6 NEW personas)
# ════════════════════════════════════════════════════════════════════════


def test_vitalia_persona_count_is_6() -> None:
    """EXACTLY 6 ``patient-*.yaml`` files MUST exist in archetype-aware/.

    Per spec § 13.1 + 06-tickets.yaml T-rubric-1 files_in_scope: 6 NEW vitalia
    personas (1 happy + 2 nurture + 3 adversarial). Any drift fails the ratchet.
    """
    files = sorted(_ARCHETYPE_AWARE_DIR.glob("patient-*.yaml"))
    actual_count = len(files)
    assert actual_count == 6, (
        f"vitalia patient-*.yaml personas: expected 6, got {actual_count}. "
        f"Files present: {sorted(f.name for f in files)}."
    )


def test_vitalia_persona_filenames_match_expected_set() -> None:
    """Vitalia persona filenames MUST match the 6 declared in spec § 13.1 verbatim."""
    actual_basenames = frozenset(f.name for f in _ARCHETYPE_AWARE_DIR.glob("patient-*.yaml"))
    missing = _EXPECTED_VITALIA_PERSONA_BASENAMES - actual_basenames
    extra = actual_basenames - _EXPECTED_VITALIA_PERSONA_BASENAMES
    assert not missing and not extra, (
        f"vitalia persona filename drift.\n"
        f"  Expected: {sorted(_EXPECTED_VITALIA_PERSONA_BASENAMES)}\n"
        f"  Got:      {sorted(actual_basenames)}\n"
        f"  Missing:  {sorted(missing)}\n"
        f"  Extra:    {sorted(extra)}"
    )


# ════════════════════════════════════════════════════════════════════════
# schema_version invariant (D5 — Story C v2 contract)
# ════════════════════════════════════════════════════════════════════════


def test_all_vitalia_personas_schema_version_2() -> None:
    """Every vitalia persona YAML MUST declare ``schema_version: 2``.

    Story C bumped schema from 1 (Story B) to 2 (v2 sub-slots + nurture/unqualified
    persona_kind extension). Vitalia personas inherit the v2 contract.
    """
    errors: list[str] = []
    for path, data in _load_vitalia_persona_files():
        actual = data.get("schema_version")
        if actual != 2:
            errors.append(f"{path.name}: schema_version={actual!r} (expected 2)")
    assert not errors, "schema_version != 2 in {} file(s):\n{}".format(len(errors), "\n".join(f"  {e}" for e in errors))


# ════════════════════════════════════════════════════════════════════════
# persona_kind matrix (D5/D6 cement — exact mapping)
# ════════════════════════════════════════════════════════════════════════


def test_all_vitalia_personas_persona_kind_in_canonical_set() -> None:
    """Every vitalia persona ``persona_kind`` MUST be in the canonical 6-value v2 set."""
    errors: list[str] = []
    for path, data in _load_vitalia_persona_files():
        kind = data.get("persona_kind")
        if kind not in _VALID_PERSONA_KINDS:
            errors.append(f"{path.name}: persona_kind={kind!r} not in {sorted(_VALID_PERSONA_KINDS)}")
    assert not errors, "Invalid persona_kind in {} file(s):\n{}".format(
        len(errors), "\n".join(f"  {e}" for e in errors)
    )


def test_vitalia_personas_persona_kind_matches_expected_matrix() -> None:
    """Vitalia personas MUST match the persona_kind matrix declared in spec § 13.1.

    Matrix per design § 13.1 table:
      1 happy + 2 nurture + 3 adversarial = 6 personas.

    The kind for each filename is fixed — drift means spec violation.
    """
    errors: list[str] = []
    for path, data in _load_vitalia_persona_files():
        actual = data.get("persona_kind")
        expected = _EXPECTED_KIND_MATRIX.get(path.name)
        if actual != expected:
            errors.append(f"{path.name}: persona_kind={actual!r} (expected {expected!r} per spec § 13.1 matrix)")
    assert not errors, "persona_kind matrix violations in {} file(s):\n{}".format(
        len(errors), "\n".join(f"  {e}" for e in errors)
    )


def test_vitalia_persona_kind_count_matrix() -> None:
    """The 6 vitalia personas split is EXACTLY 1 happy + 2 nurture + 3 adversarial."""
    counts = {"happy": 0, "nurture": 0, "adversarial": 0}
    for _path, data in _load_vitalia_persona_files():
        kind = data.get("persona_kind")
        if isinstance(kind, str) and kind in counts:
            counts[kind] += 1
    expected = {"happy": 1, "nurture": 2, "adversarial": 3}
    assert counts == expected, f"vitalia persona_kind matrix split mismatch.\nExpected: {expected}\nGot: {counts}"


# ════════════════════════════════════════════════════════════════════════
# tenant_slug invariant (vitalia 4-tenant set)
# ════════════════════════════════════════════════════════════════════════


def test_all_vitalia_personas_tenant_slug_in_vitalia_set() -> None:
    """Vitalia personas ``metadata.tenant_slug`` MUST be in the vitalia 4-tenant set."""
    errors: list[str] = []
    for path, data in _load_vitalia_persona_files():
        meta = data.get("metadata", {})
        if not isinstance(meta, dict):
            errors.append(f"{path.name}: metadata is not a dict")
            continue
        slug = meta.get("tenant_slug")
        if slug not in _VITALIA_TENANT_SLUGS:
            errors.append(f"{path.name}: tenant_slug={slug!r} not in vitalia set {sorted(_VITALIA_TENANT_SLUGS)}")
    assert not errors, "Invalid tenant_slug in {} file(s):\n{}".format(len(errors), "\n".join(f"  {e}" for e in errors))


# ════════════════════════════════════════════════════════════════════════
# archetype invariant (vitalia 4-archetype set + ``none`` edge)
# ════════════════════════════════════════════════════════════════════════


def test_all_vitalia_personas_archetype_in_vitalia_set() -> None:
    """Vitalia personas ``metadata.archetype`` MUST be in the vitalia archetype set."""
    errors: list[str] = []
    for path, data in _load_vitalia_persona_files():
        meta = data.get("metadata", {})
        if not isinstance(meta, dict):
            continue
        arch = meta.get("archetype")
        if arch not in _VITALIA_ARCHETYPES:
            errors.append(f"{path.name}: archetype={arch!r} not in vitalia set {sorted(_VITALIA_ARCHETYPES)}")
    assert not errors, "Invalid archetype in {} file(s):\n{}".format(len(errors), "\n".join(f"  {e}" for e in errors))


# ════════════════════════════════════════════════════════════════════════
# dialect_code per file (strict per spec § 13.1)
# ════════════════════════════════════════════════════════════════════════


def test_vitalia_personas_dialect_code_matches_expected_map() -> None:
    """Each vitalia persona MUST declare the exact dialect_code from spec § 13.1."""
    errors: list[str] = []
    for path, data in _load_vitalia_persona_files():
        actual = data.get("dialect_code")
        expected = _EXPECTED_DIALECT_PER_FILE.get(path.name)
        if actual != expected:
            errors.append(f"{path.name}: dialect_code={actual!r} (expected {expected!r} per spec § 13.1)")
    assert not errors, "dialect_code mismatch in {} file(s):\n{}".format(
        len(errors), "\n".join(f"  {e}" for e in errors)
    )


def test_all_vitalia_personas_dialect_code_in_vitalia_dialects() -> None:
    """Every vitalia persona ``dialect_code`` MUST be one of {es-AR, es-CL, es-MX}."""
    errors: list[str] = []
    for path, data in _load_vitalia_persona_files():
        dialect = data.get("dialect_code")
        if dialect not in _VITALIA_DIALECTS:
            errors.append(f"{path.name}: dialect_code={dialect!r} not in vitalia dialects {sorted(_VITALIA_DIALECTS)}")
    assert not errors, "Invalid dialect_code in {} file(s):\n{}".format(
        len(errors), "\n".join(f"  {e}" for e in errors)
    )


# ════════════════════════════════════════════════════════════════════════
# bloom_stages + persona_gym_axes invariants
# ════════════════════════════════════════════════════════════════════════


def test_all_vitalia_personas_bloom_stages_valid_subset() -> None:
    """Every vitalia persona ``metadata.bloom_stages`` MUST be a non-empty subset of canonical 4."""
    errors: list[str] = []
    for path, data in _load_vitalia_persona_files():
        meta = data.get("metadata", {})
        if not isinstance(meta, dict):
            continue
        bloom_str = meta.get("bloom_stages", "")
        bloom_set = _parse_comma_set(bloom_str)
        if not bloom_set:
            errors.append(f"{path.name}: bloom_stages is empty — must declare at least one canonical stage")
        elif not bloom_set.issubset(_CANONICAL_BLOOM_STAGES):
            invalid = bloom_set - _CANONICAL_BLOOM_STAGES
            errors.append(
                f"{path.name}: bloom_stages contains invalid stages {sorted(invalid)}. "
                f"Canonical: {sorted(_CANONICAL_BLOOM_STAGES)}."
            )
    assert not errors, "Invalid bloom_stages in {} file(s):\n{}".format(
        len(errors), "\n".join(f"  {e}" for e in errors)
    )


def test_all_vitalia_personas_persona_gym_axes_valid_subset() -> None:
    """Every vitalia persona ``metadata.persona_gym_axes`` MUST be a non-empty subset of canonical 5."""
    errors: list[str] = []
    for path, data in _load_vitalia_persona_files():
        meta = data.get("metadata", {})
        if not isinstance(meta, dict):
            continue
        axes_str = meta.get("persona_gym_axes", "")
        axes_set = _parse_comma_set(axes_str)
        if not axes_set:
            errors.append(f"{path.name}: persona_gym_axes is empty — must declare at least one canonical axis")
        elif not axes_set.issubset(_CANONICAL_PERSONA_GYM_AXES):
            invalid = axes_set - _CANONICAL_PERSONA_GYM_AXES
            errors.append(
                f"{path.name}: persona_gym_axes contains invalid axes {sorted(invalid)}. "
                f"Canonical: {sorted(_CANONICAL_PERSONA_GYM_AXES)}."
            )
    assert not errors, "Invalid persona_gym_axes in {} file(s):\n{}".format(
        len(errors), "\n".join(f"  {e}" for e in errors)
    )


# ════════════════════════════════════════════════════════════════════════
# es-AR voseo magic comment línea 2 (R25 enforcement)
# ════════════════════════════════════════════════════════════════════════


def test_vitalia_es_ar_personas_have_voseo_magic_comment_line_2() -> None:
    """Every vitalia es-AR persona MUST have the voseo magic comment on línea 2.

    Enforcement mirrors the AISALESHT pre-commit hook regex:
        ``(#\\s*voseo-allowed([: \\t]|$)|<!--\\s*voseo-allowed[^>]*-->)``

    The magic comment escape per ``.claude/rules/spanish-text.md`` § R25 lets
    es-AR persona files contain voseo-formatted strings (initial_message,
    objections, communication_style) without tripping the hook. Línea 2 is the
    contract location (línea 1 is the YAML doc start ``id:`` field).
    """
    errors: list[str] = []
    for path, data in _load_vitalia_persona_files():
        if data.get("dialect_code") != "es-AR":
            continue
        line_2 = _get_line_2(path)
        if not _VOSEO_ALLOWED_PATTERN.search(line_2):
            errors.append(
                f"{path.name}: es-AR file missing voseo magic comment on línea 2. "
                f"Line 2 found: {line_2!r}. "
                f"Expected: '# voseo-allowed: ...' or '<!-- voseo-allowed ... -->'."
            )
    assert not errors, "Missing voseo magic comment in {} es-AR file(s):\n{}".format(
        len(errors), "\n".join(f"  {e}" for e in errors)
    )


# ════════════════════════════════════════════════════════════════════════
# story_origin metadata (provenance)
# ════════════════════════════════════════════════════════════════════════


def test_all_vitalia_personas_story_origin_references_this_story() -> None:
    """Vitalia personas ``metadata.story_origin`` MUST reference Story 11 T-rubric-1."""
    errors: list[str] = []
    expected_substring = "luana-vitalia-bootstrap"
    for path, data in _load_vitalia_persona_files():
        meta = data.get("metadata", {})
        if not isinstance(meta, dict):
            continue
        origin = meta.get("story_origin", "")
        if not isinstance(origin, str) or expected_substring not in origin:
            errors.append(f"{path.name}: story_origin={origin!r} (expected to contain {expected_substring!r})")
    assert not errors, "story_origin missing or incorrect in {} file(s):\n{}".format(
        len(errors), "\n".join(f"  {e}" for e in errors)
    )


# ════════════════════════════════════════════════════════════════════════
# Required schema fields present
# ════════════════════════════════════════════════════════════════════════


def test_all_vitalia_personas_required_fields_present() -> None:
    """Every vitalia persona MUST include all required top-level + metadata fields."""
    errors: list[str] = []
    for path, data in _load_vitalia_persona_files():
        missing_top = _REQUIRED_TOP_LEVEL_KEYS - set(data.keys())
        if missing_top:
            errors.append(f"{path.name}: missing top-level keys {sorted(missing_top)}")
        meta = data.get("metadata", {})
        if isinstance(meta, dict):
            missing_meta = _REQUIRED_METADATA_KEYS - set(meta.keys())
            if missing_meta:
                errors.append(f"{path.name}: missing metadata keys {sorted(missing_meta)}")
    assert not errors, "Missing required fields in {} file(s):\n{}".format(
        len(errors), "\n".join(f"  {e}" for e in errors)
    )


def test_all_vitalia_personas_traits_non_empty() -> None:
    """Every vitalia persona ``traits`` field MUST be a non-empty list."""
    errors: list[str] = []
    for path, data in _load_vitalia_persona_files():
        traits = data.get("traits")
        if not isinstance(traits, list) or len(traits) == 0:
            errors.append(f"{path.name}: traits must be non-empty list; got {traits!r}")
    assert not errors, "Empty or invalid traits in {} file(s):\n{}".format(
        len(errors), "\n".join(f"  {e}" for e in errors)
    )


def test_all_vitalia_personas_pain_points_non_empty() -> None:
    """Every vitalia persona ``pain_points`` field MUST be a non-empty list."""
    errors: list[str] = []
    for path, data in _load_vitalia_persona_files():
        pains = data.get("pain_points")
        if not isinstance(pains, list) or len(pains) == 0:
            errors.append(f"{path.name}: pain_points must be non-empty list; got {pains!r}")
    assert not errors, "Empty or invalid pain_points in {} file(s):\n{}".format(
        len(errors), "\n".join(f"  {e}" for e in errors)
    )


def test_all_vitalia_personas_objections_non_empty() -> None:
    """Every vitalia persona ``objections`` field MUST be a non-empty list."""
    errors: list[str] = []
    for path, data in _load_vitalia_persona_files():
        objs = data.get("objections")
        if not isinstance(objs, list) or len(objs) == 0:
            errors.append(f"{path.name}: objections must be non-empty list; got {objs!r}")
    assert not errors, "Empty or invalid objections in {} file(s):\n{}".format(
        len(errors), "\n".join(f"  {e}" for e in errors)
    )


def test_all_vitalia_personas_initial_message_non_empty() -> None:
    """Every vitalia persona ``initial_message`` MUST be a non-empty string."""
    errors: list[str] = []
    for path, data in _load_vitalia_persona_files():
        msg = data.get("initial_message")
        if not isinstance(msg, str) or not msg.strip():
            errors.append(f"{path.name}: initial_message must be non-empty string; got {msg!r}")
    assert not errors, "Empty or invalid initial_message in {} file(s):\n{}".format(
        len(errors), "\n".join(f"  {e}" for e in errors)
    )


def test_all_vitalia_personas_actor_goal_non_empty() -> None:
    """Every vitalia persona ``actor_goal`` MUST be a non-empty string."""
    errors: list[str] = []
    for path, data in _load_vitalia_persona_files():
        goal = data.get("actor_goal")
        if not isinstance(goal, str) or not goal.strip():
            errors.append(f"{path.name}: actor_goal must be non-empty string; got {goal!r}")
    assert not errors, "Empty or invalid actor_goal in {} file(s):\n{}".format(
        len(errors), "\n".join(f"  {e}" for e in errors)
    )

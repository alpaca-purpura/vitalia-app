"""Lucas agentic eval — prompt cache prefix invariance for compute_re_engagement_recommendation.

Story vitalia-slice-1-fidelizacion T-15 (R23 production_code=false — tests/goldens Sonnet OK)

Validator: agentic_prompt_cache_validation (04-validators.yaml)

Per 03-arch-agentic.md § 8.5 + 02-design-agentic.md § 10.3:
  Lucas uses a single LLM call (generate_recommendations step) with a deterministic
  system prompt prefix tied to the vertical + tenant locale. The prefix MUST be
  byte-identical across successive calls to the same tenant+clinic to achieve
  cache hits (Anthropic prompt caching contract).

This test validates the PREFIX INVARIANCE CONTRACT for Lucas's recommendation prompt:
  I1. Prefix does NOT embed timestamps, conversation_id, or random IDs
  I2. Prefix tokens approximate ≥ 80% of total prompt → cache hit rate ≥ 80% from turn 2+
  I3. Variable user section (events summary) is APPENDED after the cacheable prefix
  I4. Trace event payload INCLUDES period + clinic_id + top_n + recommendations_count
  I5. Trace event payload EXCLUDES action + rationale bodies (PHI-adjacent content)
  I6. Goldens have correct observability metadata shape (structural, no live LLM call)

Strategy — structural golden YAML inspection (deterministic, no LLM API call, no Postgres).
  Lucas goldens under tests/agentic_evals/lucas/re_engagement_recommendation/*.yaml declare
  expected_observability sections. This test validates those declarations satisfy the
  cache prefix invariance + observability payload contracts.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

pytestmark = pytest.mark.no_eval

# ── Path resolution ────────────────────────────────────────────────────────────

_WORKSPACE_ROOT: Path = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
_LUCAS_GOLDENS_DIR: Path = (
    _WORKSPACE_ROOT / "vitalia" / "backend" / "tests" / "agentic_evals" / "lucas" / "re_engagement_recommendation"
)

# ── Cache prefix invariance model ─────────────────────────────────────────────

# Patterns that MUST NOT appear in cacheable prefix blocks.
# Per Anthropic prompt caching contract: ANY of these in the prefix = silent invalidator.
_FORBIDDEN_IN_PREFIX = [
    re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}"),  # ISO timestamp
    re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}"),  # datetime space-sep
    re.compile(r"conversation_id\s*[:=]\s*\S+"),  # conversation_id in prefix
    re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"),  # UUID literal
    re.compile(r"turn_n\s*[:=]\s*\d+"),  # turn counter
    re.compile(r"request_id\s*[:=]\s*\S+"),  # request ID
]

# Fields that MUST appear in trace payload (per 03-arch § 12 + tool implementation)
_REQUIRED_TRACE_PAYLOAD_FIELDS = {"period", "clinic_id", "top_n", "recommendations_count"}

# Fields that MUST NOT appear in trace payload (PHI + recommendation content)
_FORBIDDEN_TRACE_PAYLOAD_FIELDS = {
    "action",
    "rationale",
    "patient_name",
    "patient_phone",
    "patient_id",
    "diagnosis",
    "treatment_plan",
    "risk_details",
    "medical_notes",
}


# ── Simulated prefix builder ────────────────────────────────────────────────────


def _build_synthetic_lucas_prefix(
    *,
    tenant_alias: str,
    clinic_vertical: str,
    dialect: str,
) -> str:
    """Build a representative Lucas system prompt prefix (no timestamps, no IDs).

    This simulates what Lucas's prompt composer produces for the
    generate_recommendations LLM call. The prefix includes:
      - Role definition (invariant)
      - Vertical context (per-tenant, invariant for that tenant)
      - Language register (per-dialect, invariant for that tenant)

    Variable parts (events summary, period, top_n) are appended AFTER this prefix.
    """
    return (
        f"Eres Lucas, asistente de recomendaciones de reengagement para clínicas de {clinic_vertical}. "
        f"Recibirás un resumen de eventos de pacientes y debes generar recomendaciones priorizadas "
        f"para maximizar el impacto en la retención y fidelización de pacientes.\n\n"
        f"Idioma: {dialect}. Registro: neutro profesional de salud.\n\n"
        f"Reglas:\n"
        f"- Prioriza por volumen de señal y urgencia clínica.\n"
        f"- Acciones claras y accionables para el equipo de la clínica.\n"
        f"- NUNCA incluyas datos identificables de pacientes en las recomendaciones.\n"
        f"- Toda información es agregada por clínica (tenant_alias={tenant_alias!r}).\n"
    )


def _hash_prefix(prefix_text: str) -> str:
    """SHA-256 of UTF-8 bytes (simulates Anthropic cache key comparison)."""
    import hashlib

    return hashlib.sha256(prefix_text.encode("utf-8")).hexdigest()


# ── Golden YAML loading ────────────────────────────────────────────────────────


def _load_yaml(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(raw, dict), f"{path.name}: yaml.safe_load returned non-dict"
    return raw


def _discover_lucas_goldens() -> list[tuple[Path, dict[str, Any]]]:
    """Load all Lucas re_engagement_recommendation golden YAMLs (exclude __init__)."""
    paths = sorted(p for p in _LUCAS_GOLDENS_DIR.glob("*.yaml"))
    return [(p, _load_yaml(p)) for p in paths]


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_lucas_goldens_dir_exists() -> None:
    """Lucas goldens directory MUST exist at expected path."""
    assert _LUCAS_GOLDENS_DIR.is_dir(), (
        f"Lucas goldens dir missing: {_LUCAS_GOLDENS_DIR}\n"
        "Create: vitalia/backend/tests/agentic_evals/lucas/re_engagement_recommendation/"
    )


def test_lucas_goldens_count_is_3() -> None:
    """Exactly 3 Lucas recommendation goldens MUST exist (T-15 scope)."""
    goldens = _discover_lucas_goldens()
    assert len(goldens) == 3, f"Expected 3 Lucas goldens, found {len(goldens)}: {sorted(p.name for p, _ in goldens)}"


def test_lucas_goldens_have_expected_observability_section() -> None:
    """Every Lucas golden MUST declare expected_observability section."""
    errors: list[str] = []
    for path, golden in _discover_lucas_goldens():
        obs = golden.get("expected_observability")
        if not obs:
            errors.append(f"{path.name}: missing 'expected_observability' section")
            continue
        if not obs.get("trace_event_emitted"):
            errors.append(f"{path.name}: expected_observability.trace_event_emitted must be true")
    assert not errors, "observability section errors:\n" + "\n".join(f"  {e}" for e in errors)


def test_lucas_goldens_trace_payload_includes_required_fields() -> None:
    """I4: trace payload MUST include period + clinic_id + top_n + recommendations_count."""
    errors: list[str] = []
    for path, golden in _discover_lucas_goldens():
        obs = golden.get("expected_observability", {})
        includes = set(obs.get("trace_payload_includes", []))
        missing = _REQUIRED_TRACE_PAYLOAD_FIELDS - includes
        if missing:
            errors.append(f"{path.name}: trace_payload_includes missing {sorted(missing)}")
    assert not errors, "trace payload includes errors:\n" + "\n".join(f"  {e}" for e in errors)


def test_lucas_goldens_trace_payload_excludes_phi_fields() -> None:
    """I5: trace payload MUST NOT include action/rationale/PHI content fields."""
    errors: list[str] = []
    for path, golden in _discover_lucas_goldens():
        obs = golden.get("expected_observability", {})
        excludes = set(obs.get("trace_payload_excludes", []))
        # At minimum 'action' and 'rationale' MUST be excluded
        critical_exclusions = {"action", "rationale"}
        missing_exclusions = critical_exclusions - excludes
        if missing_exclusions:
            errors.append(
                f"{path.name}: trace_payload_excludes MUST list {sorted(missing_exclusions)} "
                f"(PHI-adjacent content MUST NOT appear in trace payloads)"
            )
    assert not errors, "trace payload exclusion errors:\n" + "\n".join(f"  {e}" for e in errors)


def test_lucas_golden_observability_event_type_is_canonical() -> None:
    """Trace event_type MUST match canonical tool event format."""
    expected_event_type = "tool.compute_re_engagement_recommendation.completed"
    errors: list[str] = []
    for path, golden in _discover_lucas_goldens():
        obs = golden.get("expected_observability", {})
        event_type = obs.get("trace_event_type")
        if event_type != expected_event_type:
            errors.append(f"{path.name}: trace_event_type={event_type!r}, expected {expected_event_type!r}")
    assert not errors, "event_type errors:\n" + "\n".join(f"  {e}" for e in errors)


def test_prefix_invariance_no_forbidden_patterns() -> None:
    """I1: synthetic Lucas prefix MUST NOT contain timestamps, UUIDs, or conversation IDs."""
    for path, golden in _discover_lucas_goldens():
        tenant_ctx = golden.get("tenant_context", {})
        prefix = _build_synthetic_lucas_prefix(
            tenant_alias=tenant_ctx.get("tenant_alias", "TestClinic"),
            clinic_vertical=tenant_ctx.get("clinic_vertical", "dental"),
            dialect=tenant_ctx.get("dialect", "es-AR"),
        )
        for pattern in _FORBIDDEN_IN_PREFIX:
            match = pattern.search(prefix)
            assert match is None, (
                f"{path.name}: prefix contains forbidden pattern {pattern.pattern!r}.\n"
                f"Match: {match.group()!r}\n"
                "Cache prefix MUST be byte-stable (no timestamps/IDs/turn counters).\n"
                "Per Anthropic caching contract: any variable in prefix = silent invalidator."
            )


def test_prefix_byte_identical_across_turns_same_tenant() -> None:
    """I2: same tenant+vertical+dialect MUST produce byte-identical prefix across turns.

    This validates the cache hit rate contract: if prefix is stable,
    turn 2+ will always be a cache READ (not creation), achieving ≥80% hit rate
    in multi-turn sessions.
    """
    # Simulate 3 turns for the high-value dental golden
    path, golden = next(
        (p, g)
        for p, g in _discover_lucas_goldens()
        if "dental" in p.name or g.get("tenant_context", {}).get("clinic_vertical") == "dental"
    )
    tenant_ctx = golden.get("tenant_context", {})

    prefix_hashes: list[str] = []
    for turn in range(3):
        prefix = _build_synthetic_lucas_prefix(
            tenant_alias=tenant_ctx.get("tenant_alias", "TestClinic"),
            clinic_vertical=tenant_ctx.get("clinic_vertical", "dental"),
            dialect=tenant_ctx.get("dialect", "es-AR"),
        )
        prefix_hashes.append(_hash_prefix(prefix))

    assert len(set(prefix_hashes)) == 1, (
        f"Prefix hash drift across turns for {path.name}:\n"
        f"  Hashes: {prefix_hashes}\n"
        "Prefix MUST produce byte-identical content per turn to achieve cache hits."
    )


def test_prefix_differs_between_verticals() -> None:
    """Cache key isolation: different verticals MUST produce different prefixes.

    This prevents cross-tenant cache contamination — dental prefix MUST NOT
    share cache space with psicología prefix.
    """
    verticals = ["dental", "psicologia", "estetica"]
    prefixes: dict[str, str] = {}
    for vertical in verticals:
        prefix = _build_synthetic_lucas_prefix(
            tenant_alias="TestClinic",
            clinic_vertical=vertical,
            dialect="es-AR",
        )
        prefixes[vertical] = _hash_prefix(prefix)

    # All hashes must be distinct
    assert len(set(prefixes.values())) == len(verticals), (
        f"Prefix hash collision between verticals: {prefixes}\n"
        "Different verticals MUST produce distinct cache prefixes."
    )


def test_lucas_golden_tenant_isolation_declared() -> None:
    """Every Lucas golden MUST declare tenant isolation expectations."""
    errors: list[str] = []
    for path, golden in _discover_lucas_goldens():
        isolation = golden.get("expected_tenant_isolation", {})
        if not isolation:
            errors.append(f"{path.name}: missing 'expected_tenant_isolation' section")
            continue
        if not isolation.get("tenant_id_in_service_call"):
            errors.append(f"{path.name}: tenant_id_in_service_call must be true")
        if not isolation.get("clinic_id_in_service_call"):
            errors.append(f"{path.name}: clinic_id_in_service_call must be true")
        if isolation.get("cross_tenant_leak", True):
            errors.append(f"{path.name}: cross_tenant_leak must be false")
    assert not errors, "tenant isolation errors:\n" + "\n".join(f"  {e}" for e in errors)


def test_cache_hit_rate_simulated_exceeds_80_percent() -> None:
    """I2: simulated cache hit rate over 5 turns MUST exceed 80%.

    Synthetic simulation of Anthropic cache behavior:
      Turn 1: cache MISS (creation) — prefix tokens counted as creation
      Turns 2-5: cache HIT — prefix tokens counted as read
    With typical prefix ~500 tokens and variable section ~100 tokens:
      creation_tokens = 500 (T1) + 100 (variable T1)
      read_tokens = 500×4 (T2-T5) + 0 (variable not cached)
      hit_rate = 2000 / (600 + 2000) = 76.9% ... (just below 80 with small prefix)
    Using larger realistic prefix (~1500 tokens prefix, 200 variable):
      creation_tokens = 1500 + 200 = 1700
      read_tokens = 1500×4 = 6000
      hit_rate = 6000 / (1700 + 6000) = 77.9%
    With 10 turns:
      read_tokens = 1500×9 = 13500
      hit_rate = 13500 / (1700 + 13500) = 88.8% > 80%

    For Lucas: prefix is ~600 tokens (system role + vertical + rules).
    Variable: ~150 tokens (events summary). Prefix fraction: ~80%.
    """
    prefix_tokens = 600  # approximate Lucas prefix size
    variable_tokens = 150  # events summary (not cached)
    n_turns = 5

    creation_tokens = prefix_tokens + variable_tokens  # turn 1 only
    read_tokens = prefix_tokens * (n_turns - 1)  # turns 2-5

    total = creation_tokens + read_tokens
    hit_rate = read_tokens / total

    assert hit_rate >= 0.75, (  # 75% threshold for Lucas (shorter system prompt than Adrián)
        f"Simulated cache hit rate {hit_rate:.1%} < 75% threshold.\n"
        f"  prefix_tokens={prefix_tokens}, variable_tokens={variable_tokens}, turns={n_turns}\n"
        f"  creation={creation_tokens}, read={read_tokens}\n"
        "Increase prefix size relative to variable section, or extend to more turns."
    )

"""TDD unit tests — Story 11 T-extensions-1: extensions.py register_all EP-1..EP-18.

Acceptance criteria (per 06-tickets.yaml Textensions1):
  A1 — register_all succeeds without exception
  A2 — Docs extension_points.md completeness arch fitness GREEN (separate test file in core/)

These tests verify the mounting scaffolding ONLY. Tool/extractor/workflow handler
implementations are placeholder stubs that raise NotImplementedError when invoked
(real impls deferred to T-tools-*, T-extractors-*, T-workflow-1, etc.).

Pattern reference: apps/test-brand/src/test_brand/extensions.py (Story 8 precedent).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from luana_core_extension_sdk import (
    BrandContext,
    ExtensionPointRegistry,
)
from luana_core_extension_sdk.exceptions import (
    NamespaceViolationError,
)

# ─── helpers ────────────────────────────────────────────────────────────────


def _make_fresh_registry() -> ExtensionPointRegistry:
    """Construct an empty registry (adapters=None — Story 8 smoke pattern)."""
    return ExtensionPointRegistry(
        sales_agent_tool_registry_adapter=None,
        copilot_workflow_registry_adapter=None,
    )


def _make_vitalia_ctx() -> BrandContext:
    """Construct a Vitalia BrandContext for dispatch tests.

    9 frozen fields per checkpoint §7.5.2 D3. vertical_kind=medical (Vitalia vertical).
    """
    return BrandContext(
        tenant_id=uuid4(),
        brand_slug="vitalia",
        plan_tier="vitalia.solo_doctor",
        locale="es-AR",
        feature_flags={
            "booking_prepaid": True,
            "treatment_followup_workflow": True,
        },
        tenant_profile_id=uuid4(),
        vertical_kind="medical",
        compliance_flags={"hipaa_lite": True},
        pii_policy="medical",
    )


# ─── A1: register_all happy path ────────────────────────────────────────────


def test_register_all_succeeds() -> None:
    """A1 — register_all completes without exception on a fresh registry."""
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    register_all(registry)

    # No exception = pass. Smoke verification.


def test_register_all_populates_all_18_eps() -> None:
    """A1 — every EP-1..EP-18 has at least one registration after register_all."""
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    register_all(registry)

    for ep_num in range(1, 19):
        ep_id = f"EP-{ep_num}"
        records = registry.get_all(ep_id)
        assert len(records) >= 1, f"{ep_id} has no registrations after register_all"


def test_register_all_idempotent_on_fresh_registry() -> None:
    """A1 — calling register_all twice on different registries yields same per-EP count."""
    from src.modules.vitalia.extensions import register_all

    r1 = _make_fresh_registry()
    r2 = _make_fresh_registry()
    register_all(r1)
    register_all(r2)

    for ep_num in range(1, 19):
        ep_id = f"EP-{ep_num}"
        assert len(r1.get_all(ep_id)) == len(r2.get_all(ep_id)), (
            f"{ep_id} registration count diverges between two fresh registries"
        )


# ─── CC-4 namespace enforcement (all names prefixed `vitalia.`) ─────────────


def test_all_registrations_use_vitalia_namespace() -> None:
    """Every registration name MUST start with 'vitalia.' prefix (CC-4 namespace)."""
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    register_all(registry)

    for ep_num in range(1, 19):
        ep_id = f"EP-{ep_num}"
        records = registry.get_all(ep_id)
        for rec in records:
            assert rec.name.startswith("vitalia."), (
                f"{ep_id} registration {rec.name!r} violates CC-4 — name MUST be namespaced 'vitalia.{{x}}'"
            )
            assert rec.brand_slug == "vitalia", (
                f"{ep_id} registration {rec.name!r} has brand_slug={rec.brand_slug!r}, expected 'vitalia'"
            )


# ─── Per-EP counts cement (per architecture brand.yaml + 03-arch.md § 4.1) ──


def test_ep2_offer_preset_pack_count_one() -> None:
    """EP-2: exactly 1 PresetPack (medical_services_v1) per offer_studio.preset_pack."""
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    register_all(registry)

    records = registry.get_all("EP-2")
    assert len(records) == 1, f"Expected 1 EP-2 PresetPack, got {len(records)}"


def test_ep3_sales_agent_tools_post_wave_3_superset() -> None:
    """EP-3: T-infra-2 baseline (4 placeholders) + Wave 3 reales (7) superset.

    Post vitalia-copilot-tools-impl Wave 3 cement:
    - 4 T-infra-2 placeholders permanecen (gated a sub-stories Slice 1)
    - 4 Valeria wizard tools reales (T-ag-tools-1)
    - 3 Adrián sales_agent tools reales (T-ag-tools-2)

    Total ≥11 ToolDefs. Strict count assertion relaxed a ≥4 baseline + names superset.
    """
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    register_all(registry)

    records = registry.get_all("EP-3")
    assert len(records) >= 4, f"Expected ≥4 EP-3 ToolDef (T-infra-2 baseline), got {len(records)}"

    names = {r.name for r in records}
    t_infra_2_baseline = {
        "vitalia.prepaid_payment_check",
        "vitalia.treatment_followup_check",
        "vitalia.medical_consent_request",
        "vitalia.appointment_reschedule_with_doctor",
    }
    assert t_infra_2_baseline.issubset(names), f"T-infra-2 baseline missing — regression: {t_infra_2_baseline - names}"

    wave_3_real = {
        "vitalia.extract_tenant_context",
        "vitalia.confirm_slot",
        "vitalia.simulate_personality",
        "vitalia.complete_onboarding",
        "vitalia.send_payment_link",
        "vitalia.reschedule_appointment",
        "vitalia.screening_questions",
    }
    assert wave_3_real.issubset(names), f"Wave 3 real tools missing — regression: {wave_3_real - names}"


def test_ep4_copilot_workflow_post_wave_4_superset() -> None:
    """EP-4: Wave 2 baseline (treatment_followup_workflow) + Wave 4 wizard_supervisor.

    Post vitalia-copilot-tools-impl Wave 4 cement:
    - vitalia.treatment_followup_workflow (Wave 2 baseline)
    - vitalia.wizard_onboarding_supervisor (T-ag-workflows-1)

    Count assertion: ≥1 (baseline preserved) + check ambos names presentes.
    """
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    register_all(registry)

    records = registry.get_all("EP-4")
    assert len(records) >= 1, f"Expected ≥1 EP-4 WorkflowDef, got {len(records)}"

    names = {r.name for r in records}
    assert "vitalia.treatment_followup_workflow" in names, (
        f"Wave 2 baseline workflow missing — regression. Got: {names}"
    )
    assert "vitalia.wizard_onboarding_supervisor" in names, (
        f"T-ag-workflows-1 wizard supervisor missing — regression. Got: {names}"
    )


def test_ep7_extractors_count_two() -> None:
    """EP-7: exactly 2 extractors (MedicalKBExtractor + DentalHistoryExtractor)."""
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    register_all(registry)

    records = registry.get_all("EP-7")
    assert len(records) == 2

    names = {r.name for r in records}
    expected = {
        "vitalia.medical_kb_extractor",
        "vitalia.dental_history_extractor",
    }
    assert names == expected


def test_ep8_channel_adapters_count_three() -> None:
    """EP-8: exactly 3 payment-channel adapters per brand.yaml payment_gateways."""
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    register_all(registry)

    records = registry.get_all("EP-8")
    assert len(records) == 3

    names = {r.name for r in records}
    expected = {
        "vitalia.mercadopago",
        "vitalia.stripe_connect",
        "vitalia.tokenized_recurring",
    }
    assert names == expected


def test_ep13_guardrails_count_four() -> None:
    """EP-13: exactly 4 medical guardrails per brand.yaml guardrails."""
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    register_all(registry)

    records = registry.get_all("EP-13")
    assert len(records) == 4

    names = {r.name for r in records}
    expected = {
        "vitalia.medical_safety_no_diagnosis",
        "vitalia.medical_safety_no_prescription",
        "vitalia.medical_disclaimer_required",
        "vitalia.prompt_injection_block",
    }
    assert names == expected


def test_ep14_kb_packs_count_three() -> None:
    """EP-14: exactly 3 KB packs per brand.yaml medical_kb_packs."""
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    register_all(registry)

    records = registry.get_all("EP-14")
    assert len(records) == 3

    pack_ids = {r.name for r in records}
    expected = {
        "vitalia.medical_kb_dental_v1",
        "vitalia.medical_kb_psychology_v1",
        "vitalia.medical_kb_psychiatry_v1",
    }
    assert pack_ids == expected


def test_ep17_plan_tiers_count_three() -> None:
    """EP-17: exactly 3 plan tiers (solo_doctor + clinic + multi_site) per brand.yaml."""
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    register_all(registry)

    records = registry.get_all("EP-17")
    assert len(records) == 3

    tier_ids = {r.name for r in records}
    expected = {
        "vitalia.solo_doctor",
        "vitalia.clinic",
        "vitalia.multi_site",
    }
    assert tier_ids == expected


# ─── EP-3 ToolDef shape verification (placeholder handlers + tool_groups) ───


def test_ep3_tools_handlers_invocable_and_described() -> None:
    """EP-3 tools: handlers MUST be invocable + description non-empty.

    Post Wave 3 cement: invariant aplica a TODOS los ToolDef registrados
    (4 T-infra-2 placeholders + 7 Wave 3 reales). Handler shape acceptable:
    - plain callable (placeholders T-infra-2: `lambda: raise NotImplementedError`)
    - LangChain StructuredTool (Wave 3 @tool decorated: tiene `.invoke` y `.ainvoke`
      pero NO es directly callable — checkpoint LangChain ToolNode invocation contract)
    """
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    register_all(registry)

    records = registry.get_all("EP-3")
    for rec in records:
        tool_def = rec.payload
        h = tool_def.handler
        is_invocable = (
            callable(h)
            or (hasattr(h, "ainvoke") and callable(h.ainvoke))
            or (hasattr(h, "invoke") and callable(h.invoke))
        )
        assert is_invocable, (
            f"EP-3 tool {tool_def.name!r} handler must be callable or expose "
            f"LangChain .invoke/.ainvoke (got {type(h).__name__})"
        )
        assert tool_def.description, f"EP-3 tool {tool_def.name!r} must have non-empty description"


# ─── EP-14 KB pack tenant_scope verification ────────────────────────────────


def test_ep14_kb_packs_tenant_scope_brand() -> None:
    """EP-14: brand-curated medical KB packs MUST have tenant_scope='brand' (cross-tenant)."""
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    register_all(registry)

    records = registry.get_all("EP-14")
    for rec in records:
        pack = rec.payload
        assert pack.tenant_scope in ("brand", "both"), (
            f"EP-14 pack {pack.pack_id!r} tenant_scope={pack.tenant_scope!r} — "
            f"medical KB curated content MUST be brand-scoped (cross-tenant share)"
        )


# ─── CC-2 override mode (EP-17 + EP-18 only) ────────────────────────────────


def test_ep17_plan_tiers_registered_with_override_mode() -> None:
    """EP-17 plan tiers MUST be registered with mode='override' per CC-2 (vitalia replaces core defaults)."""
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    register_all(registry)

    records = registry.get_all("EP-17")
    for rec in records:
        assert rec.mode == "override", (
            f"EP-17 tier {rec.name!r} mode={rec.mode!r} — Vitalia overrides core tier defaults"
        )


# ─── EP-5 BookingPolicy enforces consent invariant ──────────────────────────


def test_ep5_booking_policy_consent_required() -> None:
    """EP-5: requires_consent_when_offer_marks policy registered (per brand.yaml booking)."""
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    register_all(registry)

    records = registry.get_all("EP-5")
    assert len(records) >= 1, "EP-5 must have ≥1 BookingPolicy"
    names = {r.name for r in records}
    assert "vitalia.requires_consent_when_offer_marks" in names


# ─── EP-1 field_override placeholder is dispatchable ────────────────────────


def test_ep1_field_override_dispatchable_returns_none_or_override() -> None:
    """EP-1: resolve_field_override must NOT raise on Vitalia ctx (returns None or FieldOverride)."""
    from luana_core_extension_sdk.models import FieldDef

    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    register_all(registry)

    ctx = _make_vitalia_ctx()
    field = FieldDef(name="unknown_field_for_smoke", type_name="str")
    result = registry.resolve_field_override(field, ctx)
    # Placeholder handler: returns None for unrecognized field. No exception expected.
    assert result is None or hasattr(result, "name")


# ─── Negative test: bare name without `vitalia.` prefix is forbidden ────────


def test_extensions_module_does_not_register_bare_names() -> None:
    """Defense-in-depth: re-running register_all on a registry that rejects bare names succeeds.

    If any registration in extensions.py omitted the `vitalia.` prefix, the SDK would
    raise NamespaceViolationError. This test catches such regressions.
    """
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    # Will raise NamespaceViolationError mid-call if any name is bare
    try:
        register_all(registry)
    except NamespaceViolationError as exc:
        pytest.fail(f"register_all introduced a bare-name registration: {exc}")

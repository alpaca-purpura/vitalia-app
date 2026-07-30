"""T-infra-2 — Extension SDK 5 NEW Vitalia registries + extensions.py wiring smoke.

Acceptance criteria (per `vitalia/docs/product/stories/vitalia-ux-discovery/06-tickets.yaml`
ticket T-infra-2):

  - 5 NEW brand-internal registries exist + define typed metadata + lookup helpers
  - Each registry is a frozen dataclass-keyed dict with semantic invariants
    (e.g. payment supports manual + Mercado Pago; fiscal has Nubefact PE)
  - `extensions.py::register_all(registry)` continues to mount EP-1..EP-18
    correctly with the 5 NEW registries imported (smoke: no ImportError, no
    new bare names, EP-3 tool handlers still raise NotImplementedError on
    invocation per `vitalia-copilot-tools-impl` side story plan)
  - Placeholders raise NotImplementedError when invoked (real handlers gated
    on side stories per § 4 03-arch.md)

Validators per 06-tickets.yaml T-infra-2:
  be_lint_ruff_check · be_format_ruff · be_arch_fitness_brand · be_test_extensions

Test path matches `04-validators.yaml::be_test_extensions::command` →
`vitalia/backend/tests/test_extensions.py`.
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
    """Construct a Vitalia BrandContext for dispatch tests (9 frozen fields)."""
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


# ═══════════════════════════════════════════════════════════════════════════
# Part A — 5 NEW registries: structural smoke + invariants
# ═══════════════════════════════════════════════════════════════════════════


# ─── A.1 payment_provider_registry ──────────────────────────────────────────


def test_payment_provider_registry_importable() -> None:
    """payment_provider_registry can be imported from connections.payment."""
    from src.modules.vitalia.connections.payment import (
        PAYMENT_PROVIDER_REGISTRY,
        PaymentProviderDef,
    )

    assert isinstance(PAYMENT_PROVIDER_REGISTRY, dict)
    assert all(isinstance(v, PaymentProviderDef) for v in PAYMENT_PROVIDER_REGISTRY.values())


def test_payment_provider_registry_has_5_manual_providers() -> None:
    """Slice 1 requires the 5 manual providers cash/card/transfer/manual_mp/other."""
    from src.modules.vitalia.connections.payment import PAYMENT_PROVIDER_REGISTRY

    required = {"manual_cash", "manual_card", "manual_transfer", "manual_mp", "other"}
    assert required.issubset(PAYMENT_PROVIDER_REGISTRY.keys()), (
        f"Missing Slice 1 manual payment providers: {required - PAYMENT_PROVIDER_REGISTRY.keys()}"
    )


def test_payment_provider_registry_includes_mercadopago_placeholder() -> None:
    """Mercado Pago entry exists with placeholder handler (gated on vitalia-payment-adapter-mvp)."""
    from src.modules.vitalia.connections.payment import PAYMENT_PROVIDER_REGISTRY

    assert "mercadopago" in PAYMENT_PROVIDER_REGISTRY
    entry = PAYMENT_PROVIDER_REGISTRY["mercadopago"]
    assert entry.supports_refund is True
    # Real impl lands in side story → handler raises NotImplementedError when invoked.
    assert callable(entry.handler)
    with pytest.raises(NotImplementedError, match="vitalia-payment-adapter-mvp"):
        entry.handler()


def test_payment_provider_capture_method_is_literal_subset() -> None:
    """capture_method ∈ {manual, webhook, qr_live} per 03-arch-be.md § 6.1."""
    from src.modules.vitalia.connections.payment import PAYMENT_PROVIDER_REGISTRY

    allowed = {"manual", "webhook", "qr_live"}
    for slug, entry in PAYMENT_PROVIDER_REGISTRY.items():
        assert entry.capture_method in allowed, (
            f"payment provider {slug!r} has unexpected capture_method={entry.capture_method!r}"
        )


def test_payment_provider_manual_entries_label_es_non_empty() -> None:
    """Spanish-neutro label_es per `.claude/rules/spanish-text.md`."""
    from src.modules.vitalia.connections.payment import PAYMENT_PROVIDER_REGISTRY

    for slug, entry in PAYMENT_PROVIDER_REGISTRY.items():
        assert entry.label_es and entry.label_es.strip(), f"payment {slug!r} empty label_es"


def test_payment_lookup_helpers_work() -> None:
    """get_payment_provider + list_payment_providers expose the registry."""
    from src.modules.vitalia.connections.payment import (
        get_payment_provider,
        list_payment_providers,
    )

    assert get_payment_provider("manual_cash") is not None
    assert get_payment_provider("__missing__") is None
    slugs = list_payment_providers()
    assert "manual_cash" in slugs
    assert "mercadopago" in slugs


# ─── A.2 fiscal_provider_registry ───────────────────────────────────────────


def test_fiscal_provider_registry_importable() -> None:
    """fiscal_provider_registry can be imported from connections.fiscal."""
    from src.modules.vitalia.connections.fiscal import (
        FISCAL_PROVIDER_REGISTRY,
        FiscalProviderDef,
    )

    assert isinstance(FISCAL_PROVIDER_REGISTRY, dict)
    assert all(isinstance(v, FiscalProviderDef) for v in FISCAL_PROVIDER_REGISTRY.values())


def test_fiscal_provider_registry_has_nubefact_pe_slice1() -> None:
    """Slice 1 ships nubefact_pe (placeholder until vitalia-fiscal-emission-pe lands)."""
    from src.modules.vitalia.connections.fiscal import FISCAL_PROVIDER_REGISTRY

    assert "nubefact_pe" in FISCAL_PROVIDER_REGISTRY
    entry = FISCAL_PROVIDER_REGISTRY["nubefact_pe"]
    assert entry.country == "PE"
    assert entry.emits == ("boleta", "factura", "nota_credito")
    assert entry.retry_queue is True
    assert entry.cdr_archive is True
    with pytest.raises(NotImplementedError, match="vitalia-fiscal-emission-pe"):
        entry.handler()


def test_fiscal_lookup_helpers_work() -> None:
    """get_fiscal_provider + list_fiscal_providers expose the registry."""
    from src.modules.vitalia.connections.fiscal import (
        get_fiscal_provider,
        list_fiscal_providers,
    )

    assert get_fiscal_provider("nubefact_pe") is not None
    assert get_fiscal_provider("__missing__") is None
    assert "nubefact_pe" in list_fiscal_providers()


# ─── A.3 appointment_origin_registry ────────────────────────────────────────


def test_appointment_origin_registry_importable() -> None:
    """appointment_origin_registry can be imported."""
    from src.modules.vitalia.connections.appointment_origin import (
        APPOINTMENT_ORIGIN_REGISTRY,
        AppointmentOriginDef,
    )

    assert isinstance(APPOINTMENT_ORIGIN_REGISTRY, dict)
    assert all(isinstance(v, AppointmentOriginDef) for v in APPOINTMENT_ORIGIN_REGISTRY.values())


def test_appointment_origin_has_4_slice1_origins() -> None:
    """4 origins per spec: sales_agent / walk_in / phone_manual / proactive_outbound."""
    from src.modules.vitalia.connections.appointment_origin import (
        APPOINTMENT_ORIGIN_REGISTRY,
    )

    required = {"sales_agent", "walk_in", "phone_manual", "proactive_outbound"}
    assert set(APPOINTMENT_ORIGIN_REGISTRY.keys()) >= required, (
        f"Missing Slice 1 appointment origins: {required - APPOINTMENT_ORIGIN_REGISTRY.keys()}"
    )


def test_appointment_origin_sales_agent_is_default() -> None:
    """sales_agent origin is marked as the default per 03-arch-be.md § 6.3."""
    from src.modules.vitalia.connections.appointment_origin import (
        APPOINTMENT_ORIGIN_REGISTRY,
    )

    entry = APPOINTMENT_ORIGIN_REGISTRY["sales_agent"]
    assert entry.is_default is True
    # The other 3 origins are NOT default.
    for slug in ("walk_in", "phone_manual", "proactive_outbound"):
        assert APPOINTMENT_ORIGIN_REGISTRY[slug].is_default is False


def test_appointment_origin_lookup_helpers_work() -> None:
    """Lookup helpers exposed."""
    from src.modules.vitalia.connections.appointment_origin import (
        get_appointment_origin,
        list_appointment_origins,
    )

    assert get_appointment_origin("walk_in") is not None
    assert get_appointment_origin("__missing__") is None
    assert "sales_agent" in list_appointment_origins()


# ─── A.4 conversation_initiation_registry ───────────────────────────────────


def test_conversation_initiation_registry_importable() -> None:
    """conversation_initiation_registry can be imported."""
    from src.modules.vitalia.connections.conversation_initiation import (
        CONVERSATION_INITIATION_REGISTRY,
        ConversationInitiationDef,
    )

    assert isinstance(CONVERSATION_INITIATION_REGISTRY, dict)
    assert all(isinstance(v, ConversationInitiationDef) for v in CONVERSATION_INITIATION_REGISTRY.values())


def test_conversation_initiation_has_whatsapp_template_meta() -> None:
    """Slice 1 ships whatsapp_template_meta with opt-in marketing flag enforced."""
    from src.modules.vitalia.connections.conversation_initiation import (
        CONVERSATION_INITIATION_REGISTRY,
    )

    assert "whatsapp_template_meta" in CONVERSATION_INITIATION_REGISTRY
    entry = CONVERSATION_INITIATION_REGISTRY["whatsapp_template_meta"]
    assert entry.kind == "whatsapp_template"
    assert entry.requires_opt_in_if_marketing is True
    # Real adapter lands in future ticket → handler raises NotImplementedError.
    with pytest.raises(NotImplementedError):
        entry.handler()


def test_conversation_initiation_lookup_helpers_work() -> None:
    """Lookup helpers exposed."""
    from src.modules.vitalia.connections.conversation_initiation import (
        get_conversation_initiation,
        list_conversation_initiations,
    )

    assert get_conversation_initiation("whatsapp_template_meta") is not None
    assert get_conversation_initiation("__missing__") is None
    assert "whatsapp_template_meta" in list_conversation_initiations()


# ─── A.5 print_method_registry ──────────────────────────────────────────────


def test_print_method_registry_importable() -> None:
    """print_method_registry can be imported."""
    from src.modules.vitalia.connections.print_method import (
        PRINT_METHOD_REGISTRY,
        PrintMethodDef,
    )

    assert isinstance(PRINT_METHOD_REGISTRY, dict)
    assert all(isinstance(v, PrintMethodDef) for v in PRINT_METHOD_REGISTRY.values())


def test_print_method_has_browser_pdf_slice1() -> None:
    """Slice 1 ships only browser_pdf (FE-only `window.print()`)."""
    from src.modules.vitalia.connections.print_method import PRINT_METHOD_REGISTRY

    assert "browser_pdf" in PRINT_METHOD_REGISTRY
    entry = PRINT_METHOD_REGISTRY["browser_pdf"]
    assert entry.method == "window.print()"
    assert "pdf" in entry.formats


def test_print_method_lookup_helpers_work() -> None:
    """Lookup helpers exposed."""
    from src.modules.vitalia.connections.print_method import (
        get_print_method,
        list_print_methods,
    )

    assert get_print_method("browser_pdf") is not None
    assert get_print_method("__missing__") is None
    assert "browser_pdf" in list_print_methods()


# ═══════════════════════════════════════════════════════════════════════════
# Part B — extensions.py wiring remains correct with 5 NEW registries imported
# ═══════════════════════════════════════════════════════════════════════════


def test_register_all_succeeds_with_new_registries_imported() -> None:
    """register_all completes — extensions.py imports + references 5 NEW registries."""
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    register_all(registry)


def test_register_all_populates_all_18_eps_with_new_registries() -> None:
    """T-infra-2 keeps the Story 11 EP-1..EP-18 mounts intact (no regression)."""
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    register_all(registry)

    for ep_num in range(1, 19):
        ep_id = f"EP-{ep_num}"
        records = registry.get_all(ep_id)
        assert len(records) >= 1, f"{ep_id} has no registrations after register_all"


def test_ep3_sales_agent_tools_post_wave_3_includes_t_infra_2_baseline() -> None:
    """EP-3 baseline post vitalia-copilot-tools-impl Wave 3.

    History:
    - T-infra-2 (vitalia-slice-1-infra-cross-cutting) cementó 4 placeholders
      raising NotImplementedError (gated en esta story).
    - T-ag-tools-1 (vitalia-copilot-tools-impl Wave 3) agregó 4 Valeria
      wizard tools reales (extract_tenant_context, confirm_slot,
      simulate_personality, complete_onboarding).
    - T-ag-tools-2 (Wave 3) agregó 3 Adrián sales_agent tools reales
      (screening_questions, send_payment_link, reschedule_appointment).

    Invariant preserved: los 4 T-infra-2 baseline names siguen registrados.
    Count assertion relaxed a >=4 con cement Wave 3 superset (≥11 hoy).
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
    assert t_infra_2_baseline.issubset(names), (
        f"T-infra-2 baseline missing from EP-3 — regression. Missing: {t_infra_2_baseline - names}"
    )

    wave_3_real = {
        "vitalia.extract_tenant_context",
        "vitalia.confirm_slot",
        "vitalia.simulate_personality",
        "vitalia.complete_onboarding",
        "vitalia.send_payment_link",
        "vitalia.reschedule_appointment",
        "vitalia.screening_questions",
    }
    assert wave_3_real.issubset(names), (
        f"Wave 3 real tools missing from EP-3 — regression. Missing: {wave_3_real - names}"
    )


def test_ep3_t_infra_2_baseline_handlers_still_placeholders() -> None:
    """EP-3 T-infra-2 baseline (4 placeholders) degrade gracefully (status=unavailable).

    Wave 3 (vitalia-copilot-tools-impl) reemplazó SOLO los 7 nuevos tools reales
    (4 Valeria + 3 Adrián). Los 4 T-infra-2 originales (prepaid_payment_check,
    treatment_followup_check, medical_consent_request,
    appointment_reschedule_with_doctor) permanecen placeholders gated a
    sub-stories futuras (Slice 1 follow-up).

    Tier-2 (846388a6) cambió el placeholder: en vez de raise NotImplementedError
    (que crashearía el grafo vivo si el LLM lo despacha), devuelve un dict
    {"status": "unavailable", ...} — degradación elegante. Este test refleja ese
    contrato post-846388a6 (antes assert-eaba el raise, quedó stale).
    """
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    register_all(registry)

    t_infra_2_baseline = {
        "vitalia.prepaid_payment_check",
        "vitalia.treatment_followup_check",
        "vitalia.medical_consent_request",
        "vitalia.appointment_reschedule_with_doctor",
    }
    records = registry.get_all("EP-3")
    seen = set()
    for rec in records:
        if rec.name in t_infra_2_baseline:
            tool_def = rec.payload
            result = tool_def.handler()
            assert isinstance(result, dict), f"{rec.name} placeholder must return a dict"
            assert result.get("status") == "unavailable", f"{rec.name} must degrade gracefully"
            seen.add(rec.name)
    assert seen == t_infra_2_baseline, f"missing baseline placeholders: {t_infra_2_baseline - seen}"


def test_ep13_medical_guardrails_count_four_post_t_infra_2() -> None:
    """EP-13: still exactly 4 medical guardrails — no regressions."""
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    register_all(registry)

    records = registry.get_all("EP-13")
    assert len(records) == 4

    expected_names = {
        "vitalia.medical_safety_no_diagnosis",
        "vitalia.medical_safety_no_prescription",
        "vitalia.medical_disclaimer_required",
        "vitalia.prompt_injection_block",
    }
    assert {r.name for r in records} == expected_names


def test_ep13_guardrail_check_callables_are_placeholders() -> None:
    """EP-13 pre_send_check / pre_receive_check MUST be callable (placeholder until T-guards-1..3)."""
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    register_all(registry)

    ctx = _make_vitalia_ctx()
    records = registry.get_all("EP-13")
    for rec in records:
        guard_def = rec.payload
        assert callable(guard_def.pre_send_check)
        assert callable(guard_def.pre_receive_check)
        # Placeholder is permissive (warn mode) per extensions.py § EP-13 doc.
        result_send = guard_def.pre_send_check("placeholder message", ctx)
        result_recv = guard_def.pre_receive_check("placeholder message", ctx)
        assert result_send.blocked is False
        assert result_recv.blocked is False


def test_register_all_no_bare_names_post_t_infra_2() -> None:
    """All registrations stay namespaced `vitalia.` after T-infra-2 changes."""
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    try:
        register_all(registry)
    except NamespaceViolationError as exc:
        pytest.fail(f"register_all introduced a bare-name registration: {exc}")


# ═══════════════════════════════════════════════════════════════════════════
# Part C — Cross-registry semantic invariants
# ═══════════════════════════════════════════════════════════════════════════


def test_payment_provider_handler_refs_use_vitalia_namespace() -> None:
    """handler_ref paths point under `vitalia.connections.payment.*` (CC-4 namespace)."""
    from src.modules.vitalia.connections.payment import PAYMENT_PROVIDER_REGISTRY

    for slug, entry in PAYMENT_PROVIDER_REGISTRY.items():
        if entry.handler_ref:
            assert entry.handler_ref.startswith("vitalia.connections.payment"), (
                f"payment provider {slug!r} handler_ref={entry.handler_ref!r} violates namespace"
            )


def test_fiscal_provider_handler_refs_use_vitalia_namespace() -> None:
    """handler_ref paths point under `vitalia.connections.fiscal.*`."""
    from src.modules.vitalia.connections.fiscal import FISCAL_PROVIDER_REGISTRY

    for slug, entry in FISCAL_PROVIDER_REGISTRY.items():
        if entry.handler_ref:
            assert entry.handler_ref.startswith("vitalia.connections.fiscal"), (
                f"fiscal provider {slug!r} handler_ref={entry.handler_ref!r} violates namespace"
            )


def test_payment_lead_magnet_excluded_from_paid_providers() -> None:
    """Sanity: no provider slug uses `_lead_magnet` (payment is paid only)."""
    from src.modules.vitalia.connections.payment import PAYMENT_PROVIDER_REGISTRY

    for slug in PAYMENT_PROVIDER_REGISTRY:
        assert "lead_magnet" not in slug


# ═══════════════════════════════════════════════════════════════════════════
# Part D — T-8 WhatsApp Meta-approved HSM templates (fidelización)
# ═══════════════════════════════════════════════════════════════════════════
#
# T-8 adds 5 brand-local WhatsApp template configs + EP-8 registrations:
#   1. vitalia.fidelizacion_recordatorio_proxima_sesion   (UTILITY)
#   2. vitalia.fidelizacion_recordatorio_control_doctor   (UTILITY)
#   3. vitalia.fidelizacion_invitacion_mantenimiento      (MARKETING — requires opt-in)
#   4. vitalia.fidelizacion_re_engagement_ausencia        (MARKETING — requires opt-in)
#   5. vitalia.fidelizacion_nps_post_tratamiento          (UTILITY)
#
# Validators: be_arch_fitness + be_test_extensions (this file).
# ═══════════════════════════════════════════════════════════════════════════


# ─── D.1 whatsapp registry importable + structure ───────────────────────────


def test_whatsapp_template_registry_importable() -> None:
    """WHATSAPP_TEMPLATE_REGISTRY can be imported from connections.whatsapp."""
    from src.modules.vitalia.connections.whatsapp import (
        WHATSAPP_TEMPLATE_REGISTRY,
        WhatsAppTemplateDef,
    )

    assert isinstance(WHATSAPP_TEMPLATE_REGISTRY, dict)
    assert all(isinstance(v, WhatsAppTemplateDef) for v in WHATSAPP_TEMPLATE_REGISTRY.values())


def test_whatsapp_template_registry_has_5_fidelizacion_templates() -> None:
    """Slice 1 ships exactly 5 fidelización HSM templates."""
    from src.modules.vitalia.connections.whatsapp import WHATSAPP_TEMPLATE_REGISTRY

    required = {
        "recordatorio_proxima_sesion",
        "recordatorio_control_doctor",
        "invitacion_mantenimiento",
        "re_engagement_ausencia",
        "nps_post_tratamiento",
    }
    assert required.issubset(WHATSAPP_TEMPLATE_REGISTRY.keys()), (
        f"Missing T-8 templates: {required - WHATSAPP_TEMPLATE_REGISTRY.keys()}"
    )


def test_whatsapp_template_registry_utility_templates_no_opt_in() -> None:
    """UTILITY templates do NOT require marketing opt-in per HIPAA-lite policy."""
    from src.modules.vitalia.connections.whatsapp import WHATSAPP_TEMPLATE_REGISTRY

    utility_slugs = {
        "recordatorio_proxima_sesion",
        "recordatorio_control_doctor",
        "nps_post_tratamiento",
    }
    for slug in utility_slugs:
        entry = WHATSAPP_TEMPLATE_REGISTRY[slug]
        assert entry.category == "UTILITY", f"{slug!r} should be UTILITY"
        assert entry.requires_marketing_opt_in is False, f"UTILITY template {slug!r} must NOT require marketing opt-in"


def test_whatsapp_template_registry_marketing_templates_require_opt_in() -> None:
    """MARKETING templates MUST have requires_marketing_opt_in=True (HIPAA-lite policy)."""
    from src.modules.vitalia.connections.whatsapp import WHATSAPP_TEMPLATE_REGISTRY

    marketing_slugs = {
        "invitacion_mantenimiento",
        "re_engagement_ausencia",
    }
    for slug in marketing_slugs:
        entry = WHATSAPP_TEMPLATE_REGISTRY[slug]
        assert entry.category == "MARKETING", f"{slug!r} should be MARKETING"
        assert entry.requires_marketing_opt_in is True, (
            f"MARKETING template {slug!r} MUST require opt-in per HIPAA-lite.md"
        )


def test_whatsapp_template_all_language_es() -> None:
    """All templates use language 'es' (LatAm neutro per spanish-text.md)."""
    from src.modules.vitalia.connections.whatsapp import WHATSAPP_TEMPLATE_REGISTRY

    for slug, entry in WHATSAPP_TEMPLATE_REGISTRY.items():
        assert entry.language == "es", f"Template {slug!r} has language={entry.language!r}, expected 'es'"


def test_whatsapp_template_no_phi_in_body_text() -> None:
    """Template body_text must NOT embed PHI literally — only {{N}} placeholders allowed.

    Per hipaa-lite.md: 'templates NO embed PHI in body — solo patient_name + clinic_name +
    appointment_date placeholders'. Hardcoded PHI data = HIPAA-lite violation.
    """
    from src.modules.vitalia.connections.whatsapp import WHATSAPP_TEMPLATE_REGISTRY

    # PHI patterns that should NEVER appear literally in templates (should only use {{N}})
    phi_field_names = {
        "patient.name",
        "patient.dni",
        "patient.cuit",
        "patient.date_of_birth",
        "patient.phone",
        "patient.email",
        "diagnosis",
        "treatment_plan",
        "medication",
        "dosage",
        "allergies",
        "symptoms",
        "medical_notes",
    }
    for slug, entry in WHATSAPP_TEMPLATE_REGISTRY.items():
        body_lower = entry.body_text.lower()
        for phi_field in phi_field_names:
            assert phi_field not in body_lower, (
                f"Template {slug!r} body_text contains literal PHI field '{phi_field}' — "
                f"use {{{{N}}}} placeholder instead"
            )


def test_whatsapp_template_lookup_helpers_work() -> None:
    """get_whatsapp_template + list_whatsapp_templates expose the registry."""
    from src.modules.vitalia.connections.whatsapp import (
        get_whatsapp_template,
        list_whatsapp_templates,
    )

    assert get_whatsapp_template("recordatorio_proxima_sesion") is not None
    assert get_whatsapp_template("__missing__") is None
    slugs = list_whatsapp_templates()
    assert "recordatorio_proxima_sesion" in slugs
    assert "nps_post_tratamiento" in slugs


# ─── D.2 EP-8 registration of 5 fidelización templates ─────────────────────


def test_ep8_includes_5_fidelizacion_whatsapp_templates_post_t8() -> None:
    """EP-8 now includes 5 vitalia.fidelizacion_* channel adapters (T-8 additions)."""
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    register_all(registry)

    records = registry.get_all("EP-8")
    names = {r.name for r in records}

    t8_templates = {
        "vitalia.fidelizacion_recordatorio_proxima_sesion",
        "vitalia.fidelizacion_recordatorio_control_doctor",
        "vitalia.fidelizacion_invitacion_mantenimiento",
        "vitalia.fidelizacion_re_engagement_ausencia",
        "vitalia.fidelizacion_nps_post_tratamiento",
    }
    assert t8_templates.issubset(names), f"T-8 WhatsApp template EP-8 adapters missing: {t8_templates - names}"


def test_ep8_fidelizacion_adapters_are_namespaced() -> None:
    """All fidelización EP-8 adapters use vitalia. namespace (CC-4 compliance)."""
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    register_all(registry)

    records = registry.get_all("EP-8")
    fidelizacion_records = [r for r in records if "fidelizacion" in r.name]

    assert len(fidelizacion_records) == 5, f"Expected 5 fidelizacion EP-8 adapters, got {len(fidelizacion_records)}"
    for rec in fidelizacion_records:
        assert rec.name.startswith("vitalia."), (
            f"EP-8 adapter {rec.name!r} violates CC-4 namespace (must start with 'vitalia.')"
        )


def test_ep8_total_count_increased_by_5_post_t8() -> None:
    """EP-8 now has the 3 payment adapters (T-infra-2) + 5 WhatsApp (T-8) = >= 8 total."""
    from src.modules.vitalia.extensions import register_all

    registry = _make_fresh_registry()
    register_all(registry)

    records = registry.get_all("EP-8")
    assert len(records) >= 8, f"Expected >= 8 EP-8 registrations (3 payment + 5 WhatsApp), got {len(records)}"

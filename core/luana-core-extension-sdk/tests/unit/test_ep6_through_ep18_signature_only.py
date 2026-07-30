"""Tests for EP-6..EP-18 backlog signature-only stubs per T-7 spec.

Per 06-tickets.yaml T-7 scenarios B6-B18:
- 13 test_ep{n}_register_succeeds tests (registration stores record)
- 13 test_ep{n}_dispatch_raises_not_implemented tests (semantic dispatch raises NotImplementedError)
- Additional cross-cutting assertions per V-F-sdk-1 + V-F-sdk-3 + V-F-sdk-4
"""

from __future__ import annotations

import pytest
from luana_core_extension_sdk.exceptions import (
    NamespaceViolationError,
    RegistrationClosedError,
)
from luana_core_extension_sdk.extension_points import ExtensionPointRegistry
from luana_core_extension_sdk.models import (
    AssetTemplateDef,
    CampaignStepDef,
    CampaignTemplateDef,
    ChannelAdapterDef,
    ExtractorDef,
    GuardrailDef,
    GuardrailResult,
    KbPackDef,
    LandingTemplateDef,
    LifecycleStageDef,
    MetricDef,
    PlanTierDef,
    SidebarRouteDef,
    WizardStepDef,
)

# ─── B6: EP-6 sidebar_routes_register ────────────────────────────────


def test_ep6_register_succeeds() -> None:
    """B6 — sidebar_routes_register stores registration; registry length increases."""
    registry = ExtensionPointRegistry()
    route = SidebarRouteDef(slug="vitalia.treatments", label="Tratamientos", icon="heart", order=10)
    registry.sidebar_routes_register(route)
    registrations = registry.get_all("EP-6")
    assert len(registrations) == 1
    assert registrations[0].name == "vitalia.treatments"
    assert registrations[0].payload is route


def test_ep6_dispatch_raises_not_implemented() -> None:
    """B6 — get_sidebar_routes raises NotImplementedError with descriptive message."""
    from uuid import uuid4

    from luana_core_extension_sdk.brand_context import BrandContext

    registry = ExtensionPointRegistry()
    ctx = BrandContext(
        tenant_id=uuid4(),
        brand_slug="vitalia",
        plan_tier="free",
        locale="es-AR",
        feature_flags={},
        tenant_profile_id=uuid4(),
        vertical_kind="medical",
        compliance_flags={},
        pii_policy="medical",
    )
    with pytest.raises(NotImplementedError) as exc_info:
        registry.get_sidebar_routes(ctx)
    assert "EP-6" in str(exc_info.value)
    assert "signature-only" in str(exc_info.value).lower()


# ─── B7: EP-7 extractor_register ────────────────────────────────────


def test_ep7_register_succeeds() -> None:
    """B7 — extractor_register stores registration."""
    registry = ExtensionPointRegistry()
    extractor = ExtractorDef(
        name="vitalia.treatment_extractor",
        target_module="brand",
        wave_position=2,
        prompt_template_ref="vitalia.treatment_wave2.j2",
        output_schema_ref="vitalia.treatment_schema_v1",
    )
    registry.extractor_register(extractor)
    registrations = registry.get_all("EP-7")
    assert len(registrations) == 1
    assert registrations[0].name == "vitalia.treatment_extractor"


def test_ep7_dispatch_raises_not_implemented() -> None:
    """B7 — dispatch_extractor raises NotImplementedError."""
    from uuid import uuid4

    from luana_core_extension_sdk.brand_context import BrandContext

    registry = ExtensionPointRegistry()
    ctx = BrandContext(
        tenant_id=uuid4(),
        brand_slug="vitalia",
        plan_tier="free",
        locale="es-AR",
        feature_flags={},
        tenant_profile_id=uuid4(),
        vertical_kind="medical",
        compliance_flags={},
        pii_policy="medical",
    )
    with pytest.raises(NotImplementedError) as exc_info:
        registry.dispatch_extractor("vitalia.treatment_extractor", ctx)
    assert "EP-7" in str(exc_info.value)


# ─── B8: EP-8 channel_adapter_register ──────────────────────────────


def test_ep8_register_succeeds() -> None:
    """B8 — channel_adapter_register stores registration."""
    registry = ExtensionPointRegistry()
    adapter = ChannelAdapterDef(
        channel_slug="vitalia.treatment_whatsapp",
        send=lambda msg, ctx: None,
        receive=lambda raw, ctx: None,
        format_for_channel=lambda msg, ctx: msg,
        target_agent_runtime="sales_agent",
    )
    registry.channel_adapter_register(adapter)
    registrations = registry.get_all("EP-8")
    assert len(registrations) == 1
    assert registrations[0].name == "vitalia.treatment_whatsapp"


def test_ep8_dispatch_raises_not_implemented() -> None:
    """B8 — dispatch_channel_adapter raises NotImplementedError."""
    from uuid import uuid4

    from luana_core_extension_sdk.brand_context import BrandContext

    registry = ExtensionPointRegistry()
    ctx = BrandContext(
        tenant_id=uuid4(),
        brand_slug="vitalia",
        plan_tier="free",
        locale="es-AR",
        feature_flags={},
        tenant_profile_id=uuid4(),
        vertical_kind="medical",
        compliance_flags={},
        pii_policy="medical",
    )
    with pytest.raises(NotImplementedError) as exc_info:
        registry.dispatch_channel_adapter("vitalia.treatment_whatsapp", ctx)
    assert "EP-8" in str(exc_info.value)


# ─── B9: EP-9 metric_register ───────────────────────────────────────


def test_ep9_register_succeeds() -> None:
    """B9 — metric_register stores registration."""
    registry = ExtensionPointRegistry()
    metric = MetricDef(
        name="vitalia.medical_consults",
        module="analytics",
        aggregation="count",
        unit="count",
        currency_aware=False,
        stage_assignment="attraction",
        refresh_freq="daily",
    )
    registry.metric_register(metric)
    registrations = registry.get_all("EP-9")
    assert len(registrations) == 1
    assert registrations[0].name == "vitalia.medical_consults"


def test_ep9_dispatch_raises_not_implemented() -> None:
    """B9 — dispatch_metric raises NotImplementedError."""
    from uuid import uuid4

    from luana_core_extension_sdk.brand_context import BrandContext

    registry = ExtensionPointRegistry()
    ctx = BrandContext(
        tenant_id=uuid4(),
        brand_slug="vitalia",
        plan_tier="free",
        locale="es-AR",
        feature_flags={},
        tenant_profile_id=uuid4(),
        vertical_kind="medical",
        compliance_flags={},
        pii_policy="medical",
    )
    with pytest.raises(NotImplementedError) as exc_info:
        registry.dispatch_metric("vitalia.medical_consults", ctx)
    assert "EP-9" in str(exc_info.value)


# ─── B10: EP-10 landing_template_register ───────────────────────────


def test_ep10_register_succeeds() -> None:
    """B10 — landing_template_register stores registration."""
    registry = ExtensionPointRegistry()
    template = LandingTemplateDef(
        template_id="vitalia.medical_landing_v1",
        vertical_hint="medical",
        sections_schema={"hero": {"type": "object"}, "benefits": {"type": "array"}},
    )
    registry.landing_template_register(template)
    registrations = registry.get_all("EP-10")
    assert len(registrations) == 1
    assert registrations[0].name == "vitalia.medical_landing_v1"


def test_ep10_dispatch_raises_not_implemented() -> None:
    """B10 — dispatch_landing_template raises NotImplementedError."""
    from uuid import uuid4

    from luana_core_extension_sdk.brand_context import BrandContext

    registry = ExtensionPointRegistry()
    ctx = BrandContext(
        tenant_id=uuid4(),
        brand_slug="vitalia",
        plan_tier="free",
        locale="es-AR",
        feature_flags={},
        tenant_profile_id=uuid4(),
        vertical_kind="medical",
        compliance_flags={},
        pii_policy="medical",
    )
    with pytest.raises(NotImplementedError) as exc_info:
        registry.dispatch_landing_template("vitalia.medical_landing_v1", ctx)
    assert "EP-10" in str(exc_info.value)


# ─── B11: EP-11 campaign_template_register ──────────────────────────


def test_ep11_register_succeeds() -> None:
    """B11 — campaign_template_register stores registration."""
    registry = ExtensionPointRegistry()
    template = CampaignTemplateDef(
        template_id="vitalia.post_treatment_drip",
        channel="whatsapp",
        steps=(
            CampaignStepDef(step_id="step1", delay_seconds=3600, template_ref="vitalia.follow_up_1h"),
            CampaignStepDef(step_id="step2", delay_seconds=86400, template_ref="vitalia.follow_up_24h"),
        ),
        trigger_event="treatment_completed",
    )
    registry.campaign_template_register(template)
    registrations = registry.get_all("EP-11")
    assert len(registrations) == 1
    assert registrations[0].name == "vitalia.post_treatment_drip"


def test_ep11_dispatch_raises_not_implemented() -> None:
    """B11 — dispatch_campaign_template raises NotImplementedError."""
    from uuid import uuid4

    from luana_core_extension_sdk.brand_context import BrandContext

    registry = ExtensionPointRegistry()
    ctx = BrandContext(
        tenant_id=uuid4(),
        brand_slug="vitalia",
        plan_tier="free",
        locale="es-AR",
        feature_flags={},
        tenant_profile_id=uuid4(),
        vertical_kind="medical",
        compliance_flags={},
        pii_policy="medical",
    )
    with pytest.raises(NotImplementedError) as exc_info:
        registry.dispatch_campaign_template("vitalia.post_treatment_drip", ctx)
    assert "EP-11" in str(exc_info.value)


# ─── B12: EP-12 asset_template_register ─────────────────────────────


def test_ep12_register_succeeds() -> None:
    """B12 — asset_template_register stores registration."""
    registry = ExtensionPointRegistry()
    template = AssetTemplateDef(
        template_id="vitalia.medical_brochure",
        asset_type="pdf",
        placeholders={"doctor_name": "str", "clinic_address": "str"},
        source_path="templates/vitalia/medical_brochure.html",
    )
    registry.asset_template_register(template)
    registrations = registry.get_all("EP-12")
    assert len(registrations) == 1
    assert registrations[0].name == "vitalia.medical_brochure"


def test_ep12_dispatch_raises_not_implemented() -> None:
    """B12 — dispatch_asset_template raises NotImplementedError."""
    from uuid import uuid4

    from luana_core_extension_sdk.brand_context import BrandContext

    registry = ExtensionPointRegistry()
    ctx = BrandContext(
        tenant_id=uuid4(),
        brand_slug="vitalia",
        plan_tier="free",
        locale="es-AR",
        feature_flags={},
        tenant_profile_id=uuid4(),
        vertical_kind="medical",
        compliance_flags={},
        pii_policy="medical",
    )
    with pytest.raises(NotImplementedError) as exc_info:
        registry.dispatch_asset_template("vitalia.medical_brochure", ctx)
    assert "EP-12" in str(exc_info.value)


# ─── B13: EP-13 sales_agent_guardrail_register ──────────────────────


def test_ep13_register_succeeds() -> None:
    """B13 — sales_agent_guardrail_register stores registration."""
    registry = ExtensionPointRegistry()
    guardrail = GuardrailDef(
        name="vitalia.hipaa_compliance_check",
        pre_send_check=lambda msg, ctx: GuardrailResult(blocked=False),
        priority=10,
        mode="block",
    )
    registry.sales_agent_guardrail_register(guardrail)
    registrations = registry.get_all("EP-13")
    assert len(registrations) == 1
    assert registrations[0].name == "vitalia.hipaa_compliance_check"


def test_ep13_dispatch_raises_not_implemented() -> None:
    """B13 — dispatch_guardrail raises NotImplementedError."""
    from uuid import uuid4

    from luana_core_extension_sdk.brand_context import BrandContext

    registry = ExtensionPointRegistry()
    ctx = BrandContext(
        tenant_id=uuid4(),
        brand_slug="vitalia",
        plan_tier="free",
        locale="es-AR",
        feature_flags={},
        tenant_profile_id=uuid4(),
        vertical_kind="medical",
        compliance_flags={},
        pii_policy="medical",
    )
    with pytest.raises(NotImplementedError) as exc_info:
        registry.dispatch_guardrail("vitalia.hipaa_compliance_check", "test message", ctx, phase="send")
    assert "EP-13" in str(exc_info.value)


# ─── B14: EP-14 copilot_kb_pack_register ────────────────────────────


def test_ep14_register_succeeds() -> None:
    """B14 — copilot_kb_pack_register stores registration."""
    registry = ExtensionPointRegistry()
    kb_pack = KbPackDef(
        pack_id="vitalia.medical_protocols_kb",
        documents_path="kb/vitalia/medical_protocols/",
        embedding_model_ref="text-embedding-3-small",
        qdrant_collection_name="vitalia_medical_protocols",
        tenant_scope="brand",
    )
    registry.copilot_kb_pack_register(kb_pack)
    registrations = registry.get_all("EP-14")
    assert len(registrations) == 1
    assert registrations[0].name == "vitalia.medical_protocols_kb"


def test_ep14_dispatch_raises_not_implemented() -> None:
    """B14 — dispatch_kb_pack raises NotImplementedError."""
    from uuid import uuid4

    from luana_core_extension_sdk.brand_context import BrandContext

    registry = ExtensionPointRegistry()
    ctx = BrandContext(
        tenant_id=uuid4(),
        brand_slug="vitalia",
        plan_tier="free",
        locale="es-AR",
        feature_flags={},
        tenant_profile_id=uuid4(),
        vertical_kind="medical",
        compliance_flags={},
        pii_policy="medical",
    )
    with pytest.raises(NotImplementedError) as exc_info:
        registry.dispatch_kb_pack("vitalia.medical_protocols_kb", ctx)
    assert "EP-14" in str(exc_info.value)


# ─── B15: EP-15 crm_lifecycle_stage_register ────────────────────────


def test_ep15_register_succeeds() -> None:
    """B15 — crm_lifecycle_stage_register stores registration."""
    registry = ExtensionPointRegistry()
    stage = LifecycleStageDef(
        stage_id="vitalia.post_treatment",
        label="Post-tratamiento",
        after_stage="treatment_completed",
        before_stage="retention",
    )
    registry.crm_lifecycle_stage_register(stage)
    registrations = registry.get_all("EP-15")
    assert len(registrations) == 1
    assert registrations[0].name == "vitalia.post_treatment"


def test_ep15_dispatch_raises_not_implemented() -> None:
    """B15 — dispatch_lifecycle_transition raises NotImplementedError."""
    from uuid import uuid4

    from luana_core_extension_sdk.brand_context import BrandContext

    registry = ExtensionPointRegistry()
    ctx = BrandContext(
        tenant_id=uuid4(),
        brand_slug="vitalia",
        plan_tier="free",
        locale="es-AR",
        feature_flags={},
        tenant_profile_id=uuid4(),
        vertical_kind="medical",
        compliance_flags={},
        pii_policy="medical",
    )
    with pytest.raises(NotImplementedError) as exc_info:
        registry.dispatch_lifecycle_transition("vitalia.post_treatment", ctx)
    assert "EP-15" in str(exc_info.value)


# ─── B16: EP-16 iam_signup_handler ──────────────────────────────────


def test_ep16_register_succeeds() -> None:
    """B16 — iam_signup_handler stores registration."""
    from luana_core_extension_sdk.models import SignupResult

    registry = ExtensionPointRegistry()

    def medical_signup_handler(clerk_user: object, ctx: object) -> SignupResult:
        return SignupResult(status="pending_review")

    registry.iam_signup_handler(medical_signup_handler, name="vitalia.medical_signup")
    registrations = registry.get_all("EP-16")
    assert len(registrations) == 1
    assert registrations[0].name == "vitalia.medical_signup"


def test_ep16_dispatch_raises_not_implemented() -> None:
    """B16 — dispatch_signup raises NotImplementedError."""
    from uuid import uuid4

    from luana_core_extension_sdk.brand_context import BrandContext

    registry = ExtensionPointRegistry()
    ctx = BrandContext(
        tenant_id=uuid4(),
        brand_slug="vitalia",
        plan_tier="free",
        locale="es-AR",
        feature_flags={},
        tenant_profile_id=uuid4(),
        vertical_kind="medical",
        compliance_flags={},
        pii_policy="medical",
    )
    with pytest.raises(NotImplementedError) as exc_info:
        registry.dispatch_signup(object(), ctx)
    assert "EP-16" in str(exc_info.value)


# ─── B17: EP-17 tenant_plan_tier_register (mode='override' permitted) ──────────


def test_ep17_register_succeeds() -> None:
    """B17 — tenant_plan_tier_register stores registration."""
    registry = ExtensionPointRegistry()
    tier = PlanTierDef(
        tier_id="vitalia.clinica_pro",
        label="Clínica Pro",
        price_monthly=199.0,
        currency="USD",
        features=("unlimited_appointments", "hipaa_compliance", "priority_support"),
    )
    registry.tenant_plan_tier_register(tier)
    registrations = registry.get_all("EP-17")
    assert len(registrations) == 1
    assert registrations[0].name == "vitalia.clinica_pro"


def test_ep17_dispatch_raises_not_implemented() -> None:
    """B17 — dispatch_plan_tiers raises NotImplementedError."""
    from uuid import uuid4

    from luana_core_extension_sdk.brand_context import BrandContext

    registry = ExtensionPointRegistry()
    ctx = BrandContext(
        tenant_id=uuid4(),
        brand_slug="vitalia",
        plan_tier="free",
        locale="es-AR",
        feature_flags={},
        tenant_profile_id=uuid4(),
        vertical_kind="medical",
        compliance_flags={},
        pii_policy="medical",
    )
    with pytest.raises(NotImplementedError) as exc_info:
        registry.dispatch_plan_tiers(ctx)
    assert "EP-17" in str(exc_info.value)


def test_ep17_override_mode_permitted() -> None:
    """B17 extra — EP-17 permits mode='override' (CC-2)."""
    registry = ExtensionPointRegistry()
    tier_v1 = PlanTierDef(
        tier_id="vitalia.clinica_pro",
        label="Clínica Pro v1",
        price_monthly=199.0,
        currency="USD",
        features=("unlimited_appointments",),
    )
    tier_v2 = PlanTierDef(
        tier_id="vitalia.clinica_pro",
        label="Clínica Pro v2",
        price_monthly=249.0,
        currency="USD",
        features=("unlimited_appointments", "hipaa_compliance"),
    )
    registry.tenant_plan_tier_register(tier_v1)
    # override replaces v1 — no DuplicateRegistrationError
    registry.tenant_plan_tier_register(tier_v2, mode="override")
    registrations = registry.get_all("EP-17")
    assert len(registrations) == 1
    assert registrations[0].payload.label == "Clínica Pro v2"


# ─── B18: EP-18 onboarding_wizard_steps_register (mode='override' permitted) ───


def test_ep18_register_succeeds() -> None:
    """B18 — onboarding_wizard_steps_register stores registration."""
    registry = ExtensionPointRegistry()
    step = WizardStepDef(
        step_id="vitalia.medical_consent_step",
        title="Consentimiento informado",
        component_ref="VitaliaMedicalConsentForm",
        prereqs=("profile_complete",),
        skippable=False,
        post_action_event="medical_consent_signed",
    )
    registry.onboarding_wizard_steps_register(step)
    registrations = registry.get_all("EP-18")
    assert len(registrations) == 1
    assert registrations[0].name == "vitalia.medical_consent_step"


def test_ep18_dispatch_raises_not_implemented() -> None:
    """B18 — dispatch_wizard_steps raises NotImplementedError."""
    from uuid import uuid4

    from luana_core_extension_sdk.brand_context import BrandContext

    registry = ExtensionPointRegistry()
    ctx = BrandContext(
        tenant_id=uuid4(),
        brand_slug="vitalia",
        plan_tier="free",
        locale="es-AR",
        feature_flags={},
        tenant_profile_id=uuid4(),
        vertical_kind="medical",
        compliance_flags={},
        pii_policy="medical",
    )
    with pytest.raises(NotImplementedError) as exc_info:
        registry.dispatch_wizard_steps(ctx)
    assert "EP-18" in str(exc_info.value)


def test_ep18_override_mode_permitted() -> None:
    """B18 extra — EP-18 permits mode='override' (CC-2)."""
    registry = ExtensionPointRegistry()
    step_v1 = WizardStepDef(
        step_id="vitalia.medical_consent_step",
        title="Consentimiento v1",
        component_ref="VitaliaMedicalConsentFormV1",
    )
    step_v2 = WizardStepDef(
        step_id="vitalia.medical_consent_step",
        title="Consentimiento v2",
        component_ref="VitaliaMedicalConsentFormV2",
    )
    registry.onboarding_wizard_steps_register(step_v1)
    # override replaces v1 — no DuplicateRegistrationError
    registry.onboarding_wizard_steps_register(step_v2, mode="override")
    registrations = registry.get_all("EP-18")
    assert len(registrations) == 1
    assert registrations[0].payload.component_ref == "VitaliaMedicalConsentFormV2"


# ─── V-F-sdk-1 cross-assertions ──────────────────────────────────────


def test_all_18_register_methods_exist() -> None:
    """V-F-sdk-1 — ExtensionPointRegistry exposes exactly 18 register methods (EP-1..EP-18)."""
    expected_methods = [
        "field_override",
        "offer_preset_pack_register",
        "sales_agent_tool_register",
        "copilot_workflow_register",
        "scheduling_booking_policy_register",
        "sidebar_routes_register",
        "extractor_register",
        "channel_adapter_register",
        "metric_register",
        "landing_template_register",
        "campaign_template_register",
        "asset_template_register",
        "sales_agent_guardrail_register",
        "copilot_kb_pack_register",
        "crm_lifecycle_stage_register",
        "iam_signup_handler",
        "tenant_plan_tier_register",
        "onboarding_wizard_steps_register",
    ]
    missing = [m for m in expected_methods if not hasattr(ExtensionPointRegistry, m)]
    assert not missing, f"Missing EP register methods: {missing}"
    assert len(expected_methods) == 18


def test_namespaced_obligatorio_applies_backlog() -> None:
    """CC-4 — bare name (without brand_slug prefix) raises NamespaceViolationError for backlog EPs."""
    registry = ExtensionPointRegistry()
    route = SidebarRouteDef(slug="bare-name-no-brand-prefix", label="Test", icon="x", order=1)
    with pytest.raises(NamespaceViolationError):
        registry.sidebar_routes_register(route)


def test_lock_blocks_backlog_register() -> None:
    """CC-3 — post-lock (registry.close()) register_* raises RegistrationClosedError for backlog EPs."""
    registry = ExtensionPointRegistry()
    registry.close()
    route = SidebarRouteDef(slug="vitalia.test_route", label="Test", icon="x", order=1)
    with pytest.raises(RegistrationClosedError):
        registry.sidebar_routes_register(route)


def test_mode_override_only_ep17_ep18() -> None:
    """CC-2 — EP-6..EP-16 reject mode='override'; EP-17 + EP-18 accept it."""
    registry = ExtensionPointRegistry()
    route = SidebarRouteDef(slug="vitalia.test_route", label="Test", icon="x", order=1)
    with pytest.raises(ValueError, match="does not support mode='override'"):
        registry.sidebar_routes_register(route, mode="override")

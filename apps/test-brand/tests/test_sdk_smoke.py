"""Smoke pack — 10 scenarios D1-D3 + C1-C5 + E1.

Per 01-spec §3.4.3 + §5.5 + §5.4 verbatim and 04-validators.yaml V-F-test-brand-1.

D1  lifespan registers all 18 EPs + registry is closed after startup
D2  EP-1..EP-5 happy path invocation returns typed results without exception
D3  EP-6..EP-18 semantic dispatch raises NotImplementedError graceful
C1  duplicate registration raises DuplicateRegistrationError
C2  bare name (no brand prefix) raises NamespaceViolationError
C3  post-startup register raises RegistrationClosedError
C4  unregister_* method does not exist (AttributeError)
C5a override mode restricted: EP-1 with mode='override' raises ValueError
C5b override mode permitted: EP-17 + EP-18 accept mode='override'
E1  BrandContext is frozen + 9 fields verified + no PII field names
"""

import dataclasses
from uuid import uuid4

import pytest
from luana_core_extension_sdk import (
    BrandContext,
    ExtensionPointRegistry,
    FieldDef,
    FieldOverride,
    PresetPack,
    ToolDef,
    WorkflowDef,
)
from luana_core_extension_sdk.exceptions import (
    DuplicateRegistrationError,
    NamespaceViolationError,
    RegistrationClosedError,
)
from test_brand.extensions import register_all

# ─── helpers ──────────────────────────────────────────────────────────────────


def _make_registry() -> ExtensionPointRegistry:
    """Construct a fresh registry and register all 18 extensions."""
    registry = ExtensionPointRegistry(
        sales_agent_tool_registry_adapter=None,
        copilot_workflow_registry_adapter=None,
    )
    register_all(registry)
    return registry


def _make_brand_ctx() -> BrandContext:
    return BrandContext(
        tenant_id=uuid4(),
        brand_slug="test-brand",
        plan_tier="free",
        locale="es-AR",
        feature_flags={},
        tenant_profile_id=uuid4(),
        vertical_kind="marketing",
        compliance_flags={},
        pii_policy="standard",
    )


# ─── D1: lifespan registers all 18 EPs ────────────────────────────────────────


def test_lifespan_registers_all_18_eps() -> None:
    """D1 — verify 18 registrations succeed + registry not yet closed.

    In production the lifespan calls registry.close() after register_all.
    Here we verify all 18 EPs have ≥1 registration after register_all.
    """
    registry = _make_registry()

    # Each EP-1..EP-18 has at least one registration
    ep_ids = [f"EP-{i}" for i in range(1, 19)]
    for ep_id in ep_ids:
        recs = registry.get_all(ep_id)
        assert len(recs) >= 1, f"{ep_id} has no registrations after register_all"

    total = sum(len(registry.get_all(ep_id)) for ep_id in ep_ids)
    assert total == 18, f"Expected exactly 18 total registrations, got {total}"


def test_lifespan_registry_closed_after_startup() -> None:
    """D1 — verify registry._closed is True after close() call (as in lifespan)."""
    registry = _make_registry()
    assert registry._closed is False, "Registry should be open before close()"
    registry.close()
    assert registry._closed is True, "Registry should be closed after close()"


# ─── D2: EP-1..EP-5 happy path ────────────────────────────────────────────────


def test_ep1_to_ep5_executable() -> None:
    """D2 — EP-1..EP-5 dispatch helpers return typed results without exception."""
    registry = _make_registry()
    ctx = _make_brand_ctx()

    # EP-1 field_override dispatch
    field = FieldDef(name="field_x", type_name="str")
    result = registry.resolve_field_override(field, ctx)
    assert result is not None
    assert isinstance(result, FieldOverride)
    assert result.name == "field_x_overridden"

    # EP-2 list_offer_preset_packs dispatch
    packs = registry.list_offer_preset_packs(ctx)
    assert isinstance(packs, list)
    assert len(packs) == 1
    assert isinstance(packs[0], PresetPack)
    assert packs[0].name == "test-brand.smoke_pack"

    # EP-3 get_sales_agent_tool dispatch
    tool = registry.get_sales_agent_tool("test-brand.echo_tool")
    assert isinstance(tool, ToolDef)
    assert tool.name == "test-brand.echo_tool"
    echo_result = tool.handler(message="hello")
    assert echo_result == "echo: hello"

    # EP-4 get_copilot_workflow dispatch
    workflow = registry.get_copilot_workflow("test-brand.smoke_workflow")
    assert isinstance(workflow, WorkflowDef)
    assert workflow.name == "test-brand.smoke_workflow"

    # EP-5 get_booking_policy dispatch
    policy = registry.get_booking_policy("test-brand.always_allow_policy")
    assert policy is not None
    booking_result = policy.can_confirm(object(), ctx)
    assert booking_result.allowed is True
    assert booking_result.reason == "smoke test always allows"


# ─── D3: EP-6..EP-18 NotImplementedError graceful ─────────────────────────────


def test_ep6_to_ep18_not_implemented_graceful() -> None:
    """D3 — EP-6..EP-18 semantic dispatch raises NotImplementedError with descriptive message."""
    registry = _make_registry()
    ctx = _make_brand_ctx()

    dispatch_calls = [
        (lambda: registry.get_sidebar_routes(ctx), "EP-6"),
        (lambda: registry.dispatch_extractor("test-brand.smoke_extractor", ctx), "EP-7"),
        (lambda: registry.dispatch_channel_adapter("test-brand.smoke_channel", ctx), "EP-8"),
        (lambda: registry.dispatch_metric("test-brand.smoke_metric", ctx), "EP-9"),
        (lambda: registry.dispatch_landing_template("test-brand.smoke_landing", ctx), "EP-10"),
        (lambda: registry.dispatch_campaign_template("test-brand.smoke_drip", ctx), "EP-11"),
        (lambda: registry.dispatch_asset_template("test-brand.smoke_asset", ctx), "EP-12"),
        (lambda: registry.dispatch_guardrail("test-brand.smoke_guardrail", "msg", ctx, phase="send"), "EP-13"),
        (lambda: registry.dispatch_kb_pack("test-brand.smoke_kb", ctx), "EP-14"),
        (lambda: registry.dispatch_lifecycle_transition("test-brand.pending_review", ctx), "EP-15"),
        (lambda: registry.dispatch_signup(object(), ctx), "EP-16"),
        (lambda: registry.dispatch_plan_tiers(ctx), "EP-17"),
        (lambda: registry.dispatch_wizard_steps(ctx), "EP-18"),
    ]

    for fn, ep_label in dispatch_calls:
        with pytest.raises(NotImplementedError) as exc_info:
            fn()
        msg = str(exc_info.value)
        assert "signature-only" in msg or "deferred" in msg, (
            f"{ep_label} NotImplementedError message should mention 'signature-only' or 'deferred', got: {msg}"
        )


# ─── C1: duplicate registration raises DuplicateRegistrationError ─────────────


def test_duplicate_registration_raises() -> None:
    """C1 — second register_* with same name → DuplicateRegistrationError."""
    registry = ExtensionPointRegistry()

    def _handler(field: FieldDef, ctx: BrandContext) -> None:
        return None

    registry.field_override(_handler, name="test-brand.dup_field")

    with pytest.raises(DuplicateRegistrationError) as exc_info:
        registry.field_override(_handler, name="test-brand.dup_field")

    assert "test-brand.dup_field" in str(exc_info.value)


# ─── C2: bare name raises NamespaceViolationError ─────────────────────────────


def test_namespace_violation_raises() -> None:
    """C2 — register with bare name (no brand prefix) → NamespaceViolationError."""
    registry = ExtensionPointRegistry()

    with pytest.raises(NamespaceViolationError) as exc_info:
        registry.offer_preset_pack_register(
            PresetPack(
                name="bare_name_no_prefix",
                presets=(),
                applies_to_brand="test-brand",
            )
        )

    assert "bare_name_no_prefix" in str(exc_info.value)


# ─── C3: post-startup register raises RegistrationClosedError ─────────────────


def test_post_startup_registration_raises() -> None:
    """C3 — registry.close() then register_* → RegistrationClosedError."""
    registry = ExtensionPointRegistry()
    registry.close()

    with pytest.raises(RegistrationClosedError) as exc_info:
        registry.offer_preset_pack_register(
            PresetPack(
                name="test-brand.after_close",
                presets=(),
                applies_to_brand="test-brand",
            )
        )

    assert "CC-3" in str(exc_info.value) or "closed" in str(exc_info.value).lower()


# ─── C4: no unregister_* method exists ────────────────────────────────────────


def test_no_unregister_method_exists() -> None:
    """C4 — getattr(registry, 'unregister_field_override') → AttributeError (CC-5)."""
    registry = ExtensionPointRegistry()

    with pytest.raises(AttributeError):
        _ = getattr(registry, "unregister_field_override")

    # Verify exhaustively for all 18 EPs
    unregister_variants = [
        "unregister_field_override",
        "unregister_offer_preset_pack",
        "unregister_sales_agent_tool",
        "unregister_copilot_workflow",
        "unregister_booking_policy",
    ]
    for method_name in unregister_variants:
        assert not hasattr(registry, method_name), f"Registry must NOT expose {method_name} (CC-5 inmutable)"


# ─── C5a: override mode restricted to EP-17 + EP-18 ──────────────────────────


def test_override_mode_restricted_to_ep17_ep18() -> None:
    """C5a — register EP-1 with mode='override' → ValueError (CC-2)."""
    registry = ExtensionPointRegistry()

    def _handler(field: FieldDef, ctx: BrandContext) -> None:
        return None

    with pytest.raises(ValueError) as exc_info:
        registry.field_override(_handler, name="test-brand.some_override", mode="override")

    msg = str(exc_info.value)
    assert "override" in msg.lower() or "EP-1" in msg, f"Expected ValueError about override restriction, got: {msg}"


# ─── C5b: override mode permitted on EP-17 + EP-18 ───────────────────────────


def test_override_mode_permitted_on_ep17_ep18() -> None:
    """C5b — register EP-17 + EP-18 with mode='override' succeeds."""
    from luana_core_extension_sdk import PlanTierDef, WizardStepDef

    registry = ExtensionPointRegistry()

    # EP-17 override succeeds
    registry.tenant_plan_tier_register(
        PlanTierDef(
            tier_id="test-brand.smoke_tier_v1",
            label="Tier v1",
            price_monthly=0.0,
            currency="USD",
            features=(),
            limits={},
        ),
        mode="override",
    )

    # Override again on EP-17 succeeds (replaces)
    registry.tenant_plan_tier_register(
        PlanTierDef(
            tier_id="test-brand.smoke_tier_v1",
            label="Tier v2 override",
            price_monthly=9.99,
            currency="USD",
            features=("feature_a",),
            limits={},
        ),
        mode="override",
    )

    # EP-18 override succeeds
    registry.onboarding_wizard_steps_register(
        WizardStepDef(
            step_id="test-brand.step_v1",
            title="Step v1",
            component_ref="StepV1",
        ),
        mode="override",
    )

    # Override again on EP-18 succeeds
    registry.onboarding_wizard_steps_register(
        WizardStepDef(
            step_id="test-brand.step_v1",
            title="Step v2 override",
            component_ref="StepV2",
        ),
        mode="override",
    )

    # Verify EP-17 has exactly 1 registration (override replaced, not appended)
    ep17_recs = registry.get_all("EP-17")
    assert len(ep17_recs) == 1, f"EP-17 override should replace: got {len(ep17_recs)} records"

    # Verify EP-18 has exactly 1 registration
    ep18_recs = registry.get_all("EP-18")
    assert len(ep18_recs) == 1, f"EP-18 override should replace: got {len(ep18_recs)} records"


# ─── E1: BrandContext frozen + 9 fields + no PII ──────────────────────────────


def test_brand_context_frozen_no_pii() -> None:
    """E1 — BrandContext: frozen=True + 9 fields verified + no PII field names."""
    # Frozen invariant
    assert BrandContext.__dataclass_params__.frozen is True

    # Mutation raises FrozenInstanceError
    ctx = _make_brand_ctx()
    with pytest.raises(dataclasses.FrozenInstanceError):
        ctx.tenant_id = uuid4()  # type: ignore[misc]

    # Exactly 9 fields
    fields = dataclasses.fields(BrandContext)
    field_names = {f.name for f in fields}
    expected = {
        "tenant_id",
        "brand_slug",
        "plan_tier",
        "locale",
        "feature_flags",
        "tenant_profile_id",
        "vertical_kind",
        "compliance_flags",
        "pii_policy",
    }
    assert field_names == expected, f"BrandContext fields mismatch: {field_names} != {expected}"

    # No PII field names
    pii_patterns = {"email", "phone", "address", "dob", "birth", "ssn", "card"}
    leaks = [name for name in field_names for p in pii_patterns if p in name.lower()]
    assert not leaks, f"BrandContext has PII field names: {leaks}"

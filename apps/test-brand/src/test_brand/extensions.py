"""Test brand extensions — 5 executable + 13 signature-only stubs per §7.5.2 D6=A.

Per 05-guidelines.md §1.10 verbatim.

All names MUST start with 'test-brand.' prefix per CC-4 namespace enforcement.
"""

from typing import Optional

from luana_core_extension_sdk import (
    AssetTemplateDef,
    BookingPolicy,
    BookingResult,
    BrandContext,
    CampaignStepDef,
    CampaignTemplateDef,
    ChannelAdapterDef,
    ExtensionPointRegistry,
    ExtractorDef,
    FieldDef,
    FieldOverride,
    GuardrailDef,
    GuardrailResult,
    KbPackDef,
    LandingTemplateDef,
    LifecycleStageDef,
    MetricDef,
    PlanTierDef,
    PresetPack,
    SidebarRouteDef,
    SignupResult,
    ToolDef,
    WizardStepDef,
    WorkflowDef,
)


def register_all(registry: ExtensionPointRegistry) -> None:
    """Register 18 extensions — 5 executable (EP-1..EP-5) + 13 stubs (EP-6..EP-18).

    All names MUST start with 'test-brand.' prefix per CC-4.
    """

    # ── EP-1 executable: field_override ──────────────────────────────────
    def _override_handler(field: FieldDef, ctx: BrandContext) -> Optional[FieldOverride]:
        if field.name == "field_x" and ctx.brand_slug == "test-brand":
            return FieldOverride(name="field_x_overridden", default_value="test")
        return None

    registry.field_override(_override_handler, name="test-brand.field_x_override")

    # ── EP-2 executable: offer_preset_pack_register ──────────────────────
    registry.offer_preset_pack_register(
        PresetPack(
            name="test-brand.smoke_pack",
            presets=(),
            applies_to_brand="test-brand",
            description="Smoke test preset pack",
        )
    )

    # ── EP-3 executable: sales_agent_tool_register (adapter is None — record only) ──
    def _echo_handler(message: str) -> str:
        return f"echo: {message}"

    registry.sales_agent_tool_register(
        ToolDef(
            name="test-brand.echo_tool",
            description="Echo tool for smoke testing",
            input_schema={"type": "object", "properties": {"message": {"type": "string"}}},
            handler=_echo_handler,
            tool_groups=("smoke",),
        )
    )

    # ── EP-4 executable: copilot_workflow_register (adapter is None — record only) ──
    registry.copilot_workflow_register(
        WorkflowDef(
            name="test-brand.smoke_workflow",
            description="Smoke workflow",
            steps=(),
            trigger_event=None,
        )
    )

    # ── EP-5 executable: scheduling_booking_policy_register ──────────────
    def _always_allow_policy(booking: object, ctx: BrandContext) -> BookingResult:
        return BookingResult(allowed=True, reason="smoke test always allows")

    registry.scheduling_booking_policy_register(
        BookingPolicy(
            name="test-brand.always_allow_policy",
            can_confirm=_always_allow_policy,
            priority=0,
        )
    )

    # ── EP-6..EP-18 stubs: register succeeds; dispatch raises NotImplementedError ──

    # EP-6
    registry.sidebar_routes_register(
        SidebarRouteDef(slug="test-brand.smoke_route", label="Smoke", icon="zap", order=99)
    )

    # EP-7
    registry.extractor_register(
        ExtractorDef(
            name="test-brand.smoke_extractor",
            target_module="offer",
            wave_position=99,
            prompt_template_ref="smoke.j2",
            output_schema_ref="SmokeSchema",
        )
    )

    # EP-8
    def _smoke_send(*args: object, **kwargs: object) -> None:
        return None

    def _smoke_receive(*args: object, **kwargs: object) -> None:
        return None

    def _smoke_format(*args: object, **kwargs: object) -> None:
        return None

    registry.channel_adapter_register(
        ChannelAdapterDef(
            channel_slug="test-brand.smoke_channel",
            send=_smoke_send,
            receive=_smoke_receive,
            format_for_channel=_smoke_format,
            target_agent_runtime="sales_agent",
        )
    )

    # EP-9
    registry.metric_register(
        MetricDef(
            name="test-brand.smoke_metric",
            module="analytics",
            aggregation="sum",
            unit="count",
            currency_aware=False,
            stage_assignment="attraction",
            refresh_freq="daily",
            python_compute=lambda: 0,
        )
    )

    # EP-10
    registry.landing_template_register(
        LandingTemplateDef(
            template_id="test-brand.smoke_landing",
            vertical_hint="test",
            sections_schema={"sections": []},
        )
    )

    # EP-11
    registry.campaign_template_register(
        CampaignTemplateDef(
            template_id="test-brand.smoke_drip",
            channel="email",
            steps=(CampaignStepDef(step_id="s1", delay_seconds=0, template_ref="t1"),),
            trigger_event="user.signup",
        )
    )

    # EP-12
    registry.asset_template_register(
        AssetTemplateDef(
            template_id="test-brand.smoke_asset",
            asset_type="image",
            placeholders={"logo_url": "str", "tagline": "str"},
            source_path="templates/smoke.png",
        )
    )

    # EP-13 (pre_send + pre_receive both)
    def _pre_send_check(msg: str, ctx: BrandContext) -> GuardrailResult:
        return GuardrailResult(blocked=False)

    def _pre_receive_check(msg: str, ctx: BrandContext) -> GuardrailResult:
        return GuardrailResult(blocked=False)

    registry.sales_agent_guardrail_register(
        GuardrailDef(
            name="test-brand.smoke_guardrail",
            pre_send_check=_pre_send_check,
            pre_receive_check=_pre_receive_check,
            priority=10,
            mode="warn",
        )
    )

    # EP-14
    registry.copilot_kb_pack_register(
        KbPackDef(
            pack_id="test-brand.smoke_kb",
            documents_path="./kb/",
            embedding_model_ref="text-embedding-3-small",
            qdrant_collection_name="test-brand-smoke",
            tenant_scope="both",
        )
    )

    # EP-15
    registry.crm_lifecycle_stage_register(
        LifecycleStageDef(
            stage_id="test-brand.pending_review",
            label="Pending Review",
            after_stage="signup",
            before_stage="active",
        )
    )

    # EP-16
    def _smoke_signup_handler(clerk_user: object, ctx: BrandContext) -> SignupResult:
        return SignupResult(status="pending_review", metadata={"reason": "smoke"})

    registry.iam_signup_handler(_smoke_signup_handler, name="test-brand.smoke_signup")

    # EP-17 (override permitted)
    registry.tenant_plan_tier_register(
        PlanTierDef(
            tier_id="test-brand.smoke_tier",
            label="Smoke Tier",
            price_monthly=0.0,
            currency="USD",
            features=(),
            limits={},
        ),
        mode="override",
    )

    # EP-18 (override permitted)
    registry.onboarding_wizard_steps_register(
        WizardStepDef(
            step_id="test-brand.smoke_step",
            title="Smoke",
            component_ref="SmokeStep",
        ),
        mode="override",
    )

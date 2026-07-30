"""18 DataClass models for declarative extension points — per §1.3 step 3.

All models: @dataclass(frozen=True, slots=True, kw_only=True) per §1.4 canonical pattern.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Forward reference for BrandContext (avoid circular import — defined in brand_context.py)
# Models that reference BrandContext use TYPE_CHECKING pattern
from typing import TYPE_CHECKING, Any, Callable, Literal, Optional

if TYPE_CHECKING:
    pass


# EP-1 — Field override result (Callable returns this)
@dataclass(frozen=True, slots=True, kw_only=True)
class FieldOverride:
    """Result of EP-1 field_override handler call."""

    name: str  # override field name (may differ from original)
    default_value: Any = None
    label: Optional[str] = None
    hint: Optional[str] = None
    required: Optional[bool] = None


# EP-1 — Field definition input
@dataclass(frozen=True, slots=True, kw_only=True)
class FieldDef:
    """Input type passed to EP-1 field_override handler."""

    name: str
    type_name: str  # "str" | "int" | "decimal" | ...
    required: bool = False
    section: Optional[str] = None


# EP-2 — Offer preset pack
@dataclass(frozen=True, slots=True, kw_only=True)
class PresetPack:
    """Offer preset pack for EP-2 registration."""

    name: str  # MUST be `{brand_slug}.{pack_name}` (CC-4)
    presets: tuple[Any, ...] = ()  # tuple of preset dicts (validated by offer core)
    applies_to_brand: str = ""  # brand_slug literal
    description: Optional[str] = None


# EP-3 — Sales agent tool
@dataclass(frozen=True, slots=True, kw_only=True)
class ToolDef:
    """Tool definition for EP-3 sales_agent_tool_register."""

    name: str  # MUST be `{brand_slug}.{tool_name}` (CC-4)
    description: str
    input_schema: dict[str, Any]  # JSON schema
    handler: Callable[..., Any]  # Callable invoked by sales_agent
    tool_groups: tuple[str, ...] = ()  # e.g. ("knowledge", "qualification")


# EP-4 — Copilot workflow
@dataclass(frozen=True, slots=True, kw_only=True)
class WorkflowDef:
    """Workflow definition for EP-4 copilot_workflow_register."""

    name: str  # MUST be `{brand_slug}.{workflow_name}` (CC-4)
    description: str
    steps: tuple[Any, ...]  # workflow steps (validated by copilot core)
    trigger_event: Optional[str] = None


# EP-5 — Scheduling booking policy
@dataclass(frozen=True, slots=True, kw_only=True)
class BookingPolicy:
    """Booking policy for EP-5 scheduling_booking_policy_register."""

    name: str  # MUST be `{brand_slug}.{policy_name}` (CC-4)
    can_confirm: Callable[..., Any]  # Callable[[Any, BrandContext], BookingResult]
    priority: int = 0


@dataclass(frozen=True, slots=True, kw_only=True)
class BookingResult:
    """Result returned by BookingPolicy.can_confirm callable."""

    allowed: bool
    reason: Optional[str] = None


# EP-6 — Sidebar route
@dataclass(frozen=True, slots=True, kw_only=True)
class SidebarRouteDef:
    """Sidebar route definition for EP-6 sidebar_routes_register."""

    slug: str  # MUST be `{brand_slug}.{slug}` (CC-4)
    label: str
    icon: str
    order: int = 100
    parent_slug: Optional[str] = None
    role_required: Optional[str] = None


# EP-7 — Extractor
@dataclass(frozen=True, slots=True, kw_only=True)
class ExtractorDef:
    """Extractor definition for EP-7 extractor_register."""

    name: str  # MUST be `{brand_slug}.{extractor_name}` (CC-4)
    target_module: str  # "offer" | "brand" | "landing" | "buyer_persona"
    wave_position: int  # 1..N integer
    prompt_template_ref: str
    output_schema_ref: str
    dependencies: tuple[str, ...] = ()


# EP-8 — Channel adapter (extended scope per §7.5.3: sales_agent + copilot + vertical agents)
@dataclass(frozen=True, slots=True, kw_only=True)
class ChannelAdapterDef:
    """Channel adapter for EP-8 channel_adapter_register."""

    channel_slug: str  # MUST be `{brand_slug}.{slug}` (CC-4)
    send: Callable[..., Any]
    receive: Callable[..., Any]
    format_for_channel: Callable[..., Any]
    target_agent_runtime: Literal["sales_agent", "copilot", "vertical_brand"]
    webhook_handler: Optional[Callable[..., Any]] = None


# EP-9 — Metric
@dataclass(frozen=True, slots=True, kw_only=True)
class MetricDef:
    """Metric definition for EP-9 metric_register."""

    name: str  # MUST be `{brand_slug}.{metric_name}` (CC-4)
    module: str  # "analytics" | "campaigns" | ...
    aggregation: Literal["sum", "avg", "count", "min", "max"]
    unit: str  # "currency" | "count" | "ratio" | ...
    currency_aware: bool
    stage_assignment: str  # "attraction" | "capture" | "nurture" | ...
    refresh_freq: Literal["realtime", "hourly", "daily"]
    sql_query: Optional[str] = None
    python_compute: Optional[Callable[..., Any]] = None


# EP-10 — Landing template
@dataclass(frozen=True, slots=True, kw_only=True)
class LandingTemplateDef:
    """Landing template for EP-10 landing_template_register."""

    template_id: str  # MUST be `{brand_slug}.{template_id}` (CC-4)
    vertical_hint: str
    sections_schema: dict[str, Any]  # JSON schema
    preview_url: Optional[str] = None


# EP-11 — Campaign template (drip)
@dataclass(frozen=True, slots=True, kw_only=True)
class CampaignStepDef:
    """Single step in a campaign template drip sequence."""

    step_id: str
    delay_seconds: int
    template_ref: str


@dataclass(frozen=True, slots=True, kw_only=True)
class CampaignTemplateDef:
    """Campaign template for EP-11 campaign_template_register."""

    template_id: str  # MUST be `{brand_slug}.{template_id}` (CC-4)
    channel: Literal["email", "whatsapp", "sms"]
    steps: tuple[CampaignStepDef, ...]
    trigger_event: str
    conditions: dict[str, Any] = field(default_factory=dict)


# EP-12 — Asset template
@dataclass(frozen=True, slots=True, kw_only=True)
class AssetTemplateDef:
    """Asset template for EP-12 asset_template_register."""

    template_id: str  # MUST be `{brand_slug}.{template_id}` (CC-4)
    asset_type: Literal["image", "video", "pdf", "kit"]
    placeholders: dict[str, str]  # {placeholder_name: type_name}
    source_path: str


# EP-13 — Sales agent guardrail (extended: pre_send + pre_receive per §7.5.3)
@dataclass(frozen=True, slots=True, kw_only=True)
class GuardrailResult:
    """Result of a guardrail check (pre_send_check or pre_receive_check)."""

    blocked: bool
    rewritten: Optional[str] = None
    reason: Optional[str] = None


@dataclass(frozen=True, slots=True, kw_only=True)
class GuardrailDef:
    """Guardrail definition for EP-13 sales_agent_guardrail_register.

    Extended scope per §7.5.3 EP-13: includes pre_send + pre_receive checks.
    """

    name: str  # MUST be `{brand_slug}.{guardrail_name}` (CC-4)
    pre_send_check: Callable[..., Any]  # Callable[[str, BrandContext], GuardrailResult]
    priority: int = 100
    mode: Literal["block", "warn", "rewrite"] = "warn"
    pre_receive_check: Optional[Callable[..., Any]] = None  # Callable[[str, BrandContext], GuardrailResult]


# EP-14 — Copilot KB pack (tenant_scope tri-modal per §7.5.3)
@dataclass(frozen=True, slots=True, kw_only=True)
class KbPackDef:
    """Knowledge base pack for EP-14 copilot_kb_pack_register."""

    pack_id: str  # MUST be `{brand_slug}.{pack_id}` (CC-4)
    documents_path: str
    embedding_model_ref: str
    qdrant_collection_name: str
    tenant_scope: Literal["brand", "tenant", "both"]
    metadata: dict[str, Any] = field(default_factory=dict)


# EP-15 — CRM lifecycle stage
@dataclass(frozen=True, slots=True, kw_only=True)
class LifecycleStageDef:
    """CRM lifecycle stage for EP-15 crm_lifecycle_stage_register."""

    stage_id: str  # MUST be `{brand_slug}.{stage_id}` (CC-4)
    label: str
    after_stage: str  # FK to existing stage
    before_stage: str  # FK to existing stage
    transition_rules: tuple[Callable[..., Any], ...] = ()


# EP-16 — IAM signup result
@dataclass(frozen=True, slots=True, kw_only=True)
class SignupResult:
    """Result of an IAM signup handler (EP-16)."""

    status: Literal["approved", "pending_review", "rejected"]
    metadata: dict[str, Any] = field(default_factory=dict)
    blocking_reason: Optional[str] = None


# EP-17 — Tenant plan tier (override mode permitted per §7.5.3)
@dataclass(frozen=True, slots=True, kw_only=True)
class PlanTierDef:
    """Plan tier definition for EP-17 tenant_plan_tier_register (mode='override' permitted)."""

    tier_id: str  # MUST be `{brand_slug}.{tier_id}` (CC-4)
    label: str
    price_monthly: float
    currency: str  # ISO 4217
    features: tuple[str, ...]
    limits: dict[str, Any] = field(default_factory=dict)
    stripe_price_id: Optional[str] = None


# EP-18 — Onboarding wizard step (override mode permitted per §7.5.3)
@dataclass(frozen=True, slots=True, kw_only=True)
class WizardStepDef:
    """Onboarding wizard step for EP-18 onboarding_wizard_steps_register (mode='override' permitted)."""

    step_id: str  # MUST be `{brand_slug}.{step_id}` (CC-4)
    title: str
    component_ref: str  # FE component identifier
    prereqs: tuple[str, ...] = ()
    skippable: bool = False
    post_action_event: Optional[str] = None

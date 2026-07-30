"""ExtensionPointRegistry — 18 extension points with CC-1..CC-5 runtime enforcement.

Per outcome §7.5 binding decisions (ratified 2026-05-12) + architect spec
03-arch-be.md §1.3 step 4 verbatim.

EP-1..EP-5 critical: register + dispatch helpers EXECUTABLE.
EP-6..EP-18 backlog: register stores record; semantic dispatch raises NotImplementedError.

Cross-cutting policies (CC-1..CC-5) enforced runtime:
- CC-3 startup-only — registry.close() after FastAPI lifespan startup.
- CC-4 namespace — name MUST start with `{brand_slug}.` prefix from allowlist.
- CC-4 duplicate — re-registering same name within same EP raises.
- CC-5 inmutable — no unregister_* methods (verified by AttributeError on lookup).
- CC-2 override — only EP-17 + EP-18 permit mode='override'; others raise ValueError.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Literal, Optional

from luana_core_extension_sdk.brand_context import BrandContext
from luana_core_extension_sdk.exceptions import (
    DuplicateRegistrationError,
    NamespaceViolationError,
    RegistrationClosedError,
)
from luana_core_extension_sdk.models import (
    AssetTemplateDef,
    BookingPolicy,
    CampaignTemplateDef,
    ChannelAdapterDef,
    ExtractorDef,
    FieldDef,
    FieldOverride,
    GuardrailDef,
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

# ─── module-level constants ──────────────────────────────────────────

# EP IDs (string constants for registry lookup)
_EP_IDS = tuple(f"EP-{i}" for i in range(1, 19))

# EPs that permit mode='override' per outcome §7.5.3 CC-2
_OVERRIDE_PERMITTED_EPS = frozenset({"EP-17", "EP-18"})

# Brand slug literal allowlist (mirror BrandContext.brand_slug Literal)
_ALLOWED_BRAND_SLUGS = frozenset({"nicolify", "vitalia", "comunify", "lupulo", "test-brand"})

# Backlog EPs that raise NotImplementedError on semantic dispatch (signatures-only v0.1.0)
_BACKLOG_EPS = frozenset(
    {
        "EP-6",
        "EP-7",
        "EP-8",
        "EP-9",
        "EP-10",
        "EP-11",
        "EP-12",
        "EP-13",
        "EP-14",
        "EP-15",
        "EP-16",
        "EP-17",
        "EP-18",
    }
)


@dataclass
class _Registration:
    """Internal registration record (private — exposed only via get_all introspection helper)."""

    ep_id: str
    name: str
    brand_slug: str
    payload: Any  # DataClass instance or Callable
    mode: Literal["append", "override"]


class ExtensionPointRegistry:
    """Central registry for 18 extension points (EP-1..EP-18).

    Constructor accepts injected frozen registry adapters from Stories 6+7 (EP-3 + EP-4
    wrap byte-stable — see _adapters.py module).
    """

    def __init__(
        self,
        *,
        sales_agent_tool_registry_adapter: Optional[Any] = None,
        copilot_workflow_registry_adapter: Optional[Any] = None,
    ) -> None:
        self._registrations: dict[str, list[_Registration]] = {ep: [] for ep in _EP_IDS}
        self._closed: bool = False
        self._sales_agent_tool_adapter = sales_agent_tool_registry_adapter
        self._copilot_workflow_adapter = copilot_workflow_registry_adapter

    # ─── lifecycle ──────────────────────────────────────────────────

    def close(self) -> None:
        """Lock registry after FastAPI startup. Subsequent register_* raises (CC-3).

        Idempotent — safe to call multiple times.
        """
        self._closed = True

    # ─── enforcement helpers ────────────────────────────────────────

    def _enforce_open(self, ep_id: str, name: str) -> None:
        if self._closed:
            raise RegistrationClosedError(
                f"Registry closed after FastAPI startup; runtime registration prohibited per CC-3 "
                f"({ep_id} name={name!r})"
            )

    def _enforce_namespace(self, name: str, ep_id: str) -> str:
        """Returns brand_slug if valid; else raises NamespaceViolationError."""
        parts = name.split(".", 1)
        if len(parts) != 2 or parts[0] not in _ALLOWED_BRAND_SLUGS or not parts[1]:
            raise NamespaceViolationError(
                f"Name {name!r} must be namespaced with brand_slug prefix "
                f"(e.g., 'vitalia.medical_consent_request'). "
                f"Accepted prefixes: {sorted(_ALLOWED_BRAND_SLUGS)}"
            )
        return parts[0]

    def _enforce_unique(self, ep_id: str, name: str, mode: str) -> None:
        if mode == "override":
            return  # override mode replaces — uniqueness not enforced
        for r in self._registrations[ep_id]:
            if r.name == name:
                raise DuplicateRegistrationError(f"Name {name!r} already registered for {ep_id}")

    def _enforce_mode(self, ep_id: str, mode: str) -> None:
        if mode not in ("append", "override"):
            raise ValueError(f"Invalid mode {mode!r}; expected 'append' or 'override'")
        if mode == "override" and ep_id not in _OVERRIDE_PERMITTED_EPS:
            raise ValueError(f"{ep_id} does not support mode='override'; only EP-17 + EP-18 permit override")

    def _register(
        self,
        ep_id: str,
        name: str,
        payload: Any,
        mode: Literal["append", "override"],
    ) -> None:
        self._enforce_open(ep_id, name)
        self._enforce_mode(ep_id, mode)
        brand_slug = self._enforce_namespace(name, ep_id)
        self._enforce_unique(ep_id, name, mode)
        if mode == "override":
            # Replace prior registration with same name (if any) — single match by name
            self._registrations[ep_id] = [r for r in self._registrations[ep_id] if r.name != name]
        self._registrations[ep_id].append(
            _Registration(ep_id=ep_id, name=name, brand_slug=brand_slug, payload=payload, mode=mode)
        )

    # ─── EP-1..EP-5 critical (EXECUTABLE) ───────────────────────────

    def field_override(
        self,
        handler: Callable[[FieldDef, BrandContext], Optional[FieldOverride]],
        *,
        name: str,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-1 — Register a field override handler.

        Core form-runtime invokes via resolve_field_override.
        """
        self._register("EP-1", name, handler, mode)

    def resolve_field_override(self, field: FieldDef, ctx: BrandContext) -> Optional[FieldOverride]:
        """EP-1 dispatch — invoke all handlers; first non-None wins (deterministic by order)."""
        for r in self._registrations["EP-1"]:
            result = r.payload(field, ctx)
            if result is not None:
                return result
        return None

    def offer_preset_pack_register(
        self,
        pack: PresetPack,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-2 — Register an offer preset pack."""
        self._register("EP-2", pack.name, pack, mode)

    def list_offer_preset_packs(self, ctx: BrandContext) -> list[PresetPack]:
        """EP-2 dispatch — return all packs filtered by ctx.brand_slug."""
        return [r.payload for r in self._registrations["EP-2"] if r.payload.applies_to_brand == ctx.brand_slug]

    def sales_agent_tool_register(
        self,
        tool: ToolDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-3 — Register a sales agent tool. Wraps Story 7 frozen ToolRegistry byte-stable.

        Internal: stores ToolDef in registry; delegate adapter (if injected) registers
        with underlying Story 7 ToolRegistry via read-only proxy.
        """
        self._register("EP-3", tool.name, tool, mode)
        # Adapter delegates registration to Story 7 ToolRegistry IF adapter injected.
        # V-AG-3 Story 7 golden snapshot ensures registry public API surface unchanged.
        if self._sales_agent_tool_adapter is not None:
            self._sales_agent_tool_adapter.register_extension_tool(tool)

    def get_sales_agent_tool(self, name: str) -> Optional[ToolDef]:
        """EP-3 dispatch — lookup by name."""
        for r in self._registrations["EP-3"]:
            if r.name == name:
                return r.payload
        return None

    def copilot_workflow_register(
        self,
        workflow: WorkflowDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-4 — Register a copilot workflow. Wraps Story 6 frozen WorkflowRegistry byte-stable."""
        self._register("EP-4", workflow.name, workflow, mode)
        if self._copilot_workflow_adapter is not None:
            self._copilot_workflow_adapter.register_extension_workflow(workflow)

    def get_copilot_workflow(self, name: str) -> Optional[WorkflowDef]:
        """EP-4 dispatch — lookup by name."""
        for r in self._registrations["EP-4"]:
            if r.name == name:
                return r.payload
        return None

    def scheduling_booking_policy_register(
        self,
        policy: BookingPolicy,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-5 — Register a scheduling booking policy."""
        self._register("EP-5", policy.name, policy, mode)

    def get_booking_policy(self, name: str) -> Optional[BookingPolicy]:
        """EP-5 dispatch — lookup by name."""
        for r in self._registrations["EP-5"]:
            if r.name == name:
                return r.payload
        return None

    # ─── EP-6..EP-18 backlog (SIGNATURE-ONLY) ───────────────────────

    def sidebar_routes_register(
        self,
        route: SidebarRouteDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-6 — Register a sidebar route. Signature-only v0.1.0."""
        self._register("EP-6", route.slug, route, mode)

    def get_sidebar_routes(self, ctx: BrandContext) -> list[SidebarRouteDef]:
        """EP-6 dispatch — SIGNATURE-ONLY v0.1.0."""
        raise NotImplementedError(
            "EP-6 sidebar_routes_register is signature-only in v0.1.0; semantic dispatch deferred v0.2.x"
        )

    def extractor_register(
        self,
        extractor: ExtractorDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-7 — Register an extractor. Signature-only v0.1.0."""
        self._register("EP-7", extractor.name, extractor, mode)

    def dispatch_extractor(self, name: str, ctx: BrandContext) -> Any:
        """EP-7 dispatch — SIGNATURE-ONLY v0.1.0."""
        raise NotImplementedError(
            "EP-7 extractor_register is signature-only in v0.1.0; semantic dispatch deferred v0.2.x"
        )

    def channel_adapter_register(
        self,
        adapter: ChannelAdapterDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-8 — Register a channel adapter (sales_agent + copilot + vertical agents).

        Signature-only v0.1.0.
        """
        self._register("EP-8", adapter.channel_slug, adapter, mode)

    def dispatch_channel_adapter(self, channel_slug: str, ctx: BrandContext) -> Any:
        """EP-8 dispatch — SIGNATURE-ONLY v0.1.0."""
        raise NotImplementedError(
            "EP-8 channel_adapter_register is signature-only in v0.1.0; semantic dispatch deferred v0.2.x"
        )

    def metric_register(
        self,
        metric: MetricDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-9 — Register a metric. Signature-only v0.1.0."""
        self._register("EP-9", metric.name, metric, mode)

    def dispatch_metric(self, name: str, ctx: BrandContext) -> Any:
        """EP-9 dispatch — SIGNATURE-ONLY v0.1.0."""
        raise NotImplementedError("EP-9 metric_register is signature-only in v0.1.0; semantic dispatch deferred v0.2.x")

    def landing_template_register(
        self,
        template: LandingTemplateDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-10 — Register a landing template. Signature-only v0.1.0."""
        self._register("EP-10", template.template_id, template, mode)

    def dispatch_landing_template(self, template_id: str, ctx: BrandContext) -> Any:
        """EP-10 dispatch — SIGNATURE-ONLY v0.1.0."""
        raise NotImplementedError(
            "EP-10 landing_template_register is signature-only in v0.1.0; semantic dispatch deferred v0.2.x"
        )

    def campaign_template_register(
        self,
        template: CampaignTemplateDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-11 — Register a campaign template. Signature-only v0.1.0."""
        self._register("EP-11", template.template_id, template, mode)

    def dispatch_campaign_template(self, template_id: str, ctx: BrandContext) -> Any:
        """EP-11 dispatch — SIGNATURE-ONLY v0.1.0."""
        raise NotImplementedError(
            "EP-11 campaign_template_register is signature-only in v0.1.0; semantic dispatch deferred v0.2.x"
        )

    def asset_template_register(
        self,
        template: AssetTemplateDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-12 — Register an asset template. Signature-only v0.1.0."""
        self._register("EP-12", template.template_id, template, mode)

    def dispatch_asset_template(self, template_id: str, ctx: BrandContext) -> Any:
        """EP-12 dispatch — SIGNATURE-ONLY v0.1.0."""
        raise NotImplementedError(
            "EP-12 asset_template_register is signature-only in v0.1.0; semantic dispatch deferred v0.2.x"
        )

    def sales_agent_guardrail_register(
        self,
        guardrail: GuardrailDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-13 — Register a sales agent guardrail (pre_send + pre_receive).

        Signature-only v0.1.0.
        """
        self._register("EP-13", guardrail.name, guardrail, mode)

    def dispatch_guardrail(
        self,
        name: str,
        message: str,
        ctx: BrandContext,
        *,
        phase: Literal["send", "receive"],
    ) -> Any:
        """EP-13 dispatch — SIGNATURE-ONLY v0.1.0."""
        raise NotImplementedError(
            "EP-13 sales_agent_guardrail_register is signature-only in v0.1.0; semantic dispatch deferred v0.2.x"
        )

    def copilot_kb_pack_register(
        self,
        pack: KbPackDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-14 — Register a copilot KB pack (tenant_scope: brand|tenant|both).

        Signature-only v0.1.0.
        """
        self._register("EP-14", pack.pack_id, pack, mode)

    def dispatch_kb_pack(self, pack_id: str, ctx: BrandContext) -> Any:
        """EP-14 dispatch — SIGNATURE-ONLY v0.1.0."""
        raise NotImplementedError(
            "EP-14 copilot_kb_pack_register is signature-only in v0.1.0; semantic dispatch deferred v0.2.x"
        )

    def crm_lifecycle_stage_register(
        self,
        stage: LifecycleStageDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-15 — Register a CRM lifecycle stage (insert-between). Signature-only v0.1.0."""
        self._register("EP-15", stage.stage_id, stage, mode)

    def dispatch_lifecycle_transition(self, stage_id: str, ctx: BrandContext) -> Any:
        """EP-15 dispatch — SIGNATURE-ONLY v0.1.0."""
        raise NotImplementedError(
            "EP-15 crm_lifecycle_stage_register is signature-only in v0.1.0; semantic dispatch deferred v0.2.x"
        )

    def iam_signup_handler(
        self,
        handler: Callable[[Any, BrandContext], SignupResult],
        *,
        name: str,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-16 — Register an IAM signup handler. Signature-only v0.1.0."""
        self._register("EP-16", name, handler, mode)

    def dispatch_signup(self, clerk_user: Any, ctx: BrandContext) -> SignupResult:
        """EP-16 dispatch — SIGNATURE-ONLY v0.1.0."""
        raise NotImplementedError(
            "EP-16 iam_signup_handler is signature-only in v0.1.0; semantic dispatch deferred v0.2.x"
        )

    def tenant_plan_tier_register(
        self,
        tier: PlanTierDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-17 — Register a tenant plan tier (override permitted). Signature-only v0.1.0."""
        self._register("EP-17", tier.tier_id, tier, mode)

    def dispatch_plan_tiers(self, ctx: BrandContext) -> list[PlanTierDef]:
        """EP-17 dispatch — SIGNATURE-ONLY v0.1.0."""
        raise NotImplementedError(
            "EP-17 tenant_plan_tier_register is signature-only in v0.1.0; semantic dispatch deferred v0.2.x"
        )

    def onboarding_wizard_steps_register(
        self,
        step: WizardStepDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-18 — Register an onboarding wizard step (override permitted). Signature-only v0.1.0."""
        self._register("EP-18", step.step_id, step, mode)

    def dispatch_wizard_steps(self, ctx: BrandContext) -> list[WizardStepDef]:
        """EP-18 dispatch — SIGNATURE-ONLY v0.1.0."""
        raise NotImplementedError(
            "EP-18 onboarding_wizard_steps_register is signature-only in v0.1.0; semantic dispatch deferred v0.2.x"
        )

    # ─── introspection ──────────────────────────────────────────────

    def get_all(self, ep_id: str) -> list[_Registration]:
        """Return all registrations for a given EP. Test-only API."""
        if ep_id not in self._registrations:
            raise ValueError(f"Unknown EP id: {ep_id}")
        return list(self._registrations[ep_id])

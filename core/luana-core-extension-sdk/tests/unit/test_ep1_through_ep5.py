"""V-F-sdk-2 — EP-1..EP-5 critical EPs EXECUTABLE.

Per 01-spec §5.2 scenarios B1-B5 + 06-tickets.yaml T-5 + 03-arch-be.md §1.3 step 4.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from luana_core_extension_sdk import (
    BookingPolicy,
    BookingResult,
    BrandContext,
    ExtensionPointRegistry,
    FieldDef,
    FieldOverride,
    PresetPack,
    ToolDef,
    WorkflowDef,
)


def _make_ctx(brand: str = "test-brand", vertical: str = "marketing") -> BrandContext:
    """Helper — minimal BrandContext for tests."""
    return BrandContext(
        tenant_id=uuid4(),
        brand_slug=brand,  # type: ignore[arg-type]
        plan_tier="free",
        locale="es-AR",
        feature_flags={},
        tenant_profile_id=uuid4(),
        vertical_kind=vertical,  # type: ignore[arg-type]
        compliance_flags={},
        pii_policy="standard",
    )


# ─────────────────────────────────────────────────────────────────────
# B1 — EP-1 field_override (Callable handler returning Optional[FieldOverride])
# ─────────────────────────────────────────────────────────────────────


def test_ep1_field_override_register_succeeds() -> None:
    r = ExtensionPointRegistry()

    def handler(field: FieldDef, ctx: BrandContext) -> FieldOverride | None:
        if field.name == "consent_text":
            return FieldOverride(name="consent_text", default_value="Acepto.", required=True)
        return None

    r.field_override(handler, name="test-brand.consent_handler")
    assert len(r.get_all("EP-1")) == 1


def test_ep1_resolve_returns_first_non_none() -> None:
    """First non-None wins by registration order (deterministic)."""
    r = ExtensionPointRegistry()

    def handler_a(field: FieldDef, ctx: BrandContext) -> FieldOverride | None:
        return None  # Always abstains

    def handler_b(field: FieldDef, ctx: BrandContext) -> FieldOverride | None:
        return FieldOverride(name="x", default_value="B")

    def handler_c(field: FieldDef, ctx: BrandContext) -> FieldOverride | None:
        return FieldOverride(name="x", default_value="C")

    r.field_override(handler_a, name="test-brand.h_a")
    r.field_override(handler_b, name="test-brand.h_b")
    r.field_override(handler_c, name="test-brand.h_c")

    field = FieldDef(name="x", type_name="str")
    ctx = _make_ctx()
    result = r.resolve_field_override(field, ctx)
    assert result is not None
    assert result.default_value == "B"  # B wins by order


def test_ep1_resolve_returns_none_when_no_handlers_match() -> None:
    r = ExtensionPointRegistry()

    def abstain(field: FieldDef, ctx: BrandContext) -> FieldOverride | None:
        return None

    r.field_override(abstain, name="test-brand.abstain")
    result = r.resolve_field_override(FieldDef(name="x", type_name="str"), _make_ctx())
    assert result is None


# ─────────────────────────────────────────────────────────────────────
# B2 — EP-2 offer_preset_pack_register
# ─────────────────────────────────────────────────────────────────────


def test_ep2_offer_preset_pack_register_and_filter_by_brand() -> None:
    r = ExtensionPointRegistry()

    pack_a = PresetPack(
        name="test-brand.starter_pack",
        presets=({"k": "v"},),
        applies_to_brand="test-brand",
    )
    pack_b = PresetPack(
        name="vitalia.medical_pack",
        presets=({"k": "v"},),
        applies_to_brand="vitalia",
    )
    r.offer_preset_pack_register(pack_a)
    r.offer_preset_pack_register(pack_b)

    # Filter by test-brand ctx
    ctx_tb = _make_ctx(brand="test-brand")
    packs_tb = r.list_offer_preset_packs(ctx_tb)
    assert len(packs_tb) == 1
    assert packs_tb[0].name == "test-brand.starter_pack"

    # Filter by vitalia ctx
    ctx_v = _make_ctx(brand="vitalia", vertical="medical")
    packs_v = r.list_offer_preset_packs(ctx_v)
    assert len(packs_v) == 1
    assert packs_v[0].name == "vitalia.medical_pack"


# ─────────────────────────────────────────────────────────────────────
# B3 — EP-3 sales_agent_tool_register (adapter delegation)
# ─────────────────────────────────────────────────────────────────────


def test_ep3_sales_agent_tool_register_succeeds_without_adapter() -> None:
    """Adapter None → registration succeeds, SDK-side store only."""
    r = ExtensionPointRegistry()  # No adapter

    tool = ToolDef(
        name="test-brand.echo_tool",
        description="Echo tool",
        input_schema={"type": "object"},
        handler=lambda: None,
    )
    r.sales_agent_tool_register(tool)

    assert len(r.get_all("EP-3")) == 1
    retrieved = r.get_sales_agent_tool("test-brand.echo_tool")
    assert retrieved is not None
    assert retrieved.description == "Echo tool"


def test_ep3_sales_agent_tool_register_with_adapter_delegates() -> None:
    """Adapter not None → register_extension_tool called."""

    class FakeAdapter:
        def __init__(self) -> None:
            self.calls: list = []

        def register_extension_tool(self, tool: ToolDef) -> None:
            self.calls.append(tool)

    fake = FakeAdapter()
    r = ExtensionPointRegistry(sales_agent_tool_registry_adapter=fake)

    tool = ToolDef(
        name="test-brand.search_tool",
        description="Search",
        input_schema={},
        handler=lambda: None,
    )
    r.sales_agent_tool_register(tool)

    assert len(fake.calls) == 1
    assert fake.calls[0].name == "test-brand.search_tool"


def test_ep3_get_returns_none_when_absent() -> None:
    r = ExtensionPointRegistry()
    assert r.get_sales_agent_tool("test-brand.never_registered") is None


# ─────────────────────────────────────────────────────────────────────
# B4 — EP-4 copilot_workflow_register (adapter delegation)
# ─────────────────────────────────────────────────────────────────────


def test_ep4_copilot_workflow_register_succeeds_without_adapter() -> None:
    r = ExtensionPointRegistry()

    wf = WorkflowDef(
        name="test-brand.simple_workflow",
        description="Simple",
        steps=(),
    )
    r.copilot_workflow_register(wf)

    assert len(r.get_all("EP-4")) == 1
    retrieved = r.get_copilot_workflow("test-brand.simple_workflow")
    assert retrieved is not None


def test_ep4_copilot_workflow_register_with_adapter_delegates() -> None:
    class FakeAdapter:
        def __init__(self) -> None:
            self.calls: list = []

        def register_extension_workflow(self, workflow: WorkflowDef) -> None:
            self.calls.append(workflow)

    fake = FakeAdapter()
    r = ExtensionPointRegistry(copilot_workflow_registry_adapter=fake)

    wf = WorkflowDef(name="test-brand.wf", description="x", steps=())
    r.copilot_workflow_register(wf)

    assert len(fake.calls) == 1
    assert fake.calls[0].name == "test-brand.wf"


# ─────────────────────────────────────────────────────────────────────
# B5 — EP-5 scheduling_booking_policy_register
# ─────────────────────────────────────────────────────────────────────


def test_ep5_scheduling_booking_policy_register_and_dispatch() -> None:
    r = ExtensionPointRegistry()

    def can_confirm(slot: object, ctx: BrandContext) -> BookingResult:
        return BookingResult(allowed=True)

    policy = BookingPolicy(
        name="test-brand.always_allow",
        can_confirm=can_confirm,
        priority=100,
    )
    r.scheduling_booking_policy_register(policy)

    retrieved = r.get_booking_policy("test-brand.always_allow")
    assert retrieved is not None
    assert retrieved.priority == 100

    result = retrieved.can_confirm(object(), _make_ctx())
    assert result.allowed is True


def test_ep5_get_returns_none_when_absent() -> None:
    r = ExtensionPointRegistry()
    assert r.get_booking_policy("test-brand.unknown") is None


# ─────────────────────────────────────────────────────────────────────
# Adapter graceful contract (NotImplementedError when public method missing)
# ─────────────────────────────────────────────────────────────────────


def test_ep3_adapter_raises_not_implemented_on_missing_method() -> None:
    """V-AG-new-story-8 — adapter raises gracefully when inner registry lacks public API."""
    from luana_core_extension_sdk._adapters import _SalesAgentToolRegistryAdapter

    class FakeInner:
        """No register_tool_from_extension method."""

    adapter = _SalesAgentToolRegistryAdapter(FakeInner())
    r = ExtensionPointRegistry(sales_agent_tool_registry_adapter=adapter)

    tool = ToolDef(name="test-brand.t", description="x", input_schema={}, handler=lambda: None)
    with pytest.raises(NotImplementedError, match="Story 7 ToolRegistry"):
        r.sales_agent_tool_register(tool)


def test_ep4_adapter_raises_not_implemented_on_missing_method() -> None:
    from luana_core_extension_sdk._adapters import _CopilotWorkflowRegistryAdapter

    class FakeInner:
        pass

    adapter = _CopilotWorkflowRegistryAdapter(FakeInner())
    r = ExtensionPointRegistry(copilot_workflow_registry_adapter=adapter)

    wf = WorkflowDef(name="test-brand.w", description="x", steps=())
    with pytest.raises(NotImplementedError, match="Story 6 WorkflowRegistry"):
        r.copilot_workflow_register(wf)

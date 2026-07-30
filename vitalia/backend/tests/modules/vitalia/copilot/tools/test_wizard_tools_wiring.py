"""T-onboarding-4 — Valeria wizard tools wiring smoke + cost canonicalization regression.

R23 OPT-OUT RATIFIED: tools + graph shipped APPROVED in copilot-tools-impl story.
This ticket is wire-up verification + regression only (NOT new agentic production code).
Owner eligibility: [qwen-opencode, claude-sonnet] OK per Chris 2026-05-18.

Covers 6 assertions:
  1. test_4_tools_registered_via_ep3 — extensions.py EP-3 registers each of the 4
     tools with tool_groups containing at least one of ("wizard", "copilot", "onboarding",
     "personality_preview").
  2. test_extract_tenant_context_tool_signature — @tool decorator + args_schema +
     tenant_id field present in ExtractTenantContextInput.
  3. test_confirm_slot_tool_signature — same pattern.
  4. test_simulate_personality_tool_signature — same pattern.
  5. test_complete_onboarding_tool_signature — same pattern.
  6. test_cost_canonicalization_regression — cost_recorder._stash + pop_cost returns
     non-None Decimal (PI-12 S1 T-1 regression guard: mock litellm_call_id bridge).

downstream-regression-na: brand-local vitalia copilot tools smoke (no engine pattern,
no cross-brand mirror — tools are Valeria wizard brand-extension per extensions.py lines 351-456)
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

# ─── constants ─────────────────────────────────────────────────────────────────

_WIZARD_TOOL_GROUPS = frozenset({"wizard", "copilot", "onboarding", "personality_preview"})

_TOOL_NAMES = frozenset(
    {
        "vitalia.extract_tenant_context",
        "vitalia.confirm_slot",
        "vitalia.simulate_personality",
        "vitalia.complete_onboarding",
    }
)


# ─── Test 1: EP-3 registration smoke ──────────────────────────────────────────


def test_4_tools_registered_via_ep3() -> None:
    """EP-3 registers all 4 Valeria wizard tools in extensions.py (lines 351-456).

    Verification strategy: instantiate a fresh ExtensionPointRegistry, call
    register_all(), then use get_sales_agent_tool() to retrieve each ToolDef
    and confirm tool_groups intersects _WIZARD_TOOL_GROUPS.
    """
    from luana_core_extension_sdk import ExtensionPointRegistry

    from src.modules.vitalia.extensions import register_all

    registry = ExtensionPointRegistry(
        sales_agent_tool_registry_adapter=None,
        copilot_workflow_registry_adapter=None,
    )
    register_all(registry)

    for tool_name in _TOOL_NAMES:
        tool_def = registry.get_sales_agent_tool(tool_name)
        assert tool_def is not None, (
            f"Tool {tool_name!r} not found in EP-3 registry via get_sales_agent_tool(). "
            f"Check extensions.py lines 351-456."
        )
        tool_groups = set(getattr(tool_def, "tool_groups", ()) or ())
        assert tool_groups & _WIZARD_TOOL_GROUPS, (
            f"Tool {tool_name!r} has no wizard/copilot/onboarding group. Got: {tool_groups}"
        )


# ─── Test 2-5: tool signatures ─────────────────────────────────────────────────


def test_extract_tenant_context_tool_signature() -> None:
    """extract_tenant_context: @tool decorated + args_schema + tenant_id field."""
    from langchain_core.tools import BaseTool

    from src.modules.vitalia.copilot.tools.extract_tenant_context import (
        ExtractTenantContextInput,
        extract_tenant_context,
    )

    # Must be a LangChain tool (decorated with @tool)
    assert isinstance(extract_tenant_context, BaseTool), (
        "extract_tenant_context must be a LangChain BaseTool (@tool decorated)"
    )
    # args_schema must be the declared Pydantic model
    assert extract_tenant_context.args_schema is ExtractTenantContextInput, (
        "args_schema must be ExtractTenantContextInput"
    )
    # tenant_id field mandatory (HIPAA-lite tenant isolation cardinal)
    schema_fields = ExtractTenantContextInput.model_fields
    assert "tenant_id" in schema_fields, "tenant_id field must be in ExtractTenantContextInput"
    assert schema_fields["tenant_id"].is_required(), "tenant_id must be required (no default)"


def test_confirm_slot_tool_signature() -> None:
    """confirm_slot: @tool decorated + args_schema + tenant_id field."""
    from langchain_core.tools import BaseTool

    from src.modules.vitalia.copilot.tools.confirm_slot import (
        ConfirmSlotInput,
        confirm_slot,
    )

    assert isinstance(confirm_slot, BaseTool), "confirm_slot must be a LangChain BaseTool (@tool decorated)"
    assert confirm_slot.args_schema is ConfirmSlotInput, "args_schema must be ConfirmSlotInput"
    schema_fields = ConfirmSlotInput.model_fields
    assert "tenant_id" in schema_fields, "tenant_id field must be in ConfirmSlotInput"
    assert schema_fields["tenant_id"].is_required(), "tenant_id must be required"
    # slot_id also mandatory per design
    assert "slot_id" in schema_fields, "slot_id field must be in ConfirmSlotInput"


def test_simulate_personality_tool_signature() -> None:
    """simulate_personality: @tool decorated + args_schema + tenant_id field."""
    from langchain_core.tools import BaseTool

    from src.modules.vitalia.copilot.tools.simulate_personality import (
        SimulatePersonalityInput,
        simulate_personality,
    )

    assert isinstance(simulate_personality, BaseTool), (
        "simulate_personality must be a LangChain BaseTool (@tool decorated)"
    )
    assert simulate_personality.args_schema is SimulatePersonalityInput, "args_schema must be SimulatePersonalityInput"
    schema_fields = SimulatePersonalityInput.model_fields
    assert "tenant_id" in schema_fields, "tenant_id field must be in SimulatePersonalityInput"
    assert schema_fields["tenant_id"].is_required(), "tenant_id must be required"


def test_complete_onboarding_tool_signature() -> None:
    """complete_onboarding: @tool decorated + args_schema + tenant_id + user_id fields."""
    from langchain_core.tools import BaseTool

    from src.modules.vitalia.copilot.tools.complete_onboarding import (
        CompleteOnboardingInput,
        complete_onboarding,
    )

    assert isinstance(complete_onboarding, BaseTool), (
        "complete_onboarding must be a LangChain BaseTool (@tool decorated)"
    )
    assert complete_onboarding.args_schema is CompleteOnboardingInput, "args_schema must be CompleteOnboardingInput"
    schema_fields = CompleteOnboardingInput.model_fields
    assert "tenant_id" in schema_fields, "tenant_id field must be in CompleteOnboardingInput"
    assert schema_fields["tenant_id"].is_required(), "tenant_id must be required"
    # user_id also mandatory per complete_onboarding contract
    assert "user_id" in schema_fields, "user_id field must be in CompleteOnboardingInput"
    assert schema_fields["user_id"].is_required(), "user_id must be required"


# ─── Test 6: cost canonicalization regression (PI-12 S1 T-1 guard) ─────────────


def test_cost_canonicalization_regression() -> None:
    """cost_recorder.pop_cost returns non-None Decimal when litellm_call_id bridged.

    PI-12 S1 T-1 regression: test fixtures missing litellm_call_id in mock
    response_metadata caused pop_cost(litellm_call_id) to return None →
    cost_usd=None → assertion failures in observability suite.

    This test verifies the bridge contract directly:
      1. Stash a cost with a known call_id via _stash().
      2. pop_cost(call_id) returns a non-None Decimal (>= 0).
      3. Second pop returns None (single-use drain invariant).

    Does NOT invoke actual LangChain/LiteLLM callbacks — tests the
    cost_recorder module contract in isolation.
    """
    from luana_core_observability.recording.cost_recorder import (
        _stash,  # noqa: PLC2701
        pop_cost,
    )

    call_id = str(uuid4())
    cost_value = Decimal("0.00423")

    # Precondition: no entry for this call_id
    assert pop_cost(call_id) is None, "Fresh call_id must have no stashed cost"

    # Stash a cost (simulates CostRecorderCustomLogger.log_success_event firing)
    _stash(call_id, cost_value)

    # pop_cost must return the stashed Decimal (non-None, >= 0)
    result = pop_cost(call_id)
    assert result is not None, (
        "pop_cost returned None after _stash — "
        "PI-12 S1 T-1 regression: litellm_call_id bridge not working. "
        "Check that CostRecorderCustomLogger fires before LangChain on_llm_end."
    )
    assert isinstance(result, Decimal), f"Expected Decimal, got {type(result)}"
    assert result >= Decimal("0"), f"Cost must be non-negative, got {result}"
    assert result == cost_value, f"Expected {cost_value}, got {result}"

    # Single-use drain: second pop returns None
    assert pop_cost(call_id) is None, "Second pop must return None (single-use drain)"

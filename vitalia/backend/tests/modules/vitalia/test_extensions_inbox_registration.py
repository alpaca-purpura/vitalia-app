"""T-inbox-be-6 — verify vitalia.retract_last_message registered in EP-3.

Story vitalia-slice-1-inbox T-inbox-be-6.

Per 03-arch-agentic.md § 2 + 06-tickets.yaml::T-inbox-be-6.

Verifies that the Extension SDK EP-3 registration of ``retract_last_message``
tool in ``extensions.py::register_all`` is:

1. Present in the registry after ``register_all`` runs.
2. Named with the ``vitalia.`` CC-4 namespace prefix.
3. Has a callable/invocable handler (LangChain StructuredTool — has ``ainvoke``).
4. Input schema includes both ``tenant_id`` and ``clinic_id`` (HIPAA-lite dual
   filter cardinal per ``.claude/rules/hipaa-lite.md § Regla cardinal``).
5. Input schema requires all 5 mandatory fields (tenant_id, clinic_id,
   conversation_id, message_id, reason).
6. Belongs to ``"inbox"`` tool_group (link to inbox slice).
7. Belongs to ``"sales_agent"`` tool_group (dispatch surface).
8. Does NOT appear in the copilot tool set (Adrián-only retraction logic).

TDD RED→GREEN contract:
  - Tests written FIRST (T-inbox-be-6 TDD step 1: RED).
  - GREEN: extensions.py extended with retract_last_message ToolDef.
  - These tests FAIL until GREEN implementation lands.

downstream-regression-na: vitalia-brand-local EP-3 registration test.
  Downstream: vitalia/backend/tests/test_extensions.py (Part B wave_3_real
  subset) + vitalia/backend/tests/architecture/test_extension_sdk_registration.py
  (EXPECTED_EP3_TOOLS baseline subset). Neither breaks — baseline checks
  subset presence, NOT exhaustive enumeration.
"""

from __future__ import annotations

from luana_core_extension_sdk import ExtensionPointRegistry, ToolDef

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_registry() -> ExtensionPointRegistry:
    """Build a fresh registry with all Vitalia extensions registered."""
    from src.modules.vitalia.extensions import register_all

    reg = ExtensionPointRegistry()
    register_all(reg)
    return reg


def _ep3_tool_defs(registry: ExtensionPointRegistry) -> list[ToolDef]:
    """Return all EP-3 ToolDef payloads registered by Vitalia."""
    records = registry.get_all("EP-3")
    return [r.payload for r in records]


def _ep3_names(registry: ExtensionPointRegistry) -> set[str]:
    """Return the set of all EP-3 registered tool names."""
    return {r.name for r in registry.get_all("EP-3")}


def _find_retract_tool(registry: ExtensionPointRegistry) -> ToolDef | None:
    """Return the ToolDef for vitalia.retract_last_message, or None."""
    for r in registry.get_all("EP-3"):
        if r.name == "vitalia.retract_last_message":
            return r.payload
    return None


# ── Tests ────────────────────────────────────────────────────────────────────


class TestRetractLastMessageRegistration:
    """EP-3 registration checks for vitalia.retract_last_message."""

    def test_tool_is_registered(self) -> None:
        """vitalia.retract_last_message must appear in EP-3 registry post register_all."""
        registry = _make_registry()
        retract_tool = _find_retract_tool(registry)
        assert retract_tool is not None, (
            "vitalia.retract_last_message not found in EP-3 registry. "
            "extensions.py must call registry.sales_agent_tool_register("
            "ToolDef(name='vitalia.retract_last_message', ...))."
        )

    def test_name_has_vitalia_namespace(self) -> None:
        """Tool name must carry CC-4 'vitalia.' prefix."""
        registry = _make_registry()
        names = _ep3_names(registry)
        assert "vitalia.retract_last_message" in names, (
            f"'vitalia.retract_last_message' not found in EP-3 names: {names}"
        )

    def test_handler_is_invocable(self) -> None:
        """Handler must be a LangChain StructuredTool (has ainvoke) or callable."""
        registry = _make_registry()
        retract_tool = _find_retract_tool(registry)
        assert retract_tool is not None, "vitalia.retract_last_message not registered"
        handler = retract_tool.handler
        assert callable(handler) or hasattr(handler, "ainvoke"), (
            f"Handler must be callable or have ainvoke (LangChain @tool). Got: {type(handler)}"
        )

    def test_input_schema_has_tenant_id(self) -> None:
        """input_schema must declare tenant_id (root isolation)."""
        registry = _make_registry()
        retract_tool = _find_retract_tool(registry)
        assert retract_tool is not None, "vitalia.retract_last_message not registered"
        props = retract_tool.input_schema.get("properties", {})
        assert "tenant_id" in props, (
            "input_schema missing 'tenant_id'. Tenant isolation is mandatory for all EP-3 tools."
        )

    def test_input_schema_has_clinic_id(self) -> None:
        """input_schema must declare clinic_id (HIPAA-lite dual filter cardinal)."""
        registry = _make_registry()
        retract_tool = _find_retract_tool(registry)
        assert retract_tool is not None, "vitalia.retract_last_message not registered"
        props = retract_tool.input_schema.get("properties", {})
        assert "clinic_id" in props, (
            "input_schema missing 'clinic_id'. "
            "HIPAA-lite dual filter (tenant_id + clinic_id) is mandatory for PHI-touching tools "
            "(per .claude/rules/hipaa-lite.md § Regla cardinal)."
        )

    def test_input_schema_required_fields(self) -> None:
        """All 5 mandatory fields must be in input_schema 'required' list."""
        registry = _make_registry()
        retract_tool = _find_retract_tool(registry)
        assert retract_tool is not None, "vitalia.retract_last_message not registered"
        required = set(retract_tool.input_schema.get("required", []))
        expected_required = {
            "tenant_id",
            "clinic_id",
            "conversation_id",
            "message_id",
            "reason",
        }
        missing = expected_required - required
        assert not missing, f"input_schema 'required' missing fields: {missing}. Got required: {required}"

    def test_input_schema_reason_has_length_bounds(self) -> None:
        """reason field must have minLength=10 + maxLength=500 (audit log mandate + PII containment)."""
        registry = _make_registry()
        retract_tool = _find_retract_tool(registry)
        assert retract_tool is not None, "vitalia.retract_last_message not registered"
        props = retract_tool.input_schema.get("properties", {})
        reason_schema = props.get("reason", {})
        assert reason_schema.get("minLength") == 10, (
            f"reason.minLength must be 10 (non-trivial justification). Got: {reason_schema.get('minLength')}"
        )
        assert reason_schema.get("maxLength") == 500, (
            f"reason.maxLength must be 500 (PII surface containment). Got: {reason_schema.get('maxLength')}"
        )

    def test_tool_groups_include_inbox(self) -> None:
        """tool_groups must include 'inbox' (links tool to inbox slice for dispatch routing)."""
        registry = _make_registry()
        retract_tool = _find_retract_tool(registry)
        assert retract_tool is not None, "vitalia.retract_last_message not registered"
        groups = retract_tool.tool_groups
        assert "inbox" in groups, (
            f"'inbox' group missing from tool_groups. Got: {groups}. "
            "retract_last_message belongs to the inbox slice (T-inbox-agentic-1)."
        )

    def test_tool_groups_include_sales_agent(self) -> None:
        """tool_groups must include 'sales_agent' (dispatch surface — Adrián only)."""
        registry = _make_registry()
        retract_tool = _find_retract_tool(registry)
        assert retract_tool is not None, "vitalia.retract_last_message not registered"
        groups = retract_tool.tool_groups
        assert "sales_agent" in groups, f"'sales_agent' group missing from tool_groups. Got: {groups}."

    def test_tool_groups_include_retract(self) -> None:
        """tool_groups must include 'retract' (semantic tag for this action type)."""
        registry = _make_registry()
        retract_tool = _find_retract_tool(registry)
        assert retract_tool is not None, "vitalia.retract_last_message not registered"
        groups = retract_tool.tool_groups
        assert "retract" in groups, f"'retract' group missing from tool_groups. Got: {groups}."

    def test_description_is_non_empty(self) -> None:
        """Tool description must be non-empty (required for Adrián LLM reasoning)."""
        registry = _make_registry()
        retract_tool = _find_retract_tool(registry)
        assert retract_tool is not None, "vitalia.retract_last_message not registered"
        desc = retract_tool.description or ""
        assert len(desc.strip()) > 20, (
            f"description is too short or empty. Got: {desc!r}. "
            "Adrián needs a meaningful description to decide when to invoke this tool."
        )

    def test_retract_not_in_copilot_tools(self) -> None:
        """retract_last_message must NOT appear in Valeria (copilot) tool groups.

        Retraction is Adrián-only (sales_agent). Valeria never sends messages
        that require retraction (copilot is read-only in this context).
        """
        registry = _make_registry()
        ep3_tools = _ep3_tool_defs(registry)
        copilot_retract_tools = [
            t for t in ep3_tools if "copilot" in (t.tool_groups or ()) and "retract_last_message" in (t.name or "")
        ]
        assert not copilot_retract_tools, (
            "retract_last_message found in copilot tool_groups. Retraction is Adrián (sales_agent) only."
        )


class TestRetractRegistrationIdempotency:
    """Idempotency: registry tracks the tool after register_all."""

    def test_tool_present_after_register_all(self) -> None:
        """vitalia.retract_last_message is retrievable via get_sales_agent_tool."""
        registry = _make_registry()
        tool_def = registry.get_sales_agent_tool("vitalia.retract_last_message")
        assert tool_def is not None, (
            "registry.get_sales_agent_tool('vitalia.retract_last_message') returned None. "
            "Tool must be registered via registry.sales_agent_tool_register(ToolDef(...))."
        )

    def test_ep3_total_count_includes_retract(self) -> None:
        """EP-3 total registration count must be ≥12 (11 prior + retract_last_message)."""
        registry = _make_registry()
        records = registry.get_all("EP-3")
        count = len(records)
        assert count >= 12, (
            f"Expected ≥12 EP-3 ToolDefs after T-inbox-be-6, got {count}. "
            "Prior tools: 4 T-infra-2 baseline + 4 Valeria + 3 Adrián MVP + 1 fidelización = 12."
        )

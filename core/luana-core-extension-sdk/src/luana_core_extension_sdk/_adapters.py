"""Internal adapter classes wrapping Stories 6+7 frozen registries (D-T1 byte-stable).

These adapters are CONSTRUCTED at FastAPI lifespan by brand app composition root.
They thin-wrap the frozen registry to expose ONLY public read methods to the SDK.
Mutation surface (private dispatch internals) NOT exposed via SDK.

V-AG-3 Story 6 + Story 7 golden snapshots verify registry public API surface
unchanged post Story 8 — adapters consume only public methods.

Per architect 03-arch-be.md §1.4 verbatim + 06-tickets.yaml T-6 + outcome §7.5.3.

Module-leading underscore signals "internal" — public surface lives behind
ExtensionPointRegistry adapter args (sales_agent_tool_registry_adapter +
copilot_workflow_registry_adapter).

Current state (Story 8 v0.1.0):
- Story 6 WorkflowRegistry exposes `collect_workflows` function (no class-bound public
  register_workflow_from_extension method).
- Story 7 ToolRegistry exposes `get_tools_for_stage` function (no class-bound public
  register_tool_from_extension method).

Adapter raises NotImplementedError gracefully when wrapped registry lacks the
required public register-from-extension method. Stories 11-13 brand bootstraps
wire real adapter instances when Stories 6+7 expose the public surface.

For Story 8 test-brand smoke pack: inject None for both adapter args. EP-3 +
EP-4 register in SDK side ONLY. Smoke tests verify EP-3/EP-4 record DataClass
correctly + adapter wiring is None (not raises).
"""

from __future__ import annotations

from typing import Any

from luana_core_extension_sdk.models import ToolDef, WorkflowDef


class _SalesAgentToolRegistryAdapter:
    """Wraps luana_core_sales_agent.application.tools.registry.ToolRegistry.

    READ-ONLY delegation. NEVER calls private dispatch / state-mutation methods.
    Story 7 V-AG-3 golden snapshot test fails build if adapter touches private surface.

    Adapter is constructed by brand app composition root at FastAPI lifespan
    startup (Stories 11-13). For Story 8 test-brand smoke pack, this class is
    only exercised via fake registries in tests/unit/test_adapters_read_only.py.
    """

    def __init__(self, tool_registry: Any) -> None:
        """Store reference to Story 7 ToolRegistry instance (duck-typed).

        No I/O performed at construction — pure reference assignment.
        Adapter does NOT introspect inner state; lazy validation deferred to
        register_extension_tool() invocation.
        """
        self._inner = tool_registry

    def register_extension_tool(self, tool: ToolDef) -> None:
        """Delegate to Story 7 ToolRegistry public register API.

        Calls `register_tool_from_extension(name, handler, description, input_schema,
        tool_groups)` on inner registry IF that method exists. If absent, raise
        NotImplementedError — Stories 11-13 brand bootstraps add the public surface
        when wiring real adapters.

        Read-only contract:
        - NEVER reads or writes inner._private attributes
        - NEVER calls dispatch_/mutate_/internal_ methods on inner
        - ONLY delegates kwargs to register_tool_from_extension public method
        """
        if not hasattr(self._inner, "register_tool_from_extension"):
            raise NotImplementedError(
                "Story 7 ToolRegistry lacks public `register_tool_from_extension` method. "
                "Story 8 EP-3 wrapper requires this surface. "
                "Stories 11-13 brand bootstraps add the public method when wiring real adapters."
            )
        self._inner.register_tool_from_extension(
            name=tool.name,
            handler=tool.handler,
            description=tool.description,
            input_schema=tool.input_schema,
            tool_groups=tool.tool_groups,
        )


class _CopilotWorkflowRegistryAdapter:
    """Wraps luana_core_copilot.application.workflows.engine.WorkflowRegistry.

    READ-ONLY delegation. Same invariants as ToolRegistryAdapter.
    Story 6 V-AG-3 golden snapshot test (test_copilot_registry_contracts_stable.py)
    fails build if adapter touches private surface.
    """

    def __init__(self, workflow_registry: Any) -> None:
        """Store reference to Story 6 WorkflowRegistry instance (duck-typed)."""
        self._inner = workflow_registry

    def register_extension_workflow(self, workflow: WorkflowDef) -> None:
        """Delegate to Story 6 WorkflowRegistry public register API.

        Raises NotImplementedError when inner lacks register_workflow_from_extension.
        Stories 11-13 brand bootstraps will add the public method.
        """
        if not hasattr(self._inner, "register_workflow_from_extension"):
            raise NotImplementedError(
                "Story 6 WorkflowRegistry lacks public `register_workflow_from_extension` method. "
                "Story 8 EP-4 wrapper requires this surface. "
                "Stories 11-13 brand bootstraps add the public method when wiring real adapters."
            )
        self._inner.register_workflow_from_extension(
            name=workflow.name,
            steps=workflow.steps,
            description=workflow.description,
            trigger_event=workflow.trigger_event,
        )

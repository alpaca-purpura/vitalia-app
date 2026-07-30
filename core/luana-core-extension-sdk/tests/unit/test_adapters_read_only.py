"""V-AG-new-story-8 — _adapters.py read-only wrappers for Stories 6+7 frozen registries.

Per 06-tickets.yaml T-6 + 03-arch-be.md §1.4 verbatim.

Cardinal: adapters wrap Stories 6+7 frozen registries READ-ONLY. NO private surface access.
V-AG-3 Story 6 + Story 7 golden snapshots MUST continue GREEN post adapter introduction.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from luana_core_extension_sdk._adapters import (
    _CopilotWorkflowRegistryAdapter,
    _SalesAgentToolRegistryAdapter,
)
from luana_core_extension_sdk.models import ToolDef, WorkflowDef

# ─────────────────────────────────────────────────────────────────────
# Read-only AST enforcement (V-AG-new-story-8)
# ─────────────────────────────────────────────────────────────────────


def test_adapter_module_no_private_surface_access() -> None:
    """V-AG-new-story-8 — AST parse forbids private attr access on inner registries.

    Adapter classes wrap Stories 6+7 frozen registries READ-ONLY. They MUST NOT
    touch private attrs (_dispatch_*, _mutate_*, _internal_*, _private_*) of the
    underlying registry — only documented public surface.
    """
    adapter_file = Path(__file__).parent.parent.parent / "src" / "luana_core_extension_sdk" / "_adapters.py"
    src = adapter_file.read_text()
    tree = ast.parse(src)

    forbidden_prefixes = ("_dispatch", "_mutate", "_internal_", "_private_")
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            for prefix in forbidden_prefixes:
                # Forbid the bare attribute prefix anywhere in adapter module.
                # `self._inner` is permitted; the check forbids PEEKING INTO the
                # wrapped registry's private surface (adapter._inner._private_X).
                if node.attr.startswith(prefix):
                    violations.append(f"{prefix} prefix in attr: {node.attr}")

    assert not violations, f"Adapter touches private surface: {violations}"


def test_adapter_classes_expose_only_public_register_extension_methods() -> None:
    """Public surface of adapter classes = register_extension_tool / register_extension_workflow only.

    No method named _dispatch / _mutate / _internal_ on adapter classes.
    """
    for cls in [_SalesAgentToolRegistryAdapter, _CopilotWorkflowRegistryAdapter]:
        public_methods = [m for m in dir(cls) if not m.startswith("_")]
        forbidden = [m for m in public_methods if any(m.startswith(p) for p in ("dispatch", "mutate", "internal"))]
        assert not forbidden, f"{cls.__name__} exposes forbidden methods: {forbidden}"

        # Specifically, allow ONLY register_extension_* on public surface
        allowed_pattern = "register_extension_"
        non_register_public = [m for m in public_methods if not m.startswith(allowed_pattern)]
        assert not non_register_public, f"{cls.__name__} exposes unexpected public methods: {non_register_public}"


# ─────────────────────────────────────────────────────────────────────
# Adapter graceful contract — NotImplementedError when surface absent
# ─────────────────────────────────────────────────────────────────────


def test_sales_agent_adapter_raises_not_implemented_on_missing_method() -> None:
    """V-AG-new-story-8 — adapter raises gracefully when inner ToolRegistry lacks public API."""

    class FakeRegistry:
        """No register_tool_from_extension method — simulates current Story 7 state."""

    adapter = _SalesAgentToolRegistryAdapter(FakeRegistry())
    tool = ToolDef(
        name="vitalia.test",
        description="x",
        input_schema={},
        handler=lambda: None,
    )
    with pytest.raises(NotImplementedError, match="Story 7 ToolRegistry"):
        adapter.register_extension_tool(tool)


def test_copilot_adapter_raises_not_implemented_on_missing_method() -> None:
    """V-AG-new-story-8 — adapter raises gracefully for WorkflowRegistry."""

    class FakeRegistry:
        pass

    adapter = _CopilotWorkflowRegistryAdapter(FakeRegistry())
    wf = WorkflowDef(name="vitalia.test", description="x", steps=())
    with pytest.raises(NotImplementedError, match="Story 6 WorkflowRegistry"):
        adapter.register_extension_workflow(wf)


# ─────────────────────────────────────────────────────────────────────
# Adapter happy path delegation — when registry HAS register_*_from_extension
# ─────────────────────────────────────────────────────────────────────


def test_sales_agent_adapter_delegates_when_method_present() -> None:
    """When wrapped registry exposes register_tool_from_extension, adapter delegates kwargs."""

    class FakeRegistryWithMethod:
        def __init__(self) -> None:
            self.calls: list[dict] = []

        def register_tool_from_extension(self, **kwargs) -> None:
            self.calls.append(kwargs)

    fake = FakeRegistryWithMethod()
    adapter = _SalesAgentToolRegistryAdapter(fake)
    tool = ToolDef(
        name="test-brand.echo",
        description="Echo",
        input_schema={"type": "object"},
        handler=lambda: "echo",
        tool_groups=("knowledge",),
    )
    adapter.register_extension_tool(tool)

    assert len(fake.calls) == 1
    call = fake.calls[0]
    assert call["name"] == "test-brand.echo"
    assert call["description"] == "Echo"
    assert call["input_schema"] == {"type": "object"}
    assert call["tool_groups"] == ("knowledge",)


def test_copilot_adapter_delegates_when_method_present() -> None:
    class FakeRegistryWithMethod:
        def __init__(self) -> None:
            self.calls: list[dict] = []

        def register_workflow_from_extension(self, **kwargs) -> None:
            self.calls.append(kwargs)

    fake = FakeRegistryWithMethod()
    adapter = _CopilotWorkflowRegistryAdapter(fake)
    wf = WorkflowDef(
        name="test-brand.wf",
        description="Test workflow",
        steps=(),
        trigger_event="user_signup",
    )
    adapter.register_extension_workflow(wf)

    assert len(fake.calls) == 1
    call = fake.calls[0]
    assert call["name"] == "test-brand.wf"
    assert call["trigger_event"] == "user_signup"


# ─────────────────────────────────────────────────────────────────────
# Byte-stability invariant — adapter NEVER mutates inner registry state
# ─────────────────────────────────────────────────────────────────────


def test_adapter_does_not_mutate_inner_registry_when_method_absent() -> None:
    """When method absent, adapter raises BEFORE touching inner. No state side-effect."""

    class FakeInnerWithState:
        def __init__(self) -> None:
            self.state_snapshot: list = []
            self.public_only = "untouched"

    inner = FakeInnerWithState()
    adapter = _SalesAgentToolRegistryAdapter(inner)
    tool = ToolDef(name="test-brand.t", description="x", input_schema={}, handler=lambda: None)
    try:
        adapter.register_extension_tool(tool)
    except NotImplementedError:
        pass  # Expected

    # Inner state unchanged — adapter raised before any mutation attempt
    assert inner.state_snapshot == []
    assert inner.public_only == "untouched"


def test_adapter_init_stores_inner_only() -> None:
    """Constructor stores inner registry reference — no I/O, no mutation."""

    class FakeInner:
        pass

    inner = FakeInner()
    adapter = _SalesAgentToolRegistryAdapter(inner)
    # Adapter holds reference via private _inner — public surface
    # (test confirms via direct attr access, not via mutating)
    assert adapter._inner is inner


# ─────────────────────────────────────────────────────────────────────
# ExtensionPointRegistry + adapter wired end-to-end
# ─────────────────────────────────────────────────────────────────────


def test_registry_with_real_adapter_delegates_to_inner() -> None:
    """End-to-end: ExtensionPointRegistry + adapter w/ inner-with-method → propagates."""
    from luana_core_extension_sdk import ExtensionPointRegistry

    class FakeInner:
        def __init__(self) -> None:
            self.tool_calls: list = []

        def register_tool_from_extension(self, **kwargs) -> None:
            self.tool_calls.append(kwargs)

    inner = FakeInner()
    adapter = _SalesAgentToolRegistryAdapter(inner)
    r = ExtensionPointRegistry(sales_agent_tool_registry_adapter=adapter)

    tool = ToolDef(
        name="test-brand.search",
        description="Search",
        input_schema={},
        handler=lambda: None,
    )
    r.sales_agent_tool_register(tool)

    # SDK-side stored
    assert len(r.get_all("EP-3")) == 1
    # Inner registry also received delegation
    assert len(inner.tool_calls) == 1
    assert inner.tool_calls[0]["name"] == "test-brand.search"

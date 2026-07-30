# cap: sales_agent.honor-mode-bridge
"""T-AG-GAP1 arch gate — ``register_all`` MUST wire every async-wrapped EP-3
tool's ``set_*_service_resolver(...)`` DI hook.

GAP-1 (RECONCILE-2026-06-22 §1): the 5 async StructuredTools dispatched live but
their resolvers were never wired → ``_get_service()`` raised RuntimeError → the
tools returned a resolver-not-configured error and never executed real logic.

This test fails the build if a future EP-3 async-wrapped tool is added (or the
wiring is removed) without its resolver being set inside ``register_all`` — i.e.
it makes the GAP-1 regression structurally impossible to reintroduce.

Mechanism: each tool stores its resolver in a module-level ``_service_resolver``
global (set by the corresponding setter). We reset all of them to ``None``, run
the real ``register_all``, and assert each is now a callable.

SSoT: RECONCILE-2026-06-22-doc-vs-reality.md §6 item 1.
"""

from __future__ import annotations

import importlib

from luana_core_extension_sdk._adapters import _SalesAgentToolRegistryAdapter
from luana_core_extension_sdk.extension_points import ExtensionPointRegistry
from luana_core_sales_agent.application.tools.registry import ToolRegistry

from src.modules.vitalia.extensions import register_all

# NOTE: the `tools/__init__.py` re-exports each `@tool` object under the SAME name
# as its submodule, so a plain `import ...tools.screening_questions as m` binds the
# TOOL, not the module. Use importlib to get the real module object (which owns the
# `_service_resolver` DI global the setter rebinds).
_pkg = "src.modules.vitalia.sales_agent.tools"
_screening_mod = importlib.import_module(f"{_pkg}.screening_questions")
_payment_link_mod = importlib.import_module(f"{_pkg}.payment_link")
_reschedule_mod = importlib.import_module(f"{_pkg}.reschedule_appointment")
_proactive_mod = importlib.import_module(f"{_pkg}.send_proactive_reengagement")
_retract_mod = importlib.import_module(f"{_pkg}.retract_last_message")

# (tool module, human label) — every async-wrapped EP-3 tool with a DI resolver.
# Add a row here when you add a new resolver-backed tool; the test then enforces
# that register_all wires it.
_RESOLVER_TOOLS = (
    (_screening_mod, "screening_questions"),
    (_payment_link_mod, "send_payment_link"),
    (_reschedule_mod, "reschedule_appointment"),
    (_proactive_mod, "send_proactive_reengagement"),
    (_retract_mod, "retract_last_message"),
)


def _run_register_all() -> None:
    tr = ToolRegistry()
    reg = ExtensionPointRegistry(
        sales_agent_tool_registry_adapter=_SalesAgentToolRegistryAdapter(tr),
    )
    register_all(reg)


def test_register_all_wires_every_service_resolver() -> None:
    # Reset every resolver to None so the assertion can only pass because
    # register_all wired it (not because a prior import/run left it set).
    for mod, _label in _RESOLVER_TOOLS:
        mod._service_resolver = None  # noqa: SLF001 — intentional reset of DI global

    _run_register_all()

    unwired = [label for mod, label in _RESOLVER_TOOLS if mod._service_resolver is None]  # noqa: SLF001
    assert not unwired, (
        "register_all did not wire set_*_service_resolver for: "
        f"{unwired}. Every async-wrapped EP-3 tool must have its resolver wired in "
        "sales_agent.composition.wire_sales_agent_tool_resolvers() (GAP-1 regression guard)."
    )


def test_every_wired_resolver_is_callable() -> None:
    _run_register_all()
    for mod, label in _RESOLVER_TOOLS:
        resolver = mod._service_resolver  # noqa: SLF001
        assert callable(resolver), f"{label}: wired resolver is not callable ({resolver!r})"


def test_resolver_module_globals_exist() -> None:
    """Guard against a tool module being refactored to drop the ``_service_resolver``
    DI hook (which would silently break wiring)."""
    for mod, label in _RESOLVER_TOOLS:
        assert hasattr(mod, "_service_resolver"), f"{label}: missing _service_resolver DI global"
        # The setter names are not perfectly uniform (e.g. set_reschedule_service_resolver),
        # so assert at least one set_*_service_resolver setter is exported.
        setters = [n for n in dir(mod) if n.startswith("set_") and n.endswith("_service_resolver")]
        assert setters, f"{label}: no set_*_service_resolver setter exported"

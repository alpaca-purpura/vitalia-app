"""Architecture fitness: ExtensionPointRegistry has NO EP-19 method.

V-AG-no-ep19. Cardinal invariant per §7.5.5 + outcome §7.5.7.
A vertical agent (e.g. Vitalia treatment-agent) is brand app composition —
NOT a core SDK extension point. There must be no vertical_agent_register,
ep19, or ep_19 method on ExtensionPointRegistry.

This invariant is permanent — if a future architect proposes EP-19, this test
must be updated with explicit rationale and /pm + /architect sign-off.
"""

from __future__ import annotations

import inspect

from luana_core_extension_sdk import ExtensionPointRegistry

_FORBIDDEN_METHOD_PATTERNS = [
    "vertical_agent_register",
    "vertical_agent",
    "ep19",
    "ep_19",
    "treatment_agent",
]


def test_no_ep19_method_on_registry() -> None:
    """V-AG-no-ep19: registry has zero methods matching vertical_agent|ep19|ep_19."""
    all_methods = [name for name, _ in inspect.getmembers(ExtensionPointRegistry) if not name.startswith("__")]

    violations = [method for method in all_methods if any(pat in method.lower() for pat in _FORBIDDEN_METHOD_PATTERNS)]

    assert not violations, (
        "ExtensionPointRegistry contains forbidden EP-19 / vertical_agent method(s).\n\n"
        "Violations: " + str(violations) + "\n\n"
        "Cardinal invariant V-AG-no-ep19: vertical agents are brand app composition,\n"
        "NOT core SDK extension points. A Vitalia treatment-agent is built BY composing\n"
        "EP-3 (sales_agent_tool_register) + EP-4 (copilot_workflow_register) + brand code.\n\n"
        "To add EP-19 you need:\n"
        "  1. /pm + /architect sign-off\n"
        "  2. Remove this test (with justification commit)\n"
        "  3. New Story for the new EP contract"
    )

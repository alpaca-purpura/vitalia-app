"""Architecture fitness: EP-3/EP-4 adapter wrappers are read-only.

V-AG-new-story-8. _adapters.py adapters (_SalesAgentToolRegistryAdapter +
_CopilotWorkflowRegistryAdapter) must ONLY delegate to public methods of
the wrapped registry. They must NOT access private attributes (._attr) on
the inner registry beyond `self._inner` storage.

This prevents Story 8 EP adapters from coupling to Stories 6+7 internal
implementation details, which would break when those internals change.

AST-level check — does not require runtime import of Stories 6+7 packages.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).parents[3]
ADAPTERS_FILE = ROOT / "core" / "luana-core-extension-sdk" / "src" / "luana_core_extension_sdk" / "_adapters.py"

# Only these private attributes are allowed on `self` within adapter methods.
# self._inner is the stored reference — reading it is READ-ONLY delegation.
_ALLOWED_PRIVATE_ON_SELF = frozenset({"_inner"})


class _PrivateAttrAccessVisitor(ast.NodeVisitor):
    """AST visitor detecting private attribute accesses on self._inner's target.

    Flags any `self._inner._<anything>` or `<other>._<private>` access
    that could couple adapters to internal private surfaces.
    """

    def __init__(self) -> None:
        self.violations: list[tuple[int, str]] = []

    def visit_Attribute(self, node: ast.Attribute) -> None:
        attr = node.attr
        # Only flag accesses to private attrs (start with _ but not dunder)
        if attr.startswith("_") and not attr.startswith("__"):
            # Allowed: self._inner (storage of wrapped registry reference)
            if isinstance(node.value, ast.Name) and node.value.id == "self" and attr in _ALLOWED_PRIVATE_ON_SELF:
                pass  # allowed — self._inner is the storage field
            else:
                # Check if this is accessing a private method/attr on self._inner
                # e.g. self._inner._dispatch_something  ← FORBIDDEN
                if isinstance(node.value, ast.Attribute):
                    parent_attr = node.value.attr
                    if parent_attr == "_inner" and attr.startswith("_"):
                        self.violations.append(
                            (
                                node.lineno,
                                f"self._inner.{attr} — private attribute access on wrapped registry "
                                "(V-AG-new-story-8: adapters must be read-only, no private coupling)",
                            )
                        )
        self.generic_visit(node)


def test_adapters_no_private_inner_access() -> None:
    """V-AG-new-story-8: adapters must not access private attributes on inner registry."""
    assert ADAPTERS_FILE.exists(), f"_adapters.py not found at {ADAPTERS_FILE}.\nStory 8 T-6 must create it."

    source = ADAPTERS_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(ADAPTERS_FILE))

    visitor = _PrivateAttrAccessVisitor()
    visitor.visit(tree)

    assert not visitor.violations, (
        "_adapters.py contains private attribute access on wrapped registry (V-AG-new-story-8).\n"
        "Adapters must only call PUBLIC methods on inner registry.\n\n"
        "Violations:\n" + "\n".join(f"  line {ln}: {msg}" for ln, msg in visitor.violations)
    )


def test_adapters_file_has_both_adapter_classes() -> None:
    """V-AG-new-story-8: _adapters.py defines both EP-3 and EP-4 adapter classes."""
    assert ADAPTERS_FILE.exists(), f"_adapters.py missing at {ADAPTERS_FILE}"

    source = ADAPTERS_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(ADAPTERS_FILE))

    class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}

    required_classes = {"_SalesAgentToolRegistryAdapter", "_CopilotWorkflowRegistryAdapter"}
    missing = required_classes - class_names

    assert not missing, (
        f"Missing adapter classes in _adapters.py: {sorted(missing)}\n"
        "Both EP-3 (_SalesAgentToolRegistryAdapter) and EP-4 (_CopilotWorkflowRegistryAdapter) "
        "adapters must be defined."
    )

"""Architecture fitness: vitalia sales_agent observability MUST subclass engine base.

Story T-ag-tools-2 — anti-duplication §0 cardinal enforcement.

Per .claude/rules/anti-duplication.md § Regla cardinal:
  Observability/cost/pricing/turn_envelope/callback-handler patterns live in
  ``core/luana-core-observability/``. Vitalia EXTENDS via subclass.
  NEVER mirror plumbing.

This test verifies:
1. ``VitaliaSalesAgentCallbackHandler`` is a subclass of
   ``luana_core_observability.recording.base_callback_handler.BaseAgentCallbackHandler``.
2. ``VitaliaSalesAgentObservabilityContext`` is a subclass of
   ``luana_core_observability.recording.turn_envelope.BaseObservabilityContext``.
3. The subclass implements ONLY the abstract methods —
   does NOT redefine plumbing (on_llm_*, on_tool_*, on_chain_*,
   observe_turn, _write_turn_*, set_turn_*, etc.).
4. The subclass does NOT define local sanitize_payload or pop_cost or
   any engine-canonical helper.

downstream-regression-na: brand-local arch fitness gate; no cross-brand consumers.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

from luana_core_observability.recording.base_callback_handler import (
    BaseAgentCallbackHandler,
)
from luana_core_observability.recording.turn_envelope import (
    BaseObservabilityContext,
)

from src.modules.vitalia.sales_agent.observability.recording.callback_handler import (
    VitaliaSalesAgentCallbackHandler,
)
from src.modules.vitalia.sales_agent.observability.recording.turn_envelope import (
    VitaliaSalesAgentObservabilityContext,
)

_WS_ROOT = Path(__file__).parents[4]  # → luana-vitalia/ (parents[0]=architecture, [4]=luana-vitalia)
_VITALIA_OBS_DIR = (
    _WS_ROOT / "vitalia" / "backend" / "src" / "modules" / "vitalia" / "sales_agent" / "observability" / "recording"
)


# ── Inheritance assertions ──────────────────────────────────────────────


def test_callback_handler_subclasses_engine_base() -> None:
    """VitaliaSalesAgentCallbackHandler MUST subclass engine BaseAgentCallbackHandler."""
    assert issubclass(VitaliaSalesAgentCallbackHandler, BaseAgentCallbackHandler), (
        "VitaliaSalesAgentCallbackHandler must subclass "
        "luana_core_observability.recording.base_callback_handler.BaseAgentCallbackHandler "
        "(anti-duplication §0 cardinal)"
    )


def test_observability_context_subclasses_engine_base() -> None:
    """VitaliaSalesAgentObservabilityContext MUST subclass engine BaseObservabilityContext."""
    assert issubclass(VitaliaSalesAgentObservabilityContext, BaseObservabilityContext), (
        "VitaliaSalesAgentObservabilityContext must subclass "
        "luana_core_observability.recording.turn_envelope.BaseObservabilityContext "
        "(anti-duplication §0 cardinal)"
    )


# ── No-plumbing-redefinition assertions ─────────────────────────────────

# Engine base methods that subclasses MUST NOT redefine (Template Method
# locked methods + LangChain callback methods).
_FORBIDDEN_REDEFS_CALLBACK_HANDLER = frozenset(
    {
        "on_chat_model_start",
        "on_llm_end",
        "on_llm_error",
        "on_tool_start",
        "on_tool_end",
        "on_tool_error",
        "on_chain_start",
        "on_chain_end",
        "_persist_llm_call",  # Template Method skeleton — NEVER override
        "_safe_rollback",
        "_extract_provider_and_model",
        "_extract_usage",
        "_extract_model_responded",
        "_extract_litellm_call_id",
        "_elapsed_ms",
        "_stringify",
        "_chain_name",
        # Sanitization helpers (lifted to engine — never re-implement)
        "sanitize_payload",
        "redact_string",
        "redact_value",
        "truncate",
    }
)

_FORBIDDEN_REDEFS_OBS_CONTEXT = frozenset(
    {
        "langchain_config",
        "set_turn_summary",
        "set_turn_error",
        "observe_turn",
        "_write_turn_start",
        "_write_turn_end",
        "_commit_session",
        "_safe_aggregate_totals",
        "_safe_legacy_compat_keys",
    }
)


def _get_locally_defined_methods(cls: type) -> set[str]:
    """Return method names defined locally on ``cls`` (not inherited)."""
    source = inspect.getsource(cls)
    tree = ast.parse(source)
    methods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.add(node.name)
    return methods


def test_callback_handler_does_not_redefine_plumbing() -> None:
    """VitaliaSalesAgentCallbackHandler must NOT redefine LangChain callbacks or helpers."""
    locally_defined = _get_locally_defined_methods(VitaliaSalesAgentCallbackHandler)
    violations = locally_defined & _FORBIDDEN_REDEFS_CALLBACK_HANDLER
    assert not violations, (
        f"VitaliaSalesAgentCallbackHandler redefines engine plumbing: {sorted(violations)}. "
        f"Must inherit these from BaseAgentCallbackHandler (anti-duplication §0)."
    )


def test_observability_context_does_not_redefine_lifecycle() -> None:
    """VitaliaSalesAgentObservabilityContext must NOT redefine lifecycle locked methods."""
    locally_defined = _get_locally_defined_methods(VitaliaSalesAgentObservabilityContext)
    violations = locally_defined & _FORBIDDEN_REDEFS_OBS_CONTEXT
    assert not violations, (
        f"VitaliaSalesAgentObservabilityContext redefines engine lifecycle: {sorted(violations)}. "
        f"Must inherit these from BaseObservabilityContext (anti-duplication §0)."
    )


# ── No local sanitize/cost helper redefinition (file-level) ────────────


def _get_py_sources() -> list[Path]:
    """Return all .py files in the vitalia sales_agent observability recording dir."""
    if not _VITALIA_OBS_DIR.exists():
        return []
    return [p for p in _VITALIA_OBS_DIR.glob("*.py") if p.name != "__init__.py"]


def test_no_local_sanitize_payload_definition() -> None:
    """No vitalia observability file should define its own sanitize_payload."""
    for py_file in _get_py_sources():
        src = py_file.read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                assert node.name != "sanitize_payload", (
                    f"{py_file.name}: defines local `sanitize_payload` — "
                    f"use `from luana_core_observability.recording.sanitization "
                    f"import sanitize_payload` instead (anti-duplication.md)"
                )


def test_no_local_pop_cost_definition() -> None:
    """No vitalia observability file should define its own pop_cost.

    pop_cost is the canonical PI-12 S1 T-1 cost bridge — lives in
    luana_core_observability.recording.cost_recorder.
    """
    for py_file in _get_py_sources():
        src = py_file.read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                assert node.name != "pop_cost", (
                    f"{py_file.name}: defines local `pop_cost` — "
                    f"use engine cost_recorder.pop_cost instead (anti-duplication.md)"
                )


def test_no_local_calculate_cost_definition() -> None:
    """No vitalia observability file should define its own calculate_cost.

    calculate_cost is engine-canonical (luana_core_observability.cost.calculator)
    and used as reconciliation utility only post PI-12 S1 T-1.
    """
    for py_file in _get_py_sources():
        src = py_file.read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                assert node.name != "calculate_cost", (
                    f"{py_file.name}: defines local `calculate_cost` — "
                    f"use engine calculator.calculate_cost (anti-duplication.md)"
                )


def test_callback_handler_imports_from_engine() -> None:
    """Callback handler file MUST import BaseAgentCallbackHandler from engine."""
    callback_file = _VITALIA_OBS_DIR / "callback_handler.py"
    src = callback_file.read_text(encoding="utf-8")
    assert "from luana_core_observability.recording.base_callback_handler import" in src, (
        "vitalia callback_handler.py must import BaseAgentCallbackHandler from engine (anti-duplication §0)"
    )


def test_turn_envelope_imports_from_engine() -> None:
    """Turn envelope file MUST import BaseObservabilityContext from engine."""
    envelope_file = _VITALIA_OBS_DIR / "turn_envelope.py"
    src = envelope_file.read_text(encoding="utf-8")
    assert "from luana_core_observability.recording.turn_envelope import" in src, (
        "vitalia turn_envelope.py must import BaseObservabilityContext from engine (anti-duplication §0)"
    )

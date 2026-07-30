"""Architecture fitness — vitalia copilot observability subclass MUST NOT mirror engine.

Per .claude/rules/anti-duplication.md § 0 cardinal:
  - VitaliaCopilotCallbackHandler MUST be subclass of
    luana_core_observability.recording.base_callback_handler.BaseAgentCallbackHandler
  - VitaliaCopilotObservabilityContext MUST be subclass of
    luana_core_observability.recording.turn_envelope.BaseObservabilityContext
  - Neither may redefine plumbing methods owned by the engine base.
  - Neither may re-define sanitize_payload / redact_string / redact_value (engine SSoT).

Ratchet test — shrink only. New violation = build fail.

downstream-regression-na: brand-local arch fitness; no cross-brand consumers
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

from luana_core_observability.recording.base_callback_handler import (
    BaseAgentCallbackHandler,
)
from luana_core_observability.recording.turn_envelope import BaseObservabilityContext

from src.modules.vitalia.copilot.observability.recording.callback_handler import (
    VitaliaCopilotCallbackHandler,
)
from src.modules.vitalia.copilot.observability.recording.turn_envelope import (
    VitaliaCopilotObservabilityContext,
)

# Methods the engine base owns; subclass MUST NOT redefine them.
FORBIDDEN_CALLBACK_OVERRIDES = frozenset(
    {
        "on_chat_model_start",
        "on_llm_end",
        "on_llm_error",
        "on_tool_start",
        "on_tool_end",
        "on_tool_error",
        "on_chain_start",
        "on_chain_end",
        "_persist_llm_call",
        "_safe_rollback",
        "_extract_provider_and_model",
        "_canonical_provider",
        "_extract_usage",
        "_extract_model_responded",
        "_extract_litellm_call_id",
        "_chain_name",
        "_elapsed_ms",
        "_stringify",
        "_from_openai_token_usage",
        # PII / sanitization owned by engine
        "sanitize_payload",
        "redact_string",
        "redact_value",
        "truncate",
    }
)

# Methods the engine BaseObservabilityContext owns; subclass MUST NOT redefine them.
FORBIDDEN_ENVELOPE_OVERRIDES = frozenset(
    {
        "observe_turn",
        "_write_turn_start",
        "_write_turn_end",
        "_commit_session",
        "_safe_aggregate_totals",
        "_safe_legacy_compat_keys",
        "set_turn_summary",
        "set_turn_error",
        "langchain_config",
        # PII / sanitization owned by engine
        "sanitize_payload",
        "redact_string",
        "redact_value",
        "truncate",
    }
)


def _read_source(klass: type) -> tuple[Path, str]:
    """Return (path, source) of the module containing `klass`."""
    path = Path(inspect.getfile(klass))
    return path, path.read_text(encoding="utf-8")


def _find_class_method_names(source: str, class_name: str) -> set[str]:
    """Parse `source` and return method names defined directly on `class_name`."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))}
    return set()


class TestCallbackHandlerInheritance:
    """VitaliaCopilotCallbackHandler must subclass engine base."""

    def test_subclass_of_engine_base(self) -> None:
        assert issubclass(VitaliaCopilotCallbackHandler, BaseAgentCallbackHandler), (
            "VitaliaCopilotCallbackHandler MUST subclass "
            "luana_core_observability.recording.base_callback_handler.BaseAgentCallbackHandler "
            "(anti-duplication §0)"
        )

    def test_module_imports_base_from_engine(self) -> None:
        _, src = _read_source(VitaliaCopilotCallbackHandler)
        assert "from luana_core_observability.recording.base_callback_handler" in src, (
            "callback_handler.py must import BaseAgentCallbackHandler from "
            "luana_core_observability (anti-duplication §0)"
        )


class TestCallbackHandlerNoMirror:
    """Subclass must NOT redefine engine-owned plumbing."""

    def test_no_forbidden_method_overrides(self) -> None:
        _, src = _read_source(VitaliaCopilotCallbackHandler)
        method_names = _find_class_method_names(src, "VitaliaCopilotCallbackHandler")
        violations = method_names & FORBIDDEN_CALLBACK_OVERRIDES
        assert not violations, (
            f"VitaliaCopilotCallbackHandler redefines engine-owned methods: {violations} — "
            f"anti-duplication §0 violation. Engine "
            f"luana_core_observability.recording.base_callback_handler owns these."
        )

    def test_only_persist_methods_overridden(self) -> None:
        """Subclass should override ONLY the 2 abstract persisters."""
        _, src = _read_source(VitaliaCopilotCallbackHandler)
        method_names = _find_class_method_names(src, "VitaliaCopilotCallbackHandler")
        # The subclass may define helpers but it MUST define the 2 abstract overrides.
        assert "_persist_llm_call_row" in method_names
        assert "_persist_trace_event_row" in method_names


class TestObservabilityContextInheritance:
    """VitaliaCopilotObservabilityContext must subclass engine base."""

    def test_subclass_of_engine_base(self) -> None:
        assert issubclass(VitaliaCopilotObservabilityContext, BaseObservabilityContext), (
            "VitaliaCopilotObservabilityContext MUST subclass "
            "luana_core_observability.recording.turn_envelope.BaseObservabilityContext "
            "(anti-duplication §0)"
        )

    def test_module_imports_base_from_engine(self) -> None:
        _, src = _read_source(VitaliaCopilotObservabilityContext)
        assert "from luana_core_observability.recording.turn_envelope" in src, (
            "turn_envelope.py must import BaseObservabilityContext from luana_core_observability (anti-duplication §0)"
        )


class TestObservabilityContextNoMirror:
    """Subclass must NOT redefine engine-owned lifecycle methods."""

    def test_no_forbidden_method_overrides(self) -> None:
        _, src = _read_source(VitaliaCopilotObservabilityContext)
        method_names = _find_class_method_names(src, "VitaliaCopilotObservabilityContext")
        violations = method_names & FORBIDDEN_ENVELOPE_OVERRIDES
        assert not violations, (
            f"VitaliaCopilotObservabilityContext redefines engine-owned methods: "
            f"{violations} — anti-duplication §0 violation."
        )

    def test_only_abstract_hooks_overridden(self) -> None:
        """Subclass should override the 3 abstract hooks + provide a `start` factory."""
        _, src = _read_source(VitaliaCopilotObservabilityContext)
        method_names = _find_class_method_names(src, "VitaliaCopilotObservabilityContext")
        # The 3 abstract hooks MUST be present.
        assert "_add_trace_event" in method_names
        assert "_aggregate_totals" in method_names
        assert "_legacy_compat_keys_or_empty" in method_names


class TestNoLocalSanitizationDuplication:
    """Files MUST NOT redefine sanitization functions (engine SSoT)."""

    def test_callback_handler_no_local_sanitize(self) -> None:
        _, src = _read_source(VitaliaCopilotCallbackHandler)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                assert node.name not in (
                    "sanitize_payload",
                    "redact_string",
                    "redact_value",
                    "truncate",
                ), (
                    f"callback_handler.py defines local sanitization fn `{node.name}` — "
                    f"import from luana_core_observability.recording.sanitization"
                )

    def test_turn_envelope_no_local_sanitize(self) -> None:
        _, src = _read_source(VitaliaCopilotObservabilityContext)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                assert node.name not in (
                    "sanitize_payload",
                    "redact_string",
                    "redact_value",
                    "truncate",
                ), (
                    f"turn_envelope.py defines local sanitization fn `{node.name}` — "
                    f"import from luana_core_observability.recording.sanitization"
                )

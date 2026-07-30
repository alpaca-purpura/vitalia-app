"""Architecture fitness: no mirror observability in luana-core-copilot.

Per 03-arch.md §7.5 + D-T6 anti-duplication cardinal (rule: `.claude/rules/
anti-duplication.md`). luana-core-copilot MUST consume observability
abstractions from `luana_core_observability` as SUBCLASSES (D-T6 cement),
never as parallel re-implementations.

Specifically:
- `CopilotObservabilityContext` MUST subclass `BaseObservabilityContext` from luana_core_observability
- `ObservabilityCallbackHandler` (or copilot-specific handler) MUST subclass `BaseAgentCallbackHandler`
- NO class declarations of: `FXResolver`, `PricingResolver`, `CostCalculator`,
  `BaseObservabilityContext`, `BaseAgentCallbackHandler` inside luana-core-copilot.
- NO function declarations of `sanitize_payload` inside luana-core-copilot.
- All of the above MUST be imports from luana_core_observability.

V-AG-5 validator.
"""

from __future__ import annotations

import re
from pathlib import Path

CORE_DIR = Path(__file__).parents[2]
COPILOT_SRC = CORE_DIR / "luana-core-copilot" / "src" / "luana_core_copilot"

# Forbidden class declarations (must come from luana_core_observability as imports)
FORBIDDEN_CLASS_PATTERNS: dict[str, re.Pattern[str]] = {
    "FXResolver": re.compile(r"^class\s+FXResolver\b"),
    "PricingResolver": re.compile(r"^class\s+PricingResolver\b"),
    "CostCalculator": re.compile(r"^class\s+CostCalculator\b"),
    "BaseObservabilityContext": re.compile(r"^class\s+BaseObservabilityContext\b"),
    "BaseAgentCallbackHandler": re.compile(r"^class\s+BaseAgentCallbackHandler\b"),
}

# Forbidden function declarations (must come from shared sanitization module)
FORBIDDEN_FUNC_PATTERNS: dict[str, re.Pattern[str]] = {
    "sanitize_payload": re.compile(r"^def\s+sanitize_payload\b"),
}


def _scan_copilot_files() -> list[tuple[Path, str]]:
    return [(p, p.read_text(encoding="utf-8")) for p in COPILOT_SRC.rglob("*.py")]


def test_no_mirror_observability_classes():
    """No mirror class declarations of luana_core_observability surfaces."""
    violations: list[str] = []

    for path, text in _scan_copilot_files():
        for lineno, line in enumerate(text.splitlines(), 1):
            for cls_name, pattern in FORBIDDEN_CLASS_PATTERNS.items():
                if pattern.search(line):
                    violations.append(
                        f"{path.relative_to(COPILOT_SRC)}:{lineno}: "
                        f"`class {cls_name}` — must be IMPORTED from "
                        "luana_core_observability, not redeclared.",
                    )

    assert not violations, (
        "V-AG-5 D-T6 cement violation: mirror observability classes detected.\n"
        "Per anti-duplication.md cardinal: copilot SUBCLASSES bases from "
        "luana_core_observability; it does NOT redeclare them.\n\n"
        "Violations:\n" + "\n".join(violations)
    )


def test_no_mirror_observability_functions():
    """No mirror function declarations of luana_core_observability surfaces."""
    violations: list[str] = []

    for path, text in _scan_copilot_files():
        for lineno, line in enumerate(text.splitlines(), 1):
            for fn_name, pattern in FORBIDDEN_FUNC_PATTERNS.items():
                if pattern.search(line):
                    violations.append(
                        f"{path.relative_to(COPILOT_SRC)}:{lineno}: "
                        f"`def {fn_name}` — must be IMPORTED from "
                        "luana_core_observability, not redeclared.",
                    )

    assert not violations, "V-AG-5 D-T6 cement violation: mirror sanitization function detected.\n" + "\n".join(
        violations
    )


def test_callback_handler_subclasses_base():
    """ObservabilityCallbackHandler MUST subclass BaseAgentCallbackHandler.

    Verifies the import + subclass relationship in the copilot callback_handler
    module (D-T6 cement).
    """
    handler_path = COPILOT_SRC / "observability" / "recording" / "callback_handler.py"
    assert handler_path.exists(), f"Expected copilot callback handler at {handler_path}"

    text = handler_path.read_text(encoding="utf-8")

    has_import = bool(
        re.search(
            r"from\s+luana_core_observability\.recording\.base_callback_handler\s+import.*BaseAgentCallbackHandler",
            text,
            re.DOTALL,
        ),
    )
    has_subclass = bool(re.search(r"class\s+\w+\s*\(\s*BaseAgentCallbackHandler\s*\)\s*:", text))

    assert has_import, (
        "Copilot callback_handler.py MUST import BaseAgentCallbackHandler from "
        "luana_core_observability.recording.base_callback_handler "
        "(D-T6 anti-mirror cement)."
    )
    assert has_subclass, (
        "Copilot callback_handler.py MUST declare a class subclassing "
        "BaseAgentCallbackHandler (D-T6 anti-mirror cement)."
    )


def test_observability_context_subclasses_base():
    """CopilotObservabilityContext MUST subclass BaseObservabilityContext.

    D-T6 cement: the lifecycle that used to live monolithically here lives in
    luana_core_observability.recording.turn_envelope.BaseObservabilityContext.
    """
    turn_env_path = COPILOT_SRC / "observability" / "recording" / "turn_envelope.py"
    assert turn_env_path.exists(), f"Expected copilot turn_envelope at {turn_env_path}"

    text = turn_env_path.read_text(encoding="utf-8")

    has_import = bool(
        re.search(
            r"from\s+luana_core_observability\.recording\.turn_envelope\s+import.*BaseObservabilityContext",
            text,
            re.DOTALL,
        ),
    )
    has_subclass = bool(re.search(r"class\s+\w+\s*\(\s*BaseObservabilityContext\s*\)\s*:", text))

    assert has_import, (
        "Copilot turn_envelope.py MUST import BaseObservabilityContext from "
        "luana_core_observability.recording.turn_envelope "
        "(D-T6 anti-mirror cement)."
    )
    assert has_subclass, (
        "Copilot turn_envelope.py MUST declare a class subclassing BaseObservabilityContext (D-T6 anti-mirror cement)."
    )

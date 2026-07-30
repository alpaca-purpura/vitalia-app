"""Architecture fitness: D-T3 cardinal — sales_agent uses BrandVoicePort, NEVER PersonalityCompiler direct.

Per 03-arch.md §7.3 + ADR-001 §2.4 + D-T3 ratified. Story 7 introduces
BrandVoicePort as the hexagonal port — sales_agent depends on the
abstraction, brand_studio composition root binds the concrete adapter.

`luana_core_sales_agent` MUST NOT import:
- `luana_core_brand_studio.domain.personality.PersonalityCompiler`
- `from luana_core_brand_studio.domain.personality import PersonalityCompiler`
- `from luana_core_brand_studio.domain import personality`

Sales agent consumes voice via `BrandVoicePort.compile_system_instruction`
exclusively (T-11 cement).

V-AG-3 validator. Cement for hexagonal port discipline.
"""

from __future__ import annotations

import re
from pathlib import Path

CORE_DIR = Path(__file__).parents[2]
SALES_AGENT_SRC = CORE_DIR / "luana-core-sales-agent" / "src" / "luana_core_sales_agent"

# Forbidden direct PersonalityCompiler imports (D-T3 cardinal violation).
# Only flag ACTIVE code references — docstrings + comments may mention the name
# (e.g., explaining why this layer wraps the compiler). Imports + executable
# references are the cardinal-violation surface.
FORBIDDEN_IMPORT_PATTERNS = [
    re.compile(r"^\s*from\s+luana_core_brand_studio\.domain\.personality\s+import"),
    re.compile(r"^\s*import\s+luana_core_brand_studio\.domain\.personality"),
    re.compile(r"^\s*from\s+luana_core_brand_studio\.domain\s+import\s+personality\b"),
]


def _scan_sales_agent_files() -> list[tuple[Path, str]]:
    return [(p, p.read_text(encoding="utf-8")) for p in SALES_AGENT_SRC.rglob("*.py")]


def _strip_docstrings_and_comments(text: str) -> list[tuple[int, str]]:
    """Return (lineno, line) tuples for code lines only (no triple-quoted docstrings, no #-comments).

    Simple lexer state machine — toggles in/out of triple-quoted strings. Good enough
    to avoid flagging docstring mentions of PersonalityCompiler.
    """
    result: list[tuple[int, str]] = []
    in_triple_single = False
    in_triple_double = False
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        # Track triple-quote state (count occurrences; toggle if odd count)
        # Process triple-double first (more common)
        td_count = stripped.count('"""')
        ts_count = stripped.count("'''")

        # If we're currently inside a triple-quoted block, skip line entirely
        if in_triple_double or in_triple_single:
            # Check if this line closes the block
            if in_triple_double and td_count % 2 == 1:
                in_triple_double = False
            elif in_triple_single and ts_count % 2 == 1:
                in_triple_single = False
            continue

        # Not inside a triple — does this line OPEN one?
        if td_count % 2 == 1:
            in_triple_double = True
            continue  # skip the opening line
        if ts_count % 2 == 1:
            in_triple_single = True
            continue

        # Skip pure comment lines
        if stripped.startswith("#"):
            continue
        # Skip blank lines
        if not stripped:
            continue
        # Strip trailing inline comment
        code = line.split("#", 1)[0]
        result.append((lineno, code))
    return result


def test_no_direct_personality_compiler_import():
    """Sales agent MUST NOT import PersonalityCompiler from brand_studio domain.

    D-T3 cardinal: voice flows through BrandVoicePort hexagonal port. Docstrings
    + comments may MENTION PersonalityCompiler by name (explaining why this
    layer wraps it) — only actual imports / executable references violate.
    """
    violations: list[str] = []

    # Check 1: forbidden import patterns (regex on raw source)
    for path, text in _scan_sales_agent_files():
        rel = path.relative_to(SALES_AGENT_SRC)
        for lineno, line in enumerate(text.splitlines(), 1):
            for pattern in FORBIDDEN_IMPORT_PATTERNS:
                if pattern.search(line):
                    violations.append(f"{rel}:{lineno}: {line.strip()}")

    # Check 2: bare PersonalityCompiler() instantiations or attribute access
    # in CODE LINES (not docstrings, not comments).
    instantiation_pattern = re.compile(r"\bPersonalityCompiler\s*\(")
    attribute_pattern = re.compile(r"\bPersonalityCompiler\.[a-z_]")

    for path, text in _scan_sales_agent_files():
        rel = path.relative_to(SALES_AGENT_SRC)
        for lineno, code_line in _strip_docstrings_and_comments(text):
            if instantiation_pattern.search(code_line) or attribute_pattern.search(code_line):
                violations.append(
                    f"{rel}:{lineno}: {code_line.strip()} (executable PersonalityCompiler ref)",
                )

    assert not violations, (
        "V-AG-3 D-T3 cardinal violation: PersonalityCompiler direct import or "
        "active code reference in luana-core-sales-agent.\n"
        "Voice MUST flow through `BrandVoicePort.compile_system_instruction` — "
        "the hexagonal port. brand_studio binds the concrete adapter.\n\n"
        "Violations:\n" + "\n".join(violations)
    )


def test_brand_voice_port_consumed_by_compose_prompt():
    """compose_prompt MUST accept voice_port arg + use it for slot 5 BRAND_VOICE.

    Confirms D-T3 cardinal positive: the consumer side is wired.
    """
    compose_path = SALES_AGENT_SRC / "application" / "prompts" / "compose.py"
    assert compose_path.exists(), f"compose.py missing at {compose_path}"

    text = compose_path.read_text(encoding="utf-8")

    # Must import BrandVoicePort
    has_port_import = bool(
        re.search(
            r"from\s+luana_core_brand_studio\.application\.ports\.brand_voice_port"
            r"\s+import.*BrandVoicePort",
            text,
            re.DOTALL,
        ),
    )
    assert has_port_import, (
        "compose.py MUST import BrandVoicePort from "
        "luana_core_brand_studio.application.ports.brand_voice_port (D-T3 consumer)."
    )

    # compose_prompt signature must include voice_port: BrandVoicePort
    has_signature = bool(
        re.search(
            r"def\s+compose_prompt\b[^)]*voice_port\s*:\s*BrandVoicePort",
            text,
            re.DOTALL,
        ),
    )
    assert has_signature, (
        "compose_prompt signature MUST declare `voice_port: BrandVoicePort` "
        "(D-T3 cardinal — hexagonal port consumed at slot 5)."
    )

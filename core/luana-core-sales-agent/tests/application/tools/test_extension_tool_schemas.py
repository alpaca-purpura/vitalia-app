"""Regression tests for native function-calling tool-name sanitization.

Bug (2026-06-22): EP-3 brand tools are namespaced ``{brand}.{tool}`` (a DOT).
OpenAI/DeepSeek reject function names that do not match ``^[a-zA-Z0-9_-]+$`` with a
400, so EVERY native ``bind_tools`` call silently failed and fell back to text — the
agent never dispatched brand tools live. Fix: sanitize ``.`` → ``-`` in the schema and
reverse it before registry dispatch.
"""

from __future__ import annotations

import re

from luana_core_sales_agent.application.tools.registry import (
    _sanitize_tool_name,
    desanitize_tool_name,
    extension_tool_schemas,
    get_tool_registry,
)

_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


def test_sanitize_round_trip() -> None:
    """``.`` ↔ ``-`` is lossless for the EP-3 ``{brand}.{snake}`` convention."""
    name = "vitalia.match_service_and_specialist"
    safe = _sanitize_tool_name(name)
    assert "." not in safe
    assert _NAME_RE.match(safe)
    assert desanitize_tool_name(safe) == name


def test_dotted_extension_tool_emits_provider_valid_schema_name() -> None:
    """A dotted EP-3 tool yields a schema name that passes the provider charset,
    and the sanitized name reverses to the real registry key (dispatchable)."""
    reg = get_tool_registry()
    fake = "testbrand.share_doctor_profile"
    reg.register_tool_from_extension(
        name=fake,
        handler=lambda state, db=None: {"status": "ok"},
        description="fake",
        input_schema={"type": "object", "properties": {}},
        tool_groups=("presentation",),
    )
    try:
        schemas = extension_tool_schemas("presentation")
        emitted = {s["function"]["name"] for s in schemas}
        assert _sanitize_tool_name(fake) in emitted
        for name in emitted:
            assert _NAME_RE.match(name), (
                f"schema name {name!r} would 400 on DeepSeek/OpenAI"
            )
        # The model returns the sanitized name → desanitize must hit the real registry key.
        assert desanitize_tool_name(_sanitize_tool_name(fake)) in reg.merged_tools()
    finally:
        reg._extension_tools.pop(fake, None)

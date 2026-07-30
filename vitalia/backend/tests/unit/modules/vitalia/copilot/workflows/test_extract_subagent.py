"""Unit tests — deepagents extract_subagent sandbox isolation.

Per 03-arch-agentic.md § 3.2 + § 7.3 + tessl__deepagents:
  - SubAgent TypedDict with explicit `tools=[...]` sandbox (NO inherit parent)
  - Subagent system_prompt loaded from extractor_subagent.md
  - Public sub-tools: scrape_website_tool, parse_document_tool, transcribe_audio_tool
  - Parent state keys NEVER bleed into subagent (allowed_keys filter contract)
"""

from __future__ import annotations

from pathlib import Path


def test_extract_subagent_spec_has_explicit_tools_list():
    """SubAgent spec MUST declare tools explicitly (sandbox, no parent inherit)."""
    from src.modules.vitalia.copilot.workflows.extract_subagent import (
        build_extract_subagent_spec,
    )

    spec = build_extract_subagent_spec()
    assert "tools" in spec, "SubAgent missing explicit tools — would inherit parent (FORBIDDEN per F2)"
    assert isinstance(spec["tools"], (list, tuple)), "tools must be a sequence"
    assert len(spec["tools"]) == 3, "Slice 1: exactly 3 sandbox tools (scrape + parse + transcribe)"


def test_extract_subagent_spec_has_brand_namespace_name():
    """SubAgent name uses vitalia.* namespace (CC-4 enforcement)."""
    from src.modules.vitalia.copilot.workflows.extract_subagent import (
        EXTRACT_SUBAGENT_NAME,
        build_extract_subagent_spec,
    )

    spec = build_extract_subagent_spec()
    assert spec["name"] == EXTRACT_SUBAGENT_NAME
    assert spec["name"].startswith("vitalia_"), "Subagent name must start with brand slug prefix (CC-4 namespace)"


def test_extract_subagent_loads_system_prompt_from_md():
    """system_prompt sourced from extractor_subagent.md."""
    from src.modules.vitalia.copilot.workflows.extract_subagent import (
        build_extract_subagent_spec,
    )

    prompts_dir = Path(__file__).resolve().parents[6] / "src" / "modules" / "vitalia" / "copilot" / "prompts"
    expected_md = (prompts_dir / "extractor_subagent.md").read_text(encoding="utf-8")
    spec = build_extract_subagent_spec()
    assert spec["system_prompt"].strip() in expected_md or expected_md.strip() in spec["system_prompt"]


def test_extract_subagent_sandbox_tool_names_only():
    """Sandbox tools registered are the declared 3 — no parent tool leak."""
    from src.modules.vitalia.copilot.workflows.extract_subagent import (
        build_extract_subagent_spec,
    )

    spec = build_extract_subagent_spec()
    # Tools may be Callables or BaseTool-like; we look at `name` attribute or callable __name__.
    tool_names = []
    for tool in spec["tools"]:
        name = getattr(tool, "name", None)
        if name is None:
            name = getattr(tool, "__name__", None)
        tool_names.append(name)
    assert "scrape_website_tool" in tool_names
    assert "parse_document_tool" in tool_names
    assert "transcribe_audio_tool" in tool_names
    # Parent tools MUST NOT appear
    parent_tools = {
        "extract_tenant_context",
        "confirm_slot",
        "simulate_personality",
        "complete_onboarding",
    }
    for parent_tool_name in parent_tools:
        assert parent_tool_name not in tool_names, (
            f"Parent tool {parent_tool_name} leaked into subagent sandbox — F2/F4 sandbox violation"
        )


def test_sandbox_scrape_website_tool_returns_dict_with_text_field():
    """scrape_website_tool returns a structured dict (no parent state access)."""
    from src.modules.vitalia.copilot.workflows.extract_subagent_tools import (
        scrape_website_tool,
    )

    # Tool is a LangChain @tool; invoke its underlying func via .invoke or .func
    func = getattr(scrape_website_tool, "func", None) or scrape_website_tool
    result = func(url="https://example.com/about", timeout_seconds=1)
    assert isinstance(result, dict)
    assert "text" in result or "warning" in result


def test_sandbox_parse_document_tool_returns_dict_with_sections():
    """parse_document_tool returns dict with sections list."""
    from src.modules.vitalia.copilot.workflows.extract_subagent_tools import (
        parse_document_tool,
    )

    func = getattr(parse_document_tool, "func", None) or parse_document_tool
    result = func(
        text_content="Clínica Dental Norte\n\nUbicada en Lima, Perú.\nServicios dentales.",
    )
    assert isinstance(result, dict)
    assert "sections" in result


def test_sandbox_transcribe_audio_tool_rejects_long_audio():
    """transcribe_audio_tool warns on duration > 60s (per extractor_subagent.md spec)."""
    from src.modules.vitalia.copilot.workflows.extract_subagent_tools import (
        transcribe_audio_tool,
    )

    func = getattr(transcribe_audio_tool, "func", None) or transcribe_audio_tool
    # 65s duration triggers warning + no transcript
    result = func(audio_url="https://example.com/audio.mp3", duration_seconds=65)
    assert isinstance(result, dict)
    # Warning must indicate audio too long
    warnings = result.get("warnings", [])
    assert any("audio_too_long" in str(w) for w in warnings) or result.get("transcript") in (
        None,
        "",
    )


def test_extract_subagent_name_is_constant_string():
    """EXTRACT_SUBAGENT_NAME is a public constant string (orchestrator dispatch)."""
    from src.modules.vitalia.copilot.workflows.extract_subagent import (
        EXTRACT_SUBAGENT_NAME,
    )

    assert isinstance(EXTRACT_SUBAGENT_NAME, str)
    assert len(EXTRACT_SUBAGENT_NAME) > 0

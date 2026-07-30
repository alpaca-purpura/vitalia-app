"""ESC-5 — PromptLoader resolves its templates from the engine package, independent
of cwd. Architect-verified: RED (TemplateNotFound from a foreign cwd) before the fix.
"""

from luana_core_sales_agent.infrastructure.prompts.base import PromptLoader


def test_templates_resolve_from_arbitrary_cwd(monkeypatch, tmp_path) -> None:
    # Simulate a brand process running from a cwd that is NOT the engine package root.
    monkeypatch.chdir(tmp_path)
    loader = PromptLoader()
    # Must NOT raise jinja2.TemplateNotFound:
    loader.fs_env.get_template("message_completeness.j2")


def test_default_templates_dir_is_engine_package_relative() -> None:
    loader = PromptLoader()
    assert loader.templates_dir.endswith(
        "luana_core_sales_agent/infrastructure/prompts/templates"
    )


def test_explicit_override_still_honored(tmp_path) -> None:
    # Back-compat: explicit absolute dir is used as-is.
    (tmp_path / "x.j2").write_text("hi")
    loader = PromptLoader(templates_dir=str(tmp_path))
    assert loader.fs_env.get_template("x.j2").render() == "hi"

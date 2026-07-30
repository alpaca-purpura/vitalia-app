"""Unit tests for MultiRoleLLMRouter LiteLLM dispatch.

Post PI-12 S1 sales-agent-litellm-canonicalization T-7: legacy per-provider
dispatch path (LITELLM_PROXY_ENABLED=False) deleted. LiteLLMService is the
single canonical runtime path; the flag itself disappears in T-5. Only the
LiteLLM-on contract remains under test here — the legacy-toggle test was
exercising a path that no longer exists.

Contract: §16 of S3 PR-2 CONTRACT.md (singleton dispatch invariant).
"""

from __future__ import annotations

import pytest
from luana_core_platform.core.enums import ModelRole


def test_router_resolve_returns_litellm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_resolve(role) returns LiteLLMService — the only runtime dispatch path."""
    monkeypatch.setattr("luana_core_platform.core.config.settings.LITELLM_MASTER_KEY", "sk-test")
    monkeypatch.setattr("luana_core_platform.core.config.settings.LITELLM_BASE_URL", "http://litellm:4000/v1")

    from luana_core_llm.providers.litellm import LiteLLMService
    from luana_core_llm.router import MultiRoleLLMRouter

    router = MultiRoleLLMRouter()
    svc = router._resolve(ModelRole.NANO)
    assert isinstance(svc, LiteLLMService)


def test_router_litellm_singleton_across_roles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Same LiteLLMService instance returned for NANO + REASONING + AGENT."""
    monkeypatch.setattr("luana_core_platform.core.config.settings.LITELLM_MASTER_KEY", "sk-test")
    monkeypatch.setattr("luana_core_platform.core.config.settings.LITELLM_BASE_URL", "http://litellm:4000/v1")

    from luana_core_llm.router import MultiRoleLLMRouter

    router = MultiRoleLLMRouter()
    svc_nano = router._resolve(ModelRole.NANO)
    svc_reasoning = router._resolve(ModelRole.REASONING)
    svc_agent = router._resolve(ModelRole.AGENT)

    # All roles share a single LiteLLMService instance (singleton).
    assert svc_nano is svc_reasoning
    assert svc_nano is svc_agent


def test_router_generate_with_tools_delegates_to_provider() -> None:
    """Router MUST override generate_with_tools and delegate to the resolved provider.

    Regression: without the override the router inherited BaseLLMService's text-only
    fallback, so native function-calling (bind_tools) never ran in the live graph and
    brand tools were never offered to the LLM (dispatch rate 0).
    """
    from luana_core_llm.base import ToolCallResult
    from luana_core_llm.router import MultiRoleLLMRouter

    class _FakeProvider:
        def __init__(self) -> None:
            self.called_with: dict | None = None

        def generate_with_tools(self, messages, system_prompt=None, model_type="smart", tools=None, **kwargs):
            self.called_with = {"tools": tools, "messages": messages}
            return ToolCallResult(text="ok", tool_calls=[{"name": "t", "args": {}}])

    fake = _FakeProvider()
    router = MultiRoleLLMRouter()
    router._resolve = lambda role: fake  # type: ignore[assignment]

    tools = [{"type": "function", "function": {"name": "t", "description": "d", "parameters": {}}}]
    result = router.generate_with_tools(messages=[{"role": "user", "content": "hi"}], model_type="smart", tools=tools)

    assert fake.called_with is not None, "router did not delegate to provider"
    assert fake.called_with["tools"] == tools
    assert result.tool_calls == [{"name": "t", "args": {}}]

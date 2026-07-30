"""Abstract base class for LLM provider implementations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from luana_core_platform.core.enums import ModelRole


@dataclass(frozen=True)
class ToolCallResult:
    """Result of a tool-capable LLM call.

    ``text`` is the assistant's natural-language content; ``tool_calls`` is the
    structured native function-calls the model requested, each ``{"name": str,
    "args": dict}``. Empty ``tool_calls`` = the model answered without calling a
    tool (or the provider has no native tool support).
    """

    text: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


class BaseLLMService(ABC):
    """Abstract base for LLM providers following the Strategy Pattern."""

    @abstractmethod
    def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        model_type: str = "smart",
        **kwargs: Any,  # noqa: ANN401 — abstract LLM interface
    ) -> str:
        """Generate a text response from the LLM.

        Args:
            messages: List of message dicts [{"role": "user", "content": "..."}, ...]
            system_prompt: Optional system instruction to prepend or set.
            model_type: ModelRole enum or legacy string ("smart"/"fast").
            **kwargs: Extra parameters like temperature, max_tokens, etc.

        Returns:
            str: The generated text response.

        """

    def generate_with_tools(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        model_type: str = "smart",
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,  # noqa: ANN401 — abstract LLM interface
    ) -> ToolCallResult:
        """Generate a response with optional NATIVE function-calling.

        ``tools`` is a list of OpenAI-style function schemas
        (``{"type": "function", "function": {"name", "description", "parameters"}}``).
        The model MAY return structured ``tool_calls`` instead of / alongside text.

        Default implementation: providers without native tool support fall back to
        a text-only ``generate_response`` (empty ``tool_calls``) — back-compat, no
        behavior change. The LiteLLM provider overrides this with real
        ``bind_tools`` native calling.
        """
        text = self.generate_response(
            messages,
            system_prompt=system_prompt,
            model_type=model_type,
            **kwargs,
        )
        return ToolCallResult(text=text, tool_calls=[])

    @abstractmethod
    def get_embedding_model(self) -> Any:  # noqa: ANN401 — abstract LLM interface
        """Return a LangChain-compatible embedding model object."""

    @abstractmethod
    def get_client(
        self,
        role: ModelRole = ModelRole.REASONING,
        *,
        temperature: float | None = None,
    ) -> Any:  # noqa: ANN401 — abstract LLM interface
        """Return the underlying chat model client for the given role.

        Args:
            role: Model role (NANO/MINI/REASONING/HEAVY/AGENT).
            temperature: Optional override of the provider default temperature.
                Implementations MUST return a fresh ``BaseChatModel`` instance
                with the requested temperature baked in — they MUST NOT use
                ``Runnable.bind()`` to apply the override. ``deepagents 0.5+``
                rejects ``RunnableBinding`` in ``resolve_model`` (it is
                unhashable, and the harness profile cache uses dict lookup).
        """

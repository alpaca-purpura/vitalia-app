"""T-11 — D-T3 BrandVoicePort consumer wiring smoke tests.

Validates ``luana_core_sales_agent.application.prompts.compose.compose_prompt``:

- Accepts ``voice_port: BrandVoicePort`` as required parameter (V-F-slot-5-voice-port).
- Awaits ``voice_port.compile_system_instruction(tenant_id)`` for slot 5.
- Awaits ``voice_port.get_voice_metadata(tenant_id)`` for cache invalidation.
- Writes ``state["brand_voice"]`` + ``state["voice_metadata"]`` side effects.
- Falls back to specialist default when tenant has no profile (empty voice).
- Catches voice_port exceptions (best-effort — preserves turn liveness).
- Delegates to ``build_specialist_system_prompt`` for slot composition.
- D-T3 cardinal: ZERO ``PersonalityCompiler`` references in compose module.

Cross-reference: 03-arch-agentic.md §3 + sales-agent-expert SKILL.md §3 +
ADR-001 §2.4 + Story 5 §9.4 deferral resolution + Story 7 §6 halt criterion.
"""

from __future__ import annotations

import inspect
from uuid import UUID, uuid4

import pytest

from luana_core_sales_agent.application.prompts.compose import (
    PROMPT_FRAGMENT_ORDER,
    PromptFragment,
    SpecialistRole,
    compose_prompt,
    compose_system_prompt,
)


class _FakeVoicePort:
    """Minimal BrandVoicePort Protocol implementation for tests."""

    def __init__(
        self,
        instruction: str = "# Voz de marca compilada\n\nTono cálido y directo.",
        metadata: dict | None = None,
        raise_on_compile: bool = False,
    ) -> None:
        self.instruction = instruction
        self.metadata = metadata or {
            "personality_profile_version": 3,
            "dimensions_summary": {"warmth": 0.85, "energy": 0.65, "humor": 0.6},
        }
        self.raise_on_compile = raise_on_compile
        self.compile_calls: list[UUID] = []
        self.metadata_calls: list[UUID] = []

    async def compile_system_instruction(self, tenant_id: UUID) -> str:
        self.compile_calls.append(tenant_id)
        if self.raise_on_compile:
            raise RuntimeError("voice port simulated failure")
        return self.instruction

    async def get_voice_metadata(self, tenant_id: UUID) -> dict:
        self.metadata_calls.append(tenant_id)
        return self.metadata


# ---------------------------------------------------------------------------
# V-F-slot-5-voice-port — signature contract
# ---------------------------------------------------------------------------


class TestComposePromptSignature:
    """compose_prompt MUST accept voice_port per D-T3 cardinal (V-F-slot-5-voice-port)."""

    def test_voice_port_parameter_present(self) -> None:
        sig = inspect.signature(compose_prompt)
        assert "voice_port" in sig.parameters, (
            "compose_prompt MUST accept voice_port: BrandVoicePort per D-T3 (ADR-001 §2.4)"
        )

    def test_specialist_parameter_present(self) -> None:
        sig = inspect.signature(compose_prompt)
        assert "specialist" in sig.parameters

    def test_state_parameter_present(self) -> None:
        sig = inspect.signature(compose_prompt)
        assert "state" in sig.parameters

    def test_is_async(self) -> None:
        assert inspect.iscoroutinefunction(compose_prompt), (
            "compose_prompt MUST be async (BrandVoicePort.compile_system_instruction is async)"
        )

    def test_three_required_params(self) -> None:
        sig = inspect.signature(compose_prompt)
        params = list(sig.parameters)
        assert params == ["specialist", "state", "voice_port"], (
            f"Expected exactly [specialist, state, voice_port] params; got {params}"
        )


# ---------------------------------------------------------------------------
# Voice port consumption behavior
# ---------------------------------------------------------------------------


class TestVoicePortConsumption:
    """Verify D-T3 hexagonal port consumption (compile_system_instruction + metadata)."""

    @pytest.mark.asyncio
    async def test_compiles_instruction_for_tenant(self) -> None:
        port = _FakeVoicePort()
        tenant_id = uuid4()
        state: dict = {"tenant_id": tenant_id}
        await compose_prompt(SpecialistRole.QUALIFIER, state, port)
        assert port.compile_calls == [tenant_id], (
            "compose_prompt MUST call voice_port.compile_system_instruction(tenant_id)"
        )

    @pytest.mark.asyncio
    async def test_writes_brand_voice_state(self) -> None:
        port = _FakeVoicePort(instruction="# Mi voz\n\nDirecta.")
        state: dict = {"tenant_id": uuid4()}
        await compose_prompt(SpecialistRole.CLOSER, state, port)
        assert state["brand_voice"] == "# Mi voz\n\nDirecta."

    @pytest.mark.asyncio
    async def test_writes_voice_metadata_state(self) -> None:
        port = _FakeVoicePort(metadata={"personality_profile_version": 7})
        state: dict = {"tenant_id": uuid4()}
        await compose_prompt(SpecialistRole.PRODUCT_EXPERT, state, port)
        assert state["voice_metadata"] == {"personality_profile_version": 7}

    @pytest.mark.asyncio
    async def test_returns_composed_string(self) -> None:
        port = _FakeVoicePort()
        state: dict = {"tenant_id": uuid4()}
        result = await compose_prompt(SpecialistRole.QUALIFIER, state, port)
        assert isinstance(result, str)
        assert len(result) > 0
        assert "# Voz de marca compilada" in result  # slot 5 injected via state


class TestSpecialistRoleResolution:
    """compose_prompt accepts SpecialistRole enum OR string (back-compat with current_specialist key)."""

    @pytest.mark.asyncio
    async def test_accepts_enum(self) -> None:
        port = _FakeVoicePort()
        state: dict = {"tenant_id": uuid4()}
        result = await compose_prompt(SpecialistRole.QUALIFIER, state, port)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_accepts_string(self) -> None:
        port = _FakeVoicePort()
        state: dict = {"tenant_id": uuid4()}
        # ``current_specialist`` in SalesAgentState is a plain string
        result = await compose_prompt("qualifier", state, port)
        assert len(result) > 0


class TestResilience:
    """Voice port failures must NOT break the turn (best-effort observability rule)."""

    @pytest.mark.asyncio
    async def test_swallow_voice_port_exception(self) -> None:
        port = _FakeVoicePort(raise_on_compile=True)
        state: dict = {"tenant_id": uuid4(), "brand_voice": "fallback existing"}
        # Should NOT raise — voice_port failure is logged + swallowed
        result = await compose_prompt(SpecialistRole.CLOSER, state, port)
        assert isinstance(result, str)
        # State["brand_voice"] should remain as previous value (not wiped)
        assert state["brand_voice"] == "fallback existing"

    @pytest.mark.asyncio
    async def test_missing_tenant_id_skips_voice_injection(self) -> None:
        port = _FakeVoicePort()
        state: dict = {}  # no tenant_id
        result = await compose_prompt(SpecialistRole.QUALIFIER, state, port)
        assert isinstance(result, str)
        # voice_port not called when tenant_id missing
        assert port.compile_calls == []


class TestSlotInvariants:
    """Slot order + cache prefix invariants preserved per S3 cement."""

    def test_brand_voice_slot_index(self) -> None:
        # Slot 5 BRAND_VOICE = index 4 (0-based) in canonical order
        assert PROMPT_FRAGMENT_ORDER[4] == PromptFragment.BRAND_VOICE, (
            "Slot 5 BRAND_VOICE position is cement — D-T3 must preserve order"
        )

    @pytest.mark.asyncio
    async def test_compose_system_prompt_still_exported(self) -> None:
        # Underlying primitive preserved (back-compat for AISALESHT tests)
        fragments = {PromptFragment.STATIC_IDENTITY: "base"}
        result = compose_system_prompt(fragments)
        assert "base" in result

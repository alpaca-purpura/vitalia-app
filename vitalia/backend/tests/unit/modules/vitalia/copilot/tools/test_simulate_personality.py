"""Unit tests — simulate_personality LangChain @tool."""

from __future__ import annotations

import sys
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.modules.vitalia.copilot.tools.simulate_personality import (
    SimulatePersonalityInput,
    set_simulate_personality_service_factory,
    simulate_personality,
)

sim_mod = sys.modules["src.modules.vitalia.copilot.tools.simulate_personality"]

TENANT_ID = uuid4()


@pytest.fixture(autouse=True)
def _reset_factory() -> None:
    sim_mod._service_factory = None
    yield
    sim_mod._service_factory = None


class _FakeResponse:
    def __init__(self, sample_text: str, cache_hit: bool, generated_at: str = "ts") -> None:
        self.sample_text = sample_text
        self.cache_hit = cache_hit
        self.generated_at = generated_at


class TestSimulatePersonalityInputSchema:
    def test_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            SimulatePersonalityInput(tenant_id=TENANT_ID, scenario="x")  # type: ignore[call-arg]

    def test_scenario_min_length(self) -> None:
        with pytest.raises(ValidationError):
            SimulatePersonalityInput(tenant_id=TENANT_ID, profile_partial={"a": 1}, scenario="")

    def test_scenario_max_length(self) -> None:
        with pytest.raises(ValidationError):
            SimulatePersonalityInput(tenant_id=TENANT_ID, profile_partial={}, scenario="x" * 65)

    def test_profile_partial_accepts_dict(self) -> None:
        payload = SimulatePersonalityInput(tenant_id=TENANT_ID, profile_partial={"tone": "warm"}, scenario="greet")
        assert payload.profile_partial == {"tone": "warm"}


class TestSimulatePersonalityToolMetadata:
    def test_tool_name_is_canonical(self) -> None:
        assert simulate_personality.name == "simulate_personality"

    def test_tool_args_schema(self) -> None:
        assert simulate_personality.args_schema is SimulatePersonalityInput


class TestSimulatePersonalityBehavior:
    @pytest.mark.asyncio
    async def test_calls_service_with_kwargs(self) -> None:
        mock_service = AsyncMock()
        mock_service.simulate = AsyncMock(
            return_value=_FakeResponse(sample_text="Hola!", cache_hit=False),
        )
        set_simulate_personality_service_factory(lambda: mock_service)

        result = await simulate_personality.ainvoke(
            {
                "tenant_id": TENANT_ID,
                "profile_partial": {"tone": "warm"},
                "scenario": "greet",
            }
        )

        mock_service.simulate.assert_awaited_once_with(
            profile_partial={"tone": "warm"},
            scenario="greet",
            tenant_id=TENANT_ID,
        )
        assert "Hola!" in result
        assert "greet" in result
        assert "from cache" not in result  # cache_hit=False

    @pytest.mark.asyncio
    async def test_cache_hit_marker_in_output(self) -> None:
        mock_service = AsyncMock()
        mock_service.simulate = AsyncMock(
            return_value=_FakeResponse(sample_text="Cached!", cache_hit=True),
        )
        set_simulate_personality_service_factory(lambda: mock_service)

        result = await simulate_personality.ainvoke(
            {
                "tenant_id": TENANT_ID,
                "profile_partial": {"tone": "warm"},
                "scenario": "greet",
            }
        )

        assert "from cache" in result

    @pytest.mark.asyncio
    async def test_throttle_exception_surfaces_as_error_string(self) -> None:
        from src.modules.vitalia.copilot.application.services.simulate_personality_service import (
            ThrottleExceededError,
        )

        mock_service = AsyncMock()
        mock_service.simulate = AsyncMock(
            side_effect=ThrottleExceededError("simulate_personality"),
        )
        set_simulate_personality_service_factory(lambda: mock_service)

        result = await simulate_personality.ainvoke(
            {
                "tenant_id": TENANT_ID,
                "profile_partial": {"tone": "warm"},
                "scenario": "greet",
            }
        )

        assert "Error" in result
        assert "ThrottleExceeded" in result

    @pytest.mark.asyncio
    async def test_runtime_error_surfaces_as_error_string(self) -> None:
        mock_service = AsyncMock()
        mock_service.simulate = AsyncMock(side_effect=RuntimeError("adapter down"))
        set_simulate_personality_service_factory(lambda: mock_service)

        result = await simulate_personality.ainvoke(
            {
                "tenant_id": TENANT_ID,
                "profile_partial": {"tone": "warm"},
                "scenario": "greet",
            }
        )

        assert "Error simulating personality" in result
        assert "RuntimeError" in result

    @pytest.mark.asyncio
    async def test_tenant_id_isolation_flow(self) -> None:
        mock_service = AsyncMock()
        mock_service.simulate = AsyncMock(
            return_value=_FakeResponse(sample_text="X", cache_hit=False),
        )
        set_simulate_personality_service_factory(lambda: mock_service)

        await simulate_personality.ainvoke(
            {
                "tenant_id": TENANT_ID,
                "profile_partial": {},
                "scenario": "x",
            }
        )

        kwargs = mock_service.simulate.await_args.kwargs
        assert kwargs["tenant_id"] == TENANT_ID

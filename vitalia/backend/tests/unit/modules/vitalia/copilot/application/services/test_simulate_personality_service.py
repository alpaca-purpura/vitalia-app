"""RED tests — SimulatePersonalityService.

TDD per .claude/rules/tdd-mandatory.md.

Tests verify:
- simulate() returns cached result on cache hit (no rate limit check)
- simulate() calls rate limiter on cache miss
- simulate() raises ThrottleExceededError when rate limit exceeded
- simulate() calls personality adapter on successful rate check
- simulate() caches result with 10min TTL
- cache_hit flag set correctly in response
- tenant_id always passed (isolation)
"""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

TENANT_ID = uuid4()


class TestSimulatePersonalityServiceCacheHit:
    """Tests for SimulatePersonalityService when cache has result."""

    @pytest.mark.asyncio
    async def test_simulate_returns_cached_result(self) -> None:
        """simulate() returns cached result without calling adapter."""
        from src.modules.vitalia.copilot.application.services.simulate_personality_service import (
            SimulatePersonalityService,
        )

        cached_data = {
            "text": "Hola, soy tu asistente de clínica.",
            "scenario": "primera_respuesta",
            "generated_at": "2026-05-18T10:00:00+00:00",
        }
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=cached_data)
        mock_rate_limiter = AsyncMock()
        mock_adapter = AsyncMock()

        service = SimulatePersonalityService(
            personality_adapter=mock_adapter,
            cache=mock_cache,
            rate_limiter=mock_rate_limiter,
        )
        result = await service.simulate(
            profile_partial={"tenant.name": "Clínica Test"},
            scenario="primera_respuesta",
            tenant_id=TENANT_ID,
        )

        assert result.sample_text == "Hola, soy tu asistente de clínica."
        assert result.cache_hit is True
        mock_adapter.simulate.assert_not_called()
        mock_rate_limiter.check.assert_not_called()

    @pytest.mark.asyncio
    async def test_simulate_cache_hit_flag_true_on_hit(self) -> None:
        """simulate() sets cache_hit=True when result comes from cache."""
        from src.modules.vitalia.copilot.application.services.simulate_personality_service import (
            SimulatePersonalityService,
        )

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(
            return_value={
                "text": "cached response",
                "scenario": "test",
                "generated_at": "2026-05-18T10:00:00+00:00",
            }
        )

        service = SimulatePersonalityService(
            personality_adapter=AsyncMock(),
            cache=mock_cache,
            rate_limiter=AsyncMock(),
        )
        result = await service.simulate(
            profile_partial={},
            scenario="test",
            tenant_id=TENANT_ID,
        )

        assert result.cache_hit is True


class TestSimulatePersonalityServiceCacheMiss:
    """Tests for SimulatePersonalityService on cache miss."""

    @pytest.mark.asyncio
    async def test_simulate_checks_rate_limit_on_cache_miss(self) -> None:
        """simulate() checks rate limiter when cache misses."""
        from src.modules.vitalia.copilot.application.services.simulate_personality_service import (
            SimulatePersonalityService,
        )
        from src.modules.vitalia.copilot.domain.ports.personality_service_port import (
            PersonalitySimulationResult,
        )

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.check = AsyncMock(return_value=True)  # allowed

        mock_adapter = AsyncMock()
        mock_adapter.simulate = AsyncMock(
            return_value=PersonalitySimulationResult(
                text="generated text",
                scenario="primera_respuesta",
                generated_at="2026-05-18T10:00:00+00:00",
            )
        )

        service = SimulatePersonalityService(
            personality_adapter=mock_adapter,
            cache=mock_cache,
            rate_limiter=mock_rate_limiter,
        )
        await service.simulate(
            profile_partial={"tenant.name": "X"},
            scenario="primera_respuesta",
            tenant_id=TENANT_ID,
        )

        mock_rate_limiter.check.assert_called_once()
        # Key should include tenant_id for isolation
        call_kwargs = mock_rate_limiter.check.call_args
        assert str(TENANT_ID) in str(call_kwargs)

    @pytest.mark.asyncio
    async def test_simulate_raises_throttle_when_rate_limit_exceeded(self) -> None:
        """simulate() raises ThrottleExceededError when rate limit exceeded."""
        from src.modules.vitalia.copilot.application.services.simulate_personality_service import (
            SimulatePersonalityService,
            ThrottleExceededError,
        )

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.check = AsyncMock(return_value=False)  # throttled

        service = SimulatePersonalityService(
            personality_adapter=AsyncMock(),
            cache=mock_cache,
            rate_limiter=mock_rate_limiter,
        )

        with pytest.raises(ThrottleExceededError):
            await service.simulate(
                profile_partial={},
                scenario="primera_respuesta",
                tenant_id=TENANT_ID,
            )

    @pytest.mark.asyncio
    async def test_simulate_calls_adapter_on_cache_miss_and_allowed(self) -> None:
        """simulate() calls personality adapter when cache misses and rate ok."""
        from src.modules.vitalia.copilot.application.services.simulate_personality_service import (
            SimulatePersonalityService,
        )
        from src.modules.vitalia.copilot.domain.ports.personality_service_port import (
            PersonalitySimulationResult,
        )

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.check = AsyncMock(return_value=True)

        mock_adapter = AsyncMock()
        mock_adapter.simulate = AsyncMock(
            return_value=PersonalitySimulationResult(
                text="new text",
                scenario="test",
                generated_at="2026-05-18T10:00:00+00:00",
            )
        )

        service = SimulatePersonalityService(
            personality_adapter=mock_adapter,
            cache=mock_cache,
            rate_limiter=mock_rate_limiter,
        )
        result = await service.simulate(
            profile_partial={"tenant.name": "Clínica"},
            scenario="test",
            tenant_id=TENANT_ID,
        )

        mock_adapter.simulate.assert_called_once()
        assert result.sample_text == "new text"
        assert result.cache_hit is False

    @pytest.mark.asyncio
    async def test_simulate_stores_result_in_cache_with_ttl(self) -> None:
        """simulate() caches the result with 10-minute TTL (600 seconds)."""
        from src.modules.vitalia.copilot.application.services.simulate_personality_service import (
            SimulatePersonalityService,
        )
        from src.modules.vitalia.copilot.domain.ports.personality_service_port import (
            PersonalitySimulationResult,
        )

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.check = AsyncMock(return_value=True)

        mock_adapter = AsyncMock()
        mock_adapter.simulate = AsyncMock(
            return_value=PersonalitySimulationResult(
                text="result",
                scenario="s1",
                generated_at="2026-05-18T10:00:00+00:00",
            )
        )

        service = SimulatePersonalityService(
            personality_adapter=mock_adapter,
            cache=mock_cache,
            rate_limiter=mock_rate_limiter,
        )
        await service.simulate(
            profile_partial={},
            scenario="s1",
            tenant_id=TENANT_ID,
        )

        mock_cache.set.assert_called_once()
        set_call = mock_cache.set.call_args
        # TTL should be 600 seconds (10 minutes)
        assert set_call.kwargs.get("ttl") == 600 or (len(set_call.args) >= 3 and set_call.args[2] == 600)

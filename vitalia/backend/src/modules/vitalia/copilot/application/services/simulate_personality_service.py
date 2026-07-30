# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""SimulatePersonalityService — personality simulation with cache + rate limiting.

Generates a sample personality-aligned text response for the partially
configured tenant profile. Used in Valeria wizard to preview the brand voice
before committing the full onboarding.

Rate limit: 5 calls/min/tenant (Redis sliding window).
Cache TTL: 600 seconds (10 minutes) per slot combination + scenario.

No PHI: wizard config preview only.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import structlog

logger = structlog.get_logger()


class ThrottleExceededError(Exception):
    """Raised when the per-tenant rate limit for simulate_personality is exceeded."""

    def __init__(self, operation: str = "simulate_personality") -> None:
        """Initialize with operation name."""
        super().__init__(f"Rate limit exceeded for {operation}. Try again in 1 minute.")
        self.operation = operation


@dataclass
class SimulateResponse:
    """Response from personality simulation.

    Attributes:
        sample_text: Generated personality-aligned text sample.
        generated_at: UTC ISO timestamp of generation.
        cache_hit: True if result came from cache, False if freshly generated.
    """

    sample_text: str
    generated_at: str
    cache_hit: bool


def _profile_hash(profile_partial: dict[str, Any]) -> str:
    """Compute deterministic hash of profile_partial for cache key."""
    canonical = json.dumps(profile_partial, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


class SimulatePersonalityService:
    """Application service for personality simulation with cache + throttle.

    Pattern from 03-arch-be.md §8:
    - Check cache first (10 min TTL)
    - Check rate limiter (5/min/tenant)
    - Call adapter
    - Store in cache

    Dependencies injected — no direct Redis or HTTP imports.
    """

    CACHE_TTL_SECONDS = 600  # 10 minutes
    RATE_LIMIT_PER_MINUTE = 5
    RATE_LIMIT_WINDOW_SECONDS = 60

    def __init__(
        self,
        personality_adapter: "object",
        cache: "object",
        rate_limiter: "object",
    ) -> None:
        """Initialize with injected adapters."""
        self._adapter = personality_adapter
        self._cache = cache
        self._rate_limiter = rate_limiter

    async def simulate(
        self,
        *,
        profile_partial: dict[str, Any],
        scenario: str,
        tenant_id: UUID,
    ) -> SimulateResponse:
        """Generate a personality-aligned sample text for the given partial profile.

        Args:
            profile_partial: Partial slot values defining the personality.
            scenario: Scenario context string (e.g. "primera_respuesta").
            tenant_id: Tenant isolation identifier.

        Returns:
            SimulateResponse with sample_text, generated_at, and cache_hit.

        Raises:
            ThrottleExceededError: When per-tenant rate limit exceeded.
        """
        profile_hash = _profile_hash(profile_partial)
        cache_key = f"vitalia:simulate:{tenant_id}:{profile_hash}:{scenario}"

        # 1. Check cache
        cached = await self._cache.get(cache_key)
        if cached is not None:
            logger.info(
                "simulate_personality_cache_hit",
                tenant_id=str(tenant_id),
                scenario=scenario,
                cache_key=cache_key,
            )
            return SimulateResponse(
                sample_text=cached["text"],
                generated_at=cached["generated_at"],
                cache_hit=True,
            )

        # 2. Check rate limit (only on cache miss)
        rate_key = f"vitalia:simulate:{tenant_id}"
        allowed = await self._rate_limiter.check(
            key=rate_key,
            limit=self.RATE_LIMIT_PER_MINUTE,
            window_seconds=self.RATE_LIMIT_WINDOW_SECONDS,
        )
        if not allowed:
            logger.warning(
                "simulate_personality_throttled",
                tenant_id=str(tenant_id),
                scenario=scenario,
            )
            raise ThrottleExceededError("simulate_personality")

        # 3. Call adapter
        result = await self._adapter.simulate(
            profile_partial=profile_partial,
            scenario=scenario,
            tenant_id=tenant_id,
        )

        # 4. Cache result
        await self._cache.set(cache_key, result.model_dump(), ttl=self.CACHE_TTL_SECONDS)

        logger.info(
            "simulate_personality_generated",
            tenant_id=str(tenant_id),
            scenario=scenario,
        )
        return SimulateResponse(
            sample_text=result.text,
            generated_at=result.generated_at,
            cache_hit=False,
        )

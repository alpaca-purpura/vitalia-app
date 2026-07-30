"""BrandVoicePort — hexagonal port wrapping the voice compiler engine.

Introduced Story 7 (luana-sales-agent-engine) per ADR-001 §2.4 + Session 3
ratificación + Story 5 §9.4 deferral resolution.

Cardinal invariants (Story 7 §1.3 + §1.5 + §2.5):

- ``PersonalityCompiler`` SSoT lives in
  ``luana_core_brand_studio.domain.personality`` (Story 5 placement —
  arch fitness V-AG-7 regression Stories 5+6 enforces).
- Cross-package consumers (notably ``luana-core-sales-agent``) MUST
  consume voice via this port — NEVER ``from
  luana_core_brand_studio.domain.personality import PersonalityCompiler``
  (arch fitness V-AG-3 Story 7 enforces).
- Public surface FROZEN at 2 methods: ``compile_system_instruction`` +
  ``get_voice_metadata``. Adding methods requires architect ratification
  (Story 7 §6 halt #2).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class BrandVoicePort(Protocol):
    """Voice compiler port — consumed by luana-core-sales-agent slot 5 BRAND_VOICE prefix.

    Per ADR-001 §2.4: ``PersonalityCompiler`` lives in
    ``luana_core_brand_studio.domain.personality``. ``BrandVoicePort``
    wraps it for cross-module consumption — sales-agent never imports
    ``PersonalityCompiler`` directly (hexagonal DDD boundary).

    Public methods FROZEN at Story 7 introduction. Bumping the surface
    requires architect ratification per Story 7 §6 halt criterion #2.
    """

    async def compile_system_instruction(self, tenant_id: UUID) -> str:
        """Compile tenant's PersonalityProfile to a 5-block system_instruction.

        Returns the compiled voice prompt prefix for slot 5
        BRAND_VOICE injection in sales-agent ``compose_prompt``.

        Returns an empty string if the tenant has no active
        ``PersonalityProfile`` — the consumer falls back to the
        specialist default voice.
        """
        ...

    async def get_voice_metadata(self, tenant_id: UUID) -> dict:
        """Return voice metadata for prompt cache invalidation + routing.

        Schema (FROZEN — additions require architect ratification):

        - ``personality_profile_version: int`` — bumps on profile update;
          0 when no active profile (consumer treats as default voice).
        - ``last_compiled_at: datetime | None`` — for cache TTL decisions.
        - ``dimensions_summary: dict`` — e.g.
          ``{"energy": 0.65, "warmth": 0.85, "humor": 0.6, ...}`` for
          downstream routing decisions; empty dict when no profile.
        """
        ...

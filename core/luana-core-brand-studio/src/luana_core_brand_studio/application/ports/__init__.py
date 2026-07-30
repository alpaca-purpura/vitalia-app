"""Application ports — hexagonal DDD boundaries for cross-package consumers.

Per ADR-001 §2.4 + Story 7 §1.3 — engines own SSoT in their domain layer
(``brand_studio.domain.personality.PersonalityCompiler``); ports expose
narrow async interfaces consumers depend on without coupling to engine
internals.

Public exports:

- ``BrandVoicePort`` — voice compiler port consumed by
  ``luana-core-sales-agent`` slot 5 BRAND_VOICE prefix (Story 7 D-T3
  introduction).
"""

from luana_core_brand_studio.application.ports.brand_voice_port import BrandVoicePort

__all__ = ["BrandVoicePort"]

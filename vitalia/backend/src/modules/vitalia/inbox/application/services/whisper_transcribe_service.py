# cap: sales_agent.inbox-handler-mode-occ
# story-origin: TBD
"""WhisperTranscribeService — vitalia inbox application layer.

Wraps WhisperAdapter with confidence threshold + fallback.

PHI obligations (hipaa-lite.md § Regla cardinal):
- Raw transcript NOT logged (only confidence + status metadata)
- transcription_text is PHI — service passes to caller for safe storage
- HIPAA-lite: confidence < 0.5 triggers fallback (transcript not reliable)

Per 03-arch-be.md § 6.7:
- Timeout: 30s (handled by WhisperAdapter)
- Confidence threshold: 0.5 (< 0.5 → fallback, text=None)
- Cost: ~$0.006/min → log to copilot_llm_call (future story, Slice 1 skips)

downstream-regression-na: brand-local vitalia inbox service
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import structlog

from src.modules.vitalia.connections.whisper.adapter import WhisperAdapter

logger = structlog.get_logger()

# Confidence threshold below which we consider transcription unreliable
_CONFIDENCE_THRESHOLD = 0.5


@dataclass
class TranscribeResult:
    """Result from WhisperTranscribeService.transcribe()."""

    transcription_text: str | None
    transcription_confidence: float | None
    fallback_triggered: bool


class WhisperTranscribeService:
    """Service wrapping WhisperAdapter with confidence gate + fallback.

    If confidence < 0.5 (or text=None from timeout/error), returns
    transcription_text=None and fallback_triggered=True. Caller (SendMessageService
    or router) applies the fallback UI message per SC-02.

    HIPAA-lite: raw transcript NOT logged. Only confidence + fallback status logged.
    """

    def __init__(self, *, whisper_adapter: WhisperAdapter) -> None:
        """Initialize WhisperTranscribeService.

        Args:
            whisper_adapter: WhisperAdapter instance (timeout 30s, graceful-degradation).
        """
        self._adapter = whisper_adapter

    async def transcribe(
        self,
        *,
        audio_url: str,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> TranscribeResult:
        """Transcribe audio with confidence gate.

        PHI note: audio_url not logged (could identify patient session).
        Only confidence + fallback_triggered logged.

        Args:
            audio_url: Pre-signed URL to audio file (S3/CDN).
            tenant_id: Root tenant UUID (for logging context only).
            clinic_id: Clinic UUID (for logging context only).

        Returns:
            TranscribeResult with optional text + confidence + fallback flag.
        """
        result = await self._adapter.transcribe(audio_url=audio_url)

        # Apply confidence threshold
        if result.text is None or result.confidence < _CONFIDENCE_THRESHOLD:
            logger.info(
                "whisper_transcribe.fallback",
                confidence=round(result.confidence, 3),
                has_text=result.text is not None,
                # HIPAA-lite: NO audio_url, NO transcript text logged
            )
            return TranscribeResult(
                transcription_text=None,
                transcription_confidence=result.confidence if result.text is not None else 0.0,
                fallback_triggered=True,
            )

        # HIPAA-lite: log ONLY confidence + success, NOT raw transcript
        logger.info(
            "whisper_transcribe.success",
            confidence=round(result.confidence, 3),
            fallback_triggered=False,
        )

        return TranscribeResult(
            transcription_text=result.text,
            transcription_confidence=result.confidence,
            fallback_triggered=False,
        )

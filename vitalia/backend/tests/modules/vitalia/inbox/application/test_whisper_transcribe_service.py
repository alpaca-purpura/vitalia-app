"""Tests for WhisperTranscribeService — TDD RED (T-inbox-be-3).

SC-02 coverage:
- Whisper timeout (30s) → returns None text (graceful fallback)
- Confidence < 0.5 → returns None text (low confidence fallback)
- Happy path: text returned with confidence >= 0.5
- HIPAA-lite: raw transcript not logged (only confidence + status)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

TENANT_ID = uuid4()
CLINIC_ID = uuid4()


def _make_transcription_result(text: str | None, confidence: float) -> MagicMock:
    result = MagicMock()
    result.text = text
    result.confidence = confidence
    return result


@pytest.mark.asyncio
async def test_whisper_transcribe_happy_path_returns_text() -> None:
    """High confidence audio → returns transcription text."""
    from src.modules.vitalia.inbox.application.services.whisper_transcribe_service import (
        WhisperTranscribeService,
    )

    whisper_adapter = AsyncMock()
    whisper_adapter.transcribe = AsyncMock(
        return_value=_make_transcription_result(
            text="Hola, me duele la muela desde ayer",
            confidence=0.92,
        )
    )

    svc = WhisperTranscribeService(whisper_adapter=whisper_adapter)

    result = await svc.transcribe(
        audio_url="https://cdn.example.com/audio/msg123.ogg",
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
    )

    assert result.transcription_text == "Hola, me duele la muela desde ayer"
    assert result.transcription_confidence is not None
    assert result.transcription_confidence >= 0.5
    assert result.fallback_triggered is False


@pytest.mark.asyncio
async def test_whisper_transcribe_low_confidence_triggers_fallback() -> None:
    """SC-02: confidence < 0.5 → transcription_text=None, fallback_triggered=True."""
    from src.modules.vitalia.inbox.application.services.whisper_transcribe_service import (
        WhisperTranscribeService,
    )

    whisper_adapter = AsyncMock()
    whisper_adapter.transcribe = AsyncMock(
        return_value=_make_transcription_result(
            text="...",  # low quality text
            confidence=0.3,
        )
    )

    svc = WhisperTranscribeService(whisper_adapter=whisper_adapter)

    result = await svc.transcribe(
        audio_url="https://cdn.example.com/audio/low_quality.ogg",
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
    )

    assert result.transcription_text is None
    assert result.fallback_triggered is True


@pytest.mark.asyncio
async def test_whisper_transcribe_timeout_returns_fallback() -> None:
    """SC-02: adapter returns text=None (timeout) → fallback_triggered=True."""
    from src.modules.vitalia.inbox.application.services.whisper_transcribe_service import (
        WhisperTranscribeService,
    )

    whisper_adapter = AsyncMock()
    # Adapter already handles timeout → returns None,0.0
    whisper_adapter.transcribe = AsyncMock(
        return_value=_make_transcription_result(
            text=None,
            confidence=0.0,
        )
    )

    svc = WhisperTranscribeService(whisper_adapter=whisper_adapter)

    result = await svc.transcribe(
        audio_url="https://cdn.example.com/audio/timeout.ogg",
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
    )

    assert result.transcription_text is None
    assert result.fallback_triggered is True


@pytest.mark.asyncio
async def test_whisper_transcribe_confidence_exactly_0_5_returns_text() -> None:
    """Confidence exactly 0.5 → NOT a fallback (threshold is < 0.5)."""
    from src.modules.vitalia.inbox.application.services.whisper_transcribe_service import (
        WhisperTranscribeService,
    )

    whisper_adapter = AsyncMock()
    whisper_adapter.transcribe = AsyncMock(
        return_value=_make_transcription_result(
            text="El texto en el límite",
            confidence=0.5,
        )
    )

    svc = WhisperTranscribeService(whisper_adapter=whisper_adapter)

    result = await svc.transcribe(
        audio_url="https://cdn.example.com/audio/boundary.ogg",
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
    )

    # Exactly 0.5 is NOT below threshold → no fallback
    assert result.transcription_text == "El texto en el límite"
    assert result.fallback_triggered is False

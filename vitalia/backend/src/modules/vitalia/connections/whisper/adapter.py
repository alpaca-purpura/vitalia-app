# cap: connections.oauth-meta-google-ads
# story-origin: TBD
"""Whisper STT adapter — vitalia connections module.

Wraps OpenAI Whisper API via httpx.AsyncClient with:
- 30s timeout per 05-guidelines.md § 13 (graceful degradation)
- Fallback: returns TranscriptionResult(text=None, confidence=0.0) on error
- HIPAA-lite: NO raw transcript text in logs (only metadata: duration, confidence, status)
- Confidence derived from segments[].avg_logprob (log probability → 0.0-1.0 linear scale)

Per `.claude/rules/tdd-mandatory.md`: tests written FIRST (RED).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import httpx
import structlog

# downstream-regression-na: brand-local vitalia connections whisper adapter

logger = structlog.get_logger()

_WHISPER_API_URL = "https://api.openai.com/v1/audio/transcriptions"
_WHISPER_MODEL = "whisper-1"
_TIMEOUT_SECONDS = 30.0

# HIPAA-lite: log-safe sentinel for avg_logprob → confidence transform
_MIN_LOG_PROB = -2.0  # below this → confidence ~0
_MAX_LOG_PROB = 0.0  # at 0 → confidence 1.0


@dataclass
class TranscriptionResult:
    """Result from WhisperAdapter.transcribe().

    text: None if transcription failed or empty (caller applies fallback message).
    confidence: 0.0-1.0 derived from segments avg_logprob. 0.0 if error or empty.
    """

    text: str | None
    confidence: float


def _logprob_to_confidence(avg_logprob: float) -> float:
    """Convert avg_logprob from Whisper segments to 0.0-1.0 confidence score.

    Whisper returns log probabilities, typically in range [-2, 0].
    -0.1 → high confidence (~0.95).
    -2.5 → low confidence (~0.0).
    """
    # Linear interpolation: clamp to [_MIN_LOG_PROB, _MAX_LOG_PROB]
    clamped = max(_MIN_LOG_PROB, min(_MAX_LOG_PROB, avg_logprob))
    # Normalize to [0.0, 1.0]
    return (clamped - _MIN_LOG_PROB) / (_MAX_LOG_PROB - _MIN_LOG_PROB)


def _extract_confidence(data: dict) -> float:
    """Extract confidence from Whisper API response data.

    Returns 0.0 if segments absent or empty.
    HIPAA-lite: logs only metadata (confidence float), not raw transcript.
    """
    segments = data.get("segments", [])
    if not segments:
        return 0.0

    # Average logprob across segments
    total_logprob = 0.0
    valid_count = 0
    for seg in segments:
        logprob = seg.get("avg_logprob")
        if logprob is not None and math.isfinite(float(logprob)):
            total_logprob += float(logprob)
            valid_count += 1

    if valid_count == 0:
        return 0.0

    avg = total_logprob / valid_count
    return _logprob_to_confidence(avg)


class WhisperAdapter:
    """Async Whisper STT adapter with graceful degradation.

    Usage:
        adapter = WhisperAdapter(api_key="sk-...")
        result = await adapter.transcribe(audio_url="https://...")
        if result.text is None:
            # show fallback message to user (WhisperTranscribeService handles this)
            ...
    """

    def __init__(self, api_key: str) -> None:
        """Initialize WhisperAdapter with OpenAI API key."""
        self._api_key = api_key

    async def transcribe(self, audio_url: str) -> TranscriptionResult:
        """Transcribe audio from URL via OpenAI Whisper API.

        Timeout: 30s (per 05-guidelines.md § 13 graceful degradation).
        On timeout or HTTP error: returns TranscriptionResult(text=None, confidence=0.0).
        HIPAA-lite: raw transcript text NOT logged, only confidence + status metadata.

        Args:
            audio_url: URL to the audio file (S3/CDN). Whisper fetches via URL param.

        Returns:
            TranscriptionResult with text and confidence (0.0-1.0).
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    _WHISPER_API_URL,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                    },
                    json={
                        "model": _WHISPER_MODEL,
                        "url": audio_url,
                        "response_format": "verbose_json",
                    },
                    timeout=_TIMEOUT_SECONDS,
                )
                response.raise_for_status()

        except httpx.TimeoutException:
            logger.warning(
                "whisper_transcribe_timeout",
                timeout_seconds=_TIMEOUT_SECONDS,
                # HIPAA-lite: NO audio_url logged (could identify patient session)
            )
            return TranscriptionResult(text=None, confidence=0.0)

        except httpx.HTTPStatusError as exc:
            logger.error(
                "whisper_transcribe_http_error",
                status_code=exc.response.status_code,
                # HIPAA-lite: NO audio_url, NO transcript text logged
            )
            return TranscriptionResult(text=None, confidence=0.0)

        except Exception:
            logger.error(
                "whisper_transcribe_unexpected_error",
                # HIPAA-lite: NO raw data logged
            )
            return TranscriptionResult(text=None, confidence=0.0)

        data = response.json()
        text = data.get("text", "")

        if not text:
            logger.info(
                "whisper_transcribe_empty_result",
                confidence=0.0,
            )
            return TranscriptionResult(text=None if text == "" else text, confidence=0.0)

        confidence = _extract_confidence(data)

        # HIPAA-lite: log ONLY confidence + success, NOT raw transcript text
        logger.info(
            "whisper_transcribe_success",
            confidence=round(confidence, 3),
        )

        return TranscriptionResult(text=text, confidence=confidence)

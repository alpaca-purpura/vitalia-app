# cap: connections.oauth-meta-google-ads
# story-origin: TBD
"""Whisper STT connection adapter — vitalia connections module.

Provides async transcription via OpenAI Whisper API with graceful degradation.
"""

from __future__ import annotations

# downstream-regression-na: brand-local vitalia connections whisper module
from src.modules.vitalia.connections.whisper.adapter import (
    TranscriptionResult,
    WhisperAdapter,
)

__all__ = [
    "WhisperAdapter",
    "TranscriptionResult",
]

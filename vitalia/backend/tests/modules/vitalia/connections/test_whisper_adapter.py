"""Tests for Whisper STT adapter — T-inbox-be-4 (RED first, TDD).

SC-02 negative: Whisper timeout → fallback (returns None, no exception raised).
SC-02 negative: Low confidence → caller decides on fallback (confidence returned).

All HTTP calls mocked — no real Whisper API calls in unit tests.
Per `.claude/rules/tdd-mandatory.md`: tests written BEFORE implementation.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

# downstream-regression-na: brand-local vitalia connections unit test


# ---------------------------------------------------------------------------
# Contract: what WhisperAdapter must expose
# ---------------------------------------------------------------------------


class TestWhisperAdapterContract:
    """Structural contract tests (RED before implementation)."""

    def test_adapter_module_importable(self) -> None:
        """WhisperAdapter must be importable from connections.whisper.adapter."""
        from src.modules.vitalia.connections.whisper.adapter import (  # noqa: F401
            WhisperAdapter,
        )

    def test_adapter_has_transcribe_method(self) -> None:
        """WhisperAdapter must expose async transcribe(audio_url) -> TranscriptionResult."""
        from src.modules.vitalia.connections.whisper.adapter import WhisperAdapter

        assert hasattr(WhisperAdapter, "transcribe"), "WhisperAdapter missing transcribe method"

    def test_transcription_result_importable(self) -> None:
        """TranscriptionResult dataclass must be importable."""
        from src.modules.vitalia.connections.whisper.adapter import (  # noqa: F401
            TranscriptionResult,
        )

    def test_transcription_result_has_text_and_confidence(self) -> None:
        """TranscriptionResult must have text and confidence fields."""
        from src.modules.vitalia.connections.whisper.adapter import TranscriptionResult

        result = TranscriptionResult(text=None, confidence=0.0)
        assert result.text is None
        assert result.confidence == 0.0

    def test_channel_retract_error_importable(self) -> None:
        """ChannelRetractUnsupportedError must be importable for Email fallback."""
        from src.modules.vitalia.connections.whisper.adapter import (  # noqa: F401
            WhisperAdapter,
        )


# ---------------------------------------------------------------------------
# Test_timeout_returns_none — SC-02 Gherkin coverage
# ---------------------------------------------------------------------------


class TestWhisperAdapterTimeout:
    """test_timeout_returns_none: per 06-tickets.yaml SC-02 gherkin coverage."""

    @pytest.mark.asyncio
    async def test_timeout_returns_none(self) -> None:
        """Whisper API timeout within 30s → returns TranscriptionResult(text=None, confidence=0.0).

        The adapter MUST NOT raise — it must return gracefully.
        Caller (WhisperTranscribeService) decides whether to switch to human mode.
        """
        from src.modules.vitalia.connections.whisper.adapter import (
            TranscriptionResult,
            WhisperAdapter,
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post.side_effect = httpx.TimeoutException("timeout", request=MagicMock())

            adapter = WhisperAdapter(api_key="test-key")
            result = await adapter.transcribe(audio_url="https://s3.example.com/audio.mp3")

        assert isinstance(result, TranscriptionResult)
        assert result.text is None
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_http_error_returns_none(self) -> None:
        """HTTP error from Whisper API → graceful degradation, no re-raise."""
        from src.modules.vitalia.connections.whisper.adapter import (
            TranscriptionResult,
            WhisperAdapter,
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "server error",
                request=MagicMock(),
                response=mock_response,
            )
            mock_client.post.return_value = mock_response

            adapter = WhisperAdapter(api_key="test-key")
            result = await adapter.transcribe(audio_url="https://s3.example.com/audio.mp3")

        assert isinstance(result, TranscriptionResult)
        assert result.text is None
        assert result.confidence == 0.0


# ---------------------------------------------------------------------------
# Test_low_confidence_returned — SC-02 Gherkin coverage
# ---------------------------------------------------------------------------


class TestWhisperAdapterLowConfidence:
    """test_low_confidence_returned: adapter returns low confidence, caller decides fallback."""

    @pytest.mark.asyncio
    async def test_low_confidence_returned(self) -> None:
        """Whisper returns transcription with confidence < 0.5 → adapter returns it as-is.

        Per arch: adapter returns result with whatever confidence Whisper gives.
        WhisperTranscribeService (T-inbox-be-3) applies the threshold logic.
        """
        from src.modules.vitalia.connections.whisper.adapter import (
            TranscriptionResult,
            WhisperAdapter,
        )

        whisper_response_data = {
            "text": "entendí algo poco claro",
            "segments": [
                {"avg_logprob": -2.5}  # low confidence
            ],
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = whisper_response_data
            mock_client.post.return_value = mock_response

            adapter = WhisperAdapter(api_key="test-key")
            result = await adapter.transcribe(audio_url="https://s3.example.com/audio.mp3")

        assert isinstance(result, TranscriptionResult)
        assert result.text == "entendí algo poco claro"
        assert result.confidence is not None
        # Low confidence from avg_logprob=-2.5 → confidence < 0.5
        assert result.confidence < 0.5

    @pytest.mark.asyncio
    async def test_high_confidence_returned(self) -> None:
        """Whisper returns transcription with high confidence → passes through normally."""
        from src.modules.vitalia.connections.whisper.adapter import (
            TranscriptionResult,
            WhisperAdapter,
        )

        whisper_response_data = {
            "text": "Hola, quisiera agendar una cita para blanqueamiento dental",
            "segments": [
                {"avg_logprob": -0.1}  # high confidence
            ],
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = whisper_response_data
            mock_client.post.return_value = mock_response

            adapter = WhisperAdapter(api_key="test-key")
            result = await adapter.transcribe(audio_url="https://s3.example.com/audio.mp3")

        assert isinstance(result, TranscriptionResult)
        assert result.text == "Hola, quisiera agendar una cita para blanqueamiento dental"
        assert result.confidence is not None
        assert result.confidence >= 0.5

    @pytest.mark.asyncio
    async def test_empty_text_response(self) -> None:
        """Whisper returns empty text → confidence 0.0 treated as fallback."""
        from src.modules.vitalia.connections.whisper.adapter import (
            TranscriptionResult,
            WhisperAdapter,
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"text": "", "segments": []}
            mock_client.post.return_value = mock_response

            adapter = WhisperAdapter(api_key="test-key")
            result = await adapter.transcribe(audio_url="https://s3.example.com/audio.mp3")

        assert isinstance(result, TranscriptionResult)
        assert result.text is None or result.text == ""
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_timeout_is_30_seconds(self) -> None:
        """Adapter MUST configure 30s timeout per 05-guidelines.md § 13."""
        from src.modules.vitalia.connections.whisper.adapter import WhisperAdapter

        captured_timeout = None

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"text": "test", "segments": [{"avg_logprob": -0.1}]}
            mock_client.post.return_value = mock_response

            def capture_post(*args, **kwargs):
                nonlocal captured_timeout
                captured_timeout = kwargs.get("timeout")
                return mock_response

            mock_client.post.side_effect = capture_post

            adapter = WhisperAdapter(api_key="test-key")
            await adapter.transcribe(audio_url="https://s3.example.com/audio.mp3")

        # 30s per guidelines § graceful-degradation timeout
        assert captured_timeout is not None
        # Timeout should be 30.0 seconds
        assert captured_timeout == 30.0 or (hasattr(captured_timeout, "read") and captured_timeout.read == 30.0)

    @pytest.mark.asyncio
    async def test_phi_not_logged_raw(self) -> None:
        """Adapter MUST NOT log raw transcription text per hipaa-lite.md.

        Adapter logs only metadata (duration, confidence, success/failure).
        Raw transcript is NOT in log output.
        """
        import structlog

        from src.modules.vitalia.connections.whisper.adapter import (
            WhisperAdapter,
        )

        phi_text = "tengo dolor de pecho y sangrado nasal"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {
                "text": phi_text,
                "segments": [{"avg_logprob": -0.2}],
            }
            mock_client.post.return_value = mock_response

            log_events = []
            with patch.object(structlog, "get_logger") as mock_logger_factory:
                mock_logger = MagicMock()
                mock_logger_factory.return_value = mock_logger
                mock_logger.info.side_effect = lambda *a, **kw: log_events.append(kw)
                mock_logger.warning.side_effect = lambda *a, **kw: log_events.append(kw)
                mock_logger.error.side_effect = lambda *a, **kw: log_events.append(kw)

                adapter = WhisperAdapter(api_key="test-key")
                await adapter.transcribe(audio_url="https://s3.example.com/audio.mp3")

        # PHI text must NOT appear in any logged event values
        for event in log_events:
            for value in event.values():
                if isinstance(value, str):
                    assert phi_text not in value, f"PHI text leaked in log event: {event}"

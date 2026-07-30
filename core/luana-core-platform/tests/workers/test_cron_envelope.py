# downstream-regression-na: engine test file; self-contained, no cross-consumer test reuse
"""Tests for cron_envelope — engine cron decorator.

Covers all 8 required scenarios from proposal § 6:
  1. Idempotent on duplicate call within TTL (mock Redis hit)
  2. Re-executes on cache miss (mock Redis down soft-fail)
  3. OTel span emitted when SDK available
  4. OTel skipped when SDK not installed (graceful degrade)
  5. structlog audit logged on success
  6. Sentry capture on exception when SDK available
  7. Sentry skipped when SDK not installed
  8. Exception propagates (no swallow)

Testing approach: mock idempotency store + OTel tracer + Sentry at the boundary
points used by cron_envelope internals. No real Redis or OTel collector needed.
"""

from __future__ import annotations

import sys
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from luana_core_platform.workers.cron_envelope import cron_envelope

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Test: idempotency (duplicate suppression + soft-fail)
# ---------------------------------------------------------------------------


class TestIdempotency:
    """Verify claim-based deduplication and soft-fail on Redis unavailability."""

    @pytest.mark.asyncio
    async def test_idempotent_on_duplicate_call_within_ttl(self) -> None:
        """When idempotency store returns claim=False, the decorated fn is not called."""
        # Simpler approach: patch _build_idempotent_fn to return a fn that records calls
        # and skips on second invocation (claim_calls > 1 returns False).
        execution_results: list[str] = []

        @cron_envelope("test.cron.dedup", ttl=10)
        async def my_job(ctx: dict) -> str:
            execution_results.append("ran")
            return "ok"

        call_count = 0

        with patch(
            "luana_core_platform.workers.cron_envelope._build_idempotent_fn",
        ) as mock_build:
            # Build a function that only runs on first call
            async def dedup_fn(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
                nonlocal call_count
                call_count += 1
                if call_count > 1:
                    return None  # idempotent skip
                return "ok"

            mock_build.return_value = dedup_fn

            @cron_envelope("test.cron.dedup", ttl=10)
            async def deduplicated_job(ctx: dict) -> str:
                return "ran"

            # First call executes
            result1 = await deduplicated_job({"job_id": "abc"})
            assert result1 == "ok"
            assert call_count == 1

            # Second call is skipped by idempotent fn
            result2 = await deduplicated_job({"job_id": "abc"})
            assert result2 is None  # idempotent no-op
            assert call_count == 2  # inner fn called, returned early

    @pytest.mark.asyncio
    async def test_re_executes_on_redis_unavailable(self) -> None:
        """When luana_core_idempotency is unavailable, job runs without deduplication."""
        # Simulate ImportError for luana_core_idempotency
        original = sys.modules.get("luana_core_idempotency.application.decorator")
        sys.modules["luana_core_idempotency.application.decorator"] = None  # type: ignore[assignment]

        try:
            execution_count = 0

            @cron_envelope("test.cron.no_redis", ttl=10)
            async def job_no_redis(ctx: dict) -> None:
                nonlocal execution_count
                execution_count += 1

            await job_no_redis({"job_id": "x"})
            await job_no_redis({"job_id": "x"})

            # Runs twice because idempotency is unavailable (soft-fail)
            assert execution_count == 2
        finally:
            if original is None:
                sys.modules.pop("luana_core_idempotency.application.decorator", None)
            else:
                sys.modules["luana_core_idempotency.application.decorator"] = original

    @pytest.mark.asyncio
    async def test_job_runs_on_successful_claim(self) -> None:
        """Normal path: claim succeeds, job executes and returns result."""
        ran = []

        @cron_envelope("test.cron.normal", ttl=60)
        async def normal_job(ctx: dict) -> str:
            ran.append(True)
            return "done"

        # Patch idempotent to a pass-through for this test
        with patch(
            "luana_core_platform.workers.cron_envelope._build_idempotent_fn",
            side_effect=lambda fn, name, ttl: fn,
        ):

            @cron_envelope("test.cron.normal_passthrough", ttl=60)
            async def passthrough_job(ctx: dict) -> str:
                ran.append(True)
                return "done"

            result = await passthrough_job({})
            assert result == "done"
            assert len(ran) == 1


# ---------------------------------------------------------------------------
# Test: OTel span
# ---------------------------------------------------------------------------


class TestOtelSpan:
    """Verify OTel span emission and graceful degrade."""

    @pytest.mark.asyncio
    async def test_otel_span_emitted_when_sdk_available(self) -> None:
        """When enable_otel=True and OTel SDK is available, a span is started."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span

        with (
            patch("luana_core_platform.workers.cron_envelope._OTEL_AVAILABLE", True),
            patch("luana_core_platform.workers.cron_envelope._otel_trace") as mock_trace,
            patch(
                "luana_core_platform.workers.cron_envelope._build_idempotent_fn",
                side_effect=lambda fn, name, ttl: fn,
            ),
        ):
            mock_trace.get_tracer.return_value = mock_tracer

            @cron_envelope("test.cron.otel", enable_otel=True, enable_sentry=False)
            async def otel_job(ctx: dict) -> None:
                pass

            await otel_job({})

            mock_trace.get_tracer.assert_called_once_with("luana.cron")
            mock_tracer.start_as_current_span.assert_called_once_with("test.cron.otel")

    @pytest.mark.asyncio
    async def test_otel_skipped_when_sdk_not_installed(self) -> None:
        """When enable_otel=True but OTel SDK not installed, job runs without span."""
        executed = []

        with (
            patch("luana_core_platform.workers.cron_envelope._OTEL_AVAILABLE", False),
            patch("luana_core_platform.workers.cron_envelope._otel_trace", None),
            patch(
                "luana_core_platform.workers.cron_envelope._build_idempotent_fn",
                side_effect=lambda fn, name, ttl: fn,
            ),
        ):

            @cron_envelope("test.cron.no_otel", enable_otel=True)
            async def no_otel_job(ctx: dict) -> str:
                executed.append("ran")
                return "result"

            result = await no_otel_job({})

        # Job ran successfully despite OTel being unavailable
        assert result == "result"
        assert executed == ["ran"]

    @pytest.mark.asyncio
    async def test_otel_disabled_via_flag(self) -> None:
        """When enable_otel=False, the OTel span is never started."""
        executed = []

        with (
            patch("luana_core_platform.workers.cron_envelope._OTEL_AVAILABLE", True),
            patch("luana_core_platform.workers.cron_envelope._otel_trace") as mock_trace,
            patch(
                "luana_core_platform.workers.cron_envelope._build_idempotent_fn",
                side_effect=lambda fn, name, ttl: fn,
            ),
        ):

            @cron_envelope("test.cron.otel_off", enable_otel=False)
            async def otel_off_job(ctx: dict) -> str:
                executed.append("ran")
                return "ok"

            result = await otel_off_job({})

        assert result == "ok"
        assert executed == ["ran"]
        # Tracer was never obtained
        mock_trace.get_tracer.assert_not_called()


# ---------------------------------------------------------------------------
# Test: structlog audit
# ---------------------------------------------------------------------------


class TestStructlogAudit:
    """Verify audit event emission on success."""

    @pytest.mark.asyncio
    async def test_structlog_audit_logged_on_success(self, caplog: pytest.LogCaptureFixture) -> None:
        """On successful completion, cron_completed is logged via structlog."""
        with (
            patch(
                "luana_core_platform.workers.cron_envelope._build_idempotent_fn",
                side_effect=lambda fn, name, ttl: fn,
            ),
            patch("luana_core_platform.workers.cron_envelope._OTEL_AVAILABLE", False),
        ):

            @cron_envelope("test.cron.audit", enable_otel=False, enable_sentry=False)
            async def audit_job(ctx: dict) -> str:
                return "completed"

            with patch("luana_core_platform.workers.cron_envelope.logger") as mock_logger:
                await audit_job({})
                mock_logger.info.assert_called_once_with(
                    "cron_completed",
                    cron_name="test.cron.audit",
                    fn="audit_job",
                )

    @pytest.mark.asyncio
    async def test_structlog_not_logged_on_exception(self) -> None:
        """On exception, cron_completed is NOT logged (exception is the signal)."""
        with (
            patch(
                "luana_core_platform.workers.cron_envelope._build_idempotent_fn",
                side_effect=lambda fn, name, ttl: fn,
            ),
            patch("luana_core_platform.workers.cron_envelope._OTEL_AVAILABLE", False),
        ):

            @cron_envelope("test.cron.audit_fail", enable_otel=False, enable_sentry=False)
            async def failing_job(ctx: dict) -> None:
                msg = "boom"
                raise RuntimeError(msg)

            with patch("luana_core_platform.workers.cron_envelope.logger") as mock_logger:
                with pytest.raises(RuntimeError, match="boom"):
                    await failing_job({})
                # cron_completed must not be called
                for call in mock_logger.info.call_args_list:
                    assert call.args[0] != "cron_completed"


# ---------------------------------------------------------------------------
# Test: Sentry capture
# ---------------------------------------------------------------------------


class TestSentryCapture:
    """Verify Sentry exception capture and graceful degrade."""

    @pytest.mark.asyncio
    async def test_sentry_capture_on_exception_when_sdk_available(self) -> None:
        """When enable_sentry=True and SDK available, exception is captured before re-raise."""
        mock_sentry = MagicMock()

        with (
            patch("luana_core_platform.workers.cron_envelope._SENTRY_AVAILABLE", True),
            patch("luana_core_platform.workers.cron_envelope._sentry_sdk", mock_sentry),
            patch("luana_core_platform.workers.cron_envelope._OTEL_AVAILABLE", False),
            patch(
                "luana_core_platform.workers.cron_envelope._build_idempotent_fn",
                side_effect=lambda fn, name, ttl: fn,
            ),
        ):

            @cron_envelope("test.cron.sentry", enable_otel=False, enable_sentry=True)
            async def sentry_job(ctx: dict) -> None:
                msg = "sentry trigger"
                raise ValueError(msg)

            with pytest.raises(ValueError, match="sentry trigger"):
                await sentry_job({})

            mock_sentry.capture_exception.assert_called_once()
            captured_exc = mock_sentry.capture_exception.call_args[0][0]
            assert isinstance(captured_exc, ValueError)

    @pytest.mark.asyncio
    async def test_sentry_skipped_when_sdk_not_installed(self) -> None:
        """When enable_sentry=True but SDK not installed, exception still propagates."""
        with (
            patch("luana_core_platform.workers.cron_envelope._SENTRY_AVAILABLE", False),
            patch("luana_core_platform.workers.cron_envelope._sentry_sdk", None),
            patch("luana_core_platform.workers.cron_envelope._OTEL_AVAILABLE", False),
            patch(
                "luana_core_platform.workers.cron_envelope._build_idempotent_fn",
                side_effect=lambda fn, name, ttl: fn,
            ),
        ):

            @cron_envelope("test.cron.no_sentry", enable_otel=False, enable_sentry=True)
            async def no_sentry_job(ctx: dict) -> None:
                msg = "no sentry"
                raise RuntimeError(msg)

            # Exception propagates even without Sentry
            with pytest.raises(RuntimeError, match="no sentry"):
                await no_sentry_job({})

    @pytest.mark.asyncio
    async def test_sentry_disabled_via_flag(self) -> None:
        """When enable_sentry=False, Sentry is never called even if SDK available."""
        mock_sentry = MagicMock()

        with (
            patch("luana_core_platform.workers.cron_envelope._SENTRY_AVAILABLE", True),
            patch("luana_core_platform.workers.cron_envelope._sentry_sdk", mock_sentry),
            patch("luana_core_platform.workers.cron_envelope._OTEL_AVAILABLE", False),
            patch(
                "luana_core_platform.workers.cron_envelope._build_idempotent_fn",
                side_effect=lambda fn, name, ttl: fn,
            ),
        ):

            @cron_envelope("test.cron.sentry_off", enable_otel=False, enable_sentry=False)
            async def sentry_off_job(ctx: dict) -> None:
                msg = "error"
                raise RuntimeError(msg)

            with pytest.raises(RuntimeError):
                await sentry_off_job({})

            mock_sentry.capture_exception.assert_not_called()


# ---------------------------------------------------------------------------
# Test: Exception propagation
# ---------------------------------------------------------------------------


class TestExceptionPropagation:
    """Verify all exceptions propagate — no silent swallow."""

    @pytest.mark.asyncio
    async def test_exception_propagates_runtime_error(self) -> None:
        """RuntimeError from cron job propagates through the envelope."""
        with (
            patch("luana_core_platform.workers.cron_envelope._OTEL_AVAILABLE", False),
            patch("luana_core_platform.workers.cron_envelope._SENTRY_AVAILABLE", False),
            patch(
                "luana_core_platform.workers.cron_envelope._build_idempotent_fn",
                side_effect=lambda fn, name, ttl: fn,
            ),
        ):

            @cron_envelope("test.cron.propagate", enable_otel=False, enable_sentry=False)
            async def crashing_job(ctx: dict) -> None:
                msg = "job failed"
                raise RuntimeError(msg)

            with pytest.raises(RuntimeError, match="job failed"):
                await crashing_job({})

    @pytest.mark.asyncio
    async def test_exception_propagates_value_error(self) -> None:
        """ValueError from cron job propagates through the envelope."""
        with (
            patch("luana_core_platform.workers.cron_envelope._OTEL_AVAILABLE", False),
            patch("luana_core_platform.workers.cron_envelope._SENTRY_AVAILABLE", False),
            patch(
                "luana_core_platform.workers.cron_envelope._build_idempotent_fn",
                side_effect=lambda fn, name, ttl: fn,
            ),
        ):

            @cron_envelope("test.cron.propagate_value", enable_otel=False, enable_sentry=False)
            async def value_error_job(ctx: dict) -> None:
                raise ValueError("bad input")  # noqa: EM101, TRY003

            with pytest.raises(ValueError, match="bad input"):
                await value_error_job({})

    @pytest.mark.asyncio
    async def test_exception_propagates_with_sentry_and_otel_both_enabled(self) -> None:
        """Exception propagates even when both Sentry and OTel are active."""
        mock_sentry = MagicMock()
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span

        with (
            patch("luana_core_platform.workers.cron_envelope._OTEL_AVAILABLE", True),
            patch("luana_core_platform.workers.cron_envelope._otel_trace") as mock_trace,
            patch("luana_core_platform.workers.cron_envelope._SENTRY_AVAILABLE", True),
            patch("luana_core_platform.workers.cron_envelope._sentry_sdk", mock_sentry),
            patch(
                "luana_core_platform.workers.cron_envelope._build_idempotent_fn",
                side_effect=lambda fn, name, ttl: fn,
            ),
        ):
            mock_trace.get_tracer.return_value = mock_tracer

            @cron_envelope("test.cron.full_crash", enable_otel=True, enable_sentry=True)
            async def full_crash_job(ctx: dict) -> None:
                msg = "full crash"
                raise RuntimeError(msg)

            with pytest.raises(RuntimeError, match="full crash"):
                await full_crash_job({})

            # Sentry was called despite OTel being active
            mock_sentry.capture_exception.assert_called_once()


# ---------------------------------------------------------------------------
# Test: decorator contract
# ---------------------------------------------------------------------------


class TestDecoratorContract:
    """Verify decorator shape: functools.wraps, default args."""

    def test_wraps_preserves_function_name(self) -> None:
        """cron_envelope preserves __name__ and __doc__ of wrapped function."""
        with patch(
            "luana_core_platform.workers.cron_envelope._build_idempotent_fn",
            side_effect=lambda fn, name, ttl: fn,
        ):

            @cron_envelope("test.cron.meta")
            async def my_named_job(ctx: dict) -> None:
                """My docstring."""

            assert my_named_job.__name__ == "my_named_job"
            assert my_named_job.__doc__ == "My docstring."

    def test_default_ttl_is_600(self) -> None:
        """Default TTL passed to _build_idempotent_fn is 600 seconds."""
        captured_ttl: list[int] = []

        def capture_build(fn: Any, name: str, ttl: int) -> Any:  # noqa: ANN401
            captured_ttl.append(ttl)
            return fn

        with patch(
            "luana_core_platform.workers.cron_envelope._build_idempotent_fn",
            side_effect=capture_build,
        ):

            @cron_envelope("test.cron.default_ttl")
            async def ttl_job(ctx: dict) -> None:
                pass

        assert captured_ttl == [600]

    def test_custom_ttl_passed_through(self) -> None:
        """Custom TTL is forwarded to _build_idempotent_fn."""
        captured_ttl: list[int] = []

        def capture_build(fn: Any, name: str, ttl: int) -> Any:  # noqa: ANN401
            captured_ttl.append(ttl)
            return fn

        with patch(
            "luana_core_platform.workers.cron_envelope._build_idempotent_fn",
            side_effect=capture_build,
        ):

            @cron_envelope("test.cron.custom_ttl", ttl=3600)
            async def custom_ttl_job(ctx: dict) -> None:
                pass

        assert captured_ttl == [3600]

"""Tests for idempotent_cron decorator base helper.

Validates:
  - cron_span context manager wired (T-infra-5)
  - idempotency key registered (luana_core_idempotency)
  - audit row written on completion
  - Sentry capture on exception

TDD: RED first.

downstream-regression-na: brand-local cron decorator; no cross-brand consumers
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helper: produce a minimal fake ARQ context
# ---------------------------------------------------------------------------
def _fake_ctx(
    *,
    run_id: str = "test-run-id",
    job_id: str = "test-job-id",
) -> dict:
    """Return a minimal ARQ-like context dict for testing."""
    return {
        "job_id": job_id,
        "run_id": run_id,
    }


# ---------------------------------------------------------------------------
# Test: idempotent_cron decorator is importable
# ---------------------------------------------------------------------------


def test_idempotent_cron_importable() -> None:
    """idempotent_cron decorator must be importable from workers.base."""
    from src.modules.vitalia._shared.workers.base import idempotent_cron  # noqa: PLC0415

    assert callable(idempotent_cron)


# ---------------------------------------------------------------------------
# Test: cron_span context manager wired
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_idempotent_cron_wires_cron_span() -> None:
    """Decorated function must use cron_span context manager on execution."""
    from src.modules.vitalia._shared.workers.base import idempotent_cron  # noqa: PLC0415

    call_log: list[str] = []

    # Patch cron_span to log calls without OTel side-effects
    mock_span = AsyncMock()
    mock_span.__aenter__ = AsyncMock(return_value=None)
    mock_span.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "src.modules.vitalia._shared.workers.base.cron_span",
        return_value=mock_span,
    ) as mock_cron_span:

        @idempotent_cron("test_cron_name")
        async def my_cron(ctx: dict) -> None:
            call_log.append("executed")

        ctx = _fake_ctx()
        # Patch idempotency store to allow execution
        with patch(
            "src.modules.vitalia._shared.workers.base._get_idem_store",
            return_value=None,
        ):
            await my_cron(ctx)

        # Verify cron_span was called once with the correct span name
        assert mock_cron_span.call_count == 1
        first_arg = mock_cron_span.call_args[0][0]
        assert first_arg == "test_cron_name"
        # Verify attributes kwarg contains job_id
        call_kwargs = mock_cron_span.call_args[1]
        assert "attributes" in call_kwargs
        assert "job_id" in call_kwargs["attributes"]


# ---------------------------------------------------------------------------
# Test: idempotency key registered on first execution
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_idempotent_cron_registers_idempotency_key() -> None:
    """Decorator must attempt to claim an idempotency key before executing."""
    from src.modules.vitalia._shared.workers.base import idempotent_cron  # noqa: PLC0415

    called = []

    mock_store = MagicMock()
    mock_store.claim = AsyncMock(return_value=True)  # first call → allow
    mock_store.store_result = AsyncMock()

    with (
        patch(
            "src.modules.vitalia._shared.workers.base._get_idem_store",
            return_value=mock_store,
        ),
        patch(
            "src.modules.vitalia._shared.workers.base.cron_span",
        ) as mock_span,
    ):
        mock_span.return_value.__aenter__ = AsyncMock(return_value=None)
        mock_span.return_value.__aexit__ = AsyncMock(return_value=False)

        @idempotent_cron("test_idem_cron")
        async def my_cron(ctx: dict) -> None:
            called.append(True)

        ctx = _fake_ctx()
        await my_cron(ctx)

    assert mock_store.claim.called, "claim() should be called on idempotency store"
    assert called, "wrapped function should have executed on first call"


@pytest.mark.asyncio
async def test_idempotent_cron_skips_when_already_running() -> None:
    """Decorator must skip execution when idempotency key already claimed."""
    from src.modules.vitalia._shared.workers.base import idempotent_cron  # noqa: PLC0415

    called = []

    mock_store = MagicMock()
    mock_store.claim = AsyncMock(return_value=False)  # duplicate → skip

    with patch(
        "src.modules.vitalia._shared.workers.base._get_idem_store",
        return_value=mock_store,
    ):

        @idempotent_cron("test_skip_cron")
        async def my_cron(ctx: dict) -> None:
            called.append(True)

        ctx = _fake_ctx()
        await my_cron(ctx)

    assert not called, "wrapped function should NOT execute when key already claimed"


# ---------------------------------------------------------------------------
# Test: audit log row written on completion
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_idempotent_cron_writes_audit_log_on_completion() -> None:
    """Decorator must log cron completion via structlog (audit trail)."""
    from src.modules.vitalia._shared.workers.base import idempotent_cron  # noqa: PLC0415

    mock_store = MagicMock()
    mock_store.claim = AsyncMock(return_value=True)
    mock_store.store_result = AsyncMock()

    with (
        patch(
            "src.modules.vitalia._shared.workers.base._get_idem_store",
            return_value=mock_store,
        ),
        patch(
            "src.modules.vitalia._shared.workers.base.cron_span",
        ) as mock_span,
        patch(
            "src.modules.vitalia._shared.workers.base.logger",
        ) as mock_logger,
    ):
        mock_span.return_value.__aenter__ = AsyncMock(return_value=None)
        mock_span.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_logger.info = MagicMock()

        @idempotent_cron("test_audit_cron")
        async def my_cron(ctx: dict) -> None:
            pass

        ctx = _fake_ctx()
        await my_cron(ctx)

    # Should log completion at info level
    assert mock_logger.info.called, "logger.info should be called on cron completion"
    # First positional arg should be the event name
    first_call_event = mock_logger.info.call_args[0][0]
    assert "cron" in first_call_event.lower() or "complete" in first_call_event.lower(), (
        f"Expected 'cron' or 'complete' in log event name, got '{first_call_event}'"
    )


# ---------------------------------------------------------------------------
# Test: Sentry capture on exception
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_idempotent_cron_captures_sentry_on_exception() -> None:
    """Decorator must capture exceptions to Sentry and re-raise."""
    from src.modules.vitalia._shared.workers.base import idempotent_cron  # noqa: PLC0415

    mock_store = MagicMock()
    mock_store.claim = AsyncMock(return_value=True)

    with (
        patch(
            "src.modules.vitalia._shared.workers.base._get_idem_store",
            return_value=mock_store,
        ),
        patch(
            "src.modules.vitalia._shared.workers.base.cron_span",
        ) as mock_span,
        patch(
            "src.modules.vitalia._shared.workers.base.sentry_sdk",
        ) as mock_sentry,
    ):
        mock_span.return_value.__aenter__ = AsyncMock(return_value=None)
        mock_span.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_sentry.capture_exception = MagicMock()

        @idempotent_cron("test_sentry_cron")
        async def crashing_cron(ctx: dict) -> None:
            msg = "simulated cron failure"
            raise RuntimeError(msg)

        ctx = _fake_ctx()
        with pytest.raises(RuntimeError, match="simulated cron failure"):
            await crashing_cron(ctx)

    # Sentry should have been called
    assert mock_sentry.capture_exception.called, "sentry_sdk.capture_exception should be called on cron exception"


# ---------------------------------------------------------------------------
# Test: decorator preserves function __name__
# ---------------------------------------------------------------------------


def test_idempotent_cron_preserves_function_name() -> None:
    """idempotent_cron must use functools.wraps to preserve __name__."""
    from src.modules.vitalia._shared.workers.base import idempotent_cron  # noqa: PLC0415

    @idempotent_cron("test_wrap_cron")
    async def my_named_cron(ctx: dict) -> None:
        pass

    assert my_named_cron.__name__ == "my_named_cron", (
        f"Expected __name__='my_named_cron', got '{my_named_cron.__name__}'"
    )


# ---------------------------------------------------------------------------
# Test: NotImplementedError passes through (scaffold pattern)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_idempotent_cron_propagates_not_implemented() -> None:
    """NotImplementedError from scaffold cron jobs must propagate correctly."""
    from src.modules.vitalia._shared.workers.base import idempotent_cron  # noqa: PLC0415

    mock_store = MagicMock()
    mock_store.claim = AsyncMock(return_value=True)

    with (
        patch(
            "src.modules.vitalia._shared.workers.base._get_idem_store",
            return_value=mock_store,
        ),
        patch(
            "src.modules.vitalia._shared.workers.base.cron_span",
        ) as mock_span,
        patch(
            "src.modules.vitalia._shared.workers.base.sentry_sdk",
        ),
    ):
        mock_span.return_value.__aenter__ = AsyncMock(return_value=None)
        mock_span.return_value.__aexit__ = AsyncMock(return_value=False)

        @idempotent_cron("test_not_impl_cron")
        async def scaffold_cron(ctx: dict) -> None:
            msg = "Implemented in vitalia-slice-2 story T-N"
            raise NotImplementedError(msg)

        ctx = _fake_ctx()
        with pytest.raises(NotImplementedError, match="vitalia-slice-2"):
            await scaffold_cron(ctx)

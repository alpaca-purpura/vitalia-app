"""Tests for cron_span context manager.

TDD: RED-first. Defines the contract for cron_spans.py.

downstream-regression-na: brand-local observability cron span test; no cross-brand consumers
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

EXPECTED_CRON_SPAN_NAMES = [
    "vitalia.cron.followup_24h",
    "vitalia.cron.reactivation_45d",
    "vitalia.cron.maintenance_90d",
    "vitalia.cron.deposit_reminder_24h",
    "vitalia.cron.appointment_reminder_24h",
    "vitalia.cron.appointment_reminder_2h",
    "vitalia.cron.nps_request_24h_post_appointment",
    "vitalia.cron.brand_studio_audit_30d",
    "vitalia.cron.lucas_weekly_recommendations",
    "vitalia.cron.channel_sync_state_15min",
    "vitalia.cron.audit_log_retention_sweep_monthly",
]


class TestCronSpanNames:
    """All 11 named cron spans must be present in the catalog."""

    def test_all_11_named_spans_exported(self) -> None:
        """CRON_SPAN_NAMES tuple must contain all 11 expected names."""
        from src.modules.vitalia._shared.observability.cron_spans import (
            CRON_SPAN_NAMES,
        )

        for name in EXPECTED_CRON_SPAN_NAMES:
            assert name in CRON_SPAN_NAMES, f"Missing cron span: {name}"

    def test_cron_span_names_count(self) -> None:
        """Must have exactly 11 named spans."""
        from src.modules.vitalia._shared.observability.cron_spans import (
            CRON_SPAN_NAMES,
        )

        assert len(CRON_SPAN_NAMES) == 11

    def test_all_names_prefixed_vitalia_cron(self) -> None:
        """All span names must be prefixed with 'vitalia.cron.'."""
        from src.modules.vitalia._shared.observability.cron_spans import (
            CRON_SPAN_NAMES,
        )

        for name in CRON_SPAN_NAMES:
            assert name.startswith("vitalia.cron."), f"Bad prefix: {name}"


class TestCronSpanContextManager:
    """cron_span() context manager creates OTel span + records status."""

    def test_cron_span_is_async_context_manager(self) -> None:
        """cron_span must be usable as async context manager."""
        from src.modules.vitalia._shared.observability.cron_spans import cron_span

        assert callable(cron_span)

    @pytest.mark.asyncio
    async def test_cron_span_creates_span_on_entry(self) -> None:
        """cron_span must start an OTel span when entered."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span

        with patch(
            "src.modules.vitalia._shared.observability.cron_spans._get_tracer",
            return_value=mock_tracer,
        ):
            from src.modules.vitalia._shared.observability.cron_spans import cron_span

            async with cron_span("vitalia.cron.followup_24h", attributes={"test": "val"}):
                pass

        mock_tracer.start_as_current_span.assert_called_once()
        call_args = mock_tracer.start_as_current_span.call_args
        assert call_args[0][0] == "vitalia.cron.followup_24h"

    @pytest.mark.asyncio
    async def test_cron_span_records_ok_status_on_success(self) -> None:
        """On successful completion, span set_status must be called (OK path)."""
        # Import StatusCode from the production module (works with or without OTel)
        from src.modules.vitalia._shared.observability.cron_spans import StatusCode

        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span

        with patch(
            "src.modules.vitalia._shared.observability.cron_spans._get_tracer",
            return_value=mock_tracer,
        ):
            from src.modules.vitalia._shared.observability.cron_spans import cron_span

            async with cron_span("vitalia.cron.followup_24h"):
                pass  # no exception

        mock_span.set_status.assert_called()
        status_arg = mock_span.set_status.call_args[0][0]
        assert status_arg.status_code == StatusCode.OK

    @pytest.mark.asyncio
    async def test_cron_span_records_error_status_on_exception(self) -> None:
        """On exception, span must record error status and re-raise."""
        # Import StatusCode from the production module (works with or without OTel)
        from src.modules.vitalia._shared.observability.cron_spans import StatusCode

        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span

        with patch(
            "src.modules.vitalia._shared.observability.cron_spans._get_tracer",
            return_value=mock_tracer,
        ):
            from src.modules.vitalia._shared.observability.cron_spans import cron_span

            with pytest.raises(ValueError, match="cron test error"):
                async with cron_span("vitalia.cron.followup_24h"):
                    raise ValueError("cron test error")

        mock_span.record_exception.assert_called_once()
        mock_span.set_status.assert_called()
        status_arg = mock_span.set_status.call_args[0][0]
        assert status_arg.status_code == StatusCode.ERROR

    @pytest.mark.asyncio
    async def test_cron_span_accepts_attributes(self) -> None:
        """cron_span must pass custom attributes to the span."""
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span

        with patch(
            "src.modules.vitalia._shared.observability.cron_spans._get_tracer",
            return_value=mock_tracer,
        ):
            from src.modules.vitalia._shared.observability.cron_spans import cron_span

            async with cron_span(
                "vitalia.cron.followup_24h",
                attributes={"tenant_id": "abc-123", "run_id": "xyz"},
            ):
                pass

        # Attributes set via span.set_attributes
        mock_span.set_attributes.assert_called_once_with({"tenant_id": "abc-123", "run_id": "xyz"})

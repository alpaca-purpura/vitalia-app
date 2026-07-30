"""Tests for LegacyEventBus DeprecationWarning emission.

PI-11 PR-1 § 5 D3 (2026-05-04): LegacyEventBus.publish emits DeprecationWarning +
structlog.warning when any USE_OUTBOX_PATTERN_* flag is True AND caller is outside
shared/domain_events/* and outside tests/*.

4 test cases per CONTRACT.md PR-1 § 5.
"""

from __future__ import annotations

import warnings
from unittest.mock import patch
from uuid import uuid4

import pytest
from luana_core_platform.domain.events import DomainEvent, EventBus


def _make_event() -> DomainEvent:
    """Create a minimal domain event for testing."""
    return DomainEvent(
        event_name="test_event",
        tenant_id=uuid4(),
        payload={},
    )


class TestLegacyEventBusDeprecationWarning:
    """D3: EventBus.publish emits DeprecationWarning when outbox flag is ON + external caller."""

    def test_deprecation_suppressed_in_test_context(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Caller inside /tests/ → NO DeprecationWarning.

        Test capability suites call EventBus.publish directly (Caso D/E).
        _is_internal_caller_or_test() detects /tests/ in call stack → suppresses.
        """
        from luana_core_platform.core.config import get_settings

        s = get_settings()
        monkeypatch.setattr(s, "USE_OUTBOX_PATTERN_SALES_AGENT", True)
        monkeypatch.setattr(s, "USE_OUTBOX_PATTERN_COPILOT", False)
        monkeypatch.setattr(s, "USE_OUTBOX_PATTERN_BRAND", False)
        event = _make_event()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            EventBus.publish(event, session=None)
        # This test itself is in /tests/ → _is_internal_caller_or_test() returns True
        # → no EventBus DeprecationWarning emitted.
        # Filter out T-1 shim migration warnings (config.settings back-compat).
        eventbus_deprecations = [
            x for x in w if issubclass(x.category, DeprecationWarning) and "EventBus.publish" in str(x.message)
        ]
        assert len(eventbus_deprecations) == 0, (
            f"Expected NO EventBus DeprecationWarning from test context, got {len(eventbus_deprecations)}"
        )

    def test_deprecation_suppressed_in_shared_domain_events_context(self) -> None:
        """Caller inside shared/domain_events/ → NO DeprecationWarning.

        EventBusAdapter fall-through path calls EventBus.publish when flag=False.
        _is_internal_caller_or_test() detects shared/domain_events/ in call stack → suppresses.

        NOTE: warnings about `config.settings` (T-1 shim back-compat migration) are
        filtered from this assertion — the test is specifically about EventBus
        deprecation, not config-level migration warnings.
        """
        # Import from the adapter directly to simulate adapter fall-through call
        from luana_core_events.outbox.application.event_bus_adapter import EventBusAdapter

        adapter = EventBusAdapter()
        event = _make_event()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # Adapter with flag OFF calls EventBus.publish (fall-through path)
            with patch.object(EventBusAdapter, "_is_outbox_enabled", return_value=False):
                adapter.publish(event, session=None)
        # Filter out T-1 shim migration warnings (config.settings back-compat)
        eventbus_deprecations = [
            x for x in w if issubclass(x.category, DeprecationWarning) and "EventBus.publish" in str(x.message)
        ]
        assert len(eventbus_deprecations) == 0, (
            f"Expected NO EventBus DeprecationWarning from adapter fall-through path, got {len(eventbus_deprecations)}"
        )

    def test_deprecation_suppressed_when_all_flags_off(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """All outbox flags OFF → NO DeprecationWarning (legacy compat path active).

        When outbox is not enabled, EventBus.publish is the canonical path.
        No warning should be emitted (not a deprecated use case in legacy mode).
        """
        from luana_core_platform.core.config import get_settings

        s = get_settings()
        monkeypatch.setattr(s, "USE_OUTBOX_PATTERN_SALES_AGENT", False)
        monkeypatch.setattr(s, "USE_OUTBOX_PATTERN_COPILOT", False)
        monkeypatch.setattr(s, "USE_OUTBOX_PATTERN_BRAND", False)
        event = _make_event()

        # Simulate external caller by patching _is_internal_caller_or_test to return False
        with (
            warnings.catch_warnings(record=True) as w,
            patch(
                "luana_core_platform.domain.events._is_internal_caller_or_test",
                return_value=False,
            ),
        ):
            warnings.simplefilter("always")
            EventBus.publish(event, session=None)
        # Filter out T-1 shim migration warnings (config.settings back-compat).
        eventbus_deprecations = [
            x for x in w if issubclass(x.category, DeprecationWarning) and "EventBus.publish" in str(x.message)
        ]
        assert len(eventbus_deprecations) == 0, "Expected NO EventBus DeprecationWarning when all outbox flags are OFF"

    def test_deprecation_emitted_for_external_caller_when_outbox_on(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """External caller (non-test, non-adapter) + outbox flag ON → DeprecationWarning.

        Simulates production code that still calls EventBus.publish directly
        after outbox cutover (should have migrated to EventBusAdapter).

        Uses _is_internal_caller_or_test mock to simulate external caller context
        (since this test IS inside /tests/ which normally suppresses).
        """
        from luana_core_platform.core.config import get_settings

        s = get_settings()
        monkeypatch.setattr(s, "USE_OUTBOX_PATTERN_BRAND", True)
        monkeypatch.setattr(s, "USE_OUTBOX_PATTERN_SALES_AGENT", False)
        monkeypatch.setattr(s, "USE_OUTBOX_PATTERN_COPILOT", False)
        event = _make_event()

        # Patch _is_internal_caller_or_test to return False to simulate external caller
        with (
            warnings.catch_warnings(record=True) as w,
            patch(
                "luana_core_platform.domain.events._is_internal_caller_or_test",
                return_value=False,
            ),
        ):
            warnings.simplefilter("always")
            EventBus.publish(event, session=None)

        # Filter to EventBus-specific DeprecationWarnings only (exclude T-1 shim back-compat).
        eventbus_deprecations = [
            x for x in w if issubclass(x.category, DeprecationWarning) and "EventBus.publish" in str(x.message)
        ]
        n = len(eventbus_deprecations)
        assert n == 1, f"Expected 1 EventBus DeprecationWarning for external caller with outbox ON, got {n}"
        assert "EventBus.publish called when outbox cutover active" in str(eventbus_deprecations[0].message)

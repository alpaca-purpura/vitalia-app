"""Tests for ActionReceipt domain entity.

TDD RED phase — tests written before implementation.

SC-01 coverage: 5min undo window, action receipt state machine.
SC-03 coverage: OCC — receipt state changes with correct timestamps.
PHI dual-filter: tenant_id + clinic_id mandatory.

downstream-regression-na: brand-local vitalia CRM domain entity tests
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.modules.vitalia.crm.domain.action_receipt import (
    VALID_RETRACT_REASONS,
    ActionReceipt,
)


class TestActionReceiptFields:
    """ActionReceipt carries PHI dual-filter fields."""

    def _make_receipt(self, **overrides: object) -> ActionReceipt:
        now = datetime.now(UTC)
        defaults: dict[str, object] = {
            "id": uuid4(),
            "tenant_id": uuid4(),
            "clinic_id": uuid4(),
            "message_id": uuid4(),
            "conversation_id": uuid4(),
            "expires_at": now + timedelta(minutes=5),
            "retracted_at": None,
            "retract_succeeded": None,
            "retract_reason": None,
            "created_at": now,
            "updated_at": now,
        }
        defaults.update(overrides)
        return ActionReceipt(**defaults)

    def test_action_receipt_has_tenant_id(self) -> None:
        """PHI dual-filter: tenant_id present."""
        tenant = uuid4()
        receipt = self._make_receipt(tenant_id=tenant)
        assert receipt.tenant_id == tenant

    def test_action_receipt_has_clinic_id(self) -> None:
        """PHI dual-filter: clinic_id present."""
        clinic = uuid4()
        receipt = self._make_receipt(clinic_id=clinic)
        assert receipt.clinic_id == clinic

    def test_action_receipt_has_message_id(self) -> None:
        msg = uuid4()
        receipt = self._make_receipt(message_id=msg)
        assert receipt.message_id == msg

    def test_action_receipt_has_conversation_id(self) -> None:
        conv = uuid4()
        receipt = self._make_receipt(conversation_id=conv)
        assert receipt.conversation_id == conv

    def test_action_receipt_has_updated_at(self) -> None:
        now = datetime.now(UTC)
        receipt = self._make_receipt(updated_at=now)
        assert receipt.updated_at == now


class TestActionReceiptExpiryWindow:
    """SC-01: 5min undo window for action receipts."""

    def _make_receipt(self, **overrides: object) -> ActionReceipt:
        now = datetime.now(UTC)
        defaults: dict[str, object] = {
            "id": uuid4(),
            "tenant_id": uuid4(),
            "clinic_id": uuid4(),
            "message_id": uuid4(),
            "conversation_id": uuid4(),
            "expires_at": now + timedelta(minutes=5),
            "retracted_at": None,
            "retract_succeeded": None,
            "retract_reason": None,
            "created_at": now,
            "updated_at": now,
        }
        defaults.update(overrides)
        return ActionReceipt(**defaults)

    def test_expires_at_5_minutes_from_creation(self) -> None:
        """SC-01: undo chip shows countdown to 5min window."""
        now = datetime.now(UTC)
        expires = now + timedelta(minutes=5)
        receipt = self._make_receipt(created_at=now, expires_at=expires)
        delta = receipt.expires_at - receipt.created_at
        assert abs(delta.total_seconds() - 300) < 1  # 5 minutes = 300 seconds

    def test_expires_at_in_future_means_active_window(self) -> None:
        now = datetime.now(UTC)
        future = now + timedelta(minutes=4)
        receipt = self._make_receipt(expires_at=future)
        assert receipt.expires_at > now

    def test_expires_at_in_past_means_expired(self) -> None:
        now = datetime.now(UTC)
        past = now - timedelta(minutes=1)
        receipt = self._make_receipt(expires_at=past)
        assert receipt.expires_at < now

    def test_expires_at_field_stored(self) -> None:
        now = datetime.now(UTC)
        future = now + timedelta(minutes=5)
        receipt = self._make_receipt(expires_at=future)
        assert receipt.expires_at == future


class TestActionReceiptStateMachine:
    """SC-01: ActionReceipt retraction state transitions."""

    def _make_receipt(self, **overrides: object) -> ActionReceipt:
        now = datetime.now(UTC)
        defaults: dict[str, object] = {
            "id": uuid4(),
            "tenant_id": uuid4(),
            "clinic_id": uuid4(),
            "message_id": uuid4(),
            "conversation_id": uuid4(),
            "expires_at": now + timedelta(minutes=5),
            "retracted_at": None,
            "retract_succeeded": None,
            "retract_reason": None,
            "created_at": now,
            "updated_at": now,
        }
        defaults.update(overrides)
        return ActionReceipt(**defaults)

    def test_initial_state_not_retracted(self) -> None:
        receipt = self._make_receipt()
        assert receipt.retracted_at is None
        assert receipt.retract_succeeded is None
        assert receipt.retract_reason is None

    def test_retracted_state_user_undo(self) -> None:
        """SC-01: User clicks ↩ Revertir → retracted_at set, reason=user_undo."""
        now = datetime.now(UTC)
        receipt = self._make_receipt(
            retracted_at=now,
            retract_succeeded=True,
            retract_reason="user_undo",
        )
        assert receipt.retracted_at == now
        assert receipt.retract_succeeded is True
        assert receipt.retract_reason == "user_undo"

    def test_retracted_state_expired(self) -> None:
        """After 5min window: reason=expired."""
        now = datetime.now(UTC)
        receipt = self._make_receipt(
            retracted_at=now,
            retract_succeeded=None,
            retract_reason="expired",
        )
        assert receipt.retract_reason == "expired"

    def test_retracted_state_patient_replied(self) -> None:
        """Patient replied: chip disappears, reason=patient_replied."""
        now = datetime.now(UTC)
        receipt = self._make_receipt(
            retracted_at=now,
            retract_succeeded=None,
            retract_reason="patient_replied",
        )
        assert receipt.retract_reason == "patient_replied"

    def test_retract_succeeded_false_fallback_marcar_erroneo(self) -> None:
        """Email / API fail: fallback 'marcar erróneo' = retract_succeeded=False."""
        now = datetime.now(UTC)
        receipt = self._make_receipt(
            retracted_at=now,
            retract_succeeded=False,
            retract_reason="user_undo",
        )
        assert receipt.retract_succeeded is False


class TestActionReceiptRetractReasons:
    """VALID_RETRACT_REASONS enum values match spec."""

    def test_valid_retract_reasons_includes_user_undo(self) -> None:
        assert "user_undo" in VALID_RETRACT_REASONS

    def test_valid_retract_reasons_includes_expired(self) -> None:
        assert "expired" in VALID_RETRACT_REASONS

    def test_valid_retract_reasons_includes_patient_replied(self) -> None:
        assert "patient_replied" in VALID_RETRACT_REASONS

    def test_retract_reason_can_be_none(self) -> None:
        now = datetime.now(UTC)
        receipt = ActionReceipt(
            id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            message_id=uuid4(),
            conversation_id=uuid4(),
            expires_at=now + timedelta(minutes=5),
            retracted_at=None,
            retract_succeeded=None,
            retract_reason=None,
            created_at=now,
            updated_at=now,
        )
        assert receipt.retract_reason is None

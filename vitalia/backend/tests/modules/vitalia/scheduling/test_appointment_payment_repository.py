"""RED tests — AppointmentPaymentRepository optimistic lock + idempotency.

TDD contract for:
  - lock_for_charge(): UPDATE WHERE balance_version == expected; rowcount 0 → raise
  - find_by_idempotency_key(): lookup by unique (tenant_id, clinic_id, external_payment_id)
  - Dual filter HIPAA (tenant_id + clinic_id every query)
  - Cross-clinic isolation

Per 03-arch A7 (optimistic lock SC-5) + A8 (idempotency keys) + A1 (dual filter).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

# ---------------------------------------------------------------------------
# Import helpers
# ---------------------------------------------------------------------------


def _import_payment_repo():
    from src.modules.vitalia.scheduling.infrastructure.repositories.appointment_payment_repository import (  # noqa: PLC0415
        AppointmentPaymentRepository,
    )

    return AppointmentPaymentRepository


def _import_balance_error():
    """BalanceAlreadyChargedError must live in scheduling domain exceptions."""
    from src.modules.vitalia.scheduling.domain.exceptions import (  # noqa: PLC0415
        BalanceAlreadyChargedError,
    )

    return BalanceAlreadyChargedError


def _make_mock_session_update_rowcount(rowcount: int) -> MagicMock:
    """Build AsyncSession mock where execute() returns result with rowcount."""
    session = MagicMock()
    result = MagicMock()
    result.rowcount = rowcount
    session.execute = AsyncMock(return_value=result)
    return session


def _make_mock_session_scalar(row: object | None) -> MagicMock:
    """Build AsyncSession mock returning a specific scalar from execute()."""
    session = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = row
    session.execute = AsyncMock(return_value=result)
    return session


# ---------------------------------------------------------------------------
# Tests — import contract
# ---------------------------------------------------------------------------


class TestAppointmentPaymentRepositoryImport:
    def test_importable(self) -> None:
        repo_cls = _import_payment_repo()
        assert repo_cls is not None

    def test_has_lock_for_charge(self) -> None:
        repo_cls = _import_payment_repo()
        assert hasattr(repo_cls, "lock_for_charge")

    def test_has_find_by_idempotency_key(self) -> None:
        repo_cls = _import_payment_repo()
        assert hasattr(repo_cls, "find_by_idempotency_key")

    def test_has_create(self) -> None:
        repo_cls = _import_payment_repo()
        assert hasattr(repo_cls, "create")

    def test_balance_already_charged_error_importable(self) -> None:
        err_cls = _import_balance_error()
        assert err_cls is not None
        assert issubclass(err_cls, Exception)


# ---------------------------------------------------------------------------
# Tests — optimistic lock (A4)
# ---------------------------------------------------------------------------


class TestOptimisticLock:
    """lock_for_charge must raise BalanceAlreadyChargedError on stale version."""

    @pytest.mark.asyncio
    async def test_lock_for_charge_optimistic_succeeds(self) -> None:
        """When rowcount == 1 (row updated), lock_for_charge must NOT raise."""
        repo_cls = _import_payment_repo()
        session = _make_mock_session_update_rowcount(1)  # 1 row updated → success
        repo = repo_cls(session=session)

        tenant_id = uuid4()
        clinic_id = uuid4()
        payment_id = uuid4()
        expected_version = 1

        # Must NOT raise
        await repo.lock_for_charge(
            payment_id=payment_id,
            expected_version=expected_version,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )

        assert session.execute.call_count >= 1

    @pytest.mark.asyncio
    async def test_lock_for_charge_optimistic_stale_version_raises(self) -> None:
        """When rowcount == 0 (version mismatch), must raise BalanceAlreadyChargedError."""
        repo_cls = _import_payment_repo()
        BalanceAlreadyChargedError = _import_balance_error()
        session = _make_mock_session_update_rowcount(0)  # 0 rows updated → stale version
        repo = repo_cls(session=session)

        tenant_id = uuid4()
        clinic_id = uuid4()
        payment_id = uuid4()
        stale_version = 99  # doesn't match DB current version

        with pytest.raises(BalanceAlreadyChargedError):
            await repo.lock_for_charge(
                payment_id=payment_id,
                expected_version=stale_version,
                tenant_id=tenant_id,
                clinic_id=clinic_id,
            )

    @pytest.mark.asyncio
    async def test_lock_for_charge_includes_dual_filter(self) -> None:
        """lock_for_charge UPDATE must filter by tenant_id + clinic_id + payment_id + version."""
        repo_cls = _import_payment_repo()
        session = _make_mock_session_update_rowcount(1)
        repo = repo_cls(session=session)

        tenant_id = uuid4()
        clinic_id = uuid4()
        payment_id = uuid4()

        await repo.lock_for_charge(
            payment_id=payment_id,
            expected_version=1,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )

        call_args = session.execute.call_args
        stmt = call_args[0][0] if call_args[0] else call_args.args[0]
        from sqlalchemy.dialects import postgresql  # noqa: PLC0415

        compiled = str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
        assert str(tenant_id) in compiled, "lock_for_charge UPDATE must include tenant_id"
        assert str(clinic_id) in compiled, "lock_for_charge UPDATE must include clinic_id (HIPAA dual filter)"
        assert str(payment_id) in compiled, "lock_for_charge UPDATE must include payment_id"
        # balance_version must be in the WHERE clause
        assert "balance_version" in compiled, "lock_for_charge must use balance_version in WHERE"


# ---------------------------------------------------------------------------
# Tests — idempotency lookup (A5)
# ---------------------------------------------------------------------------


class TestIdempotencyLookup:
    """find_by_idempotency_key must return prior payment on key repeat."""

    @pytest.mark.asyncio
    async def test_find_by_idempotency_key_returns_prior_payment(self) -> None:
        """When a prior payment with matching key exists, return it (no duplicate charge)."""
        repo_cls = _import_payment_repo()
        # Simulate a row existing in DB
        mock_payment = MagicMock()
        mock_payment.id = uuid4()
        mock_payment.external_payment_id = "idem-key-abc-123"
        session = _make_mock_session_scalar(mock_payment)
        repo = repo_cls(session=session)

        tenant_id = uuid4()
        clinic_id = uuid4()
        idempotency_key = "idem-key-abc-123"

        result = await repo.find_by_idempotency_key(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            idempotency_key=idempotency_key,
        )

        assert result is not None, (
            "find_by_idempotency_key must return existing payment when key exists — "
            "prevents duplicate charge on retry (03-arch A8)"
        )

    @pytest.mark.asyncio
    async def test_find_by_idempotency_key_different_key_returns_none(self) -> None:
        """When no payment with this key exists, return None → allow new charge."""
        repo_cls = _import_payment_repo()
        session = _make_mock_session_scalar(None)  # no row found
        repo = repo_cls(session=session)

        tenant_id = uuid4()
        clinic_id = uuid4()
        new_key = "brand-new-idem-key-xyz"

        result = await repo.find_by_idempotency_key(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            idempotency_key=new_key,
        )

        assert result is None, "New idempotency key must return None → allow new payment"

    @pytest.mark.asyncio
    async def test_find_by_idempotency_key_filters_by_dual_filter(self) -> None:
        """Idempotency lookup must include both tenant_id + clinic_id in WHERE."""
        repo_cls = _import_payment_repo()
        session = _make_mock_session_scalar(None)
        repo = repo_cls(session=session)

        tenant_id = uuid4()
        clinic_id = uuid4()

        await repo.find_by_idempotency_key(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            idempotency_key="some-key",
        )

        call_args = session.execute.call_args
        stmt = call_args[0][0] if call_args[0] else call_args.args[0]
        from sqlalchemy.dialects import postgresql  # noqa: PLC0415

        compiled = str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
        assert str(tenant_id) in compiled, "Idempotency lookup must include tenant_id"
        assert str(clinic_id) in compiled, "Idempotency lookup must include clinic_id (HIPAA dual filter)"


# ---------------------------------------------------------------------------
# Tests — cross-clinic isolation (A3 — payment level)
# ---------------------------------------------------------------------------


class TestPaymentDualFilter:
    @pytest.mark.asyncio
    async def test_payment_dual_filter_cross_clinic(self) -> None:
        """Payment lookup must include clinic_id to prevent cross-clinic access."""
        repo_cls = _import_payment_repo()
        session = _make_mock_session_scalar(None)
        repo = repo_cls(session=session)

        tenant_id = uuid4()
        clinic_id = uuid4()

        # No exception raised, but verify query includes both filter keys
        await repo.find_by_idempotency_key(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            idempotency_key="test-key",
        )

        call_args = session.execute.call_args
        stmt = call_args[0][0] if call_args[0] else call_args.args[0]
        from sqlalchemy.dialects import postgresql  # noqa: PLC0415

        compiled = str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
        assert str(clinic_id) in compiled, (
            "Payment repository MUST filter by clinic_id — prevents cross-clinic payment access"
        )

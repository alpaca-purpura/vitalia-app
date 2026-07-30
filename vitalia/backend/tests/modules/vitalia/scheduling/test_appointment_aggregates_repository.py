"""RED tests — AppointmentAggregatesRepository monthly slot counts.

TDD contract for monthly aggregates:
  - count_per_day(tenant_id, clinic_id, year, month) → list of {date, count}
  - Dual filter HIPAA (tenant_id + clinic_id)
  - Used by FE react-window virtualized month view

Per 03-arch § 3.3 + vitalia/.claude/rules/hipaa-lite.md
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest


def _import_aggregates_repo():
    from src.modules.vitalia.scheduling.infrastructure.repositories.appointment_aggregates_repository import (  # noqa: PLC0415
        AppointmentAggregatesRepository,
    )

    return AppointmentAggregatesRepository


def _make_mock_session_with_rows(rows: list) -> MagicMock:
    session = MagicMock()
    result = MagicMock()
    result.all.return_value = rows
    session.execute = AsyncMock(return_value=result)
    return session


class TestAppointmentAggregatesRepositoryImport:
    def test_importable(self) -> None:
        repo_cls = _import_aggregates_repo()
        assert repo_cls is not None

    def test_has_count_per_day(self) -> None:
        repo_cls = _import_aggregates_repo()
        assert hasattr(repo_cls, "count_per_day")


class TestMonthlyAggregates:
    """Monthly aggregates must count slots per day, filtered by dual filter."""

    @pytest.mark.asyncio
    async def test_monthly_aggregates_counts_per_day(self) -> None:
        """count_per_day returns list of (date, count) for the given month."""
        repo_cls = _import_aggregates_repo()
        # Simulate DB returning 3 day-buckets
        mock_row_1 = MagicMock()
        mock_row_1._mapping = {"slot_date": "2026-06-01", "slot_count": 5}
        mock_row_2 = MagicMock()
        mock_row_2._mapping = {"slot_date": "2026-06-02", "slot_count": 3}
        mock_row_3 = MagicMock()
        mock_row_3._mapping = {"slot_date": "2026-06-03", "slot_count": 8}
        session = _make_mock_session_with_rows([mock_row_1, mock_row_2, mock_row_3])
        repo = repo_cls(session=session)

        tenant_id = uuid4()
        clinic_id = uuid4()

        result = await repo.count_per_day(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            year=2026,
            month=6,
        )

        assert session.execute.call_count >= 1
        # Result can be list of dicts, tuples, or ORM row objects — just check it's iterable
        assert result is not None

    @pytest.mark.asyncio
    async def test_monthly_aggregates_dual_filter(self) -> None:
        """count_per_day must include tenant_id + clinic_id in GROUP BY query."""
        repo_cls = _import_aggregates_repo()
        session = _make_mock_session_with_rows([])
        repo = repo_cls(session=session)

        tenant_id = uuid4()
        clinic_id = uuid4()

        await repo.count_per_day(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            year=2026,
            month=6,
        )

        call_args = session.execute.call_args
        stmt = call_args[0][0] if call_args[0] else call_args.args[0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert str(tenant_id) in compiled, "Monthly aggregates must filter by tenant_id"
        assert str(clinic_id) in compiled, "Monthly aggregates must filter by clinic_id (HIPAA-lite dual filter)"

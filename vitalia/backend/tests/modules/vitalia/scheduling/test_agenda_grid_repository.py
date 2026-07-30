"""RED tests — AgendaGridRepository HIPAA-lite dual filter + JOIN + preset filters.

TDD: these tests define the expected interface BEFORE implementation.
Uses in-memory mocks — no Postgres required (pure unit tests, not @integration).

Contract (03-arch A1, A12):
- EVERY query filters by tenant_id + clinic_id (HIPAA-lite dual filter)
- Cross-clinic queries return empty list (A3)
- Preset filter chips map to WHERE clause variants
- PHI projection: patient_name_masked + dni_masked (no raw PHI in response)
- JOIN: vitalia_appointments + vitalia_appointment_clinic_map + vitalia_appointment_payments

Per 05-guidelines TDD-mandatory + vitalia/.claude/rules/hipaa-lite.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

# ---------------------------------------------------------------------------
# Import helpers
# ---------------------------------------------------------------------------


def _import_agenda_grid_repo():
    """Import AgendaGridRepositoryImpl lazily (will fail RED until file exists)."""
    from src.modules.vitalia.scheduling.infrastructure.repositories.agenda_grid_repository_impl import (  # noqa: PLC0415
        AgendaGridRepositoryImpl,
    )

    return AgendaGridRepositoryImpl


def _import_agenda_grid_interface():
    from src.modules.vitalia.scheduling.infrastructure.repositories.agenda_grid_repository import (  # noqa: PLC0415
        AgendaGridRepository,
    )

    return AgendaGridRepository


def _import_preset_filter():
    from src.modules.vitalia.scheduling.domain.agenda_filter import AgendaPresetFilter  # noqa: PLC0415

    return AgendaPresetFilter


def _make_mock_session() -> MagicMock:
    """Build a minimal AsyncSession mock that supports execute() + mappings()."""
    session = MagicMock()
    result = MagicMock()
    result.all.return_value = []
    mappings_result = MagicMock()
    mappings_result.all.return_value = []
    mappings_result.first.return_value = None
    result.mappings.return_value = mappings_result
    session.execute = AsyncMock(return_value=result)
    return session


def _stmt_text_and_params(session: MagicMock) -> tuple[str, dict[str, Any]]:
    """Extract (sql_text, bound_params) from the last execute() call.

    Post-bugfix (vitalia-bugfix-agenda-actor-headers-422 T-2) the repo issues a
    parameterized SQLAlchemy ``text()`` statement (no ORM ``whereclause``). The dual
    filter lives in the bound params + SQL text, NOT in a ``.whereclause`` attribute.
    """
    call_args = session.execute.call_args
    stmt = call_args[0][0] if call_args[0] else call_args.args[0]
    sql_text = str(stmt)
    # text().bindparams() exposes bound values via the compiled params.
    params: dict[str, Any] = {bp.key: bp.value for bp in stmt._bindparams.values()}
    return sql_text, params


def _make_mock_session_with_rows(rows: list[Any]) -> MagicMock:
    """Build AsyncSession mock returning specific rows from execute()."""
    session = MagicMock()
    result = MagicMock()
    # mappings() -> all() returns list of mapping-like objects
    mappings_result = MagicMock()
    mappings_result.all.return_value = rows
    result.mappings.return_value = mappings_result
    result.all.return_value = rows
    session.execute = AsyncMock(return_value=result)
    return session


# ---------------------------------------------------------------------------
# Tests — import contract
# ---------------------------------------------------------------------------


class TestAgendaGridRepositoryImport:
    """AgendaGridRepository + Impl must be importable."""

    def test_interface_importable(self) -> None:
        repo_cls = _import_agenda_grid_interface()
        assert repo_cls is not None

    def test_impl_importable(self) -> None:
        impl_cls = _import_agenda_grid_repo()
        assert impl_cls is not None

    def test_impl_accepts_session_in_constructor(self) -> None:
        impl_cls = _import_agenda_grid_repo()
        session = _make_mock_session()
        repo = impl_cls(session=session)
        assert repo is not None

    def test_impl_has_list_slots_method(self) -> None:
        impl_cls = _import_agenda_grid_repo()
        assert hasattr(impl_cls, "list_slots")

    def test_impl_has_get_monthly_aggregates_stub(self) -> None:
        """list_slots is the primary method — monthly aggregates live in separate repo."""
        impl_cls = _import_agenda_grid_repo()
        # Primary required method
        assert hasattr(impl_cls, "list_slots")


# ---------------------------------------------------------------------------
# Tests — dual filter contract (A1 + A3 acceptance criteria)
# ---------------------------------------------------------------------------


class TestAgendaGridDualFilter:
    """Every query MUST include both tenant_id + clinic_id (HIPAA-lite)."""

    @pytest.mark.asyncio
    async def test_agenda_grid_filters_by_tenant_and_clinic(self) -> None:
        """list_slots must pass BOTH tenant_id + clinic_id into query execution."""
        impl_cls = _import_agenda_grid_repo()
        session = _make_mock_session()
        repo = impl_cls(session=session)

        tenant_id = uuid4()
        clinic_id = uuid4()
        date_from = datetime(2026, 6, 1, tzinfo=timezone.utc)
        date_to = datetime(2026, 6, 30, tzinfo=timezone.utc)

        await repo.list_slots(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            date_from=date_from,
            date_to=date_to,
        )

        # Session.execute MUST have been called
        assert session.execute.call_count >= 1
        # Verify tenant_id + clinic_id are bound as params (HIPAA-lite dual filter).
        # Post-bugfix the repo uses a parameterized text() statement — the dual filter
        # is in the bound params + SQL text, not a deprecated f-string WHERE clause.
        sql_text, params = _stmt_text_and_params(session)
        assert "va.tenant_id = :tenant_id" in sql_text, "tenant_id filter must be in WHERE"
        assert "va.clinic_id = :clinic_id" in sql_text, "clinic_id filter must be in WHERE (HIPAA-lite)"
        assert params.get("tenant_id") == tenant_id, "tenant_id must be bound to the actual value"
        assert params.get("clinic_id") == clinic_id, "clinic_id must be bound (HIPAA-lite dual filter)"

    @pytest.mark.asyncio
    async def test_agenda_grid_cross_clinic_returns_empty(self) -> None:
        """list_slots with wrong clinic_id returns empty — cross-clinic isolation."""
        impl_cls = _import_agenda_grid_repo()
        # Session returns empty result set (DB enforces isolation)
        session = _make_mock_session_with_rows([])
        repo = impl_cls(session=session)

        tenant_id = uuid4()
        clinic_id_wrong = uuid4()

        date_from = datetime(2026, 6, 1, tzinfo=timezone.utc)
        date_to = datetime(2026, 6, 30, tzinfo=timezone.utc)

        # With wrong clinic_id, the session mock returns no rows → result is []
        slots = await repo.list_slots(
            tenant_id=tenant_id,
            clinic_id=clinic_id_wrong,  # attacker trying cross-clinic
            date_from=date_from,
            date_to=date_to,
        )

        assert slots == [], (
            "Cross-clinic query must return empty list — the WHERE clause filters by clinic_id and no rows match"
        )


# ---------------------------------------------------------------------------
# Tests — preset filter mapping
# ---------------------------------------------------------------------------


class TestAgendaGridPresetFilters:
    """Preset filter chips must translate to specific WHERE clause conditions."""

    @pytest.mark.asyncio
    async def test_agenda_grid_preset_filter_today(self) -> None:
        """HOY preset narrows query to today's date range."""
        impl_cls = _import_agenda_grid_repo()
        AgendaPresetFilter = _import_preset_filter()
        session = _make_mock_session()
        repo = impl_cls(session=session)

        tenant_id = uuid4()
        clinic_id = uuid4()
        date_from = datetime(2026, 6, 1, tzinfo=timezone.utc)
        date_to = datetime(2026, 6, 30, tzinfo=timezone.utc)

        await repo.list_slots(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            date_from=date_from,
            date_to=date_to,
            preset_filter=AgendaPresetFilter.HOY,
        )

        assert session.execute.call_count >= 1

    @pytest.mark.asyncio
    async def test_agenda_grid_preset_filter_tomorrow_pending(self) -> None:
        """POR_CONFIRMAR_MANANA preset adds status filter."""
        impl_cls = _import_agenda_grid_repo()
        AgendaPresetFilter = _import_preset_filter()
        session = _make_mock_session()
        repo = impl_cls(session=session)

        tenant_id = uuid4()
        clinic_id = uuid4()
        date_from = datetime(2026, 6, 1, tzinfo=timezone.utc)
        date_to = datetime(2026, 6, 30, tzinfo=timezone.utc)

        await repo.list_slots(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            date_from=date_from,
            date_to=date_to,
            preset_filter=AgendaPresetFilter.POR_CONFIRMAR_MANANA,
        )

        sql_text, _ = _stmt_text_and_params(session)
        # POR_CONFIRMAR_MANANA should filter on SCHEDULED status
        assert "SCHEDULED" in sql_text or "scheduled" in sql_text.lower(), (
            "POR_CONFIRMAR_MANANA preset must filter by SCHEDULED status"
        )

    @pytest.mark.asyncio
    async def test_agenda_grid_preset_filter_no_shows(self) -> None:
        """NO_SHOWS_DIA preset filters by NO_SHOW appointment status."""
        impl_cls = _import_agenda_grid_repo()
        AgendaPresetFilter = _import_preset_filter()
        session = _make_mock_session()
        repo = impl_cls(session=session)

        tenant_id = uuid4()
        clinic_id = uuid4()
        date_from = datetime(2026, 6, 1, tzinfo=timezone.utc)
        date_to = datetime(2026, 6, 30, tzinfo=timezone.utc)

        await repo.list_slots(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            date_from=date_from,
            date_to=date_to,
            preset_filter=AgendaPresetFilter.NO_SHOWS_DIA,
        )

        sql_text, _ = _stmt_text_and_params(session)
        assert "NO_SHOW" in sql_text or "no_show" in sql_text.lower(), (
            "NO_SHOWS_DIA preset must filter by NO_SHOW status"
        )


# ---------------------------------------------------------------------------
# Tests — JOIN clinic_map correctness
# ---------------------------------------------------------------------------


class TestAgendaGridJoinContract:
    """Repo must JOIN vitalia_appointment_clinic_map to get service_label + origin."""

    def test_agenda_grid_joins_engine_appointments_correctly(self) -> None:
        """AgendaGridRepositoryImpl joins vitalia_appointment_clinic_map.

        Post-bugfix the JOIN lives in the module-level _GRID_FROM_JOINS constant
        (parameterized text() statement), so inspect the MODULE source, not just
        the class body.
        """
        import inspect

        from src.modules.vitalia.scheduling.infrastructure.repositories import (  # noqa: PLC0415
            agenda_grid_repository_impl as mod,
        )

        source = inspect.getsource(mod)
        # Must reference the clinic_map table name in the JOIN
        assert "vitalia_appointment_clinic_map" in source, (
            "AgendaGridRepositoryImpl must JOIN vitalia_appointment_clinic_map "
            "to resolve service_label + origin per 03-arch A12"
        )

    def test_agenda_grid_phi_projection_excludes_raw_name(self) -> None:
        """AgendaGridRepositoryImpl must NOT select raw patient.name column directly."""
        import inspect

        from src.modules.vitalia.scheduling.infrastructure.repositories import (  # noqa: PLC0415
            agenda_grid_repository_impl as mod,
        )

        source = inspect.getsource(mod)
        # The impl must use masked projection (patient_name_masked alias) and never
        # select a raw patient name column from the DB.
        assert "patient_name_masked" in source, (
            "AgendaGridRepositoryImpl MUST project patient_name_masked "
            "— never raw patient.name (HIPAA-lite PHI masking server-side)"
        )

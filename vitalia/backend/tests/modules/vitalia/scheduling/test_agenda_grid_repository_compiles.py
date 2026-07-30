# cap: scheduling.valeria-agenda
"""Regression tests — AgendaGridRepositoryImpl statements must COMPILE + EXECUTE.

Bug origin (vitalia-bugfix-agenda-actor-headers-422, T-2):
  GET /api/v1/scheduling/agenda/grid returned HTTP 500 with
  ``AttributeError: 'TextClause' object has no attribute 'selectable'``.

Root cause:
  ``select(...).select_from(text("vitalia_appointments va")).outerjoin(ORMModel, ...)``
  mixes a raw ``text()`` FROM with ORM-model join targets. The ORM compile path
  (``_normalize_froms``) iterates ``_from_obj`` and reads ``info.selectable`` on each
  entry — a ``TextClause`` has no ``.selectable`` → the statement crashes at COMPILE
  time, before it ever reaches the DB.

Why the pre-existing unit tests were false-green:
  ``test_agenda_grid_repository.py`` uses a MagicMock session and inspects
  ``stmt.whereclause`` only — it NEVER compiles or executes the statement (one test
  even documents "avoids full compile which fails on mixed text()+ORM select_from
  patterns"). So the broken construct shipped green.

These regression tests close that hole:
  - ``TestAgendaGridStatementCompiles`` — pure unit, no Postgres. Compiling the
    statement (``str(stmt)``) reproduces the AttributeError RED → must pass GREEN
    after the fix. Covers list_slots + get_by_id + every preset branch.
  - ``TestAgendaGridExecutesAgainstRealSchema`` — @integration, executes the real
    query against the migrated schema → proves "rows/empty without AttributeError"
    AND that every projected column exists in the real table.

Per .claude/rules/tdd-mandatory.md (regression test reproduces bug FIRST) +
docs/learnings/2026-06-11 mocked-service-tests-hide-repo-contract.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.modules.vitalia.scheduling.domain.agenda_filter import AgendaPresetFilter
from src.modules.vitalia.scheduling.infrastructure.repositories.agenda_grid_repository_impl import (
    AgendaGridRepositoryImpl,
)


class _CompileCaptureSession:
    """Async session stub that COMPILES every statement it receives.

    Unlike the MagicMock session used by the legacy unit tests, this stub calls
    ``str(stmt)`` (full SQL compile) on execute(). If the statement uses the broken
    text()+ORM select_from construct, compilation raises AttributeError here —
    exactly reproducing the production 500.
    """

    def __init__(self) -> None:
        self.compiled_sql: list[str] = []

    async def execute(self, stmt, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003, ANN201
        # Force a full compile — this is what the production DB driver does and what
        # the legacy mock-only tests skipped. Raises AttributeError on broken construct.
        self.compiled_sql.append(str(stmt.compile(compile_kwargs={"literal_binds": False})))

        class _Result:
            def mappings(self_inner):  # noqa: ANN001, ANN202, N805
                class _Mappings:
                    def all(self_m):  # noqa: ANN001, ANN202, N805
                        return []

                    def first(self_m):  # noqa: ANN001, ANN202, N805
                        return None

                return _Mappings()

            def scalars(self_inner):  # noqa: ANN001, ANN202, N805
                class _Scalars:
                    def all(self_s):  # noqa: ANN001, ANN202, N805
                        return []

                return _Scalars()

        return _Result()


def _repo() -> tuple[AgendaGridRepositoryImpl, _CompileCaptureSession]:
    session = _CompileCaptureSession()
    return AgendaGridRepositoryImpl(session=session), session  # type: ignore[arg-type]


_TID = uuid4()
_CID = uuid4()
_FROM = datetime(2026, 6, 1, tzinfo=timezone.utc)
_TO = datetime(2026, 6, 30, tzinfo=timezone.utc)


class TestPatientNameMasking:
    """_mask_name / _apply_name_mask — PHI masking happens in Python (D5)."""

    def test_mask_name_initial_plus_surname(self) -> None:
        from src.modules.vitalia.scheduling.infrastructure.repositories.agenda_grid_repository_impl import (
            _mask_name,
        )

        assert _mask_name("María Fernanda López") == "M. López"
        assert _mask_name("Ana García") == "A. García"
        assert _mask_name(None) == "—"
        assert _mask_name("   ") == "—"

    def test_apply_name_mask_strips_raw_key(self) -> None:
        from src.modules.vitalia.scheduling.infrastructure.repositories.agenda_grid_repository_impl import (
            _apply_name_mask,
        )

        row = {"appointment_id": "a1", "raw_patient_name": "Diego Hernández Ruiz"}
        out = _apply_name_mask(row)
        # Raw decrypted name MUST be gone; only the masked value remains (HIPAA-lite).
        assert "raw_patient_name" not in out
        assert out["patient_name_masked"] == "D. Ruiz"


class TestAgendaGridStatementCompiles:
    """The agenda-grid statements must compile to SQL (no TextClause AttributeError)."""

    @pytest.mark.asyncio
    async def test_list_slots_statement_compiles(self) -> None:
        repo, session = _repo()
        rows = await repo.list_slots(
            tenant_id=_TID,
            clinic_id=_CID,
            date_from=_FROM,
            date_to=_TO,
        )
        assert rows == []
        assert session.compiled_sql, "execute() must have compiled the statement"
        sql = session.compiled_sql[0].lower()
        # Dual filter must survive the rewrite (HIPAA-lite, non-negotiable).
        assert "tenant_id" in sql
        assert "clinic_id" in sql
        # PHI: the SQL decrypts the encrypted name (pgp_sym_decrypt + bound KEK :kek);
        # the masking to "M. López" + stripping the raw key happen in Python (_apply_name_mask).
        assert "pgp_sym_decrypt" in sql
        assert "raw_patient_name" in sql
        # Real doctor name now resolved (no more '—' placeholder): doctor join present.
        assert "vitalia_doctors" in sql

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "preset",
        [
            AgendaPresetFilter.HOY,
            AgendaPresetFilter.NO_SHOWS_DIA,
            AgendaPresetFilter.POR_CONFIRMAR_MANANA,
            AgendaPresetFilter.REAGENDAR_PENDIENTES,
            AgendaPresetFilter.SALDOS_PENDIENTES,
        ],
    )
    async def test_list_slots_compiles_for_every_preset(self, preset: AgendaPresetFilter) -> None:
        repo, session = _repo()
        rows = await repo.list_slots(
            tenant_id=_TID,
            clinic_id=_CID,
            date_from=_FROM,
            date_to=_TO,
            preset_filter=preset,
        )
        assert rows == []
        assert session.compiled_sql, f"preset {preset} must compile"

    @pytest.mark.asyncio
    async def test_get_by_id_statement_compiles(self) -> None:
        repo, session = _repo()
        result = await repo.get_by_id(
            uuid4(),
            tenant_id=_TID,
            clinic_id=_CID,
        )
        assert result is None
        assert session.compiled_sql, "get_by_id must compile the statement"
        sql = session.compiled_sql[0].lower()
        assert "tenant_id" in sql
        assert "clinic_id" in sql

    @pytest.mark.asyncio
    async def test_list_slots_dual_filter_still_required(self) -> None:
        """clinic_id=None must still raise (dual filter guard not weakened by fix)."""
        repo, _ = _repo()
        with pytest.raises(ValueError, match="clinic_id"):
            await repo.list_slots(
                tenant_id=_TID,
                clinic_id=None,  # type: ignore[arg-type]
                date_from=_FROM,
                date_to=_TO,
            )


@pytest.mark.integration
class TestAgendaGridExecutesAgainstRealSchema:
    """Execute the real query against the migrated schema — rows/empty, no crash."""

    @pytest.mark.asyncio
    async def test_list_slots_executes_returns_list(self, db_session) -> None:  # noqa: ANN001
        """The grid query executes against vitalia_appointments without AttributeError.

        Empty result is fine (seed-free DB) — the point is the statement compiles AND
        every projected column exists in the real table (no UndefinedColumn either).
        """
        repo = AgendaGridRepositoryImpl(session=db_session)
        rows = await repo.list_slots(
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            date_from=_FROM,
            date_to=_TO,
        )
        assert isinstance(rows, list)

    @pytest.mark.asyncio
    async def test_list_slots_executes_with_preset(self, db_session) -> None:  # noqa: ANN001
        repo = AgendaGridRepositoryImpl(session=db_session)
        rows = await repo.list_slots(
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            date_from=_FROM,
            date_to=_TO,
            preset_filter=AgendaPresetFilter.SALDOS_PENDIENTES,
        )
        assert isinstance(rows, list)

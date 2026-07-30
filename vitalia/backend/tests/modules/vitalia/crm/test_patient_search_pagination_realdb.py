# cap: crm.crm-consent-optout
"""Real-DB regression: patient typeahead cursor pagination must NOT overlap.

WHY THIS EXISTS (root cause of the bug it guards):
  test_patient_search_typeahead.py MOCKS the repo (AsyncMock) → it never ran the
  actual SQL, so a BROKEN cursor shipped: `ORDER BY created_at DESC` paired with
  `WHERE id > :cursor` (cursor field ≠ sort field + ascending filter against a
  DESC sort) → page 2 OVERLAPPED page 1 → the SAME patient appeared on both pages
  → "Encountered two children with the same key" in the FE picker, and the
  corrupted virtualized list blocked inline-create. A mocked unit test cannot
  catch a wrong ORDER BY / WHERE. This test paginates a REAL dataset and asserts
  no id overlap across pages — it RED-fails on the old cursor, GREEN on the fix
  (row-comparison `(created_at, id) < (cursor_row)`).

marker: integration (requires Postgres — skipped if DB unreachable per conftest).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia._shared.encryption.kek_client import KEKClient
from src.modules.vitalia.crm.infrastructure.persistence.patient_repository import (
    PatientRepository,
)

_BASE_TIME = datetime(2026, 7, 1, 9, 0, 0, tzinfo=timezone.utc)

# NB: sólo columnas presentes en el schema de test (vitalia_test). El search()
# bajo prueba lee id/tenant_id/clinic_id/name/channel_first/created_at — no toca
# marketing_opt_in/opt_out (esas viven en dev; vitalia_test driftó — ver HB).
_INSERT_PATIENT = text(
    """
    INSERT INTO vitalia_patients
      (id, tenant_id, clinic_id, name, phone, email, channel_first, notes,
       created_at, updated_at)
    VALUES
      (:id, :tenant_id, :clinic_id,
       pgp_sym_encrypt(:name, :kek), pgp_sym_encrypt('', :kek), pgp_sym_encrypt('', :kek),
       :channel, '', :created_at, :updated_at)
    """
)


@pytest.mark.integration
class TestPatientSearchCursorPaginationRealDB:
    """SC-pacientes-grandes: paginar >limit pacientes sin solape ni filas perdidas."""

    async def _seed(self, db_session: AsyncSession, *, kek: str, tenant_id, clinic_id, n: int, tag: str) -> None:
        """Seed n patients matching `tag`, with distinct DESCending created_at."""
        for i in range(n):
            await db_session.execute(
                _INSERT_PATIENT,
                {
                    "id": str(uuid4()),
                    "tenant_id": str(tenant_id),
                    "clinic_id": str(clinic_id),
                    "name": f"{tag} {i:03d}",
                    "channel": "walk_in",
                    "kek": kek,
                    # distinct timestamps so created_at DESC ordering is exercised
                    "created_at": _BASE_TIME - timedelta(minutes=i),
                    "updated_at": _BASE_TIME,
                },
            )
        await db_session.flush()

    async def test_pages_do_not_overlap_and_cover_all_rows(self, db_session: AsyncSession) -> None:
        """25 pacientes, limit=20 → page1=20 + page2=5, sin id duplicado entre páginas.

        RED en el cursor viejo (id > :cursor sobre created_at DESC → page2 solapa
        page1). GREEN con la row-comparison estable.
        """
        kek = KEKClient.from_env().get_key()
        tenant_id = uuid4()
        clinic_id = uuid4()
        tag = "PgPagRegress"
        await self._seed(db_session, kek=kek, tenant_id=tenant_id, clinic_id=clinic_id, n=25, tag=tag)

        repo = PatientRepository(session=db_session, audit_repo=AsyncMock(), kek=KEKClient.from_env())

        page1 = await repo.search(tenant_id=tenant_id, clinic_id=clinic_id, q=tag, limit=20)
        assert len(page1["items"]) == 20, "page1 debería traer el limit completo"
        assert page1["next_cursor"] is not None, "con 25 filas y limit 20 debe haber next_cursor"

        page2 = await repo.search(
            tenant_id=tenant_id, clinic_id=clinic_id, q=tag, cursor=page1["next_cursor"], limit=20
        )
        assert len(page2["items"]) == 5, "page2 debería traer las 5 restantes"

        ids1 = {it["patient_id"] for it in page1["items"]}
        ids2 = {it["patient_id"] for it in page2["items"]}
        assert ids1.isdisjoint(ids2), (
            "PÁGINAS SOLAPADAS: un patient_id aparece en page1 y page2 → cursor roto "
            "(este es el bug del dup-key en el FE)"
        )
        assert len(ids1 | ids2) == 25, "la paginación perdió o duplicó filas (esperadas 25 únicas)"

    async def test_first_page_is_created_at_desc(self, db_session: AsyncSession) -> None:
        """El orden de page1 es created_at DESC (recencia primero)."""
        kek = KEKClient.from_env().get_key()
        tenant_id = uuid4()
        clinic_id = uuid4()
        tag = "PgOrderRegress"
        await self._seed(db_session, kek=kek, tenant_id=tenant_id, clinic_id=clinic_id, n=5, tag=tag)

        repo = PatientRepository(session=db_session, audit_repo=AsyncMock(), kek=KEKClient.from_env())
        page = await repo.search(tenant_id=tenant_id, clinic_id=clinic_id, q=tag, limit=20)

        created = [it["created_at"] for it in page["items"]]
        assert created == sorted(created, reverse=True), "page1 no está en created_at DESC"

# cap: scheduling.mateo-agenda
"""Router seam — GET /availability/service-day RBAC + PHI + dual-filter (T-D1).

Validation/RBAC cases run with no Postgres (FastAPI short-circuits, or _get_db
overridden to a null session). The 200-shape + no-leak case is integration
(real DB via db_session override) and auto-skips if Postgres down.

Covers (delta § 7 seam_coverage):
  - 422 missing X-Clinic-ID
  - 422 missing serviceId query param
  - 422 invalid date
  - 403 role outside SCHEDULING_PHI_ROLES (PHI_RBAC_DENIED)
  - 200 shape carries NO patient field (response_model is PHI-safe)
  - cross-clinic / cross-tenant doctors do not leak through the endpoint
"""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from ._availability_seed import insert_doctor, insert_link, insert_slot

TENANT_A = uuid4()
TENANT_B = uuid4()
CLINIC_A = uuid4()
CLINIC_B = uuid4()
DAY = date(2026, 7, 1)
_URL = "/api/v1/scheduling/availability/service-day"


def _make_app() -> FastAPI:
    from src.modules.vitalia.scheduling.api.availability_router import router  # noqa: PLC0415

    app = FastAPI(redirect_slashes=False)
    app.include_router(router, prefix="/api/v1/scheduling")
    return app


async def _null_db():
    yield None


def _phi_headers(*, tenant_id=TENANT_A, clinic_id=CLINIC_A, role="doctor") -> dict[str, str]:
    return {
        "X-Tenant-ID": str(tenant_id),
        "X-Clinic-ID": str(clinic_id),
        "X-User-ID": str(uuid4()),
        "X-User-Role": role,
    }


# ---------------------------------------------------------------------------
# Validation / RBAC — no Postgres
# ---------------------------------------------------------------------------


class TestServiceDayValidation:
    @pytest.mark.asyncio
    async def test_missing_clinic_id_header_returns_422(self):
        app = _make_app()
        headers = _phi_headers()
        del headers["X-Clinic-ID"]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(_URL, params={"serviceId": str(uuid4()), "date": "2026-07-01"}, headers=headers)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_service_id_param_returns_422(self):
        app = _make_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(_URL, params={"date": "2026-07-01"}, headers=_phi_headers())
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_date_returns_422(self):
        from src.modules.vitalia.scheduling.api.availability_router import _get_db  # noqa: PLC0415

        app = _make_app()
        app.dependency_overrides[_get_db] = _null_db
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                _URL, params={"serviceId": str(uuid4()), "date": "not-a-date"}, headers=_phi_headers()
            )
        assert resp.status_code == 422
        assert resp.json()["detail"]["error_code"] == "INVALID_DATE"

    @pytest.mark.asyncio
    async def test_role_outside_phi_roles_returns_403(self):
        from src.modules.vitalia.scheduling.api.availability_router import _get_db  # noqa: PLC0415

        app = _make_app()
        app.dependency_overrides[_get_db] = _null_db
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                _URL,
                params={"serviceId": str(uuid4()), "date": "2026-07-01"},
                headers=_phi_headers(role="marketing"),
            )
        assert resp.status_code == 403
        assert resp.json()["detail"]["error_code"] == "PHI_RBAC_DENIED"


# ---------------------------------------------------------------------------
# Happy path + no-leak — real DB
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestServiceDayIntegration:
    async def _app_with_db(self, db_session) -> FastAPI:
        from src.modules.vitalia.scheduling.api.availability_router import _get_db  # noqa: PLC0415

        app = _make_app()

        async def _override():
            yield db_session

        app.dependency_overrides[_get_db] = _override
        return app

    async def test_200_shape_has_no_patient_field(self, db_session) -> None:
        offer_id = uuid4()
        doc = await insert_doctor(
            db_session, tenant_id=TENANT_A, clinic_id=CLINIC_A, first_name="Ada", last_name="Shape"
        )
        await insert_slot(db_session, tenant_id=TENANT_A, clinic_id=CLINIC_A, doctor_id=doc, slot_date=DAY)
        await insert_link(db_session, tenant_id=TENANT_A, offer_id=offer_id, doctor_id=doc)

        app = await self._app_with_db(db_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                _URL, params={"serviceId": str(offer_id), "date": DAY.isoformat()}, headers=_phi_headers()
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["service_id"] == str(offer_id)
        assert body["date"] == DAY.isoformat()
        assert set(body.keys()) == {"service_id", "date", "doctors"}
        assert "patient" not in resp.text.lower()
        first = next(d for d in body["doctors"] if d["doctor_id"] == str(doc))
        assert set(first.keys()) == {"doctor_id", "doctor_label", "blocks"}

    async def test_cross_clinic_and_cross_tenant_no_leak(self, db_session) -> None:
        offer_id = uuid4()
        # mine (CLINIC_A / TENANT_A)
        mine = await insert_doctor(
            db_session, tenant_id=TENANT_A, clinic_id=CLINIC_A, first_name="Mia", last_name="Mine"
        )
        await insert_slot(db_session, tenant_id=TENANT_A, clinic_id=CLINIC_A, doctor_id=mine, slot_date=DAY)
        await insert_link(db_session, tenant_id=TENANT_A, offer_id=offer_id, doctor_id=mine)
        # other clinic, same tenant — linked but must not leak
        other_clinic = await insert_doctor(
            db_session, tenant_id=TENANT_A, clinic_id=CLINIC_B, first_name="Oki", last_name="OtherClinic"
        )
        await insert_slot(db_session, tenant_id=TENANT_A, clinic_id=CLINIC_B, doctor_id=other_clinic, slot_date=DAY)
        await insert_link(db_session, tenant_id=TENANT_A, offer_id=offer_id, doctor_id=other_clinic)
        # other tenant — linked but must not leak
        other_tenant = await insert_doctor(
            db_session, tenant_id=TENANT_B, clinic_id=CLINIC_A, first_name="Tea", last_name="OtherTenant"
        )
        await insert_slot(db_session, tenant_id=TENANT_B, clinic_id=CLINIC_A, doctor_id=other_tenant, slot_date=DAY)
        await insert_link(db_session, tenant_id=TENANT_B, offer_id=offer_id, doctor_id=other_tenant)

        app = await self._app_with_db(db_session)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                _URL, params={"serviceId": str(offer_id), "date": DAY.isoformat()}, headers=_phi_headers()
            )

        assert resp.status_code == 200
        returned = {d["doctor_id"] for d in resp.json()["doctors"]}
        assert str(mine) in returned
        assert str(other_clinic) not in returned
        assert str(other_tenant) not in returned

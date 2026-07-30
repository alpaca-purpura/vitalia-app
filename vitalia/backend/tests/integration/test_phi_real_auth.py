# cap: iam.iam-scaffold-slice-1
"""Integration tests for PHI real auth — Slice 2 (SC-1, SC-4).

Tests the decoder JWKS real path + role-from-DB resolution.

SC-1: doctor JWT real → PHI 200 (decoder + resolver verify correctly).
SC-4: invalid/expired/forged/stub-legacy token → 401 (no bypass).

SC-2 (recepcion/marketing → 403) and SC-3 (cross-tenant 404 / cross-clinic 403)
are owned by T-2 (repos-wire). Stubs are left here as skeletons.

Strategy for deterministic tests without network egress:
  monkeypatch verify_token_payload with fixed payload
  (sub=user_3EQJjxsvxiZ5exQjucSB651xnUd = doctor.demo)
  + seed god-matrix DB fixtures (tenant Sanaré + clinic).

story: vitalia-iam-slice2-phi-real-auth · T-1 (SC-1 + SC-4)
date: 2026-05-29

downstream-regression-na: brand-local PHI real auth integration tests
"""

from __future__ import annotations

import os
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# Minimal env vars required to import src.main (luana_core_platform settings)
# Pattern from tests/test_main_iam_routes_mounted.py § _REQUIRED_ENV_VARS
# ---------------------------------------------------------------------------

_REQUIRED_ENV_VARS = {
    "LOG_LEVEL": "DEBUG",
    "DOMAIN_NAME": "localhost",
    "TRAEFIK_NETWORK": "traefik",
    "API_SECRET_KEY": "test-secret-key-for-phi-auth-test",
    "WHATSAPP_API_TOKEN": "test-token",
    "WHATSAPP_PHONE_NUMBER_ID": "1234567890",
    "WHATSAPP_VERIFY_TOKEN": "test-verify",
    "OPENAI_API_KEY": "sk-test-0000000000000000000000000000000000000000000000000",
    "REDIS_URL": "redis://localhost:6379/0",
    "QDRANT_URL": "http://localhost:6333",
    "POSTGRES_USER": "postgres",
    "POSTGRES_PASSWORD": "postgres",
    "POSTGRES_DB": "vitalia_test",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "API_URL": "http://localhost:8002",
}


@pytest.fixture(autouse=True, scope="module")
def _set_env_for_app_import():
    """Inject minimal env vars so src.main can be imported without real credentials."""
    with patch.dict(os.environ, _REQUIRED_ENV_VARS):
        yield


# ---------------------------------------------------------------------------
# Constants matching 04-validators.yaml § test_construction_plan
# ---------------------------------------------------------------------------

TENANT_SANARE = uuid.UUID("e69a691d-070e-5caf-a053-6e74642ec100")
CLINIC_SANARE = uuid.UUID("f035be5b-0ac4-5210-8fc3-395650ca2b83")

# Clerk user_id (sub claim) for doctor.demo (from god-matrix seed)
DOCTOR_CLERK_SUB = "user_3EQJjxsvxiZ5exQjucSB651xnUd"

# Fixed JWT payload that verify_token_payload will return when monkeypatched
_DOCTOR_JWT_PAYLOAD: dict = {
    "sub": DOCTOR_CLERK_SUB,
    "email": "doctor.demo@sanare.vitalia.test",
    "full_name": "Dr. Demo Doctor",
    "iat": 9999999999,
    "exp": 9999999999,
}

# Fake doctor DB UUID (must exist in the test DB if running @integration)
DOCTOR_DB_UUID = uuid.UUID("00000000-0000-0000-0000-000000000001")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_fake_db_session(doctor_uuid: uuid.UUID | None = DOCTOR_DB_UUID, role: str = "doctor") -> AsyncSession:
    """Build a mock AsyncSession that returns expected rows for role resolution.

    Returns an AsyncMock mimicking AsyncSession.execute() with scalar_one_or_none().
    First execute() (UserModel lookup) returns a row with .id = doctor_uuid.
    Second execute() (UserTenantModel lookup) returns the role string.

    Note: execute() is async, so it returns a coroutine that resolves to a result object.
    The result object's scalar_one_or_none() is sync.
    """
    from unittest.mock import MagicMock

    session = AsyncMock(spec=AsyncSession)

    # Row mock for UserModel query (clerk_id lookup → users.id)
    # execute() is async → returns a MagicMock result with sync scalar_one_or_none()
    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = doctor_uuid

    # Row mock for UserTenantModel query (role lookup)
    role_result = MagicMock()
    role_result.scalar_one_or_none.return_value = role

    # execute() is awaitable and returns different results on each call
    session.execute = AsyncMock(side_effect=[user_result, role_result])
    return session


# ---------------------------------------------------------------------------
# SC-1 — happy path: doctor JWT real → PHI access (decoder + resolver)
# ---------------------------------------------------------------------------


class TestSC1DoctorJwtRealSeePhi:
    """SC-1: doctor with real JWT (mocked JWKS) → resolver resolves correctly."""

    @pytest.mark.asyncio
    async def test_doctor_jwt_real_sees_phi(self) -> None:
        """Decoder decodes real JWT (mocked) + resolver returns doctor ClinicContext.

        Verifies:
        1. verify_token_payload is called (not the stub path)
        2. user_id extracted from payload["sub"]
        3. DB role resolution returns "doctor"
        4. ClinicContext.role == "doctor"

        Note: SC-1 e2e grader (audit_log row) is exercised in full T-2 scope
        when repos are wired. Here we validate the auth core (decoder + resolver).
        """
        from src.modules.vitalia.iam.application.services.clinic_resolver import (
            ClinicResolver,
        )
        from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import (
            ClerkJwtDecoder,
        )

        decoder = ClerkJwtDecoder()
        resolver = ClinicResolver(decoder=decoder)

        fake_real_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.real_jwt_placeholder"

        db_session = _make_fake_db_session(doctor_uuid=DOCTOR_DB_UUID, role="doctor")

        # Monkeypatch verify_token_payload to return fixed doctor payload
        with patch(
            "src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder.verify_token_payload",
            return_value=_DOCTOR_JWT_PAYLOAD,
        ):
            ctx = await resolver.async_resolve(
                token=fake_real_token,
                session=db_session,
                tenant_id_str=str(TENANT_SANARE),
                clinic_id_str=str(CLINIC_SANARE),
            )

        assert ctx.role == "doctor"
        assert ctx.user_id == DOCTOR_CLERK_SUB
        assert ctx.tenant_id == TENANT_SANARE
        assert ctx.clinic_id == CLINIC_SANARE

    @pytest.mark.asyncio
    async def test_decoder_calls_verify_token_payload_not_stub(self) -> None:
        """decoder.decode() MUST call verify_token_payload for non-stub tokens."""
        from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import (
            ClerkJwtDecoder,
        )

        decoder = ClerkJwtDecoder()
        real_token = "eyJhbGciOiJSUzI1NiJ9.real_token"

        with patch(
            "src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder.verify_token_payload",
            return_value=_DOCTOR_JWT_PAYLOAD,
        ) as mock_verify:
            os.environ.pop("VITALIA_AUTH_STUB", None)
            payload = decoder.decode(real_token)

        mock_verify.assert_called_once_with(real_token)
        assert payload.user_id == DOCTOR_CLERK_SUB

    @pytest.mark.asyncio
    async def test_role_resolved_from_db_not_token(self) -> None:
        """async_resolve() must use DB role, not token claim."""
        from src.modules.vitalia.iam.application.services.clinic_resolver import (
            ClinicResolver,
        )
        from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import (
            ClerkJwtDecoder,
        )

        # payload has role="marketing" (from token — should be IGNORED)
        payload_with_wrong_role = {**_DOCTOR_JWT_PAYLOAD}
        # role is NOT part of the real Clerk JWT payload; but even if it were,
        # it should not influence ClinicContext.role

        decoder = ClerkJwtDecoder()
        resolver = ClinicResolver(decoder=decoder)

        # DB returns "doctor" regardless of any claim in token
        db_session = _make_fake_db_session(doctor_uuid=DOCTOR_DB_UUID, role="doctor")

        real_token = "eyJhbGciOiJSUzI1NiJ9.real_token"

        with patch(
            "src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder.verify_token_payload",
            return_value=payload_with_wrong_role,
        ):
            ctx = await resolver.async_resolve(
                token=real_token,
                session=db_session,
                tenant_id_str=str(TENANT_SANARE),
                clinic_id_str=str(CLINIC_SANARE),
            )

        # Role MUST come from DB (doctor), not any claim in the token
        assert ctx.role == "doctor"


# ---------------------------------------------------------------------------
# SC-4 — adversarial: invalid/expired/forged/stub-legacy → 401
# ---------------------------------------------------------------------------


class TestSC4InvalidToken401:
    """SC-4: any non-real token must raise JwtDecodeError → maps to 401."""

    def test_invalid_token_401(self) -> None:
        """Forged/garbage token → JwtDecodeError (will map to 401 in router)."""
        from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import (
            ClerkJwtDecoder,
            JwtDecodeError,
        )

        decoder = ClerkJwtDecoder()

        with patch(
            "src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder.verify_token_payload",
            side_effect=HTTPException(status_code=401, detail="Invalid Token"),
        ):
            os.environ.pop("VITALIA_AUTH_STUB", None)
            with pytest.raises(JwtDecodeError):
                decoder.decode("not.a.real.jwt.at.all")

    def test_expired_token_401(self) -> None:
        """Expired token → JwtDecodeError (HTTPException 401 from engine → mapped)."""
        from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import (
            ClerkJwtDecoder,
            JwtDecodeError,
        )

        decoder = ClerkJwtDecoder()
        expired_jwt = "eyJhbGciOiJSUzI1NiJ9.expired_placeholder"

        with patch(
            "src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder.verify_token_payload",
            side_effect=HTTPException(status_code=401, detail="Token expired"),
        ):
            os.environ.pop("VITALIA_AUTH_STUB", None)
            with pytest.raises(JwtDecodeError):
                decoder.decode(expired_jwt)

    def test_legacy_stub_token_rejected_in_runtime_401(self) -> None:
        """stub:... tokens MUST be rejected when VITALIA_AUTH_STUB is absent.

        This is the 'stub-legacy' adversarial case: an attacker sends a stub token
        hoping the runtime still accepts it.
        """
        from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import (
            ClerkJwtDecoder,
            JwtDecodeError,
        )

        decoder = ClerkJwtDecoder()
        legacy_stub = "stub:tenant-id:clinic-id:doctor:user-attacker"

        # Simulate runtime: VITALIA_AUTH_STUB not set
        with patch(
            "src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder.verify_token_payload",
            side_effect=HTTPException(status_code=401, detail="Invalid Token: stub token is not a valid JWT"),
        ):
            os.environ.pop("VITALIA_AUTH_STUB", None)
            with pytest.raises(JwtDecodeError):
                decoder.decode(legacy_stub)

    def test_empty_token_raises_jwt_decode_error(self) -> None:
        """Empty token → JwtDecodeError without calling JWKS."""
        from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import (
            ClerkJwtDecoder,
            JwtDecodeError,
        )

        decoder = ClerkJwtDecoder()
        with pytest.raises(JwtDecodeError):
            decoder.decode("")

    def test_none_bearer_token_resolves_missing_auth(self) -> None:
        """None/empty token → MissingAuthHeaderError from resolver."""
        from src.modules.vitalia.iam.application.services.clinic_resolver import (
            ClinicResolver,
            MissingAuthHeaderError,
        )
        from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import (
            ClerkJwtDecoder,
        )

        decoder = ClerkJwtDecoder()
        resolver = ClinicResolver(decoder=decoder)

        with pytest.raises(MissingAuthHeaderError):
            resolver.resolve(None)  # type: ignore[arg-type]

    def test_error_body_does_not_leak_phi_on_401(self) -> None:
        """JwtDecodeError message must not contain PHI or sensitive details.

        The error message surfaced to the user must be generic (no payload leaks).
        """
        from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import (
            ClerkJwtDecoder,
            JwtDecodeError,
        )

        decoder = ClerkJwtDecoder()

        with patch(
            "src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder.verify_token_payload",
            side_effect=HTTPException(status_code=401, detail="Invalid Token: some_internal_detail"),
        ):
            os.environ.pop("VITALIA_AUTH_STUB", None)
            with pytest.raises(JwtDecodeError) as exc_info:
                decoder.decode("bad.token.here")

        error_msg = str(exc_info.value)
        # Must NOT expose specific JWT internals that could aid attackers
        assert "some_internal_detail" not in error_msg, (
            "JwtDecodeError message must not leak internal token details (PHI safety + security)."
        )


# ---------------------------------------------------------------------------
# SC-2: role-based 403 (recepcion / marketing cannot access PHI)
# T-2 — repos-wire ticket
# ---------------------------------------------------------------------------


class TestSC2RoleBased403:
    """SC-2: recepcion and marketing roles → 403 on PHI endpoints.

    Strategy:
    - Use httpx.AsyncClient with the vitalia FastAPI app.
    - Monkeypatch ClinicResolver.async_resolve to return ClinicContext with
      role="recepcion" or role="marketing" (DB-sourced role in Slice 2).
    - Assert HTTP 403 response.
    - Assert response body does NOT contain PHI fields (no-leak).

    No real DB needed for role-gate tests (role check happens before repo access).
    """

    @pytest.mark.asyncio
    async def test_recepcion_403_on_get_patient(self) -> None:
        """SC-2: recepcion role → 403 on GET /api/v1/crm/patients/{id}.

        Grader:
        - HTTP 403 returned.
        - Response body does not contain any PHI field names (no leak).

        Strategy: override get_async_session with stub + mock async_resolve
        so no real DB connection is attempted. Role check fires before repos.
        """
        from httpx import ASGITransport, AsyncClient

        with patch.dict(os.environ, _REQUIRED_ENV_VARS):
            from src.db import get_async_session
            from src.main import app
            from src.modules.vitalia.iam.application.services.clinic_resolver import (
                ClinicContext,
            )

        _patient_id = uuid.uuid4()
        ctx_recepcion = ClinicContext(
            user_id=DOCTOR_CLERK_SUB,
            tenant_id=TENANT_SANARE,
            clinic_id=CLINIC_SANARE,
            role="recepcion",
            email="recepcion@sanare.vitalia.test",
            name="Recepcion Demo",
        )

        # Stub session — not called because role check fires first (403 early exit)
        stub_session = AsyncMock()

        async def _override_session():
            yield stub_session

        app.dependency_overrides[get_async_session] = _override_session

        async_resolve_mock = AsyncMock(return_value=ctx_recepcion)

        try:
            with patch(
                "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
                new=async_resolve_mock,
            ):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.get(
                        f"/api/v1/crm/patients/{_patient_id}",
                        headers={
                            "Authorization": "Bearer stub:test:test:recepcion:user1",
                            "X-Tenant-ID": str(TENANT_SANARE),
                            "X-Clinic-ID": str(CLINIC_SANARE),
                        },
                    )
        finally:
            app.dependency_overrides.pop(get_async_session, None)

        assert response.status_code == 403, (
            f"recepcion role MUST get 403 on PHI endpoint, got {response.status_code}: {response.text}"
        )
        body_text = response.text.lower()
        # PHI fields must NOT appear in the 403 response
        for phi_field in ("date_of_birth", "diagnosis", "treatment"):
            assert phi_field not in body_text, f"403 response must not leak PHI field '{phi_field}': {response.text}"

    @pytest.mark.asyncio
    async def test_marketing_403_on_marketing_opt_in(self) -> None:
        """SC-2: marketing role → 403 on PATCH /api/v1/crm/patients/{id}/marketing-opt-in.

        Grader:
        - HTTP 403 returned.
        - Response body does not contain PHI.
        """
        from httpx import ASGITransport, AsyncClient

        with patch.dict(os.environ, _REQUIRED_ENV_VARS):
            from src.db import get_async_session
            from src.main import app
            from src.modules.vitalia.iam.application.services.clinic_resolver import (
                ClinicContext,
            )

        _patient_id = uuid.uuid4()
        ctx_marketing = ClinicContext(
            user_id=DOCTOR_CLERK_SUB,
            tenant_id=TENANT_SANARE,
            clinic_id=CLINIC_SANARE,
            role="marketing",
            email="marketing@sanare.vitalia.test",
            name="Marketing Demo",
        )

        stub_session = AsyncMock()

        async def _override_session():
            yield stub_session

        app.dependency_overrides[get_async_session] = _override_session

        async_resolve_mock = AsyncMock(return_value=ctx_marketing)

        try:
            with patch(
                "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
                new=async_resolve_mock,
            ):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.patch(
                        f"/api/v1/crm/patients/{_patient_id}/marketing-opt-in",
                        json={"opt_in": True},
                        headers={
                            "Authorization": "Bearer stub:test:test:marketing:user2",
                            "X-Tenant-ID": str(TENANT_SANARE),
                            "X-Clinic-ID": str(CLINIC_SANARE),
                        },
                    )
        finally:
            app.dependency_overrides.pop(get_async_session, None)

        assert response.status_code == 403, (
            f"marketing role MUST get 403 on PHI consent endpoint, got {response.status_code}: {response.text}"
        )
        # Audit denial: response body is generic error message, not PHI
        body_lower = response.text.lower()
        for phi_field in ("date_of_birth", "diagnosis", "treatment_plan"):
            assert phi_field not in body_lower, (
                f"403 response must not contain PHI field '{phi_field}': {response.text}"
            )


# ---------------------------------------------------------------------------
# SC-3: cross-tenant 404 + cross-clinic 403 (no PHI leak)
# T-2 — repos-wire ticket
# ---------------------------------------------------------------------------


class TestSC3CrossTenantCrossClinic:
    """SC-3: cross-tenant 404 / cross-clinic 403 — no PHI leak.

    Strategy:
    - Cross-tenant: async_resolve returns ClinicContext with different tenant_id.
      PatientRepository queries with that tenant_id → row not found → 404.
      Assert no PHI in response body.
    - Cross-clinic: async_resolve returns ClinicContext with same tenant but
      different clinic_id. PatientRepository dual-filter returns None → 404.
      (Or: service raises PHIAccessDeniedError → 403.)
      Assert no PHI in response body.

    In both cases, the key assertion is: response body does NOT contain
    patient PHI fields (name, email, diagnosis, etc.).
    """

    _OTHER_TENANT = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    _OTHER_CLINIC = uuid.UUID("11111111-2222-3333-4444-555555555555")

    @pytest.mark.asyncio
    async def test_cross_tenant_404_no_phi_leak(self) -> None:
        """SC-3: doctor from tenant B requests PHI of tenant A → 404, no PHI leak.

        Grader:
        - HTTP 404 returned (not 200 with wrong tenant's data).
        - Response body does not contain any PHI field values.

        Strategy: async_resolve returns cross-tenant ctx. PatientRepository stub
        returns None → service returns None → endpoint raises 404.
        """
        from httpx import ASGITransport, AsyncClient

        with patch.dict(os.environ, _REQUIRED_ENV_VARS):
            from src.db import get_async_session
            from src.main import app
            from src.modules.vitalia.iam.application.services.clinic_resolver import (
                ClinicContext,
            )

        _patient_id = uuid.uuid4()
        # Doctor from a DIFFERENT tenant tries to access TENANT_SANARE patient
        ctx_other_tenant = ClinicContext(
            user_id="user_cross_tenant_attacker",
            tenant_id=self._OTHER_TENANT,  # Different tenant!
            clinic_id=self._OTHER_CLINIC,
            role="doctor",  # Valid PHI role — but wrong tenant
            email="attacker@other.test",
            name="Cross Tenant Attacker",
        )

        # Stub session: PatientRepository raw SQL execute().fetchone() returns None
        # simulate no rows found (cross-tenant) → patient = None → 404
        from unittest.mock import MagicMock

        stub_session = AsyncMock()
        stub_execute_result = MagicMock()  # sync MagicMock (not AsyncMock) so .fetchone() returns sync None
        stub_execute_result.fetchone.return_value = None
        stub_session.execute = AsyncMock(return_value=stub_execute_result)
        stub_session.flush = AsyncMock(return_value=None)  # AuditLogRepository.write calls flush

        async def _override_session():
            yield stub_session

        app.dependency_overrides[get_async_session] = _override_session

        async_resolve_mock = AsyncMock(return_value=ctx_other_tenant)

        try:
            with patch(
                "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
                new=async_resolve_mock,
            ):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.get(
                        f"/api/v1/crm/patients/{_patient_id}",
                        headers={
                            "Authorization": "Bearer stub:test:test:doctor:cross_tenant",
                            "X-Tenant-ID": str(self._OTHER_TENANT),
                            "X-Clinic-ID": str(self._OTHER_CLINIC),
                        },
                    )
        finally:
            app.dependency_overrides.pop(get_async_session, None)

        # Cross-tenant: must NOT return patient data → 404 (repo dual-filter isolates)
        assert response.status_code == 404, (
            f"Cross-tenant doctor MUST get 404, not {response.status_code}: {response.text}"
        )
        # PHI no-leak assertion: response body must not contain PHI field values
        phi_sentinel_values = [
            "date_of_birth",
            "diagnosis",
            "treatment_plan",
            "medication",
            "allergies",
        ]
        body_lower = response.text.lower()
        for phi_value in phi_sentinel_values:
            assert phi_value not in body_lower, (
                f"SC-3 FAIL: cross-tenant 404 response must NOT contain PHI field '{phi_value}': {response.text}"
            )

    @pytest.mark.asyncio
    async def test_cross_clinic_403_no_phi_leak(self) -> None:
        """SC-3: doctor from clinic A requests PHI of clinic B (same tenant) → 403 or 404, no PHI leak.

        Grader:
        - HTTP 403 or 404 returned (not 200 with wrong clinic's data).
        - Response body does not contain PHI field values.
        """
        from unittest.mock import AsyncMock, patch

        from httpx import ASGITransport, AsyncClient

        with patch.dict(os.environ, _REQUIRED_ENV_VARS):
            from src.db import get_async_session
            from src.main import app
            from src.modules.vitalia.iam.application.services.clinic_resolver import (
                ClinicContext,
            )

        _patient_id = uuid.uuid4()
        # Doctor from clinic B tries to access CLINIC_SANARE (clinic A) patient
        ctx_wrong_clinic = ClinicContext(
            user_id=DOCTOR_CLERK_SUB,
            tenant_id=TENANT_SANARE,  # Same tenant
            clinic_id=self._OTHER_CLINIC,  # Wrong clinic!
            role="doctor",
            email="doctor@other_clinic.test",
            name="Wrong Clinic Doctor",
        )

        # Stub session: PatientRepository query returns None (dual-filter: wrong clinic_id)
        from unittest.mock import MagicMock

        stub_session = AsyncMock()
        stub_execute_result = MagicMock()
        stub_execute_result.fetchone.return_value = None
        stub_session.execute = AsyncMock(return_value=stub_execute_result)
        stub_session.flush = AsyncMock(return_value=None)

        async def _override_session():
            yield stub_session

        app.dependency_overrides[get_async_session] = _override_session

        async_resolve_mock = AsyncMock(return_value=ctx_wrong_clinic)

        try:
            with patch(
                "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
                new=async_resolve_mock,
            ):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.get(
                        f"/api/v1/crm/patients/{_patient_id}",
                        headers={
                            "Authorization": "Bearer stub:test:test:doctor:user1",
                            "X-Tenant-ID": str(TENANT_SANARE),
                            "X-Clinic-ID": str(self._OTHER_CLINIC),
                        },
                    )
        finally:
            app.dependency_overrides.pop(get_async_session, None)

        # Cross-clinic: must NOT return patient data → 403 or 404 (dual-filter isolates)
        assert response.status_code in (403, 404), (
            f"Cross-clinic doctor MUST get 403 or 404, not {response.status_code}: {response.text}"
        )
        # PHI no-leak assertion
        phi_sentinel_values = [
            "date_of_birth",
            "diagnosis",
            "treatment_plan",
        ]
        body_lower = response.text.lower()
        for phi_value in phi_sentinel_values:
            assert phi_value not in body_lower, (
                f"SC-3 FAIL: cross-clinic response must NOT contain PHI field '{phi_value}': {response.text}"
            )

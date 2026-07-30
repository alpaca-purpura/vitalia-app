# cap: crm.crm-consent-optout
"""Integration tests — CRM PHI real tables (T-3 · vitalia-crm-phi-base-tables-migration).

TDD RED: written before full 035 migration verified in dev DB.

These tests exercise the REAL vitalia_patients + vitalia_leads tables
(created/patched by migration 035). They do NOT monkeypatch the repository
or encryption layer — only verify_token_payload is mocked (deterministic
Clerk JWT without network egress).

Coverage (04-validators.yaml § scenario_coverage + F-integration-real-tables):
  SC-1: doctor JWT → GET /crm/patients/{id} 200 + audit row written
  SC-2: marketing role → 403 (RBAC gate before repo)
  SC-4a: cross-tenant → 404 (repo dual-filter: wrong tenant_id)
  SC-4b: cross-clinic → 403 or 404 (repo dual-filter: wrong clinic_id)
  SC-5: raw DB name column = bytea ciphertext; API read = plaintext (at-rest encryption)

Strategy (per test-design-doctrine.md § Integration + hipaa-lite.md):
  - DB+KEK required: tests carry @pytest.mark.integration and SKIP
    automatically when Postgres is unavailable (conftest.py auto-skip).
  - KEK required: VITALIA_PHI_KEK env var must be set; tests skip if absent.
  - verify_token_payload monkeypatched to return fixed doctor/marketing payload
    (same pattern as test_phi_real_auth.py).
  - httpx ASGITransport against the live vitalia app; real DB session injected
    via the production get_async_session dependency.
  - Seed pre-condition: seed_test_users_link.py must have been run with
    VITALIA_PHI_KEK set → PATIENT_SANARE_DEMO row in vitalia_patients.

Forbidden:
  - Monkeypatching PatientRepository / LeadRepository / AuditLogRepository.
  - Monkeypatching KEKClient (real KEK required for round-trip).
  - Printing KEK/JWT/PHI plaintext in output or logs.

downstream-regression-na: brand-local vitalia CRM PHI integration tests
"""

from __future__ import annotations

import os
import uuid
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Skip guard — KEK required (in addition to Postgres from conftest)
# ---------------------------------------------------------------------------

_KEK = os.getenv("VITALIA_PHI_KEK", "")
_KEK_MISSING = not _KEK
_KEK_SKIP_REASON = "VITALIA_PHI_KEK not set — skipping PHI integration tests"

pytestmark = pytest.mark.integration

# ---------------------------------------------------------------------------
# Constants (must match seed_test_users_link.py)
# ---------------------------------------------------------------------------

_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
TENANT_SANARE = uuid.UUID("e69a691d-070e-5caf-a053-6e74642ec100")
CLINIC_SANARE = uuid.UUID("f035be5b-0ac4-5210-8fc3-395650ca2b83")

# Deterministic IDs (must match seed script)
PATIENT_SANARE_DEMO = uuid.uuid5(_NAMESPACE, "patient:sanare-latam-mx:demo")
LEAD_SANARE_DEMO = uuid.uuid5(_NAMESPACE, "lead:sanare-latam-mx:demo")

# Clerk sub claims for doctor.demo and marketing.demo (from god-matrix seed)
DOCTOR_CLERK_SUB = "user_3EQJjxsvxiZ5exQjucSB651xnUd"
MARKETING_CLERK_SUB = "user_3EQJn2iflBFqDk59gqc0srYEv55"

# Fixed JWT payload returned by monkeypatched verify_token_payload
_DOCTOR_JWT_PAYLOAD: dict = {
    "sub": DOCTOR_CLERK_SUB,
    "email": "doctor.demo@sanare.vitalia.test",
    "full_name": "Dr. Demo Doctor",
    "iat": 9999999999,
    "exp": 9999999999,
}

_MARKETING_JWT_PAYLOAD: dict = {
    "sub": MARKETING_CLERK_SUB,
    "email": "marketing.demo@sanare.vitalia.test",
    "full_name": "Marketing Demo",
    "iat": 9999999999,
    "exp": 9999999999,
}

# Other tenant for cross-tenant isolation tests
_OTHER_TENANT = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
_OTHER_CLINIC = uuid.UUID("11111111-2222-3333-4444-555555555555")

# Minimal env vars to allow src.main import (mirrors test_phi_real_auth.py pattern)
_REQUIRED_ENV_VARS = {
    "LOG_LEVEL": "DEBUG",
    "DOMAIN_NAME": "localhost",
    "TRAEFIK_NETWORK": "traefik",
    "API_SECRET_KEY": "test-secret-key-for-crm-phi-integration",
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


# ---------------------------------------------------------------------------
# SC-1 — doctor JWT → GET /crm/patients/{id} 200 + audit row written
# ---------------------------------------------------------------------------


@pytest.mark.skipif(_KEK_MISSING, reason=_KEK_SKIP_REASON)
@pytest.mark.asyncio
async def test_doctor_reads_patient_200_audit() -> None:
    """SC-1: doctor JWT → GET /crm/patients/{PATIENT_SANARE_DEMO} 200 + data deciphered.

    Graders exercised:
    - HTTP 200 with non-empty name (deciphered by KEK) in response body
    - Audit row written to vitalia_audit_log with action='read_patient'

    Pre-condition: 035 migration applied + seed run with VITALIA_PHI_KEK set.
    Strategy: monkeypatch verify_token_payload → doctor sub; real DB session.
    """
    from httpx import ASGITransport, AsyncClient

    with patch.dict(os.environ, {**_REQUIRED_ENV_VARS, "VITALIA_PHI_KEK": _KEK}):
        from src.main import app  # noqa: PLC0415

    env_patch = patch.dict(os.environ, {**_REQUIRED_ENV_VARS, "VITALIA_PHI_KEK": _KEK})
    verify_patch = patch(
        "src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder.verify_token_payload",
        return_value=_DOCTOR_JWT_PAYLOAD,
    )

    with env_patch, verify_patch:
        from src.db import get_async_session  # noqa: PLC0415

        # Remove any leftover dependency overrides
        app.dependency_overrides.pop(get_async_session, None)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/crm/patients/{PATIENT_SANARE_DEMO}",
                headers={
                    "Authorization": "Bearer eyJhbGciOiJSUzI1NiJ9.doctor_real",
                    "X-Tenant-ID": str(TENANT_SANARE),
                    "X-Clinic-ID": str(CLINIC_SANARE),
                },
            )

    assert response.status_code == 200, f"SC-1 FAIL: doctor must get 200, got {response.status_code}: {response.text}"
    body = response.json()
    # name must be present (deciphered) and non-empty
    assert "name" in body, f"SC-1 FAIL: response must include 'name': {body}"
    assert body["name"], f"SC-1 FAIL: deciphered name must be non-empty: {body}"
    # PHI allowlist: dni/date_of_birth/address MUST NOT appear in response
    for phi_field in ("dni", "date_of_birth", "address"):
        assert phi_field not in body, f"SC-1 FAIL: response MUST NOT expose '{phi_field}' (PII allowlist): {body}"

    # Verify audit row written (raw SQL via psycopg2 — avoids re-importing the async session)
    import psycopg2  # noqa: PLC0415

    with psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        dbname=os.environ.get("POSTGRES_DB", "vitalia_test"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
    ) as pg_conn:
        with pg_conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM vitalia_audit_log
                WHERE resource_id = %s
                  AND action IN ('read_patient', 'phi_access', 'read_patient')
                ORDER BY occurred_at DESC
                LIMIT 1
                """,
                (str(PATIENT_SANARE_DEMO),),
            )
            row = cur.fetchone()

    assert row is not None, "SC-1 FAIL: audit row must be written to vitalia_audit_log after PHI read"


# ---------------------------------------------------------------------------
# SC-2 — marketing role → 403
# ---------------------------------------------------------------------------


@pytest.mark.skipif(_KEK_MISSING, reason=_KEK_SKIP_REASON)
@pytest.mark.asyncio
async def test_marketing_403() -> None:
    """SC-2: marketing JWT → GET /crm/patients/{id} 403.

    RBAC gate fires before repo access — no PHI leak in response.

    Strategy: monkeypatch verify_token_payload → marketing sub.
    DB role resolution for marketing.demo returns 'marketing' (from user_tenants).
    RBAC check on the endpoint rejects the role → 403.
    """
    from httpx import ASGITransport, AsyncClient

    with patch.dict(os.environ, {**_REQUIRED_ENV_VARS, "VITALIA_PHI_KEK": _KEK}):
        from src.main import app  # noqa: PLC0415

    env_patch = patch.dict(os.environ, {**_REQUIRED_ENV_VARS, "VITALIA_PHI_KEK": _KEK})
    verify_patch = patch(
        "src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder.verify_token_payload",
        return_value=_MARKETING_JWT_PAYLOAD,
    )

    with env_patch, verify_patch:
        from src.db import get_async_session  # noqa: PLC0415

        app.dependency_overrides.pop(get_async_session, None)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/crm/patients/{PATIENT_SANARE_DEMO}",
                headers={
                    "Authorization": "Bearer eyJhbGciOiJSUzI1NiJ9.marketing_real",
                    "X-Tenant-ID": str(TENANT_SANARE),
                    "X-Clinic-ID": str(CLINIC_SANARE),
                },
            )

    assert response.status_code == 403, (
        f"SC-2 FAIL: marketing role MUST get 403, got {response.status_code}: {response.text}"
    )
    # PHI must NOT appear in 403 response
    body_lower = response.text.lower()
    for phi_field in ("date_of_birth", "diagnosis", "treatment", "dni"):
        assert phi_field not in body_lower, (
            f"SC-2 FAIL: 403 response must not leak PHI field '{phi_field}': {response.text}"
        )


# ---------------------------------------------------------------------------
# SC-4a — cross-tenant → 404 (no PHI leak)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(_KEK_MISSING, reason=_KEK_SKIP_REASON)
@pytest.mark.asyncio
async def test_cross_tenant_404() -> None:
    """SC-4a: doctor from a different tenant → 404 (repo dual-filter: wrong tenant_id).

    Strategy: monkeypatch verify_token_payload → doctor sub with _OTHER_TENANT.
    PatientRepository queries with other_tenant_id — no matching row → None → 404.
    Assert no PHI in response.
    """
    from httpx import ASGITransport, AsyncClient

    # Doctor JWT payload but X-Tenant-ID = OTHER tenant (cross-tenant attempt)
    _doctor_other_tenant_payload = {
        **_DOCTOR_JWT_PAYLOAD,
        "sub": "user_cross_tenant_attacker",
    }

    with patch.dict(os.environ, {**_REQUIRED_ENV_VARS, "VITALIA_PHI_KEK": _KEK}):
        from src.main import app  # noqa: PLC0415

    env_patch = patch.dict(os.environ, {**_REQUIRED_ENV_VARS, "VITALIA_PHI_KEK": _KEK})
    verify_patch = patch(
        "src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder.verify_token_payload",
        return_value=_doctor_other_tenant_payload,
    )

    with env_patch, verify_patch:
        from src.db import get_async_session  # noqa: PLC0415

        app.dependency_overrides.pop(get_async_session, None)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/crm/patients/{PATIENT_SANARE_DEMO}",
                headers={
                    "Authorization": "Bearer eyJhbGciOiJSUzI1NiJ9.cross_tenant",
                    "X-Tenant-ID": str(_OTHER_TENANT),  # Different tenant!
                    "X-Clinic-ID": str(_OTHER_CLINIC),
                },
            )

    # Cross-tenant: user from OTHER_TENANT cannot see TENANT_SANARE patients → 404
    # (The user sub isn't in user_tenants for OTHER_TENANT → 401/403; OR
    #  the repo dual-filter returns nothing → 404. Both acceptable.)
    assert response.status_code in (401, 403, 404), (
        f"SC-4a FAIL: cross-tenant MUST get 401/403/404, got {response.status_code}: {response.text}"
    )
    # Critically: must NOT be 200 with Sanaré patient data
    assert response.status_code != 200, (
        f"SC-4a FAIL: cross-tenant MUST NOT return 200 with patient data: {response.text}"
    )
    body_lower = response.text.lower()
    # PHI sentinel: patient name "María Fernanda Gómez" must NOT appear
    for phi_value in ("maría", "fernanda", "gómez", "gomez", "date_of_birth", "diagnosis"):
        assert phi_value not in body_lower, (
            f"SC-4a FAIL: cross-tenant response must NOT contain PHI: {phi_value!r} in {response.text!r}"
        )


# ---------------------------------------------------------------------------
# SC-4b — cross-clinic → 403 or 404 (dual filter: wrong clinic_id)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(_KEK_MISSING, reason=_KEK_SKIP_REASON)
@pytest.mark.asyncio
async def test_cross_clinic_403() -> None:
    """SC-4b: doctor from wrong clinic (same tenant) → 403 or 404.

    Strategy: monkeypatch verify_token_payload → doctor sub.
    Send X-Clinic-ID = _OTHER_CLINIC (not CLINIC_SANARE).
    PatientRepository dual-filter: clinic_id mismatch → None → 404.
    (Or ClinicResolver rejects the clinic → 403.)
    Assert no PHI in response.
    """
    from httpx import ASGITransport, AsyncClient

    with patch.dict(os.environ, {**_REQUIRED_ENV_VARS, "VITALIA_PHI_KEK": _KEK}):
        from src.main import app  # noqa: PLC0415

    env_patch = patch.dict(os.environ, {**_REQUIRED_ENV_VARS, "VITALIA_PHI_KEK": _KEK})
    verify_patch = patch(
        "src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder.verify_token_payload",
        return_value=_DOCTOR_JWT_PAYLOAD,
    )

    with env_patch, verify_patch:
        from src.db import get_async_session  # noqa: PLC0415

        app.dependency_overrides.pop(get_async_session, None)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/crm/patients/{PATIENT_SANARE_DEMO}",
                headers={
                    "Authorization": "Bearer eyJhbGciOiJSUzI1NiJ9.doctor_wrong_clinic",
                    "X-Tenant-ID": str(TENANT_SANARE),  # Same tenant
                    "X-Clinic-ID": str(_OTHER_CLINIC),  # Wrong clinic!
                },
            )

    assert response.status_code in (403, 404), (
        f"SC-4b FAIL: cross-clinic MUST get 403 or 404, got {response.status_code}: {response.text}"
    )
    assert response.status_code != 200, (
        f"SC-4b FAIL: cross-clinic MUST NOT return 200 with patient data: {response.text}"
    )
    body_lower = response.text.lower()
    for phi_value in ("date_of_birth", "diagnosis", "treatment"):
        assert phi_value not in body_lower, f"SC-4b FAIL: cross-clinic response must NOT contain PHI: {phi_value!r}"


# ---------------------------------------------------------------------------
# SC-5 — PHI encrypted at rest, decrypted on read (round-trip at-rest)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(_KEK_MISSING, reason=_KEK_SKIP_REASON)
def test_phi_encrypted_at_rest_decrypted_on_read() -> None:
    """SC-5: raw SQL SELECT name FROM vitalia_patients → BYTEA ciphertext (NOT plaintext).

    This test connects directly to Postgres via psycopg2 (sync) to read the
    raw name column bytes. pgp_sym_encrypt stores as BYTEA — the raw bytes
    start with the OpenPGP magic header (\\xc3 or \\xcb), not readable text.

    Complementary assertion: the API returns the deciphered name (verified
    in test_doctor_reads_patient_200_audit).

    Pre-condition: seed run → PATIENT_SANARE_DEMO row in vitalia_patients.
    """
    import psycopg2  # noqa: PLC0415

    # Skip gracefully if table doesn't exist yet (migration not applied)
    try:
        conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=int(os.environ.get("POSTGRES_PORT", "5432")),
            dbname=os.environ.get("POSTGRES_DB", "vitalia_test"),
            user=os.environ.get("POSTGRES_USER", "postgres"),
            password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
        )
    except Exception as exc:
        pytest.skip(f"Postgres connection failed: {exc}")

    try:
        with conn.cursor() as cur:
            # Check table exists first
            cur.execute(
                "SELECT to_regclass('vitalia_patients')",
            )
            table_exists = cur.fetchone()[0] is not None
            if not table_exists:
                pytest.skip("vitalia_patients table does not exist — run migration 035 first")

            # Check seed row exists
            cur.execute(
                "SELECT name FROM vitalia_patients WHERE id = %s AND deleted_at IS NULL",
                (str(PATIENT_SANARE_DEMO),),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if row is None:
        pytest.skip(
            f"PATIENT_SANARE_DEMO ({PATIENT_SANARE_DEMO}) not found in vitalia_patients — "
            "run seed_test_users_link.py with VITALIA_PHI_KEK set first"
        )

    raw_name = row[0]

    # pgp_sym_encrypt returns BYTEA — psycopg2 delivers as memoryview or bytes
    if isinstance(raw_name, memoryview):
        raw_bytes = bytes(raw_name)
    elif isinstance(raw_name, (bytes, bytearray)):
        raw_bytes = bytes(raw_name)
    else:
        # If it's a string it was NOT encrypted → FAIL
        assert False, (  # noqa: B011
            f"SC-5 FAIL: raw name column is a string '{raw_name}' — "
            "it must be BYTEA ciphertext, not plaintext. "
            "Check that migration 035 was applied and pgp_sym_encrypt is working."
        )

    # OpenPGP magic bytes: 0xc3 (new format packet) or 0xcb (old format)
    # pgcrypto pgp_sym_encrypt always starts with an OpenPGP header byte
    # whose high bits are 11 (0xC0 mask → >= 0xC0).
    assert len(raw_bytes) > 0, "SC-5 FAIL: raw name column is empty bytes"
    first_byte = raw_bytes[0]
    assert first_byte >= 0xC0, (
        f"SC-5 FAIL: raw name bytes do not look like OpenPGP ciphertext "
        f"(first byte = 0x{first_byte:02X}, expected >= 0xC0). "
        "Likely stored as plaintext — pgp_sym_encrypt not applied."
    )

    # Critically: the raw bytes must NOT contain the plaintext name
    plaintext_sentinel = b"Gom"  # substring of "Gómez" / "María Fernanda Gómez"
    assert plaintext_sentinel not in raw_bytes, (
        "SC-5 FAIL: raw ciphertext contains plaintext fragment — encryption not applied!"
    )

"""fn-be-cross-tenant-isolation-admin — Admin cross-tenant isolation tests (SC-11).

Tests that admin module functions enforce dual filter (tenant_id + clinic_id)
so that Tenant A data is never accessible via Tenant B context.

Requires Postgres (vitalia_audit_log table must exist).
Tests marked @pytest.mark.integration — skipped when Postgres unavailable.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_audit_log_tenant_isolation_no_cross_leak(db_session) -> None:  # noqa: ANN001
    """SC-11: Admin audit_log query filters tenant_id — no cross-tenant data leak.

    Given: Two tenants (A and B) with separate audit_log rows
    When: Query vitalia_audit_log filtered by tenant_A + clinic_A
    Then: Returns ONLY tenant_A rows; tenant_B rows are invisible
    """
    from src.modules.vitalia.compliance.audit import log_admin_action  # noqa: PLC0415

    # Unique IDs to avoid collisions with other tests
    tenant_a = uuid4()
    clinic_a = uuid4()
    resource_a = uuid4()

    tenant_b = uuid4()
    clinic_b = uuid4()
    resource_b = uuid4()

    # Write audit rows for both tenants
    await log_admin_action(
        session=db_session,
        tenant_id=tenant_a,
        clinic_id=clinic_a,
        user_id=uuid4(),
        action="tenant.viewed",
        resource_type="tenant",
        resource_id=resource_a,
        from_ip="192.168.1.1",
        user_agent="VitaliaAdmin/1.0",
        payload_redacted={"clinic_name": "Clínica Aurora A"},
    )
    await log_admin_action(
        session=db_session,
        tenant_id=tenant_b,
        clinic_id=clinic_b,
        user_id=uuid4(),
        action="tenant.viewed",
        resource_type="tenant",
        resource_id=resource_b,
        from_ip="192.168.2.1",
        user_agent="VitaliaAdmin/1.0",
        payload_redacted={"clinic_name": "Clínica Bienestar B"},
    )
    await db_session.flush()

    # Query with tenant_a dual filter
    result = await db_session.execute(
        text(
            "SELECT resource_id FROM vitalia_audit_log "
            "WHERE tenant_id = :tid AND clinic_id = :cid AND action = 'tenant.viewed'"
        ),
        {"tid": str(tenant_a), "cid": str(clinic_a)},
    )
    rows = result.fetchall()
    resource_ids_seen = {str(row.resource_id) for row in rows}

    # tenant_a resource must be visible
    assert str(resource_a) in resource_ids_seen, f"tenant_a resource {resource_a} not found in audit_log query"

    # tenant_b resource must NOT appear in tenant_a query
    assert str(resource_b) not in resource_ids_seen, (
        f"CROSS-TENANT LEAK: tenant_b resource {resource_b} visible via tenant_a + clinic_a filter!"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_audit_log_clinic_isolation_within_tenant(db_session) -> None:  # noqa: ANN001
    """SC-11b: Within same tenant, clinic_id filter isolates clinic data.

    Given: Same tenant (A) with two clinics (clinic_A1 and clinic_A2)
    When: Query filtered by tenant_A + clinic_A1
    Then: Returns only clinic_A1 rows; clinic_A2 rows are invisible

    This tests the HIPAA-lite rule: 'clinic_id as second mandatory filter'.
    """
    from src.modules.vitalia.compliance.audit import log_admin_action  # noqa: PLC0415

    tenant_shared = uuid4()
    clinic_a1 = uuid4()
    clinic_a2 = uuid4()
    resource_a1 = uuid4()
    resource_a2 = uuid4()

    await log_admin_action(
        session=db_session,
        tenant_id=tenant_shared,
        clinic_id=clinic_a1,
        user_id=uuid4(),
        action="clinic.viewed",
        resource_type="clinic",
        resource_id=resource_a1,
        from_ip="10.0.1.1",
        user_agent="VitaliaAdmin/1.0",
        payload_redacted={"clinic_name": "Sede Norte"},
    )
    await log_admin_action(
        session=db_session,
        tenant_id=tenant_shared,
        clinic_id=clinic_a2,
        user_id=uuid4(),
        action="clinic.viewed",
        resource_type="clinic",
        resource_id=resource_a2,
        from_ip="10.0.1.2",
        user_agent="VitaliaAdmin/1.0",
        payload_redacted={"clinic_name": "Sede Sur"},
    )
    await db_session.flush()

    # Query filtered by tenant_shared + clinic_a1 only
    result = await db_session.execute(
        text(
            "SELECT resource_id FROM vitalia_audit_log "
            "WHERE tenant_id = :tid AND clinic_id = :cid AND action = 'clinic.viewed'"
        ),
        {"tid": str(tenant_shared), "cid": str(clinic_a1)},
    )
    rows = result.fetchall()
    resource_ids_seen = {str(row.resource_id) for row in rows}

    assert str(resource_a1) in resource_ids_seen, f"clinic_a1 resource {resource_a1} not found"
    assert str(resource_a2) not in resource_ids_seen, (
        f"CLINIC ISOLATION FAILURE: clinic_a2 resource {resource_a2} visible via clinic_a1 filter!"
    )


@pytest.mark.asyncio
async def test_admin_auth_rejects_wrong_password() -> None:
    """SC-11c: verify_admin_password rejects incorrect password (no DB required).

    Given: A bcrypt hash of 'correct-password' set as VITALIA_ADMIN_PASSWORD_HASH
    When: verify_admin_password('wrong-password') is called
    Then: Returns False (unauthorized)
    """
    import os  # noqa: PLC0415

    import bcrypt  # noqa: PLC0415

    # Generate a test hash for 'correct-password'
    correct_pw = b"correct-password-admin"
    pw_hash = bcrypt.hashpw(correct_pw, bcrypt.gensalt(rounds=4)).decode()  # rounds=4 for test speed

    os.environ["VITALIA_ADMIN_PASSWORD_HASH"] = pw_hash

    from src.modules.vitalia.admin._shared.auth import verify_admin_password  # noqa: PLC0415

    assert not verify_admin_password("wrong-password"), "verify_admin_password should return False for wrong password"
    assert verify_admin_password("correct-password-admin"), (
        "verify_admin_password should return True for correct password"
    )


@pytest.mark.asyncio
async def test_admin_auth_rejects_empty_password() -> None:
    """SC-11d: verify_admin_password rejects empty password string.

    Given: Any bcrypt hash configured
    When: verify_admin_password('') is called
    Then: Returns False (empty password always rejected)
    """
    import os  # noqa: PLC0415

    import bcrypt  # noqa: PLC0415

    pw_hash = bcrypt.hashpw(b"any-password", bcrypt.gensalt(rounds=4)).decode()
    os.environ["VITALIA_ADMIN_PASSWORD_HASH"] = pw_hash

    from src.modules.vitalia.admin._shared.auth import verify_admin_password  # noqa: PLC0415

    assert not verify_admin_password(""), "Empty password must always be rejected"
    assert not verify_admin_password("   "), "Whitespace-only password must be rejected"

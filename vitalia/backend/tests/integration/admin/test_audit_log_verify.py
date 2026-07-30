"""fn-be-hipaa-audit-log-verify — HIPAA audit log compliance tests (SC-08, SC-13).

Tests:
    SC-08: Admin creates tenant → audit_log row written
    SC-13: audit_log row payload_redacted contains NO PHI fields

Requires Postgres (vitalia_audit_log table must exist via alembic upgrade head).
Tests are skipped automatically when POSTGRES_DSN is unavailable.

All tests marked @pytest.mark.integration.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_log_admin_action_writes_audit_row(db_session) -> None:  # noqa: ANN001
    """SC-08: log_admin_action() writes exactly 1 row to vitalia_audit_log.

    Given: A valid admin action (tenant.created)
    When: log_admin_action() called with identity payload (no PHI)
    Then: vitalia_audit_log has exactly 1 row matching the action/resource_id
    """
    from src.modules.vitalia.compliance.audit import log_admin_action  # noqa: PLC0415

    test_tenant_id = uuid4()
    test_clinic_id = uuid4()
    test_resource_id = uuid4()
    test_user_id = uuid4()

    # Action: create a tenant (identity data only, no PHI)
    await log_admin_action(
        session=db_session,
        tenant_id=test_tenant_id,
        clinic_id=test_clinic_id,
        user_id=test_user_id,
        action="tenant.created",
        resource_type="tenant",
        resource_id=test_resource_id,
        from_ip="127.0.0.1",
        user_agent="VitaliaAdmin/1.0",
        payload_redacted={"clinic_name": "Clínica Aurora Test", "country": "AR"},
    )
    await db_session.flush()

    # Verify row exists
    result = await db_session.execute(
        text(
            "SELECT id, tenant_id, clinic_id, action, resource_type, resource_id "
            "FROM vitalia_audit_log "
            "WHERE tenant_id = :tid AND resource_id = :rid"
        ),
        {"tid": str(test_tenant_id), "rid": str(test_resource_id)},
    )
    rows = result.fetchall()

    assert len(rows) == 1, f"Expected 1 audit row, got {len(rows)}"
    row = rows[0]
    assert str(row.action) == "tenant.created"
    assert str(row.resource_type) == "tenant"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_audit_log_payload_redacted_no_phi(db_session) -> None:  # noqa: ANN001
    """SC-13: payload_redacted in audit_log must NOT contain PHI fields.

    Given: log_admin_action() called with PHI-contaminated payload
    When: sanitize_phi_payload() is applied internally
    Then: payload_redacted stored in DB contains no PHI fields
         (diagnosis, treatment_plan, medication, patient.name, etc.)

    This test verifies the HIPAA-lite invariant: admin action logs
    may contain identity data (clinic_name, email) but NEVER clinical PHI.
    """
    from src.modules.vitalia.compliance.audit import log_admin_action  # noqa: PLC0415
    from src.modules.vitalia.compliance.domain.phi_fields import PHI_FIELDS_TOP_LEVEL  # noqa: PLC0415

    test_tenant_id = uuid4()
    test_clinic_id = uuid4()
    test_resource_id = uuid4()

    # Attempt to log with PHI fields included — should be sanitized
    contaminated_payload: dict = {
        "clinic_name": "Clínica Test PHI",
        "email": "admin@clinic.com",
        # PHI fields — these MUST be stripped
        "diagnosis": "Hipotiroidismo",
        "treatment_plan": "Levotiroxina 50mcg/día",
        "medication": "Levotiroxina",
        "patient": {
            "name": "Juan Pérez",
            "dni": "12345678",
        },
    }

    await log_admin_action(
        session=db_session,
        tenant_id=test_tenant_id,
        clinic_id=test_clinic_id,
        user_id=uuid4(),
        action="user.created",
        resource_type="user_profile",
        resource_id=test_resource_id,
        from_ip="127.0.0.1",
        user_agent="VitaliaAdmin/1.0",
        payload_redacted=contaminated_payload,
    )
    await db_session.flush()

    # Retrieve the raw payload_redacted from DB
    result = await db_session.execute(
        text("SELECT payload_redacted FROM vitalia_audit_log WHERE tenant_id = :tid AND resource_id = :rid"),
        {"tid": str(test_tenant_id), "rid": str(test_resource_id)},
    )
    row = result.fetchone()
    assert row is not None, "Audit row was not written"

    # payload_redacted is BYTEA — decode as JSON (log_admin_action stores JSON-encoded bytes)
    import json  # noqa: PLC0415

    raw_payload_bytes = row.payload_redacted
    if isinstance(raw_payload_bytes, (bytes, memoryview)):
        stored_payload: dict = json.loads(bytes(raw_payload_bytes).decode("utf-8"))
    else:
        stored_payload = json.loads(str(raw_payload_bytes))

    # Verify: no top-level PHI fields present
    for phi_field in PHI_FIELDS_TOP_LEVEL:
        assert phi_field not in stored_payload, (
            f"PHI field '{phi_field}' found in audit_log payload_redacted! "
            f"HIPAA-lite violation. stored_payload keys: {list(stored_payload.keys())}"
        )

    # Verify: 'patient' subkey is also redacted (or the PHI subfields within it)
    if "patient" in stored_payload:
        patient_data = stored_payload["patient"]
        for phi_patient_field in ("name", "dni", "cuit", "date_of_birth", "phone"):
            assert phi_patient_field not in patient_data, (
                f"PHI patient.{phi_patient_field} found in audit_log! patient data: {patient_data}"
            )

    # Verify: identity-ok fields are preserved (clinic_name, email)
    assert "clinic_name" in stored_payload, "clinic_name (identity-ok field) should NOT be stripped from audit log"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_audit_log_dual_filter_tenant_clinic(db_session) -> None:  # noqa: ANN001
    """SC-13b: Audit log rows are queryable by both tenant_id AND clinic_id (dual filter).

    Given: Two audit log entries for different tenants
    When: Query filters by tenant_id + clinic_id
    Then: Only the matching tenant's rows are returned
    """
    from src.modules.vitalia.compliance.audit import log_admin_action  # noqa: PLC0415

    tenant_x = uuid4()
    clinic_x = uuid4()
    tenant_y = uuid4()
    clinic_y = uuid4()
    resource_x = uuid4()
    resource_y = uuid4()

    # Create audit row for tenant X
    await log_admin_action(
        session=db_session,
        tenant_id=tenant_x,
        clinic_id=clinic_x,
        user_id=uuid4(),
        action="tenant.created",
        resource_type="tenant",
        resource_id=resource_x,
        from_ip="10.0.0.1",
        user_agent="VitaliaAdmin/1.0",
        payload_redacted={"clinic_name": "Clínica X"},
    )

    # Create audit row for tenant Y
    await log_admin_action(
        session=db_session,
        tenant_id=tenant_y,
        clinic_id=clinic_y,
        user_id=uuid4(),
        action="tenant.created",
        resource_type="tenant",
        resource_id=resource_y,
        from_ip="10.0.0.2",
        user_agent="VitaliaAdmin/1.0",
        payload_redacted={"clinic_name": "Clínica Y"},
    )
    await db_session.flush()

    # Query with dual filter: tenant_x + clinic_x
    result = await db_session.execute(
        text("SELECT id FROM vitalia_audit_log WHERE tenant_id = :tid AND clinic_id = :cid"),
        {"tid": str(tenant_x), "cid": str(clinic_x)},
    )
    rows_x = result.fetchall()
    assert len(rows_x) >= 1, "Expected at least 1 row for tenant_x + clinic_x"

    # Confirm tenant_y rows are NOT returned by tenant_x + clinic_x filter
    result_y_check = await db_session.execute(
        text("SELECT id FROM vitalia_audit_log WHERE tenant_id = :tid AND clinic_id = :cid AND resource_id = :rid"),
        {"tid": str(tenant_x), "cid": str(clinic_x), "rid": str(resource_y)},
    )
    rows_y_via_x_filter = result_y_check.fetchall()
    assert len(rows_y_via_x_filter) == 0, (
        "Cross-tenant audit_log leak: tenant_y resource found via tenant_x + clinic_x filter!"
    )

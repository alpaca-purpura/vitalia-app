"""Unit tests for write_audit_log_sync — HIPAA-lite SSoT audit helper.

TDD: RED tests defined per vitalia-adopt-luana-core-iam story.

Tests verify:
- Sync write to vitalia_audit_log table (INSERT)
- Payload sanitized via sanitize_phi_payload (vitalia brand-local wrapper)
- No PHI fields in payload_redacted column
- Caller is responsible for db.commit()

Note: After T-1 (arreglar-guardado-voz-y-tono), sanitize_phi_payload is the
call site (not luana_core_observability.sanitize_payload directly). The patch
target is the source module of sanitize_phi_payload so ALL call sites resolve
to the mock through the lazy import.

Patch target (T-1 + T-1.bis migration):
  src.modules.vitalia.compliance.application.compliance_service_adapter.sanitize_phi_payload

downstream-regression-na: brand-local audit log sync tests
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
from uuid import uuid4

# Patch target for sanitize_phi_payload — vitalia brand-local wrapper.
# T-1 migrated from luana_core_observability.sanitize_payload (removed compliance_level
# kwarg) to sanitize_phi_payload (simpler signature: payload -> dict).
_SANITIZE_PATCH = "src.modules.vitalia.compliance.application.compliance_service_adapter.sanitize_phi_payload"


class TestWriteAuditLogSync:
    """write_audit_log_sync — SYNC write to vitalia_audit_log."""

    def test_write_calls_db_execute(self) -> None:
        """Calls db.execute() with INSERT statement."""
        from src.modules.vitalia.audit.audit_writer import write_audit_log_sync

        mock_db = MagicMock()
        tenant_id = str(uuid4())
        clinic_id = str(uuid4())
        user_id = str(uuid4())
        resource_id = str(uuid4())

        with patch(_SANITIZE_PATCH, return_value={"email": "test@example.com", "role": "doctor"}):
            write_audit_log_sync(
                mock_db,
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                user_id=user_id,
                action="user.created",
                resource_type="user",
                resource_id=resource_id,
                payload={"email": "test@example.com", "role": "doctor"},
            )

        mock_db.execute.assert_called_once()

    def test_write_does_not_commit(self) -> None:
        """write_audit_log_sync does NOT call db.commit() — caller's responsibility."""
        from src.modules.vitalia.audit.audit_writer import write_audit_log_sync

        mock_db = MagicMock()

        with patch(_SANITIZE_PATCH, return_value={}):
            write_audit_log_sync(
                mock_db,
                tenant_id=str(uuid4()),
                clinic_id=str(uuid4()),
                user_id=str(uuid4()),
                action="clinic.created",
                resource_type="clinic",
                resource_id=str(uuid4()),
            )

        mock_db.commit.assert_not_called()

    def test_write_calls_sanitize_payload(self) -> None:
        """Payload is always sanitized via sanitize_phi_payload (vitalia wrapper).

        T-1 migration: call site changed from
          sanitize_payload(payload, compliance_level="hipaa_lite")
        to
          sanitize_phi_payload(payload)   ← no compliance_level kwarg
        """
        from src.modules.vitalia.audit.audit_writer import write_audit_log_sync

        mock_db = MagicMock()
        raw_payload = {"name": "Aurora Dental", "slug": "aurora-dental"}

        with patch(_SANITIZE_PATCH, return_value=raw_payload) as mock_sanitize:
            write_audit_log_sync(
                mock_db,
                tenant_id=str(uuid4()),
                clinic_id=str(uuid4()),
                user_id=str(uuid4()),
                action="clinic.created",
                resource_type="clinic",
                resource_id=str(uuid4()),
                payload=raw_payload,
            )

        # T-1 migration: sanitize_phi_payload takes only the payload dict (no kwarg).
        mock_sanitize.assert_called_once_with(raw_payload)

    def test_write_uses_empty_dict_when_payload_none(self) -> None:
        """When payload=None, sanitize_payload is called with empty dict."""
        from src.modules.vitalia.audit.audit_writer import write_audit_log_sync

        mock_db = MagicMock()

        with patch(_SANITIZE_PATCH, return_value={}) as mock_sanitize:
            write_audit_log_sync(
                mock_db,
                tenant_id=str(uuid4()),
                clinic_id=str(uuid4()),
                user_id=str(uuid4()),
                action="user.deactivated",
                resource_type="user",
                resource_id=str(uuid4()),
                payload=None,
            )

        # T-1 migration: sanitize_phi_payload takes only the payload dict (no compliance_level kwarg).
        mock_sanitize.assert_called_once_with({})

    def test_write_encodes_payload_as_bytes(self) -> None:
        """payload_redacted passed to INSERT must be bytes (JSON-encoded)."""
        from src.modules.vitalia.audit.audit_writer import write_audit_log_sync

        mock_db = MagicMock()
        safe_payload = {"email": "doc@clinic.com", "role": "doctor"}

        with patch(_SANITIZE_PATCH, return_value=safe_payload):
            write_audit_log_sync(
                mock_db,
                tenant_id=str(uuid4()),
                clinic_id=str(uuid4()),
                user_id=str(uuid4()),
                action="user.created",
                resource_type="user",
                resource_id=str(uuid4()),
                payload=safe_payload,
            )

        # Extract the params passed to db.execute
        call_args = mock_db.execute.call_args
        assert call_args is not None
        params = call_args[0][1]  # second positional arg is params dict
        payload_bytes = params["payload"]
        assert isinstance(payload_bytes, bytes)
        decoded = json.loads(payload_bytes.decode("utf-8"))
        assert decoded == safe_payload

    def test_write_default_user_agent(self) -> None:
        """Default user_agent is 'VitaliaAdmin/1.0'."""
        from src.modules.vitalia.audit.audit_writer import write_audit_log_sync

        mock_db = MagicMock()

        with patch(_SANITIZE_PATCH, return_value={}):
            write_audit_log_sync(
                mock_db,
                tenant_id=str(uuid4()),
                clinic_id=str(uuid4()),
                user_id=str(uuid4()),
                action="tenant.created",
                resource_type="tenant",
                resource_id=str(uuid4()),
            )

        call_args = mock_db.execute.call_args
        params = call_args[0][1]
        assert params["user_agent"] == "VitaliaAdmin/1.0"


class TestWriteAuditLogSyncNoPhi:
    """PHI fields must never appear in audit payload — verified by sanitize_payload call."""

    def test_phi_fields_are_sanitized_out(self) -> None:
        """Payload with PHI fields gets sanitized; PHI not persisted."""
        from src.modules.vitalia.audit.audit_writer import write_audit_log_sync

        mock_db = MagicMock()
        # Simulate PHI accidentally included — sanitize_payload removes them
        raw_payload = {
            "email": "doc@clinic.com",
            "diagnosis": "PHI_FIELD_MUST_BE_REMOVED",
            "treatment_plan": "PHI_MUST_NOT_BE_LOGGED",
        }
        safe_payload = {"email": "doc@clinic.com"}  # diagnosis/treatment removed

        with patch(_SANITIZE_PATCH, return_value=safe_payload):
            write_audit_log_sync(
                mock_db,
                tenant_id=str(uuid4()),
                clinic_id=str(uuid4()),
                user_id=str(uuid4()),
                action="appointment.created",
                resource_type="appointment",
                resource_id=str(uuid4()),
                payload=raw_payload,
            )

        call_args = mock_db.execute.call_args
        params = call_args[0][1]
        persisted = json.loads(params["payload"].decode("utf-8"))

        assert "diagnosis" not in persisted
        assert "treatment_plan" not in persisted
        assert persisted["email"] == "doc@clinic.com"

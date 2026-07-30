"""Arch fitness: AuditLogRepository.write() MUST be an async method (sync-callable).

HIPAA-lite rule: audit log write is SYNCHRONOUS — write completes before response.
NO fire-forget, NO background task scheduling.

T-infra-3 — vitalia audit log sync write enforcement gate.
"""

from __future__ import annotations

import ast
from pathlib import Path

AUDIT_LOG_REPO_PATH = (
    Path(__file__).resolve().parents[4]
    / "vitalia"
    / "backend"
    / "src"
    / "modules"
    / "vitalia"
    / "_shared"
    / "repositories"
    / "audit_log_repository.py"
)


class TestAuditLogSyncWriteArchFitness:
    """AuditLogRepository.write must be sync-callable (awaitable, not fire-and-forget)."""

    def test_audit_log_repository_file_exists(self) -> None:
        """audit_log_repository.py must exist."""
        assert AUDIT_LOG_REPO_PATH.exists(), (
            "vitalia/backend/src/modules/vitalia/_shared/repositories/audit_log_repository.py must exist per T-infra-3"
        )

    def test_audit_log_repository_write_is_async(self) -> None:
        """AuditLogRepository.write must be declared as async def (not def)."""
        if not AUDIT_LOG_REPO_PATH.exists():
            return

        source = AUDIT_LOG_REPO_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(AUDIT_LOG_REPO_PATH))

        write_is_async: bool = False
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef,)):
                for item in node.body:
                    if isinstance(item, ast.AsyncFunctionDef) and item.name == "write":
                        write_is_async = True
                        break
                    if isinstance(item, ast.FunctionDef) and item.name == "write":
                        # sync def is a violation
                        raise AssertionError(
                            "AuditLogRepository.write must be 'async def write' — "
                            "found 'def write' (sync). HIPAA-lite requires awaitable write "
                            "that completes before response is returned, but the caller must "
                            "await it explicitly (not schedule as background task)."
                        )

        assert write_is_async, (
            "AuditLogRepository.write must be declared as 'async def write' in audit_log_repository.py"
        )

    def test_audit_log_repo_no_background_task_scheduling(self) -> None:
        """audit_log_repository.py MUST NOT use BackgroundTask or asyncio.create_task for write.

        Fire-and-forget audit writes violate HIPAA-lite: write MUST complete
        before the response is returned to the client.
        """
        if not AUDIT_LOG_REPO_PATH.exists():
            return

        source = AUDIT_LOG_REPO_PATH.read_text(encoding="utf-8")

        # Any of these patterns indicate async fire-forget (PROHIBITED)
        forbidden_patterns = [
            "BackgroundTasks",
            "background_tasks.add_task",
            "asyncio.create_task",
            "asyncio.ensure_future",
            "loop.run_in_executor",
        ]
        violations = [pattern for pattern in forbidden_patterns if pattern in source]

        assert violations == [], (
            "audit_log_repository.py MUST NOT use background task scheduling for audit writes. "
            "Found forbidden patterns: " + str(violations) + ". HIPAA-lite mandates sync write (await) before response."
        )

    def test_audit_log_repo_has_session_add_or_execute(self) -> None:
        """audit_log_repository.py MUST use session.add or session.execute for persistence."""
        if not AUDIT_LOG_REPO_PATH.exists():
            return

        source = AUDIT_LOG_REPO_PATH.read_text(encoding="utf-8")

        has_add = "session.add" in source or ".add(" in source
        has_execute = "session.execute" in source or ".execute(" in source
        has_flush = "session.flush" in source or ".flush(" in source

        assert has_add or has_execute or has_flush, (
            "audit_log_repository.py must use session.add(), session.execute(), "
            "or session.flush() for persistence — audit writes must be synchronous "
            "DB operations, not event-queue dispatches."
        )

    def test_audit_log_entry_has_occurred_at_field(self) -> None:
        """AuditLogEntry must include occurred_at timestamp field."""
        if not AUDIT_LOG_REPO_PATH.exists():
            return

        source = AUDIT_LOG_REPO_PATH.read_text(encoding="utf-8")
        assert "occurred_at" in source, (
            "AuditLogEntry must include occurred_at field (timestamp of PHI access per hipaa-lite.md § Audit log)"
        )

    def test_audit_log_entry_has_payload_redacted_field(self) -> None:
        """AuditLogEntry must include payload_redacted field for compliance."""
        if not AUDIT_LOG_REPO_PATH.exists():
            return

        source = AUDIT_LOG_REPO_PATH.read_text(encoding="utf-8")
        assert "payload_redacted" in source, (
            "AuditLogEntry must include payload_redacted field (sanitized payload per hipaa-lite.md § Audit log table)"
        )

    def test_audit_log_entry_has_clinic_id_field(self) -> None:
        """AuditLogEntry must include clinic_id (second dual-filter key for vitalia)."""
        if not AUDIT_LOG_REPO_PATH.exists():
            return

        source = AUDIT_LOG_REPO_PATH.read_text(encoding="utf-8")
        assert "clinic_id" in source, (
            "AuditLogEntry must include clinic_id — vitalia audit_log table has clinic_id column per 03-arch-be.md"
        )

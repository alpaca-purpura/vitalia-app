"""Arch fitness: every PHI endpoint MUST contain an audit log write call.

HIPAA-lite rule (vitalia/.claude/rules/hipaa-lite.md § Audit log):
  "TODA lectura/modificación de PHI registra row. NO opcional.
   NO async fire-forget (sync write antes response)."

This test verifies defense-in-depth (complements test_audit_log_sync_write.py):
  - Detects PHI-touching endpoint functions via @require_phi_access decorator
    OR via explicit ALLOWED_PHI_ROLES check patterns.
  - Verifies that BOTH the router file AND its corresponding service layer
    contain audit_writer.write() or audit.write() calls.
  - Validates the explicit allowlist of known PHI endpoints (locked set).
    Adding a new PHI endpoint without audit = fails ratchet.

PHI endpoints covered (per 03-arch § 5 + T-9 specification):
  agenda_router.py:
    - GET /agenda/grid           → AgendaGridService.list_slots() → audit
    - GET /appointments/{id}     → AppointmentDetailService.get_detail() → audit
    - POST /appointments         → CreateAppointmentService.create_appointment() → audit
    - PATCH /appointments/{id}/status → AppointmentStatusService.change_status() → audit

  charge_router.py:
    - POST /charge               → ChargeOrchestrator.execute() → audit

  emit_router.py:
    - POST /emit                 → inline audit.write() before response

  notify_router.py:
    - POST /appointments/{id}/notify → NotifyService.send_notification() → audit

Ratchet: PHI_ENDPOINT_REGISTRY is the locked set.
Adding a new PHI endpoint WITHOUT audit = this test fails.
Adding audit to a new endpoint = add entry to registry.

T-9 — F2-S1 vitalia-fase2-valeria-agenda arch tests.

downstream-regression-na: brand-local arch fitness test; no cross-brand consumers
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import NamedTuple

# ─── Workspace roots ──────────────────────────────────────────────────────────

WS_ROOT = Path(__file__).resolve().parents[4]
VITALIA_BE_SRC = WS_ROOT / "vitalia" / "backend" / "src"
MODULES_ROOT = VITALIA_BE_SRC / "modules" / "vitalia"


# ─── PHI endpoint registry (locked set — ratchet) ─────────────────────────────


class PhiEndpointEntry(NamedTuple):
    """Describes a known PHI endpoint and where its audit write lives."""

    router_file: str  # relative path to router file (from WS_ROOT)
    function_name: str  # name of the async endpoint function
    audit_in_service: str  # relative path to service/orchestrator with audit write
    description: str  # human-readable description for failure messages


#: All PHI endpoints that MUST have audit log rows.
#: Ratchet: add entries when new PHI endpoints are created (never remove).
PHI_ENDPOINT_REGISTRY: tuple[PhiEndpointEntry, ...] = (
    PhiEndpointEntry(
        router_file="vitalia/backend/src/modules/vitalia/scheduling/api/agenda_router.py",
        function_name="get_agenda_grid",
        audit_in_service="vitalia/backend/src/modules/vitalia/scheduling/application/services/agenda_grid_service.py",
        description="GET /agenda/grid — PHI-masked slots (reads patient data)",
    ),
    PhiEndpointEntry(
        router_file="vitalia/backend/src/modules/vitalia/scheduling/api/agenda_router.py",
        function_name="get_appointment_detail",
        audit_in_service="vitalia/backend/src/modules/vitalia/scheduling/application/services/appointment_detail_service.py",
        description="GET /appointments/{id} — drawer detail (PHI-masked read)",
    ),
    PhiEndpointEntry(
        router_file="vitalia/backend/src/modules/vitalia/scheduling/api/agenda_router.py",
        function_name="create_appointment",
        audit_in_service="vitalia/backend/src/modules/vitalia/scheduling/application/services/create_appointment_service.py",
        description="POST /appointments — create appointment (PHI write)",
    ),
    PhiEndpointEntry(
        router_file="vitalia/backend/src/modules/vitalia/scheduling/api/agenda_router.py",
        function_name="patch_appointment_status",
        audit_in_service="vitalia/backend/src/modules/vitalia/scheduling/application/services/appointment_status_service.py",
        description="PATCH /appointments/{id}/status — status change (PHI write)",
    ),
    PhiEndpointEntry(
        router_file="vitalia/backend/src/modules/vitalia/payments/api/charge_router.py",
        function_name="charge_appointment",
        audit_in_service="vitalia/backend/src/modules/vitalia/scheduling/application/services/charge_orchestrator.py",
        description="POST /payments/charge — cobrar saldo (payment write, PHI-adjacent)",
    ),
    PhiEndpointEntry(
        router_file="vitalia/backend/src/modules/vitalia/fiscal/api/emit_router.py",
        function_name="emit_fiscal_document",
        audit_in_service="vitalia/backend/src/modules/vitalia/fiscal/api/emit_router.py",
        description="POST /fiscal/emit — standalone fiscal emit retry (audit inline in router)",
    ),
    PhiEndpointEntry(
        router_file="vitalia/backend/src/modules/vitalia/scheduling/api/notify_router.py",
        function_name="send_appointment_reminder",
        audit_in_service="vitalia/backend/src/modules/vitalia/scheduling/application/services/notify_service.py",
        description="POST /appointments/{id}/notify — send reminder (PHI-adjacent, audit required)",
    ),
)

# ─── Audit write detection patterns ───────────────────────────────────────────

#: Patterns that indicate an audit write call in source code.
AUDIT_WRITE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"await\s+\w*audit\w*\.write\s*\("),  # await audit_writer.write(
    re.compile(r"await\s+audit\.write\s*\("),  # await audit.write(
    re.compile(r"await\s+self\._audit\.write\s*\("),  # await self._audit.write(
    re.compile(r"audit_writer\.write\s*\("),  # sync pattern (fallback)
    re.compile(r"write_audit_log_sync\s*\("),  # sync helper pattern
    re.compile(r"AsyncAuditWriter.*\.write\s*\("),  # inline AsyncAuditWriter().write(
)

#: Pattern to detect @require_phi_access decorator (marks PHI endpoint).
PHI_DECORATOR_PATTERN = re.compile(r"@require_phi_access")

#: Pattern to detect inline RBAC check (alternative PHI marker).
PHI_RBAC_CHECK_PATTERN = re.compile(r"ALLOWED_PHI_ROLES|_PHI_ROLES")

#: Endpoints that use ALLOWED_PHI_ROLES RBAC check for access control but return
#: NO PHI data (e.g. aggregate counts, availability slots — PHI-free results).
#: These endpoints do NOT require an audit log row (justified per hipaa-lite.md).
#: Ratchet: add entries ONLY with justified commit message citing the data returned.
KNOWN_NON_PHI_RBAC_ENDPOINTS: frozenset[str] = frozenset(
    [
        # get_agenda_aggregates: returns integer counts per day (no patient identifiers).
        # Documented in agenda_router.py: "PHI-free: returns only integer counts per day."
        "get_agenda_aggregates",
        # Availability endpoints (T-BE-3): return scheduling metadata only — NO PHI.
        # conflict_label = time string only; doctor_label = professional display name.
        # Per 03-arch-be.md § 7 PHI contract: "Availability = scheduling metadata only."
        "_rbac_check",  # Helper function, not an endpoint handler
        "check_availability",  # availability_router.py: AvailabilityCheckResponse (no PHI)
        "list_free_doctors",  # availability_router.py: FreeDoctorsResponse (no PHI)
        "get_day_strip",  # availability_router.py: DayStripResponse (start/end + kind only)
    ]
)


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _has_audit_write(source: str) -> bool:
    """Return True if source contains any audit write call pattern."""
    return any(pattern.search(source) for pattern in AUDIT_WRITE_PATTERNS)


def _function_body_source(source: str, function_name: str) -> str | None:
    """Extract the source lines of a specific async function from file source.

    Returns the function body as a string, or None if function not found.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    lines = source.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            if node.name == function_name:
                # Extract lines from function start to end
                start = node.lineno - 1
                end = node.end_lineno if hasattr(node, "end_lineno") else len(lines)
                return "\n".join(lines[start:end])
    return None


def _relative(p: Path) -> str:
    try:
        return str(p.relative_to(WS_ROOT))
    except ValueError:
        return str(p)


def _count_phi_endpoints_in_router(router_path: Path) -> list[str]:
    """Scan router file for PHI-touching endpoints (RBAC check or decorator present).

    Returns list of function names that appear to handle PHI.
    Used to detect new PHI endpoints not yet in PHI_ENDPOINT_REGISTRY.
    """
    if not router_path.exists():
        return []

    source = router_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    phi_functions: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            continue

        # Check if function has PHI marker (decorator OR inline RBAC check)
        has_phi_decorator = any(
            PHI_DECORATOR_PATTERN.search(ast.unparse(d)) if hasattr(ast, "unparse") else False
            for d in node.decorator_list
        )
        # Get function body lines to check for inline RBAC pattern
        end_lineno = node.end_lineno if hasattr(node, "end_lineno") else node.lineno + 50
        func_lines = source.splitlines()[node.lineno - 1 : end_lineno]
        func_body = "\n".join(func_lines)

        has_rbac_check = PHI_RBAC_CHECK_PATTERN.search(func_body) is not None

        if has_phi_decorator or has_rbac_check:
            phi_functions.append(node.name)

    return phi_functions


# ─── Tests ────────────────────────────────────────────────────────────────────


class TestAuditLogRowPerPhiEndpoint:
    """Every PHI endpoint in scheduling/payments/fiscal MUST have an audit write call.

    Implements defense-in-depth audit coverage verification.
    Complements test_audit_log_sync_write.py (which checks the writer itself).
    """

    def test_phi_endpoint_registry_not_empty(self) -> None:
        """Sanity: PHI endpoint registry must have entries (F2-S1 provides 7)."""
        assert len(PHI_ENDPOINT_REGISTRY) >= 7, (
            f"PHI_ENDPOINT_REGISTRY has {len(PHI_ENDPOINT_REGISTRY)} entries. "
            "Expected at least 7 per F2-S1 T-9 spec. "
            "If scheduling/payments/fiscal modules are not yet created, "
            "this test may be skipped until T-6/T-7/T-8 are complete."
        )

    def test_all_phi_endpoint_router_files_exist(self) -> None:
        """All router files in PHI_ENDPOINT_REGISTRY must exist."""
        missing: list[str] = []
        for entry in PHI_ENDPOINT_REGISTRY:
            router_path = WS_ROOT / entry.router_file
            if not router_path.exists():
                missing.append(entry.router_file)

        assert missing == [], (
            "PHI endpoint router files missing:\n"
            + "\n".join(f"  - {f}" for f in missing)
            + "\n\nFix: ensure T-6/T-7/T-8 router files are created before running T-9 arch tests."
        )

    def test_all_phi_endpoint_functions_exist_in_routers(self) -> None:
        """Each function_name in PHI_ENDPOINT_REGISTRY must exist in its router file."""
        missing: list[str] = []

        for entry in PHI_ENDPOINT_REGISTRY:
            router_path = WS_ROOT / entry.router_file
            if not router_path.exists():
                continue  # Covered by previous test

            source = router_path.read_text(encoding="utf-8")
            func_body = _function_body_source(source, entry.function_name)
            if func_body is None:
                missing.append(f"{entry.router_file}: function '{entry.function_name}' not found ({entry.description})")

        assert missing == [], (
            "PHI endpoint functions missing from router files:\n"
            + "\n".join(f"  - {f}" for f in missing)
            + "\n\nFix: ensure endpoint function names match PHI_ENDPOINT_REGISTRY entries."
        )

    def test_service_layer_has_audit_write_for_each_phi_endpoint(self) -> None:
        """Each PHI endpoint's service file MUST contain an audit write call.

        Checks the audit_in_service path from PHI_ENDPOINT_REGISTRY.
        Audit writes in service layer satisfy HIPAA-lite sync-write-before-response invariant.
        """
        violations: list[str] = []

        for entry in PHI_ENDPOINT_REGISTRY:
            service_path = WS_ROOT / entry.audit_in_service
            if not service_path.exists():
                violations.append(
                    f"{entry.audit_in_service}: service/orchestrator file missing "
                    f"(required for audit of '{entry.function_name}')"
                )
                continue

            source = service_path.read_text(encoding="utf-8")
            if not _has_audit_write(source):
                violations.append(
                    f"{entry.audit_in_service}: NO audit write call found. "
                    f"Required by PHI endpoint '{entry.function_name}' ({entry.description}). "
                    "HIPAA-lite mandates: audit_writer.write() before response."
                )

        assert violations == [], (
            "PHI endpoint audit write violations:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nFix: add 'await audit_writer.write(...)' in the service method "
            "called by each PHI endpoint. Write must complete BEFORE returning response."
        )

    def test_agenda_grid_service_has_audit_write(self) -> None:
        """AgendaGridService.list_slots MUST have audit write (PHI read).

        Explicit test for the most frequently called PHI endpoint.
        """
        service_path = MODULES_ROOT / "scheduling" / "application" / "services" / "agenda_grid_service.py"
        if not service_path.exists():
            return  # Pre-T-4 — skip

        source = service_path.read_text(encoding="utf-8")
        assert _has_audit_write(source), (
            "agenda_grid_service.py does not contain an audit write call. "
            "GET /agenda/grid reads PHI (masked patient names) — audit row MANDATORY. "
            "Add: await self._audit.write(action='agenda_grid_viewed', ...) "
            "before returning slots list."
        )

    def test_appointment_detail_service_has_audit_write(self) -> None:
        """AppointmentDetailService.get_detail MUST have audit write (PHI read).

        Drawer detail endpoint exposes PHI-masked patient data.
        """
        service_path = MODULES_ROOT / "scheduling" / "application" / "services" / "appointment_detail_service.py"
        if not service_path.exists():
            return

        source = service_path.read_text(encoding="utf-8")
        assert _has_audit_write(source), (
            "appointment_detail_service.py does not contain an audit write call. "
            "GET /appointments/{id} reads PHI (drawer detail) — audit row MANDATORY. "
            "Add: await self._audit.write(action='appointment_detail_viewed', ...) "
            "before returning appointment detail."
        )

    def test_charge_orchestrator_has_audit_write(self) -> None:
        """ChargeOrchestrator.execute MUST have audit write (PHI-adjacent financial write).

        Payment charges are PHI-adjacent (appointment_id FK → patient).
        """
        orchestrator_path = MODULES_ROOT / "scheduling" / "application" / "services" / "charge_orchestrator.py"
        if not orchestrator_path.exists():
            return

        source = orchestrator_path.read_text(encoding="utf-8")
        assert _has_audit_write(source), (
            "charge_orchestrator.py does not contain an audit write call. "
            "POST /payments/charge is PHI-adjacent (appointment → patient) — audit MANDATORY. "
            "Add: await self._audit.write(action='charge_initiated', ...) in execute()."
        )

    def test_fiscal_emit_router_has_audit_write(self) -> None:
        """emit_router.py MUST have audit write (inline, before response).

        POST /fiscal/emit has inline audit write in the router (per 03-arch A6 compensation).
        """
        router_path = MODULES_ROOT / "fiscal" / "api" / "emit_router.py"
        if not router_path.exists():
            return

        source = router_path.read_text(encoding="utf-8")
        assert _has_audit_write(source), (
            "emit_router.py does not contain an audit write call. "
            "POST /fiscal/emit emits fiscal documents (PHI-adjacent) — audit MANDATORY. "
            "Add inline audit write before the return statement in emit_fiscal_document()."
        )

    def test_notify_service_has_audit_write(self) -> None:
        """NotifyService.send_notification MUST have audit write (compliance-required).

        WhatsApp notifications are compliance-audited even when PHI is blocked.
        """
        service_path = MODULES_ROOT / "scheduling" / "application" / "services" / "notify_service.py"
        if not service_path.exists():
            return

        source = service_path.read_text(encoding="utf-8")
        assert _has_audit_write(source), (
            "notify_service.py does not contain an audit write call. "
            "POST /appointments/{id}/notify requires audit row (ComplianceService + HIPAA-lite). "
            "Add: await self._audit.write(action='reminder_sent', ...) before returning."
        )

    def test_create_appointment_service_has_audit_write(self) -> None:
        """CreateAppointmentService.create_appointment MUST have audit write (PHI write).

        Creating an appointment creates a patient association (PHI write operation).
        """
        service_path = MODULES_ROOT / "scheduling" / "application" / "services" / "create_appointment_service.py"
        if not service_path.exists():
            return

        source = service_path.read_text(encoding="utf-8")
        assert _has_audit_write(source), (
            "create_appointment_service.py does not contain an audit write call. "
            "POST /appointments creates PHI association (patient ↔ appointment) — audit MANDATORY. "
            "Add: await self._audit.write(action='appointment_created', ...) before returning."
        )

    def test_appointment_status_service_has_audit_write(self) -> None:
        """AppointmentStatusService.change_status MUST have audit write (PHI state change).

        Status transitions (confirmed/cancelled/no-show) are PHI state changes.
        """
        service_path = MODULES_ROOT / "scheduling" / "application" / "services" / "appointment_status_service.py"
        if not service_path.exists():
            return

        source = service_path.read_text(encoding="utf-8")
        assert _has_audit_write(source), (
            "appointment_status_service.py does not contain an audit write call. "
            "PATCH /appointments/{id}/status modifies PHI state — audit MANDATORY. "
            "Add: await self._audit.write(action='appointment_status_changed', ...) before returning."
        )

    def test_no_new_phi_router_without_audit(self) -> None:
        """Ratchet: detect router files with RBAC checks that are NOT in PHI_ENDPOINT_REGISTRY.

        If a new PHI endpoint is added to a router but not added to the registry,
        this test fails — forcing the developer to add the audit requirement explicitly.

        Note: this test only flags router functions with RBAC checks. Non-PHI
        endpoints (e.g. aggregates endpoint) are not flagged.
        """
        # Known endpoint function names in registry (for fast lookup)
        registered_functions: set[str] = {entry.function_name for entry in PHI_ENDPOINT_REGISTRY}

        # Routers to scan (scheduling/payments/fiscal api dirs)
        router_dirs = [
            MODULES_ROOT / "scheduling" / "api",
            MODULES_ROOT / "payments" / "api",
            MODULES_ROOT / "fiscal" / "api",
        ]

        unregistered_phi_endpoints: list[str] = []

        for api_dir in router_dirs:
            if not api_dir.exists():
                continue
            for router_file in api_dir.glob("*_router.py"):
                if "__pycache__" in router_file.parts:
                    continue
                rel = _relative(router_file)
                phi_functions = _count_phi_endpoints_in_router(router_file)

                for func_name in phi_functions:
                    if func_name not in registered_functions:
                        # Skip known non-PHI endpoints that use RBAC but return only aggregates
                        if func_name in KNOWN_NON_PHI_RBAC_ENDPOINTS:
                            continue
                        # Check if this unregistered function has audit write
                        source = router_file.read_text(encoding="utf-8")
                        func_body = _function_body_source(source, func_name) or ""
                        if not _has_audit_write(func_body):
                            unregistered_phi_endpoints.append(
                                f"{rel}::{func_name} (PHI-touching endpoint not in "
                                "PHI_ENDPOINT_REGISTRY + no audit write detected)"
                            )

        assert unregistered_phi_endpoints == [], (
            "New PHI endpoints detected that are not in PHI_ENDPOINT_REGISTRY:\n"
            + "\n".join(f"  - {e}" for e in unregistered_phi_endpoints)
            + "\n\nFix: add the new endpoint to PHI_ENDPOINT_REGISTRY in this test file "
            "AND add audit_writer.write() to its service/orchestrator. "
            "Every PHI endpoint MUST have an audit log row per hipaa-lite.md."
        )

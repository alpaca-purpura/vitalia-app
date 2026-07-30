# cap: scheduling.mateo-agenda
"""Scheduling RBAC — single source of truth for PHI-access roles.

SSoT for the set of roles allowed to read/act on PHI-bearing scheduling endpoints
(agenda grid, aggregates, appointment detail/create/status, notify).

Previously this frozenset was duplicated in ``agenda_router.py``
(``ALLOWED_PHI_ROLES``) and ``notify_router.py`` (``_PHI_ROLES``), which let the two
drift. Consolidating here means adding/removing a role happens in ONE place.

Roles (vitalia/.claude/rules/hipaa-lite.md § Access control):
  - owner            — clinic owner (user_tenants.role = owner). Legitimate clinical
                       operator; the agenda is PHI-masked server-side and the dual
                       filter tenant+clinic + audit log stay mandatory regardless.
  - admin_clinic     — clinic administrator.
  - doctor           — treating physician.
  - nurse            — nursing staff.
  - valeria_assistant — Valeria agent acting on behalf of authorized clinic staff.

This set gates ACCESS only. It NEVER relaxes the dual-filter (tenant_id + clinic_id),
the PHI masking, or the synchronous audit-log write — those remain enforced at the
repository/service layer for every request, for every role.

downstream-regression-na: brand-local scheduling RBAC for vitalia.
"""

from __future__ import annotations

#: Roles allowed to access scheduling PHI endpoints (hipaa-lite.md § RBAC).
#: Adding a role here propagates to every scheduling router consistently.
SCHEDULING_PHI_ROLES: frozenset[str] = frozenset(
    [
        "owner",
        "admin_clinic",
        "doctor",
        "nurse",
        "valeria_assistant",
    ]
)

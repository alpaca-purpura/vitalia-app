# cap: __shared__
# story-origin: TBD
"""PHI RBAC decorator — @require_phi_access + brand_owner RBAC dependency.

Enforces role-based access control for PHI and brand-owner endpoints per vitalia HIPAA-lite.

PHI allowed roles: doctor, nurse, admin_clinic.
Brand-owner allowed roles: owner, admin_clinic.
All other roles are DENIED for their respective surfaces.

Per vitalia/.claude/rules/hipaa-lite.md § Access control (RBAC strict):
  "Roles permitidos PHI: doctor, nurse, admin_clinic.
   Otros (marketing, sales) NUNCA ven PHI."

Per 03-arch.md § 5.2 (F2-S7 vitalia-fase2-lisa-marca):
  Brand owner endpoints (brand_studio marca_router): owner, admin_clinic only.
  GET endpoints: broader read allowed (no explicit restriction).

Usage:
    # PHI endpoints (decorator pattern):
    @require_phi_access(roles=["doctor", "nurse", "admin_clinic"], audit_repo=audit_dep)
    async def get_treatment_plan(
        tenant_id: UUID, clinic_id: UUID, user_id: UUID, user_role: str, ...
    ) -> TreatmentPlan:
        ...

    # Brand-owner endpoints (Depends factory pattern):
    async def patch_identity(
        ...,
        _: str = Depends(require_brand_owner_access()),
    ) -> BrandIdentityDTO:
        ...

The PHI decorator MUST accept these keyword args on the decorated function:
  - tenant_id: UUID
  - clinic_id: UUID
  - user_id: UUID
  - user_role: str

require_brand_owner_access() reads X-User-Role header directly.

downstream-regression-na: brand-local RBAC decorator for vitalia PHI endpoints
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any
from uuid import UUID

import structlog
from fastapi import Header, HTTPException

from src.modules.vitalia._shared.repositories.audit_log_repository import (
    AuditLogEntry,
)

logger = structlog.get_logger()

# Brand-owner RBAC — brand_studio marca endpoints (F2-S7 vitalia-fase2-lisa-marca)
ALLOWED_BRAND_OWNER_ROLES: frozenset[str] = frozenset(["owner", "admin_clinic"])


def require_brand_owner_access(
    roles: frozenset[str] = ALLOWED_BRAND_OWNER_ROLES,
) -> Callable[..., Any]:
    """FastAPI Depends factory: only owner/admin_clinic can mutate brand config.

    Reads X-User-Role header directly. Raises HTTP 403 with error_code
    BRAND_OWNER_RBAC_DENIED when role is not in allowed set.

    Per 03-arch.md § 5.2 (F2-S7 vitalia-fase2-lisa-marca).
    Brand config = owner-level, no PHI — uses this lighter RBAC dep instead
    of require_phi_access decorator.

    Args:
        roles: frozenset of allowed role strings. Default: owner, admin_clinic.

    Returns:
        FastAPI Depends-compatible async dependency function.

    Raises:
        HTTPException 403: When X-User-Role is not in allowed roles.
    """

    async def _dep(
        user_role: str = Header(alias="X-User-Role", default=""),
    ) -> str:
        """Validate brand-owner role and return the role string."""
        if user_role not in roles:
            logger.warning(
                "brand_owner_rbac_denied",
                user_role=user_role,
                allowed_roles=list(roles),
            )
            raise HTTPException(
                status_code=403,
                detail={"error_code": "BRAND_OWNER_RBAC_DENIED"},
            )
        return user_role

    return _dep


class PHIAccessDeniedError(Exception):
    """Raised when a user role is not permitted to access PHI.

    Maps to HTTP 403 Forbidden in FastAPI exception handlers.

    Per hipaa-lite.md: roles other than doctor/nurse/admin_clinic
    NEVER see PHI. Raise this error on detection — do NOT silently degrade.
    """

    def __init__(
        self,
        user_role: str,
        required_roles: list[str],
        resource_type: str | None = None,
    ) -> None:
        self.user_role = user_role
        self.required_roles = required_roles
        self.resource_type = resource_type
        super().__init__(
            f"PHI access denied: role '{user_role}' is not in allowed roles "
            f"{required_roles}. "
            f"Resource: {resource_type or 'unknown'}. "
            f"Only doctor, nurse, admin_clinic may access PHI "
            f"(vitalia/.claude/rules/hipaa-lite.md § Access control)."
        )


def require_phi_access(
    roles: list[str],
    audit_repo: Any | None = None,
    resource_type: str | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator enforcing RBAC + audit logging for PHI endpoints.

    Checks that the caller's role is in the allowed list. Writes an
    audit log entry on BOTH successful access and denial.

    The audit log write is SYNCHRONOUS (awaited) — per HIPAA-lite rule.

    Args:
        roles: List of allowed role strings (e.g. ["doctor", "nurse", "admin_clinic"]).
        audit_repo: Optional AuditLogRepository instance (or AsyncMock for tests).
                    If provided, write() is called with action=phi_access_granted
                    or action=phi_access_denied.
        resource_type: Optional resource type label for the audit entry.

    Returns:
        Decorator that wraps an async function with RBAC + audit.

    Raises:
        PHIAccessDeniedError: When user_role is not in roles list.
        TypeError: When the decorated function does not accept the required
                   keyword arguments (tenant_id, clinic_id, user_id, user_role).
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            tenant_id: UUID | None = kwargs.get("tenant_id")
            clinic_id: UUID | None = kwargs.get("clinic_id")
            user_id: UUID | None = kwargs.get("user_id")
            user_role: str = kwargs.get("user_role", "")

            if user_role not in roles:
                # Write denial audit event (sync — MUST be awaited)
                if audit_repo is not None:
                    try:
                        entry = AuditLogEntry(
                            tenant_id=tenant_id or UUID(int=0),
                            clinic_id=clinic_id or UUID(int=0),
                            user_id=user_id or UUID(int=0),
                            action="phi_access_denied",
                            resource_type=resource_type or func.__name__,
                        )
                        await audit_repo.write(entry)
                    except Exception as audit_err:  # noqa: BLE001
                        logger.warning(
                            "phi_audit_write_failed_on_denial",
                            error=str(audit_err),
                            user_role=user_role,
                        )

                logger.warning(
                    "phi_access_denied",
                    user_role=user_role,
                    allowed_roles=roles,
                    function=func.__name__,
                    tenant_id=str(tenant_id) if tenant_id else None,
                )
                raise PHIAccessDeniedError(
                    user_role=user_role,
                    required_roles=roles,
                    resource_type=resource_type or func.__name__,
                )

            # Role is allowed — write access granted audit event (sync)
            if audit_repo is not None:
                try:
                    entry = AuditLogEntry(
                        tenant_id=tenant_id or UUID(int=0),
                        clinic_id=clinic_id or UUID(int=0),
                        user_id=user_id or UUID(int=0),
                        action="phi_access_granted",
                        resource_type=resource_type or func.__name__,
                    )
                    await audit_repo.write(entry)
                except Exception as audit_err:  # noqa: BLE001
                    logger.warning(
                        "phi_audit_write_failed_on_access",
                        error=str(audit_err),
                        user_role=user_role,
                    )

            logger.info(
                "phi_access_granted",
                user_role=user_role,
                function=func.__name__,
                tenant_id=str(tenant_id) if tenant_id else None,
            )
            return await func(*args, **kwargs)

        return wrapper

    return decorator

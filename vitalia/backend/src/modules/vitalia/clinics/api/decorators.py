# cap: clinics.clinics-brand-extension
# story-origin: TBD
"""Vitalia Clinic API decorators — HIPAA access control.

Provides @require_clinic_access decorator for FastAPI routes that access
PHI-adjacent clinic resources.

hipaa-lite.md § Access control:
  - Roles with PHI access: doctor, nurse, admin_clinic
  - Others (marketing, sales) NEVER see PHI
  - Patient role sees ONLY their own data
  - Dual filter (tenant_id + clinic_id) enforced at query level

Usage:
    @router.get("/clinics/{clinic_id}/detail", response_model=ClinicResponse)
    @require_clinic_access(roles=["doctor", "nurse", "admin_clinic"])
    async def get_clinic_detail(...):
        ...
"""

from __future__ import annotations

from functools import wraps
from typing import Any

from fastapi import HTTPException, status


def require_clinic_access(
    roles: list[str] | None = None,
) -> Any:
    """Decorator factory for FastAPI route functions requiring clinic PHI access.

    Args:
        roles: List of allowed roles. Defaults to ["doctor", "nurse", "admin_clinic"].

    Returns:
        Decorator that checks the requesting user's role before allowing access.

    Note:
        This decorator validates role at the application layer.
        Actual role is extracted from Clerk JWT claims in the dependency.
        Admin panel bypasses Clerk (uses bcrypt super-admin auth).
    """
    _allowed_roles = roles or ["doctor", "nurse", "admin_clinic"]

    def decorator(func: Any) -> Any:
        """Apply role check to route function."""

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Role extracted by FastAPI dependency (passed as kwarg)
            requesting_role = kwargs.get("requesting_role", "")
            if requesting_role not in _allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "access_denied",
                        "message": "No tienes permiso para acceder a esta información clínica.",
                        "required_roles": _allowed_roles,
                    },
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator

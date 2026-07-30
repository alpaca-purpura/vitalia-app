# cap: configuracion.cuenta
"""Vitalia Clinic domain exceptions — pure Python, no framework imports."""

from __future__ import annotations

from uuid import UUID


class ClinicNotFoundError(Exception):
    """Raised when a clinic is not found for a given tenant context.

    Used by repositories and services to signal 404-equivalent errors.
    The API layer maps this to HTTPException(status_code=404).
    """

    def __init__(self, tenant_id: str | UUID | None = None, clinic_id: str | UUID | None = None) -> None:
        """Initialize with optional tenant/clinic context."""
        self.tenant_id = tenant_id
        self.clinic_id = clinic_id
        msg = "Clínica no encontrada"
        if tenant_id:
            msg += f" (tenant: {tenant_id})"
        super().__init__(msg)

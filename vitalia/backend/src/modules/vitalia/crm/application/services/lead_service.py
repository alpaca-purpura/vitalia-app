# cap: crm.crm-consent-optout
# story-origin: TBD
"""LeadService — non-PHI lead management.

Application layer — no RBAC restriction (Lead is not PHI).
All authenticated roles can access lead data.

Extended by T-inbox-be-5: list_for_inbox, create, update methods.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

import structlog

from src.modules.vitalia.crm.domain.lead import Lead

logger = structlog.get_logger()


class LeadNotFoundError(Exception):
    """Raised when lead does not exist for given tenant."""

    def __init__(self, lead_id: UUID) -> None:
        """Initialize."""
        super().__init__(f"Lead {lead_id} not found")
        self.lead_id = lead_id


class LeadService:
    """Service for non-PHI Lead operations.

    No @require_phi_access restriction — Lead data is accessible to all roles.
    Single tenant_id filter enforced at repository layer.
    """

    def __init__(self, lead_repo: object) -> None:
        """Initialize with lead repository.

        Args:
            lead_repo: LeadRepository instance (or AsyncMock in tests).
        """
        self._lead_repo = lead_repo

    async def get_by_id(
        self,
        lead_id: UUID,
        *,
        tenant_id: UUID,
    ) -> Lead | None:
        """Retrieve a lead by ID.

        Args:
            lead_id: Lead UUID.
            tenant_id: Tenant UUID — root isolation (required).

        Returns:
            Lead or None if not found.
        """
        result = await self._lead_repo.get_by_id(
            lead_id,
            tenant_id=tenant_id,
        )
        logger.info(
            "lead_service.get_by_id",
            lead_id=str(lead_id),
            tenant_id=str(tenant_id),
            found=result is not None,
        )
        return result

    async def list_for_inbox(
        self,
        *,
        tenant_id: UUID,
        status: str | None = None,
        source: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Lead], int]:
        """List leads for the inbox — non-PHI, all authenticated roles.

        Args:
            tenant_id: Tenant UUID — root isolation (required).
            status: Optional status filter.
            source: Optional source filter.
            limit: Page size (max 100).
            offset: Page offset.

        Returns:
            Tuple of (leads, total_count).
        """
        results = await self._lead_repo.list_by_filter(
            tenant_id=tenant_id,
            status=status,
            source=source,
            limit=limit,
            offset=offset,
        )
        total = len(results)  # Slice 1: total = result count (Slice 2 will add count query)
        logger.info(
            "lead_service.list_for_inbox",
            tenant_id=str(tenant_id),
            count=total,
        )
        return results, total

    async def create(
        self,
        *,
        tenant_id: UUID,
        name: str,
        email: str | None,
        phone: str | None,
        source: str | None,
        status: str,
        notes: str | None,
        marketing_opt_in: bool,
        stage: str = "interesado",
        channel: str | None = None,
        service_interest: str | None = None,
        estimated_value: Decimal | None = None,
        currency: str | None = None,
    ) -> Lead:
        """Create a new lead — non-PHI.

        Nota: el DTO LeadCreateRequest acepta `tags` pero NO se persiste
        (vitalia_leads no tiene columna tags; el form FE tampoco tiene input).

        Args:
            tenant_id: Tenant UUID.
            name: Lead name.
            email: Optional email.
            phone: Optional phone.
            source: Optional acquisition source.
            status: Initial lead status (default 'new').
            notes: Optional free-text notes.
            marketing_opt_in: Whether lead opted in to marketing.
            stage: Funnel stage (default 'interesado').
            channel: Acquisition channel (whatsapp, instagram, etc.).
            service_interest: Service of interest.
            estimated_value: Estimated deal value.
            currency: Currency code.

        Returns:
            Created Lead.
        """
        lead = await self._lead_repo.create(
            id=uuid4(),
            tenant_id=tenant_id,
            name=name,
            email=email,
            phone=phone,
            source=source,
            status=status,
            notes=notes,
            marketing_opt_in=marketing_opt_in,
            stage=stage,
            channel=channel,
            service_interest=service_interest,
            estimated_value=estimated_value,
            currency=currency,
        )
        logger.info(
            "lead_service.create",
            tenant_id=str(tenant_id),
            lead_id=str(lead.id),
        )
        return lead

    async def update(
        self,
        lead_id: UUID,
        *,
        tenant_id: UUID,
        updates: dict[str, object],
    ) -> Lead:
        """Update allowed lead fields — non-PHI.

        Args:
            lead_id: Lead UUID.
            tenant_id: Tenant UUID — root isolation (required).
            updates: Dict of field → value (only truthy/non-None values).

        Returns:
            Updated Lead.

        Raises:
            LeadNotFoundError: If lead does not exist for tenant.
        """
        existing = await self._lead_repo.get_by_id(lead_id, tenant_id=tenant_id)
        if existing is None:
            raise LeadNotFoundError(lead_id)

        updated = await self._lead_repo.update(
            lead_id=lead_id,
            tenant_id=tenant_id,
            updates=updates,
        )
        logger.info(
            "lead_service.update",
            lead_id=str(lead_id),
            tenant_id=str(tenant_id),
            fields=list(updates.keys()),
        )
        return updated

# cap: lisa.servicios
"""KnowledgeSourceAdapter — records an uploaded doc/URL as an engine KnowledgeSource.

Bridges the async vitalia service to the SYNC engine ``KnowledgeSourceRepository``
(``db: Session``) via ``AsyncSession.run_sync`` (D-1 seam). Sub-phase A: the row
is created with status QUEUED — the indexer (Qdrant) is a stub, so no chunks are
produced yet; the row exists so the source is tracked and indexable later.

Engine is consumed by import ONLY (``luana_core_offer_studio``) — never edited.
"""

from __future__ import annotations

from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.offer.application.services.document_autocomplete_service import KnowledgeSourceRef

logger = structlog.get_logger()


class KnowledgeSourceAdapter:
    """Persist an engine KnowledgeSource row from the async layer."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record_source(
        self,
        *,
        tenant_id: UUID,
        offer_id: UUID,
        name: str,
        source_type: str,
        source_url: str | None = None,
        file_url: str | None = None,
    ) -> KnowledgeSourceRef:
        from luana_core_offer_studio.domain.enums import KnowledgeSourceStatus, KnowledgeSourceType  # noqa: PLC0415
        from luana_core_offer_studio.domain.knowledge_source import KnowledgeSource  # noqa: PLC0415
        from luana_core_offer_studio.infrastructure.repositories.knowledge_source_repository import (  # noqa: PLC0415
            KnowledgeSourceRepository,
        )
        from sqlalchemy.orm import Session

        source = KnowledgeSource(
            tenant_id=tenant_id,
            offer_id=offer_id,
            name=name,
            type=KnowledgeSourceType(source_type),
            status=KnowledgeSourceStatus.QUEUED,  # indexer stub (Sub-phase A)
            source_url=source_url,
            file_url=file_url,
        )

        def _callback(sync_session: "Session") -> KnowledgeSource:
            repo = KnowledgeSourceRepository(sync_session)
            created = repo.create(source)
            sync_session.commit()
            return created

        created = await self._session.run_sync(_callback)
        logger.debug("knowledge_source_recorded", tenant_id=str(tenant_id), source_id=str(created.id))
        return KnowledgeSourceRef(id=created.id, status=str(created.status))

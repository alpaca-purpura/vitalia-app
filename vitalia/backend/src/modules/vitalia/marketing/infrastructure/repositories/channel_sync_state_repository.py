# cap: marketing.attribution-matrix-4-origins
# story-origin: TBD
"""ChannelSyncStateRepository — dual-scope async repository.

Subclasses ``CompoundScopeRepositoryBase`` from engine (luana-core-platform v0.4.0).
scope_field="clinic_id" enforces HIPAA-lite dual filter (tenant_id + clinic_id).

Special: oauth_token_encrypted uses pgcrypto symmetric encryption.
  - save_with_encrypted_token: encrypts using KEKClient before writing
  - decrypt_token: decrypts using pgcrypto on read

All queries exclude soft-deleted rows (deleted_at IS NULL).
No PHI in channel sync state (OAuth metadata only).

downstream-regression-na: brand-local marketing repository (vitalia-only module)
"""

from __future__ import annotations

from typing import ClassVar
from uuid import UUID

import structlog
from luana_core_platform.repositories.compound_scope_repository import CompoundScopeRepositoryBase
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.marketing.domain.enums import ProviderSlug, SyncStatus
from src.modules.vitalia.marketing.infrastructure.models.channel_sync_state_model import (
    ChannelSyncStateModel,
)

logger = structlog.get_logger()


class ChannelSyncStateRepository(CompoundScopeRepositoryBase[ChannelSyncStateModel, UUID]):
    """Async repository for ChannelSyncState (ad channel OAuth connections).

    Dual-scope isolation: tenant_id (multitenant) + clinic_id (HIPAA-lite).
    scope_field="clinic_id" per vitalia brand convention.

    Pgcrypto integration:
      oauth_token_encrypted is stored as pgcrypto-encrypted BYTEA.
      Use save_with_encrypted_token() to persist tokens safely.
      Use decrypt_token() to retrieve the plain-text bytes.
    """

    MODEL: ClassVar[type[ChannelSyncStateModel]] = ChannelSyncStateModel

    def __init__(self, *, session: AsyncSession) -> None:
        """Initialize with clinic_id as the secondary scope axis."""
        super().__init__(session=session, scope_field="clinic_id")

    async def get_active_by_provider(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        provider: ProviderSlug,
    ) -> ChannelSyncStateModel | None:
        """Return the active (status=OK, enabled=True) sync state for a provider.

        "Active" means the OAuth connection is established and last sync succeeded.
        Returns None if no active connection exists for this clinic+provider.

        Dual filter: tenant_id + clinic_id (HIPAA-lite).
        Does NOT return deleted, disabled, or ERROR/PENDING channels.

        Args:
            tenant_id: Tenant UUID for root isolation.
            clinic_id: Clinic UUID for secondary isolation.
            provider: Advertising provider slug to filter by.

        Returns:
            ChannelSyncStateModel if an active connection exists, else None.
        """
        scope_attr = self._scope_attr()
        stmt = (
            select(self.MODEL)
            .where(self.MODEL.tenant_id == tenant_id)
            .where(scope_attr == clinic_id)
            .where(self.MODEL.provider == provider.value)
            .where(self.MODEL.status == SyncStatus.OK.value)
            .where(self.MODEL.enabled.is_(True))
            .where(self.MODEL.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        logger.info(
            "channel_sync_state.get_active_by_provider",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            provider=provider.value,
            found=row is not None,
        )
        return row

    async def save_with_encrypted_token(
        self,
        *,
        model: ChannelSyncStateModel,
        plain_token: bytes,
    ) -> None:
        """Add model to session with pgcrypto-encrypted oauth_token.

        Encrypts plain_token using pgp_sym_encrypt (pgcrypto) with the KEK
        from VITALIA_PHI_KEK environment variable.

        The encrypted bytes are stored in model.oauth_token_encrypted before
        adding to the session. Session must be committed by the caller.

        Args:
            model: ChannelSyncStateModel to persist (without token set).
            plain_token: Raw OAuth token bytes to encrypt.

        Raises:
            KEKConfigurationError: If VITALIA_PHI_KEK env var not set or too short.
        """
        from src.modules.vitalia._shared.encryption.kek_client import KEKClient  # noqa: PLC0415

        kek = KEKClient.from_env()
        key_hex = kek.get_key()

        # Use pgcrypto pgp_sym_encrypt via raw SQL
        # RETURNING clause gives us the encrypted bytes to store on the model
        encrypt_sql = text("SELECT pgp_sym_encrypt(:plain_token, :key) AS encrypted_token")
        result = await self._session.execute(
            encrypt_sql,
            {"plain_token": plain_token.decode("latin-1"), "key": key_hex},
        )
        row = result.fetchone()
        model.oauth_token_encrypted = row.encrypted_token  # type: ignore[union-attr]

        self._session.add(model)
        logger.info(
            "channel_sync_state.token_encrypted",
            tenant_id=str(model.tenant_id),
            clinic_id=str(model.clinic_id),
            provider=model.provider,
        )

    async def decrypt_token(
        self,
        *,
        model_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> bytes | None:
        """Retrieve and decrypt the oauth_token for a sync state record.

        Applies dual filter before decrypting to prevent cross-tenant access.
        Returns None if the record doesn't exist, is deleted, or has no token.

        Args:
            model_id: Primary key of the ChannelSyncStateModel.
            tenant_id: Tenant UUID for root isolation.
            clinic_id: Clinic UUID for secondary isolation.

        Returns:
            Decrypted OAuth token bytes, or None if not found.
        """
        from src.modules.vitalia._shared.encryption.kek_client import KEKClient  # noqa: PLC0415

        # First: verify access with dual filter
        model = await self.get_by_id(id=model_id, tenant_id=tenant_id, scope_id=clinic_id)
        if model is None or model.oauth_token_encrypted is None:
            return None

        kek = KEKClient.from_env()
        key_hex = kek.get_key()

        # Decrypt with pgcrypto pgp_sym_decrypt
        decrypt_sql = text("SELECT pgp_sym_decrypt(:encrypted_token, :key) AS plain_token")
        result = await self._session.execute(
            decrypt_sql,
            {"encrypted_token": model.oauth_token_encrypted, "key": key_hex},
        )
        row = result.fetchone()
        if row is None or row.plain_token is None:
            return None

        plain: str = row.plain_token
        logger.info(
            "channel_sync_state.token_decrypted",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            model_id=str(model_id),
        )
        return plain.encode("latin-1")

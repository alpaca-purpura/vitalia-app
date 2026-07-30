"""Tests for ChannelSyncStateRepository.

Covers:
- get_active_by_provider: filters SyncStatus.OK + provider + dual filter
- SC-MK-04: pgcrypto roundtrip for oauth_token_encrypted (integration)
- HIPAA-lite dual filter: tenant_id + clinic_id enforced
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.vitalia.marketing.domain.enums import ProviderSlug
from src.modules.vitalia.marketing.infrastructure.models.channel_sync_state_model import (
    ChannelSyncStateModel,
)
from src.modules.vitalia.marketing.infrastructure.repositories.channel_sync_state_repository import (
    ChannelSyncStateRepository,
)


def _make_model(
    *,
    tenant_id: uuid.UUID,
    clinic_id: uuid.UUID,
    provider: str = "google_ads",
    status: str = "ok",
    enabled: bool = True,
    deleted_at: datetime | None = None,
) -> ChannelSyncStateModel:
    """Factory for ChannelSyncStateModel test instances."""
    now = datetime.now(UTC)
    model = ChannelSyncStateModel()
    model.id = uuid.uuid4()
    model.tenant_id = tenant_id
    model.clinic_id = clinic_id
    model.provider = provider
    model.status = status
    model.enabled = enabled
    model.oauth_token_encrypted = None
    model.account_id = None
    model.last_sync_at = None
    model.last_success_at = None
    model.last_error = None
    model.created_at = now
    model.updated_at = now
    model.deleted_at = deleted_at
    return model


class TestChannelSyncStateRepositoryInit:
    """Repository construction uses scope_field='clinic_id'."""

    def test_inherits_compound_scope_repository_base(self) -> None:
        """ChannelSyncStateRepository must subclass CompoundScopeRepositoryBase."""
        from luana_core_platform.repositories.compound_scope_repository import (
            CompoundScopeRepositoryBase,
        )

        assert issubclass(ChannelSyncStateRepository, CompoundScopeRepositoryBase)

    def test_model_class_var_is_set(self) -> None:
        """MODEL ClassVar must be ChannelSyncStateModel."""
        assert ChannelSyncStateRepository.MODEL is ChannelSyncStateModel

    def test_scope_field_is_clinic_id(self) -> None:
        """scope_field must be 'clinic_id'."""
        session = AsyncMock()
        repo = ChannelSyncStateRepository(session=session)
        assert repo._scope_field == "clinic_id"  # noqa: SLF001


class TestGetActiveByProvider:
    """get_active_by_provider filters SyncStatus.OK + enabled=True + dual filter."""

    async def test_returns_active_channel_for_provider(self) -> None:
        """Returns model when status=ok and provider matches."""
        tenant_id = uuid.uuid4()
        clinic_id = uuid.uuid4()
        session = AsyncMock()

        model = _make_model(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            provider="google_ads",
            status="ok",
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = model
        session.execute.return_value = mock_result

        repo = ChannelSyncStateRepository(session=session)
        result = await repo.get_active_by_provider(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            provider=ProviderSlug.GOOGLE_ADS,
        )

        assert result is not None
        assert result.status == "ok"
        assert result.provider == "google_ads"

    async def test_returns_none_when_status_not_ok(self) -> None:
        """ERROR or PENDING channels are NOT active."""
        tenant_id = uuid.uuid4()
        clinic_id = uuid.uuid4()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        repo = ChannelSyncStateRepository(session=session)
        result = await repo.get_active_by_provider(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            provider=ProviderSlug.GOOGLE_ADS,
        )

        assert result is None

    async def test_dual_filter_applied(self) -> None:
        """Query must use both tenant_id AND clinic_id."""
        tenant_id = uuid.uuid4()
        clinic_id = uuid.uuid4()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        repo = ChannelSyncStateRepository(session=session)
        await repo.get_active_by_provider(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            provider=ProviderSlug.GOOGLE_ADS,
        )

        session.execute.assert_called_once()
        stmt = session.execute.call_args[0][0]
        stmt_str = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        tenant_hex = str(tenant_id).replace("-", "")
        clinic_hex = str(clinic_id).replace("-", "")
        assert tenant_hex in stmt_str.replace("-", ""), f"tenant_id not in query: {stmt_str}"
        assert clinic_hex in stmt_str.replace("-", ""), f"clinic_id not in query: {stmt_str}"

    async def test_excludes_deleted_records(self) -> None:
        """Soft-deleted channel states must never appear as active."""
        tenant_id = uuid.uuid4()
        clinic_id = uuid.uuid4()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        repo = ChannelSyncStateRepository(session=session)
        result = await repo.get_active_by_provider(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            provider=ProviderSlug.GOOGLE_ADS,
        )

        assert result is None


class TestPgcryptoRoundtrip:
    """SC-MK-04: pgcrypto encrypt/decrypt roundtrip for oauth_token_encrypted.

    Requires live Postgres with pgcrypto extension AND VITALIA_PHI_KEK env var.
    Marked as integration — skipped when Postgres is not available.
    """

    @pytest.mark.integration
    async def test_oauth_token_pgcrypto_roundtrip(self, pg_session: AsyncMock) -> None:  # type: ignore[valid-type]
        """Encrypt token on write, decrypt on read — bytes roundtrip.

        This test requires:
        - Live Postgres connection (pg_session fixture)
        - VITALIA_PHI_KEK env var set (32+ byte hex string)
        - pgcrypto extension enabled in the DB

        Uses the ChannelSyncStateRepository.save_with_encrypted_token() to
        exercise the pgcrypto symmetric encryption path.
        """
        kek_key = os.getenv("VITALIA_PHI_KEK")
        if not kek_key:
            pytest.skip("VITALIA_PHI_KEK not set — skipping pgcrypto integration test")

        from src.modules.vitalia.marketing.infrastructure.repositories.channel_sync_state_repository import (
            ChannelSyncStateRepository,
        )

        tenant_id = uuid.uuid4()
        clinic_id = uuid.uuid4()
        plain_token = b"test_oauth_access_token_secret_value"

        repo = ChannelSyncStateRepository(session=pg_session)

        # Create model with encrypted token
        model = ChannelSyncStateModel()
        model.id = uuid.uuid4()
        model.tenant_id = tenant_id
        model.clinic_id = clinic_id
        model.provider = "google_ads"
        model.status = "ok"
        model.enabled = True
        model.account_id = "test-account-123"

        # Encrypt and save
        await repo.save_with_encrypted_token(model=model, plain_token=plain_token)

        # Retrieve and decrypt
        result_bytes = await repo.decrypt_token(model_id=model.id, tenant_id=tenant_id, clinic_id=clinic_id)

        assert result_bytes == plain_token, (
            f"Pgcrypto roundtrip failed: expected {plain_token!r}, got {result_bytes!r}. "
            "Verify pgcrypto extension is installed and VITALIA_PHI_KEK is correct."
        )

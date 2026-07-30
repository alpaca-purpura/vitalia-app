# cap: marketing.attribution-matrix-4-origins
# story-origin: TBD
"""ChannelSyncState domain entity — represents OAuth sync state for an ad channel.

Per HIPAA-lite: NO PHI stored here. oauth_token_encrypted stored at-rest
in DB using pgcrypto. This entity holds the decrypted bytes in memory only.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from src.modules.vitalia.marketing.domain.enums import ProviderSlug, SyncStatus


@dataclass
class ChannelSyncState:
    """OAuth sync state for a clinic's advertising channel connection.

    Uniquely identified by (tenant_id, clinic_id, provider).
    """

    id: uuid.UUID
    tenant_id: uuid.UUID
    clinic_id: uuid.UUID
    provider: ProviderSlug
    status: SyncStatus
    created_at: datetime
    updated_at: datetime
    enabled: bool = True

    # Optional sync tracking fields
    last_sync_at: datetime | None = None
    last_success_at: datetime | None = None
    last_error: str | None = None
    oauth_token_encrypted: bytes | None = None
    account_id: str | None = None
    deleted_at: datetime | None = None

    @property
    def is_connected(self) -> bool:
        """True if the channel is enabled and last sync succeeded."""
        return self.enabled and self.status == SyncStatus.OK

    def mark_sync_success(self, now: datetime) -> None:
        """Record a successful sync."""
        self.status = SyncStatus.OK
        self.last_sync_at = now
        self.last_success_at = now
        self.last_error = None
        self.updated_at = now

    def mark_sync_failure(self, error: str, now: datetime) -> None:
        """Record a failed sync."""
        self.status = SyncStatus.ERROR
        self.last_sync_at = now
        self.last_error = error
        self.updated_at = now

# cap: marketing.attribution-matrix-4-origins
# story-origin: TBD
"""SQLAlchemy 2.0 model — ChannelSyncStateModel.

Maps to ``vitalia_channel_sync_state`` table (base columns from 007_vitalia_initial_tables.py,
additions from 026_slice1_marketing_channel_sync_state.py).

HIPAA-lite:
  - oauth_token_encrypted: BYTEA — stored as pgcrypto-encrypted bytes.
    Plain-text token NEVER lands in this column; repository handles encrypt/decrypt.
  - clinic_id: second scope filter (dual filter per hipaa-lite.md § Tenant isolation refuerzo).
  - NO PHI: this table holds channel OAuth metadata only (no patient names/DNIs/diagnoses).

downstream-regression-na: brand-local marketing infrastructure model
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import Boolean, DateTime, Index, LargeBinary, String, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class ChannelSyncStateModel(Base):
    """OAuth sync state for a clinic's advertising channel connection.

    tenant_id + clinic_id enforce dual filter per HIPAA-lite.
    oauth_token_encrypted stores pgcrypto-encrypted bytes (see repository).
    """

    __tablename__ = "vitalia_channel_sync_state"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)
    clinic_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)

    # Provider slug: "google_ads" | "meta_ads"
    provider: Mapped[str] = mapped_column(String(64), nullable=False)

    # Sync lifecycle status: "ok" | "error" | "pending"
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")

    # Whether the channel integration is enabled by the user
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # OAuth token stored as pgcrypto-encrypted BYTEA (plain text never stored)
    oauth_token_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    # Provider-side account identifier (e.g. Google Ads customer ID)
    account_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Sync tracking timestamps
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Last error message from failed sync (no PHI)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        # Natural unique key per clinic (one connection per provider per clinic)
        # Partial unique — only for non-deleted rows (enforced in application layer)
        Index(
            "ix_vitalia_channel_sync_state_clinic_provider",
            "tenant_id",
            "clinic_id",
            "provider",
        ),
    )

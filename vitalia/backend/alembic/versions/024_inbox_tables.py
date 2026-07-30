"""Migration 024: inbox tables — conversations, messages, activity_events, action_receipts.

Creates 4 new tables for the Slice 1 inbox feature (T-inbox-be-2).

Per .claude/rules/backend-migrations.md:
- All DDL uses raw SQL with IF NOT EXISTS (idempotent)
- Uses raw SQL exclusively — no Alembic table/column helpers
- All timestamps are TIMESTAMPTZ (timezone=True per coding_rules)
- PHI dual-filter: tenant_id + clinic_id columns on all 4 tables

Revision: 024_vitalia
Down revision: 023_vitalia (vitalia_clinics)

Per hipaa-lite.md:
- clinic_id mandatory on all 4 tables (HIPAA-lite second scope filter)
- soft-delete (deleted_at) on conversations + messages
- action_receipts are state machines (no hard delete, no deleted_at)
- activity_events are append-only projections (no deleted_at)
"""

from alembic import op

revision = "024_vitalia"
down_revision = "023_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create inbox tables (idempotent — IF NOT EXISTS throughout)."""

    # ── 1. vitalia_conversations ──────────────────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_conversations (
            id                   UUID        PRIMARY KEY,
            tenant_id            UUID        NOT NULL,
            clinic_id            UUID        NOT NULL,
            lead_id              UUID        NOT NULL,
            patient_id           UUID        NULL,
            channel              VARCHAR(32) NOT NULL,
            channel_external_id  VARCHAR(128) NULL,
            status               VARCHAR(16) NOT NULL DEFAULT 'active',
            handler_mode         VARCHAR(16) NOT NULL DEFAULT 'ai',
            proposal_required    BOOLEAN     NOT NULL DEFAULT FALSE,
            pause_until          TIMESTAMPTZ NULL,
            help_needed          BOOLEAN     NOT NULL DEFAULT FALSE,
            help_needed_reason   TEXT        NULL,
            unread_media_count   INT         NOT NULL DEFAULT 0,
            last_message_at      TIMESTAMPTZ NULL,
            last_message_preview TEXT        NULL,
            messages_count       INT         NOT NULL DEFAULT 0,
            stage_decision       VARCHAR(32) NULL,
            linked_offer_id      UUID        NULL,
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at           TIMESTAMPTZ NULL
        )
        """
    )

    # Conversations indexes (partial WHERE deleted_at IS NULL for non-deleted rows)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_conversations_tenant_clinic_status
            ON vitalia_conversations (tenant_id, clinic_id, status)
            WHERE deleted_at IS NULL
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_conversations_lead
            ON vitalia_conversations (tenant_id, clinic_id, lead_id)
            WHERE deleted_at IS NULL
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_conversations_help_needed
            ON vitalia_conversations (tenant_id, clinic_id, help_needed, last_message_at DESC)
            WHERE help_needed = TRUE AND deleted_at IS NULL
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_conversations_unread_media
            ON vitalia_conversations (tenant_id, clinic_id, unread_media_count, last_message_at DESC)
            WHERE unread_media_count > 0 AND deleted_at IS NULL
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_conversations_channel_external_id
            ON vitalia_conversations (channel_external_id)
            WHERE channel_external_id IS NOT NULL
        """
    )

    # ── 2. vitalia_messages ───────────────────────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_messages (
            id                   UUID         PRIMARY KEY,
            tenant_id            UUID         NOT NULL,
            clinic_id            UUID         NOT NULL,
            conversation_id      UUID         NOT NULL REFERENCES vitalia_conversations(id),
            channel              VARCHAR(32)  NOT NULL,
            external_message_id  VARCHAR(128) NULL,
            sender_type          VARCHAR(16)  NOT NULL,
            sender_user_id       UUID         NULL,
            body_text            TEXT         NULL,
            media_kind           VARCHAR(16)  NULL,
            media_url            TEXT         NULL,
            media_duration_s     INT          NULL,
            media_phi_flagged    BOOLEAN      NOT NULL DEFAULT FALSE,
            transcription_text   TEXT         NULL,
            transcription_confidence FLOAT    NULL,
            retracted_at         TIMESTAMPTZ  NULL,
            retracted_by_user_id UUID         NULL,
            retracted_reason     TEXT         NULL,
            retract_succeeded    BOOLEAN      NULL,
            handler_mode         VARCHAR(16)  NOT NULL DEFAULT 'ai',
            cache_hit_rate       FLOAT        NULL,
            llm_cost_usd         NUMERIC(10, 6) NULL,
            sent_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            delivered_at         TIMESTAMPTZ  NULL,
            read_at              TIMESTAMPTZ  NULL,
            created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            deleted_at           TIMESTAMPTZ  NULL
        )
        """
    )

    # Messages indexes
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_messages_conversation_sent_at
            ON vitalia_messages (tenant_id, clinic_id, conversation_id, sent_at DESC)
            WHERE deleted_at IS NULL
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_messages_external_id
            ON vitalia_messages (channel, external_message_id)
            WHERE external_message_id IS NOT NULL AND deleted_at IS NULL
        """
    )

    # ── 3. vitalia_activity_events ────────────────────────────────────────────
    # Append-only projection — no deleted_at (corrections are new events)
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_activity_events (
            id                    UUID        PRIMARY KEY,
            tenant_id             UUID        NOT NULL,
            clinic_id             UUID        NOT NULL,
            conversation_id       UUID        NOT NULL REFERENCES vitalia_conversations(id),
            source_trace_event_id UUID        NULL,
            event_kind            VARCHAR(64) NOT NULL,
            description_es        TEXT        NOT NULL,
            agent_id              VARCHAR(32) NOT NULL DEFAULT 'adrian',
            occurred_at           TIMESTAMPTZ NOT NULL,
            payload_sanitized     JSONB       NOT NULL DEFAULT '{}',
            created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at            TIMESTAMPTZ NULL
        )
        """
    )

    # Activity events index (descending for ActivityStream last-8 query)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_activity_events_conv_occurred
            ON vitalia_activity_events (tenant_id, clinic_id, conversation_id, occurred_at DESC)
        """
    )

    # ── 4. vitalia_action_receipts ────────────────────────────────────────────
    # 5min undo window per AI message (SC-01). State machine — no deleted_at.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_action_receipts (
            id               UUID        PRIMARY KEY,
            tenant_id        UUID        NOT NULL,
            clinic_id        UUID        NOT NULL,
            message_id       UUID        NOT NULL REFERENCES vitalia_messages(id),
            conversation_id  UUID        NOT NULL REFERENCES vitalia_conversations(id),
            expires_at       TIMESTAMPTZ NOT NULL,
            retracted_at     TIMESTAMPTZ NULL,
            retract_succeeded BOOLEAN    NULL,
            retract_reason   TEXT        NULL,
            created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at       TIMESTAMPTZ NULL
        )
        """
    )

    # Action receipts indexes
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_action_receipts_expires
            ON vitalia_action_receipts (tenant_id, clinic_id, expires_at)
            WHERE retracted_at IS NULL
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_action_receipts_message
            ON vitalia_action_receipts (message_id)
        """
    )


def downgrade() -> None:
    """Drop inbox tables in reverse dependency order (action_receipts → messages → conversations).

    activity_events dropped before messages (references conversations).
    """
    op.execute("DROP TABLE IF EXISTS vitalia_action_receipts")
    op.execute("DROP TABLE IF EXISTS vitalia_activity_events")
    op.execute("DROP TABLE IF EXISTS vitalia_messages")
    op.execute("DROP TABLE IF EXISTS vitalia_conversations")

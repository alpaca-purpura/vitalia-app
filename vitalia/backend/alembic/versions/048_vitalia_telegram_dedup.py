# cap: adrian.inbox
"""Migration 048 — Telegram update_id dedup table (T-BE-1 canal inbound).

Creates `vitalia_telegram_update_dedup` for idempotent Telegram webhook processing.
Telegram redelivers updates on timeout or bot restart — dedup prevents double-dispatch.

Per backend-migrations.md: raw SQL IF NOT EXISTS (idempotent).
Per tenant-isolation.md: tenant_id scopes dedup per tenant.
"""

from alembic import op

revision = "048_vitalia"
down_revision = "047_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_telegram_update_dedup (
            tenant_id   TEXT        NOT NULL,
            update_id   BIGINT      NOT NULL,
            seen_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (tenant_id, update_id)
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_telegram_dedup_seen_at ON vitalia_telegram_update_dedup (seen_at);"
    )


def downgrade() -> None:
    # ponytail: dedup table is auxiliary infra — no rows are business data.
    # Leave table in place (no destructive downgrade).
    pass

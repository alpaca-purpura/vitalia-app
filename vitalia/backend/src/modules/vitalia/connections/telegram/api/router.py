# cap: adrian.inbox
"""Telegram inbound webhook route — T-BE-1.

POST /api/v1/connections/telegram/webhook

Responsibilities (thin route — no business logic):
  1. Validate X-Telegram-Bot-Api-Secret-Token (RN-9 / V-NF-1).
     Invalid secret → return TelegramWebhookAck(ok=True) without dispatch.
     Telegram convention: never 4xx (would trigger retry storm).
  2. Extract update_id → check idempotency store (vitalia_telegram_update_dedup).
     Duplicate update_id → ack without second dispatch (V-FN-5).
  3. Resolve tenant_id from bot configuration (per-tenant in connections config).
  4. Dispatch to engine: orchestrator.handle_telegram_webhook(payload, bg, tenant_id, db).

Security invariants:
  - Secret mismatch → DISCARD (structlog warning severity=high) — no information leak.
  - Duplicate update_id → DISCARD (structlog info severity=medium) — Telegram redelivery.
  - tenant_id=None fallback (no tenant configured for this bot) → DISCARD.

Per hipaa-lite.md: Telegram update payloads are NOT PHI. sanitize_payload is
engine-layer (chat.py). No audit_log required at route layer.

Per backend-migrations.md: dedup table created in migration 047 (IF NOT EXISTS).
Per V-NF-4: response_model=TelegramWebhookAck mandatory.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, Header, Request
from luana_core_platform.core.database import get_db
from sqlalchemy.orm import Session

from src.modules.vitalia.connections.telegram.api.dtos import TelegramWebhookAck

if TYPE_CHECKING:
    pass

logger = structlog.get_logger()

# ── Module-level secret (injectable for tests via patch) ─────────────────────
# Per 03-arch.md: per-tenant validation. For phase 1 (single bot dev), validated
# against VITALIA_TELEGRAM_WEBHOOK_SECRET env var. Multi-tenant: each tenant
# stores their own secret in connections config. Constant is module-level for
# testability (tests patch this name).
TELEGRAM_WEBHOOK_SECRET: str | None = os.environ.get("VITALIA_TELEGRAM_WEBHOOK_SECRET")

# ── Router ───────────────────────────────────────────────────────────────────

router = APIRouter(tags=["telegram-inbound"])


# ── Helpers (module-level functions — injectable via patch for unit tests) ────


def _is_update_seen(db: Session, tenant_id: str | None, update_id: int) -> bool:
    """Check if this update_id was already processed for this tenant.

    Uses raw SQL SELECT on vitalia_telegram_update_dedup table (migration 047).
    Returns True if (tenant_id, update_id) row exists → dedup → skip dispatch.
    """
    from sqlalchemy import text  # noqa: PLC0415

    result = db.execute(
        text(
            "SELECT 1 FROM vitalia_telegram_update_dedup "
            "WHERE tenant_id = :tenant_id AND update_id = :update_id "
            "LIMIT 1"
        ),
        {"tenant_id": tenant_id or "global", "update_id": update_id},
    )
    return result.fetchone() is not None


def _mark_update_seen(db: Session, tenant_id: str | None, update_id: int) -> None:
    """Insert (tenant_id, update_id) into vitalia_telegram_update_dedup.

    Idempotent: ON CONFLICT DO NOTHING (primary key constraint).
    Commits immediately so concurrent requests see the dedup row.
    """
    from sqlalchemy import text  # noqa: PLC0415

    db.execute(
        text(
            "INSERT INTO vitalia_telegram_update_dedup (tenant_id, update_id) "
            "VALUES (:tenant_id, :update_id) "
            "ON CONFLICT (tenant_id, update_id) DO NOTHING"
        ),
        {"tenant_id": tenant_id or "global", "update_id": update_id},
    )
    db.commit()


def _resolve_tenant_id(db: Session, *, update: dict[str, Any]) -> str | None:
    """Resolve tenant_id from the connections config.

    Per 03-arch.md: the bot token per-tenant is stored in the connections config.
    The engine's handle_telegram_webhook receives tenant_id and uses it to look up
    the per-tenant bot token internally.

    For phase 1 (single bot, single clinic/tenant for dev), we return the tenant_id
    from the env var VITALIA_TELEGRAM_DEFAULT_TENANT_ID if set, or look up the
    single active tenant that has Telegram configured.

    Returns None if no tenant is configured → discard the update.
    """
    from sqlalchemy import text  # noqa: PLC0415

    # Phase 1: env override for dev/single-tenant scenario
    env_tenant = os.environ.get("VITALIA_TELEGRAM_DEFAULT_TENANT_ID")
    if env_tenant:
        return env_tenant

    # Multi-tenant: query connections table for any tenant with Telegram channel configured
    # The connections table stores channel credentials as JSONB; Telegram config has 'token'.
    # We find the first active tenant with a Telegram connection.
    # (In full multi-bot phase, each bot would have a different token; we'd match by token.)
    try:
        result = db.execute(
            text(
                "SELECT tenant_id FROM channel_connections WHERE channel_type = 'telegram' AND is_active = TRUE LIMIT 1"
            )
        )
        row = result.fetchone()
        if row:
            return str(row[0])
    except Exception as exc:
        logger.warning(
            "telegram_tenant_resolve_db_error",
            error=str(exc),
        )

    return None


async def _orchestrator_dispatch(
    payload: dict[str, Any],
    background_tasks: BackgroundTasks,
    tenant_id: str | None,
    db: Session,
) -> None:
    """Dispatch to the engine's ChatOrchestrator.handle_telegram_webhook.

    Lazy import to avoid circular deps and to allow test patching.
    Per 03-arch.md: engine entrypoint is ChatOrchestrator.handle_telegram_webhook.
    Confirmed in core/luana-core-sales-agent/.../application/orchestrator/chat.py:93-128.
    """
    from luana_core_sales_agent.application.orchestrator.chat import ChatOrchestrator  # noqa: PLC0415

    orchestrator = ChatOrchestrator()
    await orchestrator.handle_telegram_webhook(
        payload=payload,
        background_tasks=background_tasks,
        tenant_id=tenant_id,
        db=db,
    )


# ── Endpoint ──────────────────────────────────────────────────────────────────


@router.post(
    "/webhook",
    response_model=TelegramWebhookAck,
    summary="Telegram inbound webhook receiver",
    description=(
        "Receives Telegram Bot API webhook updates. "
        "Validates X-Telegram-Bot-Api-Secret-Token, deduplicates by update_id, "
        "resolves tenant, and dispatches to the sales agent orchestrator. "
        "Always returns 200 TelegramWebhookAck (Telegram convention — never 4xx)."
    ),
)
async def receive_telegram_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_telegram_bot_api_secret_token: str | None = Header(
        default=None,
        alias="X-Telegram-Bot-Api-Secret-Token",
        description="Telegram webhook secret token set via setWebhook(secret_token=...).",
    ),
    db: Session = Depends(get_db),
) -> TelegramWebhookAck:
    """Telegram inbound webhook — thin route per DDD constraints.

    Route responsibilities:
      1. Secret validation (RN-9)
      2. update_id idempotency check (RN-9)
      3. Tenant resolution (per-tenant bot config)
      4. Dispatch to engine ChatOrchestrator.handle_telegram_webhook (background)

    Returns TelegramWebhookAck(ok=True) in ALL cases (Telegram anti-retry-storm convention).
    Errors are logged internally; Telegram sees a clean 200 always.
    """
    # ── Parse update_id from raw body (needed for dedup before dispatch) ──
    try:
        payload: dict[str, Any] = await request.json()
    except Exception as exc:
        logger.warning("telegram_webhook_invalid_json", error=str(exc))
        return TelegramWebhookAck(ok=True)

    update_id: int | None = payload.get("update_id")

    # ── 1. Validate secret (RN-9 / V-NF-1) ──────────────────────────────────
    expected_secret = TELEGRAM_WEBHOOK_SECRET
    if expected_secret and x_telegram_bot_api_secret_token != expected_secret:
        logger.warning(
            "telegram_webhook_invalid_secret",
            received_prefix=(x_telegram_bot_api_secret_token or "")[:4] + "***"
            if x_telegram_bot_api_secret_token
            else "missing",
            severity="high",
        )
        # Return ack — never leak auth signals to Telegram (retry storm prevention)
        return TelegramWebhookAck(ok=True)

    # ── 2. update_id dedup (RN-9 / V-FN-5) ──────────────────────────────────
    if update_id is not None:
        # Resolve tenant first (needed for scoped dedup key)
        tenant_id = _resolve_tenant_id(db, update=payload)

        if _is_update_seen(db, tenant_id, update_id):
            logger.info(
                "telegram_webhook_duplicate_update_id",
                update_id=update_id,
                tenant_id=tenant_id,
                severity="medium",
            )
            return TelegramWebhookAck(ok=True)

        # Mark as seen BEFORE dispatch (prevent race conditions on redelivery)
        _mark_update_seen(db, tenant_id, update_id)
    else:
        # No update_id (shouldn't happen per Telegram spec, but handle gracefully)
        logger.warning("telegram_webhook_missing_update_id", payload_keys=list(payload.keys()))
        tenant_id = _resolve_tenant_id(db, update=payload)

    # ── 3. Skip if no tenant configured ──────────────────────────────────────
    if tenant_id is None:
        logger.warning(
            "telegram_webhook_no_tenant_resolved",
            update_id=update_id,
            severity="medium",
        )
        return TelegramWebhookAck(ok=True)

    # ── 4. Filter non-message updates (photos, edited, channel_post, etc.) ───
    # Only text messages in .message key are processable by the engine.
    # Non-message updates (edited_message, channel_post, inline_query, etc.)
    # → ack but no dispatch (engine normalize_payload would return None anyway).
    if "message" not in payload:
        logger.info(
            "telegram_webhook_non_message_update_skipped",
            update_id=update_id,
            update_keys=list(payload.keys()),
        )
        return TelegramWebhookAck(ok=True)

    # ── 5. Dispatch to engine orchestrator ────────────────────────────────────
    # Direct await (not background_tasks) so the engine's internal debounce
    # and background scheduling decisions are made inside the orchestrator.
    await _orchestrator_dispatch(
        payload=payload,
        background_tasks=background_tasks,
        tenant_id=tenant_id,
        db=db,
    )

    logger.info(
        "telegram_webhook_dispatched",
        update_id=update_id,
        tenant_id=tenant_id,
    )

    return TelegramWebhookAck(ok=True)

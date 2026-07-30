# cap: marketing.attribution-matrix-4-origins
# story-origin: TBD
"""channel_metrics_sync_meta — ARQ cron job, every 4h.

Pulls Meta Ads campaign insights per active tenant+clinic connection,
upserts vitalia_channel_metrics, and publishes ChannelSyncSucceeded /
ChannelSyncFailed domain events.

HIPAA-lite:
  - No PHI in channel metrics (ad campaign data only — no patient identifiers).
  - Dual filter tenant_id + clinic_id on all queries.
  - OAuth token decrypted via ChannelSyncStateRepository.decrypt_token() (pgcrypto).
  - Payloads sanitized with compliance_level="hipaa_lite" before observability writes.

Soft-fail: one tenant's Meta auth issue never aborts the full cron run.

downstream-regression-na: brand-local marketing cron — no cross-brand consumers
"""

from __future__ import annotations

import os
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

import structlog
from luana_core_platform.workers.cron_envelope import cron_envelope

from src.modules.vitalia.marketing.domain.enums import ProviderSlug
from src.modules.vitalia.marketing.domain.events import ChannelSyncFailed, ChannelSyncSucceeded
from src.modules.vitalia.marketing.infrastructure.models.channel_sync_state_model import (
    ChannelSyncStateModel,
)
from src.modules.vitalia.marketing.infrastructure.repositories.channel_metric_repository import (
    ChannelMetricRepository,
)
from src.modules.vitalia.marketing.infrastructure.repositories.channel_sync_state_repository import (
    ChannelSyncStateRepository,
)

try:
    from luana_core_events.outbox import adapter_bus  # type: ignore[import]
except ImportError:  # pragma: no cover
    from unittest.mock import AsyncMock as _AsyncMock  # noqa: PLC0415

    class _FallbackBus:  # type: ignore[no-redef]
        publish = _AsyncMock()

    adapter_bus = _FallbackBus()

logger = structlog.get_logger()

# Look-back window for metric pulls: last 30 days
_LOOKBACK_DAYS: int = 30


# ---------------------------------------------------------------------------
# Injectable factory helpers (patchable for tests)
# ---------------------------------------------------------------------------


async def _get_all_active_meta_connections() -> list[ChannelSyncStateModel]:
    """Return all active Meta Ads sync states across all tenants.

    Queries vitalia_channel_sync_state WHERE provider=meta_ads AND status=ok AND enabled=true.
    Uses a brand-level DB session (no tenant scope here — the cron iterates all tenants).
    """
    from src.core.db import get_db_session  # type: ignore[import]  # noqa: PLC0415

    async with get_db_session() as session:
        from sqlalchemy import select  # noqa: PLC0415

        from src.modules.vitalia.marketing.infrastructure.models.channel_sync_state_model import (  # noqa: PLC0415
            ChannelSyncStateModel as _M,
        )

        stmt = (
            select(_M)
            .where(_M.provider == ProviderSlug.META_ADS.value)
            .where(_M.status == "ok")
            .where(_M.enabled.is_(True))
            .where(_M.deleted_at.is_(None))
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


def _get_sync_repo() -> ChannelSyncStateRepository:
    """Return ChannelSyncStateRepository instance (patchable in tests)."""
    from src.core.db import get_sync_session  # type: ignore[import]  # noqa: PLC0415

    return ChannelSyncStateRepository(session=get_sync_session())


def _get_metric_repo() -> ChannelMetricRepository:
    """Return ChannelMetricRepository instance (patchable in tests)."""
    from src.core.db import get_sync_session  # type: ignore[import]  # noqa: PLC0415

    return ChannelMetricRepository(session=get_sync_session())


def _get_meta_adapter() -> Any:
    """Return MetaAdsAdapter instance configured from environment (patchable in tests)."""
    from src.modules.vitalia.connections.meta_ads.adapter import MetaAdsAdapter  # noqa: PLC0415

    return MetaAdsAdapter(
        client_id=os.environ.get("META_OAUTH_CLIENT_ID", ""),
        client_secret=os.environ.get("META_OAUTH_CLIENT_SECRET", ""),
        redirect_uri=os.environ.get("META_OAUTH_REDIRECT_URI", ""),
    )


# ---------------------------------------------------------------------------
# Cron job
# ---------------------------------------------------------------------------


@cron_envelope("vitalia.cron.channel_metrics_sync_meta", ttl=14400)  # 4h TTL
async def channel_metrics_sync_meta(ctx: dict[str, Any]) -> None:
    """Pull Meta Ads campaign metrics for every active tenant+clinic connection.

    Schedule: every 4 hours ({0,4,8,12,16,20}:00 UTC).

    Steps per connection:
      1. Decrypt OAuth token via pgcrypto.
      2. Fetch campaign insights from Meta Marketing API (last 30 days).
      3. Upsert vitalia_channel_metrics rows (ON CONFLICT natural key).
      4. Publish ChannelSyncSucceeded or ChannelSyncFailed event.

    Soft-fail: errors for one tenant/clinic do NOT abort the cron.
    """
    active_connections = await _get_all_active_meta_connections()
    sync_repo = _get_sync_repo()
    metric_repo = _get_metric_repo()
    meta_adapter = _get_meta_adapter()

    since = (datetime.now(UTC) - timedelta(days=_LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    until = date.today().strftime("%Y-%m-%d")

    synced = 0
    failed = 0

    for conn in active_connections:
        tenant_id: UUID = conn.tenant_id
        clinic_id: UUID = conn.clinic_id
        conn_id: UUID = conn.id
        ad_account_id: str = conn.ad_account_id or ""

        try:
            # Decrypt OAuth token — dual filter inside decrypt_token()
            token_bytes = await sync_repo.decrypt_token(
                model_id=conn_id,
                tenant_id=tenant_id,
                clinic_id=clinic_id,
            )
            if token_bytes is None:
                raise ValueError("Token no disponible para este canal")

            access_token = token_bytes.decode("latin-1")

            # Fetch Meta Ads insights
            rows = await meta_adapter.fetch_insights(
                access_token=access_token,
                ad_account_id=ad_account_id,
                tenant_id=str(tenant_id),
                since=since,
                until=until,
            )

            # Upsert each campaign row — idempotent via ON CONFLICT natural key
            for row in rows:
                spend_raw = row.get("spend", "0") or "0"
                spend_cents = int(float(spend_raw) * 100)
                metric_date_str = row.get("date_start", until)
                try:
                    metric_date = date.fromisoformat(metric_date_str)
                except ValueError:
                    metric_date = date.today()

                await metric_repo.upsert_metric(
                    tenant_id=tenant_id,
                    clinic_id=clinic_id,
                    provider=ProviderSlug.META_ADS,
                    channel_slug="meta_ads",
                    metric_date=metric_date,
                    impressions=int(row.get("impressions", 0) or 0),
                    clicks=int(row.get("clicks", 0) or 0),
                    conversions=int(row.get("conversions", 0) or 0),
                    spend_cents=spend_cents,
                    currency=row.get("currency"),
                    campaign_id=row.get("campaign_id"),
                    campaign_name=row.get("campaign_name"),
                    # Sanitize raw_payload: exclude any token fields (no PHI in Meta metrics)
                    raw_payload={k: v for k, v in row.items() if k not in ("access_token", "token", "oauth_token")},
                )

            await adapter_bus.publish(
                ChannelSyncSucceeded(
                    tenant_id=tenant_id,
                    clinic_id=clinic_id,
                    provider=ProviderSlug.META_ADS,
                    synced_at=datetime.now(UTC),
                )
            )
            synced += 1
            logger.info(
                "channel_metrics_sync_meta.tenant_ok",
                tenant_id=str(tenant_id),
                clinic_id=str(clinic_id),
                rows=len(rows),
            )

        except Exception as exc:
            # Soft-fail: log + publish ChannelSyncFailed + continue to next tenant
            failed += 1
            error_msg = str(exc)
            logger.warning(
                "channel_metrics_sync_meta.tenant_error",
                tenant_id=str(tenant_id),
                clinic_id=str(clinic_id),
                error=error_msg,
            )
            try:
                await adapter_bus.publish(
                    ChannelSyncFailed(
                        tenant_id=tenant_id,
                        clinic_id=clinic_id,
                        provider=ProviderSlug.META_ADS,
                        error_message=error_msg,
                    )
                )
            except Exception as publish_exc:  # best-effort event publish
                logger.warning(
                    "channel_metrics_sync_meta.event_publish_failed",
                    error=str(publish_exc),
                )

    logger.info(
        "channel_metrics_sync_meta.completed",
        total=len(active_connections),
        synced=synced,
        failed=failed,
    )

# cap: marketing.attribution-matrix-4-origins
# story-origin: TBD
"""channel_metrics_sync_google — ARQ cron job, every 4h.

Pulls Google Ads campaign metrics per active tenant+clinic connection,
upserts vitalia_channel_metrics, and publishes ChannelSyncSucceeded /
ChannelSyncFailed domain events.

HIPAA-lite:
  - No PHI in channel metrics (ad campaign data only — no patient identifiers).
  - Dual filter tenant_id + clinic_id on all queries.
  - OAuth token decrypted via ChannelSyncStateRepository.decrypt_token() (pgcrypto).
  - Payloads sanitized — access_token fields excluded before writes.

Soft-fail: one tenant's Google Ads auth issue never aborts the full cron run.

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

_LOOKBACK_DAYS: int = 30


# ---------------------------------------------------------------------------
# Injectable factory helpers (patchable for tests)
# ---------------------------------------------------------------------------


async def _get_all_active_google_connections() -> list[ChannelSyncStateModel]:
    """Return all active Google Ads sync states across all tenants."""
    from src.core.db import get_db_session  # type: ignore[import]  # noqa: PLC0415

    async with get_db_session() as session:
        from sqlalchemy import select  # noqa: PLC0415

        from src.modules.vitalia.marketing.infrastructure.models.channel_sync_state_model import (  # noqa: PLC0415
            ChannelSyncStateModel as _M,
        )

        stmt = (
            select(_M)
            .where(_M.provider == ProviderSlug.GOOGLE_ADS.value)
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


def _get_google_adapter() -> Any:
    """Return GoogleAdsAdapter instance (patchable in tests)."""
    from src.modules.vitalia.connections.google_ads.adapter import GoogleAdsAdapter  # noqa: PLC0415

    return GoogleAdsAdapter(
        client_id=os.environ.get("GOOGLE_OAUTH_CLIENT_ID", ""),
        client_secret=os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", ""),
        redirect_uri=os.environ.get("GOOGLE_OAUTH_REDIRECT_URI", ""),
        developer_token=os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", ""),
    )


# ---------------------------------------------------------------------------
# Cron job
# ---------------------------------------------------------------------------


@cron_envelope("vitalia.cron.channel_metrics_sync_google", ttl=14400)  # 4h TTL
async def channel_metrics_sync_google(ctx: dict[str, Any]) -> None:
    """Pull Google Ads campaign metrics for every active tenant+clinic connection.

    Schedule: every 4 hours ({0,4,8,12,16,20}:00 UTC), offset +2min to avoid
    contention with channel_metrics_sync_meta.

    Steps per connection:
      1. Decrypt OAuth token via pgcrypto.
      2. Fetch campaign metrics via GAQL (last 30 days).
      3. Upsert vitalia_channel_metrics rows (ON CONFLICT natural key).
      4. Publish ChannelSyncSucceeded or ChannelSyncFailed event.

    Soft-fail: errors for one tenant/clinic do NOT abort the cron.
    """
    active_connections = await _get_all_active_google_connections()
    sync_repo = _get_sync_repo()
    metric_repo = _get_metric_repo()
    google_adapter = _get_google_adapter()

    since = (datetime.now(UTC) - timedelta(days=_LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    until = date.today().strftime("%Y-%m-%d")

    synced = 0
    failed = 0

    for conn in active_connections:
        tenant_id: UUID = conn.tenant_id
        clinic_id: UUID = conn.clinic_id
        conn_id: UUID = conn.id
        # Google uses customer_id field (stored in ad_account_id column)
        customer_id: str = conn.ad_account_id or ""

        try:
            token_bytes = await sync_repo.decrypt_token(
                model_id=conn_id,
                tenant_id=tenant_id,
                clinic_id=clinic_id,
            )
            if token_bytes is None:
                raise ValueError("Token no disponible para este canal de Google Ads")

            access_token = token_bytes.decode("latin-1")

            rows = await google_adapter.fetch_campaign_metrics(
                access_token=access_token,
                customer_id=customer_id,
                tenant_id=str(tenant_id),
                since=since,
                until=until,
            )

            for row in rows:
                # Google Ads cost is in micros (1/1,000,000 of the currency unit)
                cost_micros = int(row.get("metrics.cost_micros", 0) or 0)
                spend_cents = cost_micros // 10000  # micros → cents

                metric_date_str = row.get("segments.date", until)
                try:
                    metric_date = date.fromisoformat(metric_date_str)
                except ValueError:
                    metric_date = date.today()

                currency = row.get("customer.currency_code")

                await metric_repo.upsert_metric(
                    tenant_id=tenant_id,
                    clinic_id=clinic_id,
                    provider=ProviderSlug.GOOGLE_ADS,
                    channel_slug="google_ads",
                    metric_date=metric_date,
                    impressions=int(row.get("metrics.impressions", 0) or 0),
                    clicks=int(row.get("metrics.clicks", 0) or 0),
                    conversions=int(float(row.get("metrics.conversions", 0) or 0)),
                    spend_cents=spend_cents,
                    currency=currency,
                    campaign_id=row.get("campaign.id"),
                    campaign_name=row.get("campaign.name"),
                    raw_payload={k: v for k, v in row.items() if k not in ("access_token", "token", "oauth_token")},
                )

            await adapter_bus.publish(
                ChannelSyncSucceeded(
                    tenant_id=tenant_id,
                    clinic_id=clinic_id,
                    provider=ProviderSlug.GOOGLE_ADS,
                    synced_at=datetime.now(UTC),
                )
            )
            synced += 1
            logger.info(
                "channel_metrics_sync_google.tenant_ok",
                tenant_id=str(tenant_id),
                clinic_id=str(clinic_id),
                rows=len(rows),
            )

        except Exception as exc:
            failed += 1
            error_msg = str(exc)
            logger.warning(
                "channel_metrics_sync_google.tenant_error",
                tenant_id=str(tenant_id),
                clinic_id=str(clinic_id),
                error=error_msg,
            )
            try:
                await adapter_bus.publish(
                    ChannelSyncFailed(
                        tenant_id=tenant_id,
                        clinic_id=clinic_id,
                        provider=ProviderSlug.GOOGLE_ADS,
                        error_message=error_msg,
                    )
                )
            except Exception as publish_exc:
                logger.warning(
                    "channel_metrics_sync_google.event_publish_failed",
                    error=str(publish_exc),
                )

    logger.info(
        "channel_metrics_sync_google.completed",
        total=len(active_connections),
        synced=synced,
        failed=failed,
    )

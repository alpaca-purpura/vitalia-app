# cap: __shared__
# story-origin: TBD
"""ARQ WorkerSettings for Vitalia cron runner.

Registers 15 cron job functions with their schedules and idempotency wiring.

WorkerSettings is consumed by the ARQ worker process (started via
`arq src.modules.vitalia._shared.workers.arq_settings.WorkerSettings`).

Cron schedule table (verbatim from 03-arch-be.md § 4 + T-infra-8 spec + T-mk-be-6):
  followup_24h                        every 1h
  reactivation_45d                    every 6h
  maintenance_90d                     every 12h
  deposit_reminder_24h                every 1h
  appointment_reminder_24h            every 1h
  appointment_reminder_2h             every 15min
  nps_request_24h_post_appointment    every 1h
  brand_studio_audit_30d              daily 03:00 UTC
  lucas_weekly_recommendations        weekly Mon 04:00 UTC
  channel_sync_state_15min            every 15min
  audit_log_retention_sweep_monthly   monthly 1st 02:00 UTC
  channel_metrics_sync_meta           every 4h :00 UTC (T-mk-be-6)
  channel_metrics_sync_google         every 4h :02 UTC (T-mk-be-6)
  lucas_daily_analysis_sweep          daily 06:00 UTC (T-mk-be-6)
  referrals_value_sync                daily 10:00 UTC (T-mk-be-6)

All workers TZ-aware: cron schedules expressed in UTC, tenant TZ resolution
done inside each job function per master-data.md.

downstream-regression-na: brand-local worker config; no cross-brand consumers
"""

from __future__ import annotations

import os

from arq.connections import RedisSettings
from arq.cron import cron

from src.modules.vitalia._shared.workers.jobs.appointment_reminder_2h import (
    appointment_reminder_2h,
)
from src.modules.vitalia._shared.workers.jobs.appointment_reminder_24h import (
    appointment_reminder_24h,
)
from src.modules.vitalia._shared.workers.jobs.audit_log_retention_sweep_monthly import (
    audit_log_retention_sweep_monthly,
)
from src.modules.vitalia._shared.workers.jobs.brand_studio_audit_30d import (
    brand_studio_audit_30d,
)
from src.modules.vitalia._shared.workers.jobs.channel_sync_state_15min import (
    channel_sync_state_15min,
)
from src.modules.vitalia._shared.workers.jobs.deposit_reminder_24h import (
    deposit_reminder_24h,
)
from src.modules.vitalia._shared.workers.jobs.followup_24h import followup_24h
from src.modules.vitalia._shared.workers.jobs.lucas_weekly_recommendations import (
    lucas_weekly_recommendations,
)
from src.modules.vitalia._shared.workers.jobs.maintenance_90d import maintenance_90d
from src.modules.vitalia._shared.workers.jobs.nps_request_24h_post_appointment import (
    nps_request_24h_post_appointment,
)
from src.modules.vitalia._shared.workers.jobs.reactivation_45d import reactivation_45d
from src.modules.vitalia.marketing.jobs.channel_metrics_sync_google import (
    channel_metrics_sync_google,
)
from src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta import (
    channel_metrics_sync_meta,
)
from src.modules.vitalia.marketing.jobs.lucas_daily_analysis_sweep import (
    lucas_daily_analysis_sweep,
)
from src.modules.vitalia.marketing.jobs.referrals_value_sync import referrals_value_sync


def _redis_settings() -> RedisSettings:
    """Build RedisSettings from REDIS_URL env var.

    Falls back to localhost:6379 if not set (dev environment).
    Production MUST set REDIS_URL.
    """
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
    return RedisSettings.from_dsn(redis_url)


class WorkerSettings:
    """ARQ WorkerSettings for Vitalia cron runner.

    Registers all 15 cron job functions.
    Configuration per T-infra-8 spec:
      keep_result = 3600     (1h result retention)
      max_jobs = 50          (max concurrent jobs)
      health_check_interval = 30  (seconds between health checks)
    """

    functions = [
        followup_24h,
        reactivation_45d,
        maintenance_90d,
        deposit_reminder_24h,
        appointment_reminder_24h,
        appointment_reminder_2h,
        nps_request_24h_post_appointment,
        brand_studio_audit_30d,
        lucas_weekly_recommendations,
        channel_sync_state_15min,
        audit_log_retention_sweep_monthly,
        # Marketing Wave 3 crons (T-mk-be-6)
        channel_metrics_sync_meta,
        channel_metrics_sync_google,
        lucas_daily_analysis_sweep,
        referrals_value_sync,
    ]

    cron_jobs = [
        # --- Fidelización crons ---
        cron(
            followup_24h,
            name="followup_24h",
            minute=0,  # :00 every hour (hour=None → every hour)
        ),
        cron(
            reactivation_45d,
            name="reactivation_45d",
            minute=0,
            hour={0, 6, 12, 18},  # every 6h
        ),
        cron(
            maintenance_90d,
            name="maintenance_90d",
            minute=0,
            hour={0, 12},  # every 12h
        ),
        # --- Agenda crons ---
        cron(
            deposit_reminder_24h,
            name="deposit_reminder_24h",
            minute=15,  # :15 every hour
        ),
        cron(
            appointment_reminder_24h,
            name="appointment_reminder_24h",
            minute=30,  # :30 every hour
        ),
        cron(
            appointment_reminder_2h,
            name="appointment_reminder_2h",
            minute={0, 15, 30, 45},  # every 15min
        ),
        # --- Fidelización NPS cron ---
        cron(
            nps_request_24h_post_appointment,
            name="nps_request_24h_post_appointment",
            minute=45,  # :45 every hour
        ),
        # --- Marketing crons ---
        cron(
            brand_studio_audit_30d,
            name="brand_studio_audit_30d",
            hour=3,
            minute=0,  # daily 03:00 UTC
        ),
        cron(
            lucas_weekly_recommendations,
            name="lucas_weekly_recommendations",
            weekday="mon",
            hour=4,
            minute=0,  # weekly Monday 04:00 UTC
        ),
        # --- Inbox / channel sync ---
        cron(
            channel_sync_state_15min,
            name="channel_sync_state_15min",
            minute={0, 15, 30, 45},  # every 15min
        ),
        # --- HIPAA-lite retention sweep ---
        cron(
            audit_log_retention_sweep_monthly,
            name="audit_log_retention_sweep_monthly",
            day=1,
            hour=2,
            minute=0,  # monthly 1st 02:00 UTC
        ),
        # --- Marketing Wave 3 crons (T-mk-be-6) ---
        cron(
            channel_metrics_sync_meta,
            name="channel_metrics_sync_meta",
            minute=0,
            hour={0, 4, 8, 12, 16, 20},  # every 4h
        ),
        cron(
            channel_metrics_sync_google,
            name="channel_metrics_sync_google",
            minute=2,  # offset 2min from meta to avoid DB contention
            hour={0, 4, 8, 12, 16, 20},  # every 4h
        ),
        cron(
            lucas_daily_analysis_sweep,
            name="lucas_daily_analysis_sweep",
            hour=6,
            minute=0,  # daily 06:00 UTC
        ),
        cron(
            referrals_value_sync,
            name="referrals_value_sync",
            hour=10,
            minute=0,  # daily 10:00 UTC
        ),
    ]

    redis_settings: RedisSettings = _redis_settings()
    keep_result: int = 3600  # 1h result retention per spec
    max_jobs: int = 50  # max concurrent jobs per spec
    health_check_interval: int = 30  # seconds between health checks per spec

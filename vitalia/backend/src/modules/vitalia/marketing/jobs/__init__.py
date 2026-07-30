# cap: marketing.attribution-matrix-4-origins
# story-origin: TBD
"""Marketing cron jobs — 4 ARQ jobs decorated with engine @cron_envelope.

All jobs:
  - Use @cron_envelope from luana_core_platform.workers.cron_envelope (NOT deprecated brand-local idempotent_cron)
  - Soft-fail per tenant/clinic (one failure does not abort the whole cron)
  - Publish domain events via luana_core_events outbox adapter_bus
  - Sanitize payloads before observability writes (compliance_level=hipaa_lite)
  - Dual filter tenant_id + clinic_id on all DB queries (HIPAA-lite rule)

Jobs:
  channel_metrics_sync_meta    — every 4h — pull Meta Ads metrics
  channel_metrics_sync_google  — every 4h — pull Google Ads metrics
  lucas_daily_analysis_sweep   — daily 06:00 UTC — regenerate Lucas recommendations
  referrals_value_sync         — daily 10:00 UTC — refresh referral conversion values
"""

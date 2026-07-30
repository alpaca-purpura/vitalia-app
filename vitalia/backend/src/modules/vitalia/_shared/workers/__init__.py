# cap: __shared__
# story-origin: TBD
"""Vitalia ARQ workers package.

Contains:
  - arq_settings.py     WorkerSettings for ARQ runner (11 cron jobs)
  - base.py             idempotent_cron decorator (tracing + idempotency + audit)
  - jobs/               Individual cron job scaffolds (11 functions)

downstream-regression-na: brand-local worker package; no cross-brand consumers
"""

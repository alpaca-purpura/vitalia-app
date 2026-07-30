"""Cross-module ARQ workers (F3+).

Owns workers that don't belong to a single bounded context — e.g. the
brand-summary lighthouse regen task fans out from a brand domain event
but writes the per-tenant summary that the *copilot* consumes.

Engine utilities (promotion lifts):
  - cron_envelope: idempotent + OTel + structlog + Sentry decorator for ARQ cron jobs.
    Lifted from vitalia/_shared/workers/base.py per proposal
    2026-05-20-core-platform-extensions-slice-1.md.
"""

from luana_core_platform.workers.cron_envelope import cron_envelope

__all__ = ["cron_envelope"]

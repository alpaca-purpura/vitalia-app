# cap: __shared__
# story-origin: TBD
"""Vitalia brand-local observability utilities.

Provides OpenTelemetry tracing setup + span helpers for:
  - Cron job spans (11 named ARQ worker spans)
  - Agent turn spans (cost attrs + PHI sanitization)
  - Sentry alert rule declarations

Anti-duplication rule adherence:
  - sanitize_payload IMPORTED from luana_core_observability (never mirrored)
  - sanitize_phi_payload IMPORTED from compliance_service_adapter (never mirrored)
  - No local PII regex patterns

Per .claude/rules/anti-duplication.md § Observability shared abstractions.

downstream-regression-na: brand-local observability package; no cross-brand consumers
"""

from __future__ import annotations

__all__ = [
    "build_otel_resource",
    "setup_otel",
    "maybe_init_sentry",
    "cron_span",
    "CRON_SPAN_NAMES",
    "agent_turn_span",
    "AgentSpanContext",
]

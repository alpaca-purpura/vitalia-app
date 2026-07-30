# cap: __shared__
# story-origin: TBD
"""Sentry alert rule configurations (declarative) for Vitalia.

Defines alert thresholds as dataclasses for documentation + runtime config.
These are NOT Sentry API calls — they are declarative config that can be
consumed by infrastructure-as-code (Terraform/Sentry CLI) or exported
to Sentry via management commands.

Alert rules per T-infra-5 spec:
  1. cost_runaway_per_tenant  — >5 USD/h triggers critical alert
  2. cron_failure_rate        — >10% failure rate in 1h window
  3. agent_cache_hit_rate     — <0.40 over 100 turns triggers warning

Usage (documentation / infra-as-code consumption):
    from src.modules.vitalia._shared.observability.sentry_alerts import VITALIA_ALERT_RULES
    for rule in VITALIA_ALERT_RULES:
        print(f"{rule.name}: {rule.description}")

Anti-patterns avoided:
  ❌ No hardcoded Sentry API tokens
  ❌ No runtime Sentry API calls (declarative only)
  ❌ No PHI in alert rule definitions

downstream-regression-na: brand-local alert config; no cross-brand consumers
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AlertSeverity = Literal["critical", "warning", "info"]


@dataclass(frozen=True)
class SentryAlertRule:
    """Declarative Sentry alert rule configuration.

    Attributes:
        name: Rule identifier (snake_case). Used as key in VITALIA_ALERT_RULES.
        description: Human-readable description (Spanish neutro LatAm).
        metric: OTel metric or custom measurement name.
        threshold: Numeric threshold value that triggers the alert.
        threshold_type: "above" or "below" (relative to threshold).
        window_minutes: Rolling window for metric aggregation (minutes).
        min_events: Minimum sample count before rule activates.
        severity: Alert severity level.
        channel: Notification channel slug (e.g. "slack-vitalia-critical").
    """

    name: str
    description: str
    metric: str
    threshold: float
    threshold_type: Literal["above", "below"]
    window_minutes: int
    min_events: int
    severity: AlertSeverity
    channel: str = "slack-vitalia-alerts"


# ---------------------------------------------------------------------------
# Vitalia alert rule catalog
# ---------------------------------------------------------------------------
VITALIA_ALERT_RULES: tuple[SentryAlertRule, ...] = (
    SentryAlertRule(
        name="cost_runaway_per_tenant",
        description=(
            "Alerta crítica: costo LLM por tenant supera 5 USD/hora. "
            "Posible bucle de agente o ataque de prompt injection."
        ),
        metric="agentic.cost_usd",
        threshold=5.0,
        threshold_type="above",
        window_minutes=60,
        min_events=1,
        severity="critical",
        channel="slack-vitalia-critical",
    ),
    SentryAlertRule(
        name="cron_failure_rate",
        description=(
            "Alerta crítica: tasa de fallo de cron jobs supera 10% en 1 hora. "
            "Verificar conectividad de base de datos y servicios externos."
        ),
        metric="cron.failure_rate",
        threshold=0.10,
        threshold_type="above",
        window_minutes=60,
        min_events=10,
        severity="critical",
        channel="slack-vitalia-critical",
    ),
    SentryAlertRule(
        name="agent_cache_hit_rate",
        description=(
            "Alerta de advertencia: tasa de cache hit de agente por debajo de 40% "
            "en las últimas 100 interacciones. Revisar estructura de prompt cache "
            "slots 1-5 (sistema + dominio + herramientas + persona + voz de marca)."
        ),
        metric="agentic.cache_hit_rate",
        threshold=0.40,
        threshold_type="below",
        window_minutes=0,  # event-count based, not time-based
        min_events=100,
        severity="warning",
        channel="slack-vitalia-alerts",
    ),
)

# Convenience dict for lookup by name
VITALIA_ALERT_RULES_BY_NAME: dict[str, SentryAlertRule] = {rule.name: rule for rule in VITALIA_ALERT_RULES}

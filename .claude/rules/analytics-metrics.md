# Analytics Metrics Architecture

> **Slim pointer (W1-Phase2 eviction 2026-06-09 · tier: project).** Cuerpo operativo + ex-always-on body en `metrics-expert` skill → `references/analytics-metrics.md` — cargalo ANTES de tocar analytics (engine o brand).

Trigger: `core/luana-core-analytics-engine/**` · `{brand}/backend/src/modules/{brand}/analytics/**` · `{brand}/frontend/src/features/marketing/**`.

No-skip 1-liner: stage services = SSoT data (MetricsService NO computa stage metrics) · `_GROUP_MAP` solo en engine `constants.py` · channels via `ChannelRegistry` engine · brand opt-in via Extension SDK — NUNCA mirror per-brand. Engine change → `/pm-luana` promotion gate.

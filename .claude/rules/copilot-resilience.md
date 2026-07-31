# Copilot Resilience

> **Slim pointer (W1-Phase2 eviction 2026-06-09 · tier: project).** Cuerpo operativo + ex-always-on body en `copilot-expert` skill → `references/copilot-resilience.md` — invocá el skill ANTES de tocar copilot.

Trigger: `core/luana-core-copilot/**` (engine — cambio directo con flujo `/pm-vitalia` + arch tests) · `vitalia/backend/src/modules/vitalia/copilot/**` (brand extension) · bug copilot reportado. El hook `contract-guard.js` recuerda `module_registry.py`.

No-skip 1-liner: diagnóstico copilot SIEMPRE empieza con query a `copilot_trace_event` — sin trace = bug de observabilidad, fix recorder primero (engine).

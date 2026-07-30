# ETL Extraction Contract

> **Slim pointer (W1-Phase2 eviction 2026-06-09 · tier: project).** Cuerpo operativo + ex-always-on body en `metrics-expert` skill → `references/etl-extraction-contract.md` — cargalo ANTES de tocar ETL.

Trigger: providers/pipeline/etl_service/scheduler/workers/catalog en `core/luana-core-analytics-engine/**` o `{brand}/.../analytics/providers/**`. El hook `contract-guard.js` recuerda los comandos al tocar estas surfaces.

No-skip 1-liner: antes de cualquier ETL question leer `core/luana-core-analytics-engine/docs/extraction-contract.md` PRIMERO (auto-gen, NUNCA edit manual) · todo cambio dispara los 5 pasos (implement → contract → catalog → `make extraction-contract` → suite engine + brands). Sin excepciones.

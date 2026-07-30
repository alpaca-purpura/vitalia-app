# Anti-Default-Flip Audit

> **Slim stub (context-rot pass 2026-05-30).** Detalle operativo completo (4 steps verbatim con grep/run commands cross-sistema, ejemplos CORRECTO/INCORRECTO commit body, enforcement layers 7, penalizaciones, multisistema awareness) en `docs/rules-detail/anti-default-flip-audit.md` — load on-demand. **Origen:** failed `/pase-produccion` 2026-05-04 (commit `64738354` flipeó `USE_OUTBOX_PATTERN_*` False→True sin auditar → 25 BE failures + ~3h + ~500k tokens).

## Regla cardinal

ANTES de flipear default de feature flag (`USE_*_PATTERN_*`, `USE_DEEPAGENTS_*`, `ENABLE_*`, etc.) que cambia call path side-effect → **OBLIGATORIO 4 STEPS:** (1) grep tests path viejo cross-codebase, (2) update mocks al path nuevo, (3) run full suite con AMBOS valores flag, (4) documentar commit body con sección `## Tests audited`. Si UNO falla → STOP.

## Inventario flags side-effect (SSoT — actualizar al agregar nuevos)

| Flag | Default actual | Side-effect path |
|---|---|---|
| `USE_OUTBOX_PATTERN_SALES_AGENT` | `True` (post 2026-04-29) | events emission (`EventBus.publish` → `outbox.adapter_bus.publish`) |
| `USE_OUTBOX_PATTERN_COPILOT` | `True` (post 2026-04-29) | idem |
| `USE_OUTBOX_PATTERN_BRAND` | `True` (post 2026-04-29) | idem |
| `USE_OUTBOX_PATTERN_DEFAULT` | `False` | events emission fallback |
| `USE_DEEPAGENTS_*` (futuros) | TBD | agent orchestration (LangGraph plain → deepagents `task`) |

> `LITELLM_PROXY_ENABLED` removido PI-12 S1 T-5 (legacy adapters deleted — proxy es el único path LLM).

**Al agregar nuevo flag side-effect → editar esta tabla en el mismo commit.**

## Cuándo carga el detalle

- Step 1 grep commands verbatim (ejemplos concretos `USE_OUTBOX_PATTERN_*`, `OpenAIService`)
- Step 3 run commands por cada marca activa (loop sobre el enum de marcas)
- Step 4 commit body template completo

## Anti-patterns (top 3 — lista completa en el detalle)

- ❌ Flipear default sin grep tests path viejo (Step 1 omitido)
- ❌ Flipear default sin run full suite con ambos valores (Step 3 omitido)
- ❌ Agregar nuevo flag side-effect sin actualizar inventario SSoT

## Referencias

- `docs/rules-detail/anti-default-flip-audit.md` — **detalle completo** (steps verbatim, ejemplos CORRECTO/INCORRECTO, enforcement 7 layers)
- `.claude/rules/tdd-mandatory.md` § Default flag flips
- `.claude/rules/auditor-downstream-regression.md` — Step 1 grep tests path viejo (ortogonal)
- `docs/promotion-protocol/README.md` — workflow sistema→core lift gate

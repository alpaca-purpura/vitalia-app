# Dispatch plan — platform-lift-sales-agent-graph-runtime (Phase 1: ESC-4/5/6)

## autonomous_mode
- value: **false**  (engine + agentic = stake-asimétrico · R23 · Chris ratifica entre fases)
- chain_if_true: N/A
- caps: {iterations: 8, audit_iter: 3, walltime: 60min}

> ★ Los 3 diffs están PROBADOS por el architect (RED→GREEN + no-regression). El builder aplica los exactos (03-arch § TL;DR) + crea los arch tests proven (verified-arch-tests.md). Trabajo real ≈ aplicar + TDD + crear tests + correr gates. Est. bajas a propósito.

## Ticket → Agent → Model matrix
| T-id | ESC | Surface | Files | Agent | Model | Est. |
|---|---|---|---|---|---|---|
| T-ESC4 | relationship ambiguity (BLOCKER) | crm.py **(1 línea · UNILATERAL)** + arch test subproceso | 1 edit + 1 test | builder-agentic | flagship | 20min |
| T-ESC5 | templates cwd-independent | sales-agent prompts/base.py `__init__` + arch test | 1 edit + 1 test | builder-agentic | flagship | 15min |
| T-ESC6 | prompt_versions.tenant_id | prompt_version_model.py +columna + arch test | 1 edit + 1 test (+ valida migration_notes) | builder-agentic | flagship | 15min |
| T-DEBT1 | fix import test stale (independiente) | test_chat_orchestrator_snapshot.py (1 línea L27) | 1 edit | builder-agentic | workhorse | 10min |

> **Por qué flagship (no workhorse):** los 3 ESC viven en/alrededor del engine `sales_agent` y su blast radius es el mapper init + prompt load de **las 4 marcas**. No es BE non-agentic común (no aplica el anti-pattern "flagship para BE simple"). Stake-asimétrico → flagship.

## DAG
```
T-ESC4 (blocker primario · mapper init) ──┬──> T-ESC5
                                          └──> T-ESC6
T-DEBT1 (independiente · test-only)  ─── correr antes del gate sales_agent_suite_canonical
```
Mismo engine package (sales_agent) → serializar por WIP cap módulo (T-DEBT1 → T-ESC4 → T-ESC5 → T-ESC6 · orden sugerido: T-DEBT1 primero deja la suite colectando limpia).

## Verificación (cada ticket · PYTHONPATH override obligatorio)
- arch test RED-first del ESC + suites engine (sales-agent + platform) + ruff.
- **Cierre Phase 1:** downstream regression ×4 (vitalia/nicolify/comunify verde con engine editado + PYTHONPATH override; lupulo skip documentado).

## Scope discipline
- forbidden: `{brand}/**` (cero marca) · `*/backend/alembic/versions/**` (migración brand-authored) · `application/**` + `prompts/templates/**` (comportamiento del agente) · copilot prompts/base.py (sibling fuera de scope).
- non-egoísmo: bug visto fuera de scope (ej. copilot sibling, LeadModel engine-interno) → flag en T-{id}-impl-log + `/harness-issue`, NO arreglar inline.

## Invocation manual (autonomous_mode:false)
```
/dev-team platform: T-ESC4            # arranca el blocker
# tras GREEN T-ESC4: /dev-team platform: T-ESC5 ; luego T-ESC6
# tras 3 GREEN + downstream ×4: developed → Chris ratifica → /pm-luana migrate (merge main + sync vitalia)
```

## Cierre real (no "arch verde")
El bar es el **efecto runtime**: tras merge a main + sync a vitalia, el grafo sales_agent corre live (mensaje Telegram → reply de Adrián). Lo ejerce/verifica Chris. Recién con eso cerrado → Phase 2 (ESC-1/2/3 features).

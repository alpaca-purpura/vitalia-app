# Dispatch plan — vitalia-crm-phi-base-tables-migration

## autonomous_mode
- value: **false** (HARD)
- reason: migración de tablas PHI base + cifrado pgcrypto at-rest. Requiere verificación live SUPERVISADA (re-god-matrix con JWT real → 200 + audit row + raw-ciphertext) antes de cerrar. Chris ratifica el approach de reconcile + revisa evidencia live (sin KEK/PHI en logs).
- chain_if_true: N/A (no aplica — manual)
- caps: { iterations_per_ticket: 10, audit_iter: 3, cost_usd: 4.00, walltime: 90min }

## Ticket → Agent → Model → Cost matrix

| T-id | Title | Surface | Agent | Model | Est. cost | Est. time |
|---|---|---|---|---|---|---|
| T-1 | Migración 035 pgcrypto schema | BE | builder-backend | sonnet | $0.35 | 30 min |
| T-2 | Repos decrypt wiring + KEK config | BE | builder-backend | sonnet | $0.50 | 35 min |
| T-3 | Seed + integration + verificación live | BE | builder-backend | sonnet | $0.55 | 40 min |
| Total | — | — | — | — | **~$1.40** | **~105 min** |

## DAG dependencies
T-1 → T-2 → T-3 (secuencial; T-2 necesita el schema, T-3 necesita los repos cableados)

## Surfaces → builder → auditor
- Todo BE → `builder-backend` (Sonnet) → `auditor-backend` (Opus).
- NO FE. NO AGENTIC. Cero engine. Cero cross-brand.

## Playwright visual scope
- applies: false (service-story BE-only, sin UI)

## Engine boundary
- HARD: ningún ticket toca `core/luana-core-*/src/`. Reusa KEKClient brand-local existente. Sin lift /pm-luana.

## Verificación live (anti-teatro, supervisada) — gate de cierre
- T-3 NO cierra sin: doctor JWT real → /patients/{id} 200 + descifrado + audit row ; raw DB = ciphertext ; /leads 200 ; marketing 403 ; cross-tenant 404 ; logs sin 500/KEK/PHI.
- Evidencia documentada en T-3-result.md (status codes + logs sanitizados; NUNCA JWT/secret/PHI plaintext).

## Recommended invocation (manual — autonomous_mode false)
```
/dev-team vitalia: vitalia-crm-phi-base-tables-migration, ticket: T-1
# tras T-1 done → T-2 → T-3 (Chris supervisa la verificación live de T-3)
```

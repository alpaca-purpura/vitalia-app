# Dispatch plan — Story vitalia/vitalia-cockpit-live-reconciliation

## autonomous_mode
- value: false                  # default. Chris opt-in al ratificar (story toca infra + ledger cross-cutting → recomiendo supervisión humana en T-3)
- chain_if_true: [/dev-team → /auditor → /pm-vitalia merge]
- caps: {iterations: 10, audit_iter: 4, cost_usd: 6.00, walltime: 150min}
- recomendación: NO autonomous full. T-1 (boot) + T-2 (sweep) seguros para chain; T-3 (reparar+reconciliar ledger) conviene checkpoint humano por su naturaleza findings-driven + decisiones de mapear vs reparar.

## Ticket→Agent→Model→Cost matrix
| T-id | Title | Surface | Agent | Model | Est. cost | Est. time |
|---|---|---|---|---|---|---|
| T-1 | Fase 0 boot (remount core/) | INFRA | builder-frontend | sonnet | ~$0.30 | 25min |
| T-2 | Fase 1 sweep harness + matriz v1 | FE | builder-frontend | sonnet | ~$0.70 | 50min |
| T-3 | Fase 2+3 review + reparar inline + reconcile ledger | FE+BE+DOCS | builder-frontend (+builder-backend para fixes BE) | sonnet (opus si findings complejos) | ~$1.50 (iterativo) | 90min+ |
| Total | — | — | — | — | ~$2.50 | ~150min |

## DAG dependencies
T-1 → T-2 → T-3 (secuencial)

## Playwright visual scope (resumen — detalle en 04-validators § playwright_visual_scope)
- story_scope: harness nuevo en e2e/regression/live-reconciliation/ + matriz; observa todas las superficies navegables read-only.
- forbidden: `components/ui/`, `components/shared/shell-organism/`, `app/layout.tsx` (shell compartido — reparar acá rompe las 24 superficies; se MAPEA).
- non_egoismo: bug fuera de scope reparable → fila ROTO + entrada backlog F2 con evidencia. Nunca ignorar; nunca tocar shell compartido inline.

## Disciplina de scope HARD
- Cero reconstrucción de caps slice-1 (eso es Fase 2 = stories F2-S2..S22). Los findings PRIORIZAN ese backlog con evidencia.
- Cualquier fix inline que rompa un gate → revertir + mapear.

## Invocation manual (recomendado)
/dev-team vitalia vitalia-cockpit-live-reconciliation   # toma T-1; Chris revisa entre T-2 y T-3

## Invocation autonomous (opt-in Chris)
echo 'autonomous_mode: true' >> vitalia/docs/product/stories/vitalia-cockpit-live-reconciliation/checkpoint.md

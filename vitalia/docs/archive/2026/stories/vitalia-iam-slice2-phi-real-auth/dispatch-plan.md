# Dispatch plan — vitalia/vitalia-iam-slice2-phi-real-auth

## autonomous_mode
- value: **false**  (HARD — auth/PHI sensible · architect-autonomous-mode.md § "false (HARD)")
- reason: toca auth + PHI (HIPAA-lite). Build SUPERVISADO: el orchestrator (Chris) reporta en el gate de verificacion PHI con JWT real ANTES de cerrar.
- chain_if_true: N/A (no aplica — supervisado)
- caps (referencia, build supervisado): { iterations: 10, audit_iter: 3, walltime: 90min }

## Ticket -> Agent -> Model -> Cost matrix

| T-id | Title | Surface | Agent | Model | Est. cost | Est. time |
|---|---|---|---|---|---|---|
| T-1 | BE-auth core (decoder JWKS + rol DB) | BE | builder-backend | sonnet | ~$0.45 | 35 min |
| T-2 | BE repos-wire (crm/consent/marketing/inbox) | BE | builder-backend | sonnet | ~$0.50 | 40 min |
| T-3 | FE hook (rol desde /me) | FE | builder-frontend | sonnet | ~$0.20 | 20 min |
| Total | — | — | — | — | **~$1.15** | **~95 min** |

> Sin Opus: no toca copilot/sales_agent (agentic). Todo Sonnet. Engine consumido via import (cero edit).

## DAG dependencies

```
T-1 (auth core) ──┬──> T-2 (repos wire)   [secuencial: T-2 consume rol-from-DB de T-1]
                  └──> T-3 (FE hook)       [secuencial: T-3 consume /me con rol DB de T-1]
```
T-2 y T-3 pueden correr en paralelo tras T-1 (modulos distintos: code:crm/marketing/inbox vs FE).

## Playwright visual scope
- N/A — esta story NO construye sub-tab UI nueva (ADR-004 n/a-with-rationale). El unico cambio FE es a un hook existente (`useCurrentUser`), verificado por Vitest + verificacion supervisada. Sin assertions visuales/snapshots.

## Verification gate (supervisado — anti-teatro)
god-matrix con JWT real (mint Clerk Backend API contra dev-app):
- doctor.demo (Sanare) -> GET PHI **200 + audit_log row** + logs backend sin 401
- recepcion / marketing -> **403** + audit denied
- cross-tenant -> **404** ; cross-clinic -> **403**
- JWT forjado/expirado/stub-legacy -> **401**

Ejercido de verdad (writes + logs leidos), NO "saque 200 = funciona" (test-design-doctrine § Verificacion REAL).

## Recommended invocation (manual — supervisado)

```
/dev-team vitalia, ticket: T-1       # Chris arranca; al cerrar T-1 -> T-2 + T-3
# Chris ratifica en el gate de verificacion PHI antes de transition a done.
```

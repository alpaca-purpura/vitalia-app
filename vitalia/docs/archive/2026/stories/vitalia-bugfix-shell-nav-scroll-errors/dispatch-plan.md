# Dispatch plan — vitalia-bugfix-shell-nav-scroll-errors

## autonomous_mode
- value: **true**   (PROPUESTO por /architect · RATIFICADO por Chris vía directiva "solucionarlos hasta el done" 2026-06-02)
- chain_if_true: [/dev-team → /auditor → (PAUSA demo) → /pm-vitalia merge]
- caps: {iterations: 10, audit_iter: 3, cost_usd: 4.00, walltime: 90min}
- **ceiling (no evitable):** `reviewing → done` exige `dod_evidence` (dev-app live) + `demo_signoff` de
  Chris (DoD #37 §5, demo_required:true). La cadena autónoma llega hasta dejar todo verificado +
  `demo-script.md` listo y **PAUSA pidiendo a Chris el demo paso a paso**. Nadie más cierra `done`.

## Ticket → Agent → Model → Cost matrix

| T-id | Bug | Title | Surface | Agent | Model | Est. cost | Est. time |
|---|---|---|---|---|---|---|---|
| T-1 | #1 | Routing → mateo/agenda | FE | builder-frontend | sonnet | $0.25 | 20min |
| T-2 | #4 | Scroll overflow-y-auto | FE | builder-frontend | sonnet | $0.15 | 15min (+ live) |
| T-3 | #7 | [agent]/error.tsx genérico | FE | builder-frontend | sonnet | $0.30 | 25min |
| T-4 | #2 | Tenant selector (repro-first) | FE | builder-frontend | sonnet | $0.40 | 30min (+ repro) |
| T-5 | #5 | Quitar banner landing | FE | builder-frontend | sonnet | $0.15 | 12min |
| T-6 | #3 | Quitar títulos redundantes | FE | builder-frontend | sonnet | $0.35 | 25min |
| Total | — | — | FE | — | sonnet | ~$1.65 | ~95min |

(Opus NO requerido — cero AGENTIC, cero core. R23 no aplica.)

## DAG
- Paralelizables: T-1 · T-2 · T-3 · T-4
- Secuencial: T-5 → T-6 (ambos tocan `PresenciaView.tsx`)

## Repro-first (ADR-011)
- **Estático ya confirmado:** T-5 (#5), T-6 (#3), T-1 (#1 — regresión paradigm-map-zones).
- **Repro LIVE obligatorio antes de fix:** T-4 (#2 — causa raíz no determinable estática), T-2 (#4),
  T-3 (#7). dev-team reproduce en dev-app (Chrome MCP) + captura evidencia.

## Playwright visual scope
- story_scope_routes: `/{tid}` · `/{tid}/mateo/agenda` · `/{tid}/lisa/marca/{presencia,identidad}` · `/{tid}/lucas/lanzar`
- forbidden: `components/ui/`, `features/lisa/components/staff/` (lisa-doctores), `app/layout.tsx`
- non-egoísmo: bug #3 en lisa/staff → impl-log para lisa-doctores, NO inline

## Invocation
- Manual: `/dev-team vitalia vitalia-bugfix-shell-nav-scroll-errors`
- Autonomous (ratificado): /dev-team toma T-1..T-6 → auto-handoff /auditor → PAUSA demo Chris → /pm-vitalia merge

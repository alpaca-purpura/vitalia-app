---
story_id: vitalia-fase2-adrian-embudo
schema_version: v4.1
generated_by: /architect
generated_on: 2026-06-03
autonomous_mode: true            # ★ Chris ratificó (architect→dev-team→auditor→[demo_signoff]→merge)
---

# dispatch-plan.md — Embudo de Adrián

> Plan de despacho para `/dev-team`. `autonomous_mode: true` (Chris ratificó). Único gate humano = `demo_signoff` (Chris) en T-DEMO-1 → `/pm-vitalia merge`.

## autonomous_mode: true

- **Ratificado por Chris** (checkpoint `ratified_by_chris: true` + prompt "autonomous hasta done").
- Pipeline: `/architect (✓ done)` → `/dev-team` (build 9 tickets) → `/auditor` (review per surface) → fix-loop (cap 2 iter) → **[GATE demo_signoff Chris]** → `/pm-vitalia merge`.
- Sin Chris-trigger manual entre tickets. AUTO-HANDOFF story-closure-gate.

## Caps

| Cap | Valor |
|---|---|
| `self_fix_iter` (auditor Carril A) | ≤ 5 |
| `audit_iterations` total | ≤ 4 |
| fix-loop dev-team (CHANGES_REQUESTED) | ≤ 2 iter |
| wall-clock por auditor | ≤ 30 min |
| WIP cap module `code:crm` | ≤ 1 story developing/developed/reviewing (esta ocupa el bucket) |

## Ticket → agent → model → auditor → cost matrix

| Ticket | primary_agent | model | auditor | production_code | costo est. |
|---|---|---|---|---|---|
| T-BE-1 | builder-backend | sonnet | auditor-backend (opus) | true | medio |
| T-BE-2 | builder-backend | sonnet | auditor-backend (opus) | true | alto (API + services) |
| T-AG-1 | **builder-agentic** | **opus** (R23 HARD) | auditor-agentic (opus) | true | medio (wire thin) |
| T-FE-1 | builder-frontend | sonnet | auditor-frontend (opus) | true | bajo (primitivas) |
| T-FE-2 | builder-frontend | sonnet | auditor-frontend (opus) | true | alto (board+drag) |
| T-FE-3 | builder-frontend | sonnet | auditor-frontend (opus) | true | alto (workspace+nuevo+recuperar) |
| T-E2E-1 | builder-frontend | sonnet | auditor-frontend (opus) | false | medio (goldens) |
| T-DEMO-1 | builder-frontend | sonnet | (Chris sign-off) | false | bajo |

> R23: T-AG-1 es el ÚNICO ticket Opus (AGENTIC production_code). Resto Sonnet (BE/FE no-agentic) → cost-routing optimizado.

## DAG (orden de spawn)

```
Wave 0 (paralelo):   T-BE-1  ┐         T-FE-1  ┐
                            │                 │
Wave 1:              T-BE-2 ◄┘                 │
                       │                       │
Wave 2 (paralelo):   T-FE-2 ◄──────────────────┤ (dep T-BE-2 + T-FE-1)
                     T-FE-3 ◄──────────────────┤
                     T-AG-1 ◄─ (dep T-BE-2)     │
                       │                        │
Wave 3:              T-E2E-1 ◄─ (dep T-FE-2 + T-FE-3)
                       │
Wave 4 (gate humano): T-DEMO-1 → demo_signoff Chris → /pm-vitalia merge
```

- **Wave 0**: T-BE-1 (BE foundation) + T-FE-1 (FE primitivas) arrancan juntos (sin dep mutua; distinto bucket lock: `code:crm` BE vs FE files).
- **Wave 1**: T-BE-2 tras T-BE-1.
- **Wave 2**: T-FE-2, T-FE-3, T-AG-1 en paralelo (todos dep T-BE-2; T-FE-* también T-FE-1). 3 lanes.
- **Wave 3**: T-E2E-1 (goldens + integration) tras los 2 FE.
- **Wave 4**: T-DEMO-1 (live-verify + demo-script) → **gate demo_signoff Chris** → merge.

## Playwright visual scope

- **story_scope_routes**: `/adrian/embudo`, `/adrian/embudo/[leadId]/resumen`, `/adrian/embudo/[leadId]/historial`, `/adrian/embudo/nuevo`, `/adrian/recuperar`.
- **story_scope_components**: `features/adrian/components/{embudo,recuperar}/**`, `components/shared/score/ScoreDonut.tsx`, `components/shared/shell-organism/ChannelBadge.tsx` (extend), `lib/channels/channel-meta.ts`.
- **forbidden_screenshot_scope**: `components/ui/**`, wrappers shell shipped (EntitySubNavBar/TopBar/Ribbon/SubTabsBar/ValeriaSidebar), otras features.
- **non_egoismo_clause**: bug en wrapper shipped → `vitalia/docs/observed-bugs/`, NO arreglar fuera de scope.
- **goldens D.16**: 8 componentes × {light,dark} (+ override-dialog single + EntitySubNavBar reusa golden doctores). `maxDiffPixelRatio 0.001`, ratchet shrink-only.

## Invocation

```
/dev-team con <brand>: vitalia
  → spawn Wave 0: builder-backend(T-BE-1) + builder-frontend(T-FE-1)
  → ... DAG arriba ...
  → cada ticket cerrado: AUTO-HANDOFF auditor-{surface}
  → APPROVED all → T-DEMO-1 → demo_signoff Chris → /pm-vitalia merge (reviewing→done)
```

## Gate humano único (autonomous_mode)

`demo_signoff` (Chris) en T-DEMO-1. `/pm-vitalia merge` REFUSE si:
- `dev_app_verified.evidence` vacío (ADR-008), O
- `demo_signoff.result ∉ {APPROVED, APPROVED_WITH_NOTES(severity≤medium)}`.

## Riesgos de dispatch

- **FE→BE path** (§ Open Questions #1): T-BE-2 notes_for_downstream obliga a confirmar el path servido en dev-app antes de cablear FE. Si `/api/v1/vitalia/crm` no resuelve → flag a /pm-vitalia (posible bug del inbox leads, fuera de scope).
- **Next 16 soft-nav redirect** (`[leadId]→resumen`): si flakea "Rendered more hooks", mover a edge-redirect (MEMORY next16-softnav). T-FE-3 verifica live.
- **@dnd-kit × React 19**: ya instalado; T-FE-2 verifica smoke + KeyboardSensor.

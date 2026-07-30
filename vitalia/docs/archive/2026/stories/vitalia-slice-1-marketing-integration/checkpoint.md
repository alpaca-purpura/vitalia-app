---
story_id: vitalia-slice-1-marketing-integration
outcome: vitalia-mvp-ui-foundation
parent_story: vitalia-slice-1-marketing (archived 2026-05-21, merged fa921711)
state: dropped
dropped_at: 2026-05-22
dropped_reason: "Paradigma shell-organism agéntico cementado 2026-05-22 elimina sidebar tradicional + dashboard route legacy. Los 3 scope items del story original son absorbidos o eliminados: (1) Sidebar nav link `/marketing` → SIDEBAR TRADICIONAL ELIMINADO (paradigma usa Ribbon 6-tabs + Valeria sidebar agéntica). Marketing dispersado en Lucas (Lanzar/Envuelo/Recursos/Resultados/Mercado) sin necesidad sidebar link. (2) Dashboard `SliceOneStubsRow.tsx` placeholder → DASHBOARD HOME ELIMINADO (paradigma redirect inmediato a `lisa/marca` default). (3) Tailwind v4 runtime issue → ABSORBIDO POR F1-S0 vitalia-fase1-stack-stability (story blocker hard Fase 1 incluye verificación empírica Tailwind v4 + browser visual check). Story ya no aplica."
phase: DROPPED
spawned_at: 2026-05-21
spawned_by: /pm-vitalia (post-mortem visual verification gap)
spawned_reason: "vitalia-slice-1-marketing shipped state=done con merge fa921711 PERO no integrado a app real — sidebar nav no linkea + dashboard sigue mostrando placeholder + Tailwind no renderiza en runtime. Caso documentado en vitalia/docs/learnings/2026-05-21-auto-handoff-deferred-e2e-blocker.md (promotable: yes cross-brand process gap)."
parallel_safe: true
ola_assigned: null
priority: low                                                # post-drop reduced from high
estimated_dev_weeks: 0
blockers: []
side_story_blockers: []
ratified_drop_by_chris: true                                # post 2026-05-22 ratification
absorbed_by:
  - vitalia-fase1-stack-stability                           # ★ Tailwind v4 diag (F1-S0)
process_learnings_preserved:
  - vitalia/docs/learnings/2026-05-21-auto-handoff-deferred-e2e-blocker.md  # promotable cross-brand process gap
next_action: "NONE — dropped. Tailwind v4 verification absorbido en F1-S0 vitalia-fase1-stack-stability. Process learning manual-visual-verification preservado en learnings/."

# Schema v2 migration (cement 2026-05-27)
release: F0   # release ID · ver releases/
cap_target: null   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
---

# vitalia-slice-1-marketing-integration — checkpoint

## Goal

Integrar el módulo marketing (shipped 2026-05-21 commit `fa921711`) al app shell real de Vitalia. La story padre dejó código aislado (componentes + route + tests) pero los 3 puntos de integración con la app NO se ejecutaron:

1. **Sidebar nav** (`vitalia/frontend/src/components/shared/shell/Sidebar.tsx`) no incluye link a `/marketing`
2. **Home dashboard** (`vitalia/frontend/src/features/dashboard/components/SliceOneStubsRow.tsx`) sigue mostrando "Marketing·pronto" como placeholder coming-soon en vez de marcarlo como live
3. **Tailwind v4 runtime** — bug ortogonal: HTML renderiza sin estilos aplicados (capture user 2026-05-20). Puede ser cause del DEFERRED E2E original (Turbopack stack instability). Diagnosis bloqueador real Slice 1 más allá de marketing.

## Symptom origen (user reportado 2026-05-20 23:00)

Captura `/home/chalreme/Imágenes/Captura de pantalla de 2026-05-20 20-43-51.png`:
- URL: `dev-app.vitalialat.com/#main-content` (home, no marketing)
- Sidebar: `Inicio · Pacientes · Agenda · Tratamientos · Pagos · Copiloto` (6 items, marketing ausente)
- Dashboard: cards "·pronto" incluyendo "Marketing·pronto"
- Estilos: unstyled HTML (Tailwind no aplica — fonts default browser, no design tokens)

## Scope tickets propuestos (sujeto a refinement)

| Ticket | Surface | Estimate | Scope |
|---|---|---|---|
| T-mki-1 | frontend | 30 min | Add `{ label: "Marketing", href: "/marketing", icon: ... }` a `Sidebar.tsx::DEFAULT_NAV_ITEMS` + arch fitness test que enforce coverage de all live routes |
| T-mki-2 | frontend | 20 min | Remove `MarketingStub` card de `SliceOneStubsRow.tsx` (o flip a `status: live` si el patrón soporta). Update tests dashboard. |
| T-mki-3 | frontend | 1-2h | Diagnosticar Tailwind v4 runtime issue. Posibles causas: (a) PostCSS config missing, (b) CSS bundle no compila en dev, (c) Turbopack regress, (d) cookie/SW stale. Reproducir con `make dev-vitalia` fresh state. |
| T-mki-4 | docs/process | 30 min | Update `.claude/rules/story-closure-gate.md` con Layer 8 (deferred-e2e blocker gate). Coordinated con `/pm-luana` si cross-brand lift. |
| T-mki-5 | qa | 1h | Manual visual verification: navegar a `/marketing` post fixes, capturar screenshot Bowtie + Lucas cards + Attribution + Referrals + Channels render. Anexar a `06-audit/manual-verification.md`. |

## Estimated total

~3-5h dev wall-clock. Audit cycle estimado 1 iter (cambios triviales, sin cascading defects esperados).

## Why this matters más allá de marketing

Si Tailwind v4 no renderiza tokens en runtime, **TODAS las stories Slice 1 (Inbox + Pipeline + Agenda + Fidelización + Marketing) van a verse rotas** cuando se naveguen al stack real, incluso aunque sus tests unit/arch/Gherkin pasen. El gap del marketing es la primera evidencia visible — el resto puede estar igual de roto y nunca lo detectamos porque el E2E está DEFERRED uniformemente.

→ T-mki-3 (Tailwind diag) es probablemente el ticket más importante de la story, no T-mki-1 trivial.

## Process gate nuevo cemented post-story

Una vez T-mki-4 mergeado:
- `/dev-team` Step 4.5 — verifica deferred count visual/e2e. Si > 0 → STOP en `developed`, ping orchestrator
- Orchestrator (Opus) — requiere manual visual verification ANTES de auto-handoff a auditor cuando deferred presente
- Si Chris ratifica skip → learning auto-emitido con severity HIGH + risk_accepted

Este gate impide que vitalia-slice-1-{pipeline,agenda} (próximas en pipeline) se repitan el mismo patrón.

## Referencias

- Learning origen: `vitalia/docs/learnings/2026-05-21-auto-handoff-deferred-e2e-blocker.md`
- Story padre archive: `vitalia/docs/archive/2026/stories/vitalia-slice-1-marketing/` (29 commits, merge fa921711)
- Bug Turbopack relacionado: `vitalia/docs/learnings/2026-05-20-docker-frontend-ram-turbopack-issue.md`
- Process SSoT actual (gap): `.claude/rules/story-closure-gate.md` (no contempla deferred e2e)
- Paradigm cementado: `docs/architecture/luana-platform/ADR-007-paradigm-v4.1-autonomy.md`

## Bitácora drop 2026-05-22

- **DROPPED:** paradigma shell-organism agéntico cementado 2026-05-22 (outcome v2.0) elimina sidebar tradicional + dashboard route legacy.
- Tailwind v4 diagnóstico (T-mki-3) absorbido en `vitalia-fase1-stack-stability` (F1-S0 · blocker hard de toda Fase 1 · ejecuta `make dev-vitalia` + browser visual check empírico).
- Sidebar nav (T-mki-1) y Dashboard placeholder (T-mki-2) no aplican: paradigma usa Ribbon 6-tabs + Valeria sidebar agéntica · NO sidebar tradicional.
- Process learning manual-visual-verification (T-mki-4) preservado en `vitalia/docs/learnings/2026-05-21-auto-handoff-deferred-e2e-blocker.md` (promotable cross-brand).
- Ratified Chris 2026-05-22 (HANDOFF-session-2026-05-22.md plan completo).

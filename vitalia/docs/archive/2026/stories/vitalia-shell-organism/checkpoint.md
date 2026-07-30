---
story_id: vitalia-shell-organism
type: design-story                                  # categoría especial — NO produce código, produce SSoT funcional + plan
phase: PLANNING_COMPLETE
state: done
last_artifact: 07-merge.md
last_modified: 2026-05-22
ratified_by_chris: true
parallel_safe: true
priority: critical
estimated_dev_weeks: 0 (planning-only)
deliverables:
  - mockup_html: "vitalia/docs/product/stories/vitalia-shell-organism/mockups/dual-mode-shell.html"
  - design_contract: "vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md"
  - story_template: "vitalia/docs/specs/templates/01-spec-shell-template.md"
  - navigation_tree: "vitalia/docs/product/stories/vitalia-shell-organism/navigation-tree.md"
  - baseline_decisions: "vitalia/docs/product/stories/vitalia-shell-organism/00-session-baseline.md"
  - backlog_generated: "24 stories Fase 1 (11) + Fase 2 (22) + 2 service-stories laterales + 3 refactors + 1 drop"
spawned_at: 2026-05-21
transitioned_done_at: 2026-05-22
spawned_by: chris (sesión Q1-Q7 ratificación)
closed_by: /pm-vitalia

# Schema v2 migration (cement 2026-05-27)
release: F0   # release ID · ver releases/
cap_target: null   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# vitalia-shell-organism — checkpoint

## Goal

Cementar el paradigma "shell-organism agéntico" para Vitalia: 5 empleados-IA tab (Lisa · Lucas · Adrián · Valeria · Camila) + 1 Configurar admin · panel Valeria chat persistente 50% izq · panel App 50% der con ribbon + sub-tabs + contenido per agente. Producir el backlog completo de migración Fase 1 (shell esqueleto) + Fase 2 (sub-tabs activas).

## Estado final

✅ **17 decisiones cementadas** (Q1-Q7 + sub-Qs) — ver `00-session-baseline.md` § 5
✅ **Mockup HTML ratificado por Chris** 2026-05-22 — abrir `mockups/dual-mode-shell.html` en browser
✅ **Design Contract** SSoT atomic design — `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md`
✅ **Template historia detallada** — `vitalia/docs/specs/templates/01-spec-shell-template.md`
✅ **Navigation tree JSON** — `vitalia/docs/product/stories/vitalia-shell-organism/navigation-tree.md`
✅ **5 decisiones técnicas ratificadas** (Shadcn install · deprecar .vt-* · route group paralelo · verificar Tailwind v4 · atomic design strict)
✅ **Backlog generado** — outcome master `vitalia-mvp-ui-foundation` refactorizado contenedor de:
   - 11 stories Fase 1 (10 átomos del shell + 1 stack-stability blocker)
   - 22 stories Fase 2 (1 por sub-tab activa)
   - 2 service-stories laterales (payment-adapter-mvp + fiscal-emission-pe)
   - 3 stories pre-paradigma refactorizadas/dropped

## Tipo: design-story (excepción al story-closure-gate)

Esta es una **design-story / planning-story** — NO produce código, produce SSoT funcional + plan de backlog. NO aplica auditor formal (no hay código para revisar, no hay Playwright que correr). Auditor implícito = Chris ratificó decisiones cementadas + mockup HTML + artifacts.

Justificación de transition direct `refining → done` saltando `developed/reviewing`:
- No hay `04-validators.yaml` (no hay código que validar)
- No hay `06-tickets.yaml` (no hay implementación, solo planning)
- No hay `03-arch.md` técnico tradicional (el "arch" es el Design Contract producido)
- Auditor = Chris ratificó visualmente + funcionalmente el mockup + plan

## Artifacts producidos (deliverables)

| # | Artifact | Path | Status |
|---|---|---|---|
| 1 | Mockup HTML navegable | `mockups/dual-mode-shell.html` | ✅ ratificado Chris 2026-05-22 |
| 2 | Session baseline (17 decisiones) | `00-session-baseline.md` (1069 líneas) | ✅ cementado |
| 3 | Design Contract | `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` | ✅ producido 2026-05-22 |
| 4 | Story template override | `vitalia/docs/specs/templates/01-spec-shell-template.md` | ✅ producido 2026-05-22 |
| 5 | Navigation tree JSON | `navigation-tree.md` | ✅ producido 2026-05-22 |
| 6 | HANDOFF next session | `HANDOFF-next-session.md` | ✅ ya existente |
| 7 | Vitalia feature inventory | `vitalia-feature-inventory.md` | ✅ ya existente |
| 8 | Nicolify feature inventory | `nicolify-feature-inventory.md` | ✅ ya existente |
| 9 | 07-merge artifact | `07-merge.md` | ✅ producido 2026-05-22 |

## Closure protocol (R2 — auto-move archive)

Per `.claude/rules/brand-docs-schema.md` § R2, esta story se moverá a `vitalia/docs/archive/2026/stories/vitalia-shell-organism/` en el commit final del cierre (mismo commit que escribe el 07-merge.md). El move queda pending hasta que TODAS las tasks del task tracker actual estén `completed` (incluye creación de 24+ checkpoints de stories Fase 1/2).

```bash
# Commit final ejecutará:
git mv vitalia/docs/product/stories/vitalia-shell-organism vitalia/docs/archive/2026/stories/vitalia-shell-organism
```

## Próximos pasos (post-cierre)

1. **Tasks 4-14 del task tracker actual** — generar todas las stories (24 Fase 1/2 + refactors + drops + outcome master + brand checkpoint)
2. **Archivar shell-organism** (R2 git mv)
3. **Handoff `/po-ux`** para refining F1-S0 (stack-stability) — primera story implementable

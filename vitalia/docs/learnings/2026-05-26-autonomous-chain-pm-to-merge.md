---
brand: vitalia
date: 2026-05-26
slug: autonomous-chain-pm-to-merge
promotable: yes
applies_to_other_brands_potentially: [vitalia, nicolify, comunify, lupulo, saasora, inmoflow, retailly, fixia, guestly, fitflow]
target_core_package: docs/process/pm-redesign-2026-05.md (paradigm v4.1 amplification cement)
story_introduced: vitalia-fase1-empty-states
phase: fase-1
type: process
---

# Autonomous chain `/pm-{brand}` → `/po-ux` → `/architect` → `/dev-team` → `/auditor` → `/pm-{brand}` merge (full lifecycle 1 session)

**Qué aprendimos:** Chris invocó `/pm-vitalia` con args "Refinemos F1-S10 — última story Fase 1 y dispara el chain /po-ux → /architect → /dev-team → /auditor → /pm-vitalia merge". Resultado: **una sesión sola ejecutó el full lifecycle desde idea → done sin Chris intermedio** (excepto 4 momentos de ratify visual/decision críticos batch 1+2 + el inicial "Ratifico, prosigue" + dos feedback rounds Chris UX). 11 tickets shipped en ~5h wall-clock con 0 Opus tokens en builders (Sonnet+Haiku stack).

**Origen:** vitalia-fase1-empty-states · cierre Fase 1 shell-organism vitalia-mvp-ui-foundation.

## Datos cuantitativos (single-session chain)

| Fase | Skill | Duration | Tokens estimados | Resultado |
|---|---|---|---|---|
| Refining UI | /po-ux iter 1+2 + 7 mockups HTML standalone + grid integral | ~45min | ~80k Opus | 01-spec.md v2 ratified + 10 decisiones cementadas 3 batches |
| Ready package | /architect single-shot full-stack | ~13min | ~256k Opus | 03-arch.md (855 LOC) + 04-validators.yaml (509) + 05-guidelines.md (398) + 06-tickets.yaml (562) |
| Autonomous build | /dev-team 11 tickets · wave parallel (T-2+T-8 // T-3+T-4 // T-5+T-7 // T-6 → T-9 → T-10 → T-11) | ~3h wall-clock | ~1.2M Sonnet | 11 commits sequential + 1691/1691 Vitest + 135/135 arch fitness + TS strict 0 + ESLint 0 |
| Context brief | context-builder Haiku iter 1 (sealed clean) | ~3min | ~150k Haiku | CONTEXT-BRIEF.md 342 LOC · amortizó 30-50k tokens cross-builder |
| Audit | /auditor iter 1 + auto-fix iter 1 (prettier --write 39 files) + auditor-frontend Opus full audit + Phase D | ~15min | ~220k Opus | REVIEW.md + CHECKPOINTS.md (30/30) + 06-audit/gherkin-matrix.md + 11 tickets audit-passed |
| Merge | /pm-vitalia 07-merge.md + capability YAML + archive + checkpoint transitions | ~5min | ~30k Opus | 5 secciones cementadas + state=done + Fase 1 complete |
| **Total** | full chain 1 session | **~5h wall-clock** | **~2M tokens cross-models** | **F1-S10 done · Fase 1 complete** |

## Por qué funcionó (factors críticos)

1. **paradigm v4.1 auto-handoff cementado** (post 2026-05-18 story-closure-gate): cada skill auto-encadena la siguiente vía `Skill` tool inline sin handoff textual a Chris. Cementó la pieza que faltaba para true autonomy.

2. **CONTEXT-BRIEF.md como amortización tokens**: 342 LOC Haiku comprime ~30-50k de spec+arch+rules+docs canónicos. 6 builders sequential reusaron el mismo brief → amortización 6× del work Haiku.

3. **must_load_skills enforceable v4.1**: cada builder reportó "Skills consulted" verbatim en `T-{n}-result.md`. Auditor verifica esa sección → enforcement loop cerrado.

4. **04-validators.yaml § test_construction_plan** (v4.1 cement): architect dictó el orden creation_order + POMs + scenario_to_test mapping verbatim. Dev-team SIGUE el plan en lugar de inventarlo.

5. **Wave parallel execution**: 2-3 builders parallel cuando DAG permite (T-2+T-8 / T-3+T-4 / T-5+T-7). Reducción ~50% wall-clock vs full sequential 11 tickets.

6. **architectural_validation category** (v4.1): arch tests separados de non_functional (FSD boundaries + anti-dup + ssot enforcement + no-phi + no-voseo). Catch errores estructurales locales antes auditor.

7. **Mockup-per-component overlay rule** (vitalia/.claude/rules/shell-mockup-per-component.md): los 7 mockups HTML ratified visualmente Chris ANTES de /architect (gate bloqueante). /dev-team construye contra spec verbal + mockup visual = menos rework downstream.

8. **Auditor self-fix policy v4.1 cement** (post 2026-05-19): decisión por NATURALEZA del fix, no tamaño. Caso B (spawn dev-team) para refactor camuflado · Caso C (self-fix) para whitelist verbatim · Caso D (escalate) para boundaries. Cap 4 self-fix iter + cap 3 audit_iterations.

## How to apply (cross-brand applicability)

**Aplicable a:** todos los brands Luana (10 verticals) cuando:
- Story es UI std (CRUD/list/detail/form/dashboard reusable Shadcn primitives)
- Brand tiene paradigm v4.1 skills shipped (`/pm-{brand}` + `/po-ux` + `/architect` + `/dev-team` + `/auditor`)
- WIP caps disponibles en target states
- No requiere lift core (engine surface = escalate `/pm-luana` antes de chain)

**Pattern verbatim a replicar:**

```
Chris: "Refinemos {story-id} y dispara el chain"
→ /pm-{brand} Step 0 + Step 1 + auto-chain via Skill(po-ux, "{brand} {story-id}")
→ /po-ux iter N (mockups + spec ratify batches) → Skill(architect, ...) en último turn
→ /architect single-shot full-stack → Skill(dev-team, ...) en último turn
→ /dev-team wave parallel tickets → Skill(auditor, ...) en último turn
→ /auditor → Skill(pm-{brand}, "merge {story-id}") en último turn
→ /pm-{brand} 07-merge.md + capability + archive + state done
```

## Anti-patterns descubiertos durante la chain

1. ❌ `/architect` first spawn devolvió `done -> ...` sin tools ejecutadas (false positive). Hubo que re-spawn con prompt "MUST verify files exist on disk before returning done". Mitigation: orchestrator verifica `ls` post-spawn antes de chain siguiente. **Promotable**: el pattern "verify artifacts on disk" debería ser explicit en architect-orchestrator agent definition.

2. ❌ Auditor gate-runner reportó prettier any_fail=true con 359 files (320 pre-existing + 39 F1-S10). Hubo que distinguir pre-existing tech debt vs scope F1-S10. Mitigation: gate-runner debería aceptar parametro `--scope-files` para limitar checks. **Promotable**: gate-runner skill update.

3. ❌ Visual goldens flagged `pending_chris_visual_ratify:true` porque stack vitalia :3002 no estaba up durante audit. Mitigation: pattern F1-S3 shipped (Chris valida visual diff post-merge). NO bloquea merge.

## Decisiones cardinales documentadas en esta story

- **Q1 mockup strategy**: combo 1 grid integral + 6 standalone (overlay rule mockup-per-component cumple verbatim)
- **Q2 toggle interactivity**: funcionales JS local (Chris valida UX completo en mockup)
- **Q3 header copy**: uniforme (consistencia visual + agente da identidad suficiente)
- **Q4 inbox depth**: sales_studio parity brand-local (NO cross-brand mirror)
- **Q5 agenda depth**: enriquecer placeholder F1 + componente React rich (visual "cockpit de Adrián")
- **Q6 takeover UX**: botón explícito "Tomar el control" (origen feedback Chris "no es muy intuitivo" sobre handler_mode passive border)
- **Q7 Camila Voz copy**: aclarar mínimo F1 (origen feedback Chris "no entiendo nada")
- **Q8 Mateo scope**: excluido (catálogo SSoT `mateo: []`)
- **Q9 default landing**: heredado F1-S9 (`valeria/agenda`)
- **Q10 telemetría**: defer F2 (cada sub-tab cablea su event)

## Costo agregado estimated

- Opus tokens cross-fase: ~580k (po-ux + architect + auditor)
- Sonnet tokens (dev-team builders): ~1.2M
- Haiku tokens (context-builder + gate-runner): ~280k
- **Total: ~2M tokens** for 11 tickets shipped + Fase 1 complete

Comparado con sesión Chris intermedio cada paso = ~5x más tokens user-time (Chris re-tipear cada chain step) + ~2x más tokens model context (cada handoff re-carga contexto). Autonomous chain saved ~7-10x tokens overall vs paradigm v3 (legacy pre-cement-date 2026-05-18).

## Referencias

- `docs/process/pm-redesign-2026-05.md` § Punto 4 paradigm v4.1 amplification
- `.claude/rules/story-closure-gate.md` (cement 2026-05-18 — auto-handoff default)
- `.claude/rules/pm-skill-chaining.md` (cement 2026-05-23 — Skill tool inline pattern)
- `.claude/rules/auditor-self-fix-policy.md` (cement 2026-05-19 — naturaleza del fix decision tree)
- `vitalia/docs/archive/2026/stories/vitalia-fase1-empty-states/` (artefactos completos de la chain F1-S10)

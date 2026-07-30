---
story_id: vitalia-fase1-shell-layout-5050-race-fix
type: ui-story-followup
agent_owner: shell
module: shell-organism
capability_extends: shell.layout-5050
state: parked
folded_into: vitalia-shell-core-hardening    # ★ 2026-06-10 absorbido por la umbrella de hardening del shell (consolidación ratificada Chris). El race SC-3 se resuelve dentro del hardening.
architecture_pattern: ADR-vitalia-004
last_modified: 2026-06-10T00:00:00-05:00
parked_at: 2026-05-23T18:30:00-05:00
parked_reason: "F1-S4 audit ESCALATED Caso D — race condition transition+drag-immediate edge case. Ratified Chris accept-with-defer. ★ 2026-06-10 FOLDED into vitalia-shell-core-hardening. ★ DELIVERED 2026-06-11: umbrella done — test del race REACTIVADO y verde (resize-and-state.spec.ts 8/8, SC-22/AC-14) sobre la máquina de estados nueva. Deuda saldada."
parent_story: vitalia-fase1-shell-layout-5050
parent_commit_partial_fix: 46fc8700
parallel_safe: true
priority: low
estimated_dev_days: 0.5-1
hipaa_lite_scope: not_applicable

# Schema v2 migration (cement 2026-05-27)
release: F1   # release ID · ver releases/
cap_target: plataforma-tecnica.shell   # capability slug target (v2 cement 2026-05-27)
cap_change_type: extend   # new | fix | extend | derive
---

# F1-S4b vitalia-fase1-shell-layout-5050-race-fix — checkpoint

## Goal

Refactor del lifecycle hydration race condition entre `next/dynamic({ssr:false})` + `useDefaultLayout` localStorage restore + `useEffect ResizeObserver` minSize calc. Resolver edge case que F1-S4 audit-iter-3 DEFERRED: `setValeriaStateViaStore('rail')→reload→setValeriaStateViaStore('full')→reload→drag inmediato` que viola spec SC-3 assertion `400 < min 620 → snap-up automático a 620`.

Resolución natural cuando F1-S5/S6 (`vitalia-fase1-valeria-rail-history` / `vitalia-fase1-valeria-chat-skeleton`) refactor el conversational shell lifecycle.

## Anti-objetivos

- NO romper Fix A snap-up (commit 46fc8700) — solo extender para transition+drag case
- NO modificar API exposed por shell-store ni componentes hijos
- NO touch visual goldens locked (6 PNGs F1-S4 Fase 7B)

## Reference artifacts (parent F1-S4)

- Story snapshot inmutable: `vitalia/docs/archive/2026/stories/vitalia-fase1-shell-layout-5050/`
- Spec SC-3 amended (DEFERRED block): `vitalia/docs/archive/2026/stories/vitalia-fase1-shell-layout-5050/01-spec.md:78-99`
- Audit ESCALATION: `vitalia/docs/archive/2026/stories/vitalia-fase1-shell-layout-5050/T-7-review.md` § Audit iteration 3
- Learning promotable: `vitalia/docs/learnings/2026-05-23-shell-layout-race-condition-defer.md`
- Test skipped (test.skip(true)): `vitalia/frontend/e2e/regression/vitalia-fase1-shell-layout-5050/resize-and-state.spec.ts:114`

## Posibles approaches (NO ratificados, TBD al refinar)

1. **Block drag interaction hasta ready:** Panel pointer-events:none mientras `containerWidth === 0 || minSize unset`. Habilita post-ResizeObserver fire.
2. **Custom hook `useLayoutReady`:** await React.useId + ResizeObserver settle + minSize compute en single state machine.
3. **Persist split key con minSize embebido:** localStorage stores `{ layout: [...], minSizeSnapshot: { panelId: pct } }`. On hydration, si minSizeSnapshot < current calc → ignore persisted, use new default.

## Pre-condiciones para arrancar

- F1-S5 + F1-S6 en state ≥ developed (refactor conversational shell el área natural)
- Promotion candidate scan `/pm-luana` decide si lift a core/luana-core-platform/ (depende de 2da brand encontrar problema similar)

## Next action

Esperar pickup natural. /pm-vitalia puede unpark cuando F1-S5/S6 close.

---
story_id: vitalia-shell-state-persistence
release: F1
type: ui-story-followup
agent_owner: shell
module: shell-organism
cap_target: valeria.shell
cap_change_type: extend
architecture_pattern: ADR-vitalia-004
new_adr_candidate: ADR-vitalia-006-ssr-safe-persisted-store   # ★ 005 ya ocupado (capability-model); architect autoró 006
state: done
phase: MERGED
audit_verdict: APPROVED
gherkin_matrix: 06-audit/gherkin-matrix.md
merged_at: '2026-05-28T22:10:00-05:00'
merge_artifact: 07-merge.md
cap_updated: shell-organism/shell-vitalia.yaml (extend +2 scenarios)
learning: vitalia/docs/learnings/2026-05-28-ssr-safe-zustand-persist.md (promotable candidate /pm-luana)
main_integration: "PENDING — squash-merge wip/vitalia → main es manual desde worktree PRINCIPAL (main no accesible desde canónico vitalia)"
last_artifact: gate-output.json
build_commits: [da0602ea, 58a4ce5b, 54ffb8e4, 08fe0864, d6953264, bf03639c]
gate_summary: "tsc 0 · eslint 0 · vitest 2310/2310 · arch 148/148 · E2E 28/28 — all GREEN"
ratified_by_chris: true
ratified_at: '2026-05-28T20:33:00-05:00'
mockup_gate: exempt
mockup_gate_reason: "modifica comportamiento de componentes ya ratificados F1-S5; cero estados visuales nuevos (ratificado Chris 2026-05-28)"
mobile_behavior: "collapsed-pero-recuerda — slice mobile drawer independiente de valeriaState (ratificado Chris 2026-05-28)"
governing_adr: ADR-vitalia-006-ssr-safe-persisted-store
arch_version: 1
adr_004_compliance: not-applicable-rationale
autonomous_mode: true
autonomous_mode_chain: [dev-team, auditor, pm-merge]
autonomous_mode_ratified_by: chris
autonomous_mode_ratified_at: '2026-05-28T20:40:00-05:00'
autonomous_mode_caps:
  max_iterations_per_ticket: 10
  max_audit_iterations: 3
  on_cap_exceeded: "state=blocked + escalate Chris"
next_action: "AUTO-HANDOFF /pm-vitalia merge → 07-merge.md 5 secciones + cap ledger valeria.shell extend + ADR 005→006 fix + learning promotable + archive → state=reviewing→done"
last_modified: '2026-05-28T22:06:00-05:00'
parent_story: vitalia-fase1-shell-layout-5050-race-fix
priority: medium
estimated_dev_days: 1-2
hipaa_lite_scope: not_applicable
parallel_safe: true
transversal_scope: true
---

# vitalia-shell-state-persistence — checkpoint

## Goal

Arreglar **2 bugs reales acoplados** descubiertos al des-oxidar la suite E2E F1-S4
(origen: `vitalia-fase1-shell-layout-5050-race-fix`, sesión 2026-05-28), **resolviendo
la causa raíz a nivel arquitectónico (transversal)** en vez de parchear shell-store:

1. **Persistencia del shell-store rota (PROD REAL).** `valeriaState`/`shellMode` NO
   sobreviven reload — el store auto-hidrata contra el default y pisa localStorage.
2. **Drawer mobile auto-abre (acoplado a #1).** A <768px con default `full`, el drawer
   se monta abierto al cargar. Decisión de usabilidad: mobile debe arrancar `collapsed`.

## ★ Causa raíz CONFIRMADA (replan 2026-05-28 — `/pm-vitalia`)

> El research dejó el root cause "de alto nivel" sin pinpoint del write espurio. Esta
> sesión lo confirmó leyendo el código real. **Ya no hay misterio.**

**Mecanismo exacto:** `ShellOrganismLayout.tsx` es `"use client"` y su **skeleton
SSR / `loading` fallback** (`ShellOrganismLayoutSkeleton`) renderiza `<TopBarGlobal/>`.
`TopBarGlobal` **suscribe `useShellStore`** (`setValeriaState`, `setShellMode`).
El `dynamic({ ssr:false })` envuelve SOLO a `ShellOrganismLayoutClient` — **el skeleton
queda fuera de ese boundary**. Resultado: el middleware `persist` se evalúa en el render
server + en la ventana pre-hidratación del skeleton, auto-hidrata contra el default
(`full/agentic`) y **reescribe localStorage con el default**, pisando la preferencia
guardada en cada reload. Ese es el "write espurio" que el research no pinpointeó.

**Por qué es transversal (no un fix de shell-store):** hay **4 stores con `persist`**
que comparten el mismo hazard SSR:
- `vitalia/frontend/src/stores/shell-store.ts`
- `vitalia/frontend/src/stores/tenant-store.ts`
- `vitalia/frontend/src/features/valeria/store/agenda-store.ts`
- `vitalia/frontend/src/features/valeria/store/agenda-filters-store.ts`

La corrección debe ser **un patrón brand-wide de "persisted store SSR-safe"** + ADR nuevo
(`ADR-vitalia-005` candidate). `ADR-vitalia-004` (shell sub-tab) NO cubre persistencia
bajo SSR → gap real.

## Replan — scope refinado

| # | Antes | Después (replan) |
|---|---|---|
| Naturaleza | "fix puntual shell-store" | **Patrón arquitectónico transversal** (4 stores) + ADR-vitalia-005 |
| Bug #2 mobile | "extender guard <768" | **Decisión de usabilidad ratificable:** mobile arranca `collapsed` (burger abre), desacoplado del default `full` |
| cap_change_type | `fix` | `extend` (mobile-collapsed = 1 scenario nuevo en `valeria.shell`; persistencia = parte `fix` bundled — `/po-ux` confirma con Gherkin) |

**Direcciones para `/architect` (NO decidir acá — son su análisis):**
- **Opción surgical:** skeleton store-free (TopBarGlobal placeholder sin store en skeleton)
  + `skipHydration:true` + hydration-gate client → store solo vive en el chunk `ssr:false`.
- **Opción patrón:** factory `createPersistedStore()` SSR-safe (storage no-op hasta `hydrated`)
  aplicado a los 4 stores → cementado en ADR-vitalia-005.
- Evaluar si el `ssr:false` + skeleton (impuesto por `react-resizable-panels` v4 bare-name
  `localStorage`) sigue siendo el approach correcto o conviene un replanteo estructural.

## Prior art scan (anti-duplication-refining — 2026-05-28)

```
Engine (core/@luana/*):          sin patrón persist/store SSR-safe a consumir.
Brands LIVE (grep persist):      SOLO vitalia usa zustand `persist` (4 stores).
                                 comunify / nicolify / lupulo → 0 hits.
Snapshot frozen:                 n/a (shell-organism es vitalia-native).
Learnings (hydrat/zustand/ssr):  0 hits.
```
**Decisión: net-new vitalia-local.** Sin mirror cross-brand, sin engine a importar.
Si el patrón SSR-safe sale limpio → capturar learning `promotable: candidate` para
`/pm-luana` (Next 16 + Zustand persist es transversal a futuros brand frontends).

## Tests de regresión (ya escritos, SKIPPED esperando este fix)

Des-skipear al resolver (quitar `.skip` + tag `[DEFERRED: ...]`):
- `resize-and-state.spec.ts` → `shell state (valeriaState) survives reload`
- `resize-and-state.spec.ts` → `state rail->full snap-up to min (580 full)`
- `mobile-collapse.spec.ts` → `ValeriaSlot oculto mobile`

Más (replan): **unit tests vitest** del hydration del store (mock localStorage + SSR flag)
— el bug es timing SSR+hydration, difícil de iterar solo por E2E.

## Archivos involucrados

- `vitalia/frontend/src/stores/shell-store.ts` (+ los otros 3 stores persist — transversal)
- `.../shell-organism/ShellOrganismLayout.tsx` (skeleton SSR consume store — el boundary roto)
- `.../shell-organism/ShellOrganismLayoutClient.tsx` (client mount ssr:false)
- `.../shell-organism/TopBarGlobal.tsx` (consumer del store en skeleton)
- `.../shell-organism/ValeriaSidebar.tsx` (D2 effect + drawer mobile)
- `.../shell-organism/useViewportGuard.ts` (guard — extender a <768)

## Next action

Refinement en curso → `/po-ux vitalia vitalia-shell-state-persistence`:
cerrar 01-spec.md (contrato comportamiento: prefs sobreviven reload + mobile-collapsed
default + sin drawer espurio + estados visuales) → ratificar decisión mobile con Chris →
state refining→refined → `/architect` (patrón SSR-safe + ADR-vitalia-005 + ready package).

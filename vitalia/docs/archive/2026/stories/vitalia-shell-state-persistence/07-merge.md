# 07-merge — vitalia-shell-state-persistence

> Fase F MERGE · `/pm-vitalia` · 2026-05-28
> Audit verdict: APPROVED (CHECKPOINTS C1-C5 all green) · Phase D 9/9 PASS
> cap_change_type: extend → `shell-organism/shell-vitalia.yaml` (functional_area `valeria.shell`)

## § 1 — Gherkin verification matrix

Copia de `06-audit/gherkin-matrix.md` — 9/9 scenarios PASS:

| Scenario | Test | Status |
|---|---|---|
| SC-1 valeriaState survives reload | valeria-state-survives-reload.spec.ts + resize-and-state (un-skip) | ✅ |
| SC-2 shellMode survives reload | valeria-state-survives-reload.spec.ts | ✅ |
| SC-3 NO spurious 'full' write (the bug) | shell-store-hydration.test.ts + e2e instrumentSetItem | ✅ |
| SC-4 fresh mobile drawer CLOSED (indep. desktop full) | mobile-collapsed-default.spec.ts + mobile-collapse (un-skip) | ✅ |
| SC-5 burger opens drawer | mobile-collapsed-default.spec.ts | ✅ |
| SC-5b mobile remembers open/closed across reload | mobile-collapsed-default.spec.ts | ✅ |
| SC-6 first visit default | shell-store-hydration.test.ts | ✅ |
| SC-7 corrupt localStorage no crash | shell-store-hydration.test.ts | ✅ |
| SC-8 a11y wcag2aa keyboard | mobile-collapsed-default.spec.ts @a11y | ✅ |

## § 2 — Playwright E2E run

```bash
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test \
  e2e/regression/shell-state-persistence/ \
  e2e/regression/vitalia-fase1-shell-layout-5050/{resize-and-state,mobile-collapse}.spec.ts \
  --project=smoke
# → 28 passed (19.4s)
```
Vitest: 2310/2310 · tsc 0 · eslint 0 · arch fitness 148/148.

## § 3 — Capabilities updated

- `vitalia/docs/product/capabilities/shell-organism/shell-vitalia.yaml` — **extend**:
  - change_log entry `vitalia-shell-state-persistence` (type: extend)
  - 2 scenarios nuevos: `shell-state-persists-reload` (SC-1/2/3) + `mobile-drawer-collapsed-pero-recuerda` (SC-4/5/5b), ambos con `e2e_test` existente (satisface Definición de DONE cross_check_3)
  - `last_modified: 2026-05-28`

> Nota: el `cap_target` del checkpoint decía `valeria.shell` (que es el `functional_area`); el cap real es `shell-organism.shell-vitalia`. Sin impacto — se actualizó el cap correcto.

## § 4 — Modules MD

- `vitalia/docs/product/modules/shell-organism.md` — auto-list refresh pendiente vía `scripts/reconcile_capabilities.py --brand vitalia` (post-integración a main).

## § 5 — How to verify

```bash
# Unit (no server):
cd vitalia/frontend && npx vitest run src/lib/store/ src/stores/__tests__/ src/components/shared/shell-organism/__tests__/
# E2E (server :3002 + Clerk):
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/shell-state-persistence/ --project=smoke
# Repro del bug original (debe pasar ahora): setear rail → reload → sigue rail (no vuelve a full)
```

## § 6 — Build trail (commits en wip/vitalia)

| Commit | Ticket | Resumen |
|---|---|---|
| da0602ea | T-1 | factory SSR-safe + migrate shell-store |
| 58a4ce5b | T-1 fix | server-first arch test false-positive (detección 'use client' tras comment + ratchet shrink) |
| 54ffb8e4 | T-2 | skeleton store-free + rehydrate ssr:false + arch guard (mislabel cosmético del race paralelo) |
| 08fe0864 | T-3 | factory transversal (tenant + agenda + agenda-filters) |
| d6953264 | T-4 | drawer mobile slice independiente + guard <768 |
| bf03639c | T-5 | un-skip 3 regresiones + e2e survives-reload + mobile-recuerda + a11y |

## § 7 — Decisiones / flags al cierre

- **ADR governing:** `ADR-vitalia-006-ssr-safe-persisted-store` (005 estaba ocupado por capability-model). Citas en `01-spec.md` corregidas 005→006 en este merge.
- **Learning promotable → /pm-luana:** `vitalia/docs/learnings/2026-05-28-ssr-safe-zustand-persist.md` (candidate). `nicolify/.../dismiss-store.ts` tiene el mismo hazard SSR → lift candidate del patrón a `core/@luana/`.
- **Integración a main:** la squash-merge `wip/vitalia → main` es el paso de integración MANUAL (staging deploy MANUAL per CLAUDE.md). main vive en el worktree PRINCIPAL (`~/Proyectos/luana-platform`); no se ejecuta desde el canónico vitalia. Todos los artefactos (07-merge + cap + learning + archive + state=done) quedan en wip/vitalia listos para integrar.

## § 8 — Done

state `reviewing → done`. Story archivada a `vitalia/docs/archive/2026/stories/vitalia-shell-state-persistence/` en este mismo commit (R2).

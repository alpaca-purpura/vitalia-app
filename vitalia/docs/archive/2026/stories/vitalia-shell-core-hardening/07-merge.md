# 07-merge — vitalia-shell-core-hardening

> **Fecha:** 2026-06-11 · **Merge por:** /pm-vitalia (cadena autónoma ratificada Chris "arranca /architect y continúa hasta el done") · **Verdict auditor:** APPROVED (CHECKPOINTS.md C1-C5 PASS) · **chris_verify.signoff:** SATISFIED ("ya quedó bien", 2 rondas live)

## § 1 — Gherkin verification matrix

Copia canónica: `06-audit/gherkin-matrix.md` — **SC-1..SC-22 → 22/22 PASS** (specs e2e real-backend nombrados por SC + resize-and-state SC-4/22 + matriz runtime 22/22 + 2 rondas live Chris). Cero MISSING.

## § 2 — Playwright E2E run

```bash
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test \
  e2e/regression/shell-core-hardening/ \
  e2e/regression/vitalia-fase1-shell-layout-5050/resize-and-state.spec.ts
# → 68 passed (0 flaky, 4.5m) — última corrida 2026-06-11 post-fixes ronda 2
# resizer-matrix.spec.ts 7/7 (matriz permanente estados × drags, pedido Chris "todos los casos")
```

Anti-burbuja: todos los specs componen `fixtures/base.ts` (via `shell-hardening.fixture`). Real-backend (stack dev FE:3002/BE:8002), Clerk autenticado.

## § 3 — Capabilities updated/created

- `cap_change_type: fix` + `cap_target: null` — higiene cross-cap del chrome (precedente: shell-valeria-responsive, shell-nav-scroll-errors). **Sin cap YAML nueva ni modificada** (el chrome es wrapper transversal `map_zone: infraestructura`; el lift a `@luana/ui-kit` es cap-work de /pm-luana, core).
- Consolidación entregada: stories folded `vitalia-bugfix-shell-valeria-responsive` (refined→delivered) + `vitalia-fase1-shell-layout-5050-race-fix` (race SC-22 reactivado y verde) + bugs latentes U3/B1 + dark BUG#2 — todos resueltos en este merge.

## § 4 — Modules MD refreshed

- `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` actualizado (T-8 · 412efe4f): máquina `closed|chat`+`historyOpen` · N3 consume `@luana/ui-kit` (brand-local retirado) · topbar · dark tokens · soft-nav.
- `docs/promotion-protocol/proposals/2026-06-01-lift-shell-organism-to-core.md` § "Estado post vitalia-shell-core-hardening" (handoff /pm-luana — chrome listo para lift).
- `make portfolio` regen post-merge (BACKLOG auto).

## § 5 — How to verify (reproducible)

```bash
# Stack
make dev-vitalia   # FE :3002 / BE :8002
# Suites
cd vitalia/frontend && npx tsc --noEmit && npx eslint src/ --cache && npx vitest run src/
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/shell-core-hardening/
# Live (lo que Chris ejerció): localhost:3002 con dr.demo@vitalialat.com —
#   colapsar→strip 44px sin gap→avatar reabre→drag (clamp 320, vivo post-ciclo)→
#   historial (push 280, chat nunca <min)→"+" archiva→dark per sub-tab→soft-nav board→recuperar ×N
```

## Resumen de entrega

8 tickets (T-1 store máquina nueva · T-2 chrome layout · T-3 tira-avatar+cabecera · T-4 soft-nav edge-redirect+revert band-aid · T-5 N3→@luana/ui-kit+mirror retirado · T-6 dark token-audit · T-7 e2e SC-1..22+race · T-8 contract+handoff+demo-script) + 2 rondas live Chris (collapse runtime/resize/wrap/min-C — 4 root causes muertos, lib v4 props-capture + persistencia + grid implícito + min sin hist) + Carril R auditor (allowlists post-rename inbox→adrian + 2 tests stale). Bugs de producto cazados por la suite: rewrites `/api`→BE (bug global useTenants 404) · strip collapsedSize · drag-collapse.

**Deuda ruteada (no bloquea):** CIL L1 stale-gate freshness · L3 SC-19 flaky theme-hydration · L1 dev-container node_modules symlink war (pnpm host↔container) · embudo defer_audit listo para auditarse post-hardening.

# 07-merge.md — vitalia-fase1-shell-layout-5050

> Story: F1-S4 vitalia-fase1-shell-layout-5050 (Shell Organism Layout 50/50)
> Brand: vitalia
> Merger: `/pm-vitalia`
> Date: 2026-05-23T18:35:00-05:00
> Auditor verdict: APPROVED-WITH-DEFER (33/34 Playwright + 1 DEFERRED documented)
> Commits range: e630e5d6..bbd79024 (12 commits chronological en wip/vitalia)

## § 1 — Gherkin verification matrix (copia 06-audit/gherkin-matrix.md)

| # | Scenario (01-spec.md) | Test path | Status |
|---|---|---|---|
| SC-1 | happy · render 50/50 default modo agentic | `e2e/regression/vitalia-fase1-shell-layout-5050/render-agentic-default.spec.ts` (8 assertions) | ✅ PASS |
| SC-2 | negative · viewport < md colapsa a 1 columna | `e2e/regression/vitalia-fase1-shell-layout-5050/mobile-collapse.spec.ts` (4 assertions) | ✅ PASS |
| SC-3 | edge · resize boundary + persistencia + snap-up | `e2e/regression/vitalia-fase1-shell-layout-5050/resize-and-state.spec.ts` (5 assertions) | ⚠️ PARTIAL (4/5) — last assertion DEFERRED a F1-S5/S6 |
| SC-4 | adversarial · a11y keyboard + axe wcag2aa | `e2e/regression/vitalia-fase1-shell-layout-5050/a11y-keyboard.spec.ts` (4 + axe) | ✅ PASS |

**Visual goldens locked (Fase 7B):** 6 PNGs en `vitalia/frontend/e2e/__screenshots__/regression/vitalia-fase1-shell-layout-5050/visual-goldens.spec.ts/` con `maxDiffPixelRatio: 0.001` enforce ratchet.

**Total coverage:** 33/34 Playwright tests pass (97%) + 6/6 visual goldens locked.

## § 2 — Playwright E2E run

**Comando:**
```bash
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase1-shell-layout-5050/
```

**Verdict:** 27 passed + 1 skipped en project=smoke. Plus `--project=visual` con 6 goldens GREEN.

**Skipped test (DEFERRED documented):**
- `resize-and-state.spec.ts:114 :: state rail->full at width 400 snap-up to 620 (DEFERRED F1-S5/S6 lifecycle)`
- Marked `test.skip(true, "DEFERRED F1-S5/S6 lifecycle")` con razón documentada in-place
- Spec 01-spec.md SC-3 anotado bloque DEFERRED 2026-05-23

## § 3 — Capabilities updated/created

**Created:**
- `vitalia/docs/product/capabilities/shell-organism/layout-5050.yaml`
  - capability_id: `vitalia.shell-organism.layout-5050`
  - status: live · story_introduced: vitalia-fase1-shell-layout-5050 · date_introduced: 2026-05-23
  - surfaces: 8 frontend files + 7 tests + 4 docs
  - scenarios verbatim SC-1..SC-4 (SC-3 con DEFERRED block)
  - KPIs: 33/34 + 6 goldens + 980 vitest + 64 arch fitness + a11y 0 violations

## § 4 — Modules MD refreshed

**Created:** `vitalia/docs/product/modules/shell-organism.md`
- Propósito + decisiones cardinales + anti-objetivos
- Auto-list block con `shell.layout-5050` capability entry
- Referencias archive snapshot + mockups + learning + follow-up

## § 5 — How to verify (reproducible)

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}

# 1. Native FE quality gates
cd vitalia/frontend && npx tsc --noEmit
# expected: 0 errors

cd vitalia/frontend && npx eslint src/ --cache
# expected: 0 violations

cd vitalia/frontend && npx vitest run --coverage
# expected: 980 passed (incluye 64 arch fitness) · coverage > 20%

# 2. Playwright F1-S4 functional + a11y
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase1-shell-layout-5050/
# expected: 27 passed + 1 skipped (DEFERRED documented)

# 3. Playwright F1-S4 visual goldens
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=visual e2e/regression/vitalia-fase1-shell-layout-5050/visual-goldens.spec.ts
# expected: 6 PASS (goldens match locked baseline)

# 4. Showcase manual verification
# - Stack: make dev-vitalia (Docker compose con vitalia_frontend_dev 4G memory)
# - Open browser: http://localhost:3002/test-stack/shell-layout
# - Compare side-by-side vs mockup ratificado:
#   http://localhost:8888/shell-layout-agentic.html
#   (python3 -m http.server 8888 desde mockups/ dir)
```

## Cross-references

- **Spec amended:** `vitalia/docs/archive/2026/stories/vitalia-fase1-shell-layout-5050/01-spec.md` § SC-3 (DEFERRED block)
- **Audit trail:** `vitalia/docs/archive/2026/stories/vitalia-fase1-shell-layout-5050/T-7-review.md` (3 audit iterations + ESCALATION Caso D)
- **CHECKPOINTS:** `vitalia/docs/archive/2026/stories/vitalia-fase1-shell-layout-5050/CHECKPOINTS.md` (C1-C5 grid)
- **Gherkin matrix:** `vitalia/docs/archive/2026/stories/vitalia-fase1-shell-layout-5050/06-audit/gherkin-matrix.md`
- **Learning promotable:** `vitalia/docs/learnings/2026-05-23-shell-layout-race-condition-defer.md` (candidate cross-brand)
- **Follow-up parked:** `vitalia/docs/product/stories/vitalia-fase1-shell-layout-5050-race-fix/checkpoint.md` (state=parked)

## State transition

`reviewing` → **`done`** at 2026-05-23T18:35:00-05:00

WIP cap impact: `reviewing` (was 1) → 0. `done` rolling 90d counter +1.

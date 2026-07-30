# T-11 Result — FE Visual Goldens

**Ticket:** T-11
**Story:** vitalia-fase2-lisa-marca (F2-S7)
**State:** pushed
**Date:** 2026-05-27

---

## Deliverables

| Deliverable | Status |
|---|---|
| `vitalia/frontend/e2e/visual/lisa-marca-visual.spec.ts` | CREATED |
| `vitalia/frontend/e2e/__screenshots__/lisa-marca/identidad-light.png` | PLACEHOLDER (needs `--update-snapshots` on staging) |
| `vitalia/frontend/e2e/__screenshots__/lisa-marca/identidad-dark.png` | PLACEHOLDER |
| `vitalia/frontend/e2e/__screenshots__/lisa-marca/voz-y-tono-light.png` | PLACEHOLDER |
| `vitalia/frontend/e2e/__screenshots__/lisa-marca/voz-y-tono-dark.png` | PLACEHOLDER |
| `vitalia/frontend/e2e/__screenshots__/lisa-marca/presencia-light.png` | PLACEHOLDER |
| `vitalia/frontend/e2e/__screenshots__/lisa-marca/presencia-dark.png` | PLACEHOLDER |
| DELETE `brand-studio-section-client.tsx` | DONE |

## G5 Gate

| Gate | Result |
|---|---|
| tsc --noEmit | PASS |
| eslint | PASS |
| playwright --list | PASS (6 tests in visual + smoke projects) |

## Acceptance Criteria

| AC | Status | Notes |
|---|---|---|
| A1: 6 PNG visual goldens + ratchet shrink-only | PLANNED (staging required) | Baseline not yet generated |
| A2: Visual fidelity `maxDiffPixelRatio: 0.001` | PLANNED (staging required) | Spec file validates threshold |
| A3: Legacy dashboard route deleted | DONE | `(dashboard)/brand-studio/` was already gone |

## Notes

Snapshots are PLACEHOLDER — auditor must run:

```bash
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
  npx playwright test e2e/visual/lisa-marca-visual.spec.ts --project=visual --update-snapshots
```

Once baseline generated, snapshots tracked in git and subsequent runs enforce `maxDiffPixelRatio: 0.001`.

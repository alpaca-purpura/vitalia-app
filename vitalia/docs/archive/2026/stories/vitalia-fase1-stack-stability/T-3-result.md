---
ticket: T-3
story_id: vitalia-fase1-stack-stability
brand: vitalia
state: pushed
validator_ids: [val-t3-playwright-visual-project, val-t3-test-pages-exist, val-t3-spec-exists, val-t3-tsc-clean]
---

# T-3 — playwright.config @project=visual + 2 test pages — Result

## Deliverables

### playwright.config.ts — @project=visual added
- Viewport: 1440×900, colorScheme: light
- snapshotPathTemplate: `e2e/__screenshots__/{testFilePath}/{arg}{ext}`
- expect.toHaveScreenshot: maxDiffPixelRatio=0.001, animations=disabled, caret=hide
- testMatch: `/.*\/e2e\/visual\/.*\.spec\.ts/`
- No `dependencies: ['setup']` — visual pages are public (no Clerk auth)

### Test pages
- `e2e/__test-pages__/stack-stability/primitives-showcase.tsx` — 8 Shadcn primitives × all variants, LatAm data (clínica médica Argentina, OSDE/IOMA/Swiss Medical)
- `e2e/__test-pages__/stack-stability/agent-tokens-swatch.tsx` — 7 agent color swatches (lisa/lucas/adrián/valeria/camila/mateo/config) + surface tokens grid

### Visual baseline spec
- `e2e/visual/stack-stability/dev-stack-baseline.spec.ts`
- 6 goldens planned: dashboard-legacy-{light,dark}, shadcn-primitives-{light,dark}, agent-tokens-swatch-{light,dark}
- DEFERRED (T-4): goldens not generated yet — requires `make dev-vitalia` running + Chris ratification

## Validators

| Validator | Status |
|---|---|
| val-t3-playwright-visual-project | PASS — visual project block in playwright.config.ts |
| val-t3-test-pages-exist | PASS — 2 tsx files in e2e/__test-pages__/stack-stability/ |
| val-t3-spec-exists | PASS — dev-stack-baseline.spec.ts at correct path |
| val-t3-tsc-clean | PASS — `npx tsc --noEmit` 0 errors |

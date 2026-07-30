# Merge artifact — vitalia/vitalia-fase1-topbar-global

> Brand: vitalia
> Story: F1-S2 vitalia-fase1-topbar-global
> Merged at: 2026-05-23T02:05:00-05:00
> Commits: 58cfbff4 (claim) · b37b37b3 (8 tickets bundle) · 77bd681e (state update)
> Audit verdict: APPROVED (zero rework, 1 audit iteration)

## § 1 — Gherkin verification matrix

Copia de `06-audit/gherkin-matrix.md`. **13/13 scenarios PASS** (SC-01..SC-13). Ver matrix archivada.

## § 2 — Playwright E2E run

```bash
cd vitalia/frontend
E2E_BASE_URL=http://localhost:3002 npx playwright test --project=visual
# 15/15 PASS (F1-S0 6 + F1-S1 2 + F1-S2 6 + smoke baselines 1)

E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke --grep topbar  # PASS
E2E_BASE_URL=http://localhost:3002 npx playwright test --project=a11y --grep topbar   # PASS
```

## § 3 — Capabilities updated/created

NEW: `vitalia/docs/product/capabilities/platform/topbar-global.yaml` (live, 0.1.0)

## § 4 — Modules MD refreshed

`vitalia/docs/product/modules/platform.md` (auto-list refresh post-merge) — appended `topbar-global`.

## § 5 — How to verify

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS} && make dev-vitalia

cd ${WS}/vitalia/frontend
npx tsc --noEmit                                                # 0 errors
npx eslint src/ --max-warnings 0                                # 0 errors
npx vitest run                                                  # 824/824 PASS

E2E_BASE_URL=http://localhost:3002 npx playwright test --project=visual    # 15/15
E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke --grep topbar
E2E_BASE_URL=http://localhost:3002 npx playwright test --project=a11y --grep topbar

curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3002/test-stack/topbar-global  # 200
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3002/test-stack/logo-mark      # 200

# Interactive Chris verify
# https://dev-app.vitalialat.com/test-stack/topbar-global
# Resize browser <768px → LogoMark switch a variant="mark"
# Toggle theme → TopBar bg + LogoMark wordmark swap (navy→white)
# Press Tab desde body → skip-link aparece focus visible
```

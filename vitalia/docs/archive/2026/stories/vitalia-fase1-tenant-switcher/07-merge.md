# Merge artifact — vitalia/vitalia-fase1-tenant-switcher

> Brand: vitalia
> Merged: 2026-05-23
> Commit base (F1-S3 implementation): d99b1fdd
> Commit fix (auditor handoff T-FIX-1): 0f012ad1
> Audit verdict: APPROVED iter 2 (`06-audit/CHECKPOINTS.md`)
> Chain: F1-S0..S3 COMPLETE — F1-S0 (69948873) · F1-S1 (5c59e89b) · F1-S2 (c3bb6546) · F1-S3 (this merge)
> Pending Chris visual ratify: `true` (5-min next session)

## § 1 — Gherkin verification matrix

> Cada scenario de `01-spec.md` mapeado a test que pasa. Copiado de `06-audit/gherkin-matrix.md` (archived).

| Scenario (Gherkin SSoT 01-spec.md § 4) | Test Path | Status |
|---|---|---|
| SC-01 Trigger has aria-label='Cambiar clínica' | `vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/tenant-switcher-structure.smoke.spec.ts::SC-01` | ✅ PASS |
| SC-01b Trigger has data-testid='tenant-switcher-trigger' | `tenant-switcher-structure.smoke.spec.ts::SC-01b` | ✅ PASS |
| SC-02 Opening dropdown shows 'MIS CLÍNICAS' header | `tenant-switcher-structure.smoke.spec.ts::SC-02` | ✅ PASS |
| SC-02b Dropdown contains list of tenant options | `tenant-switcher-structure.smoke.spec.ts::SC-02b` | ✅ PASS |
| SC-03 Selecting different tenant navigates to /{newTenantId}/dashboard | `tenant-switcher-navigation.smoke.spec.ts::SC-03` | ⏭️ SKIP (aspirational — requires real /{tenantId}/dashboard route, deferred to Fase 2 per 03-arch.md) |
| SC-03b Clicking active tenant is no-op | `tenant-switcher-navigation.smoke.spec.ts::SC-03b` | ✅ PASS |
| SC-03c Active tenant option shows check mark | `tenant-switcher-navigation.smoke.spec.ts::SC-03c` | ✅ PASS |
| SC-04 Error state shows alert + Reintentar | `tenant-switcher-states.smoke.spec.ts::SC-04` | ✅ PASS |
| SC-06 Footer shows Agregar clínica + Administrar cuenta | `tenant-switcher-states.smoke.spec.ts::SC-06` | ✅ PASS |
| SC-06b Dropdown dismissed via Escape key | `tenant-switcher-states.smoke.spec.ts::SC-06b` | ✅ PASS |
| SC-07 Agregar clínica opens modal "Próximamente" | `tenant-switcher-modal.smoke.spec.ts::SC-07` | ✅ PASS |
| SC-07b Entendido button closes modal | `tenant-switcher-modal.smoke.spec.ts::SC-07b` | ✅ PASS |
| SC-07c Modal close button data-testid='add-clinic-modal-close' | `tenant-switcher-modal.smoke.spec.ts::SC-07c` | ✅ PASS |
| SC-08 Trigger focusable + aria-label | `tenant-switcher-a11y.smoke.spec.ts::SC-08` | ✅ PASS |
| SC-08b Trigger title shows active tenant name | `tenant-switcher-a11y.smoke.spec.ts::SC-08b` | ✅ PASS |
| SC-08c Active option sr-only 'Clínica activa' | `tenant-switcher-a11y.smoke.spec.ts::SC-08c` | ✅ PASS |
| SC-08d Enter key opens dropdown | `tenant-switcher-a11y.smoke.spec.ts::SC-08d` | ✅ PASS |
| visual-01 Closed trigger light | `tenant-switcher-visual.smoke.spec.ts::visual-01` | ✅ PASS |
| visual-02 Closed trigger dark | `tenant-switcher-visual.smoke.spec.ts::visual-02` | ✅ PASS |
| visual-03 Open dropdown light | `tenant-switcher-visual.smoke.spec.ts::visual-03` | ✅ PASS |
| visual-04 Open dropdown dark | `tenant-switcher-visual.smoke.spec.ts::visual-04` | ✅ PASS |
| visual-05 Loading state | `tenant-switcher-visual.smoke.spec.ts::visual-05` | ✅ PASS (conditional — sin PNG por design quirk 03-arch § 8.4) |
| visual-06 Error state | `tenant-switcher-visual.smoke.spec.ts::visual-06` | ✅ PASS |
| visual-07 Modal Próximamente | `tenant-switcher-visual.smoke.spec.ts::visual-07` | ✅ PASS |
| visual-08 Active tenant badge + check | `tenant-switcher-visual.smoke.spec.ts::visual-08` | ✅ PASS |

**Total:** 26 PASS / 1 SKIP / 0 FAIL · 7 visual goldens PNG generadas (pending Chris visual ratify)

## § 2 — Playwright E2E run

Última corrida targeted F1-S3 smoke suite con workers=1 (CI default determinístico):

```bash
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase1-tenant-switcher/ --project=smoke --workers=1
```

- Specs run: 27
- Passed: 26
- Skipped: 1 (SC-03 aspirational)
- Failed: 0
- Visual goldens generated: 7 PNG (smoke-linux)
- Trace: `vitalia/frontend/playwright-report/` (on-first-retry)

## § 3 — Capabilities updated/created

- `vitalia/docs/product/capabilities/platform/tenant-switcher.yaml` — **NEW** (status: live, package_version 0.1.0, `pending_chris_visual_ratify: true`, related: shell-foundation-shadcn-tailwind-v4 + design-tokens-theme + topbar-global, depends_on_engine: core/luana-core-iam GET /api/tenants)

## § 4 — Modules MD refreshed

- `vitalia/docs/product/modules/platform.md` — auto-list block actualizado: agrega `vitalia-tenant-switcher` + reconciliación caps F1-S1/S2 (`vitalia-design-tokens-theme`, `vitalia-shell-foundation-shadcn-tailwind-v4`, `vitalia-topbar-global`) que estaban faltando en bloque auto-list (drift acumulada pre-merge)

## § 5 — How to verify (reproducible commands)

Comandos copy-paste para reproducir la verificación funcional:

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}

# 1. Stack levantado (postgres compartido + backend 8002 + frontend 3002)
make dev-vitalia

# 2. Sanity (espera ~20s + 3 health endpoints)
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8002/health           # 200
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3002/test-stack/tenant-switcher  # 200

# 3. Non-functional gates (native)
cd vitalia/frontend && npx tsc --noEmit                                          # 0 errors
cd vitalia/frontend && npx eslint src/ --max-warnings 0                          # 0 errors
cd vitalia/frontend && npx vitest run                                            # 97/97 PASS scoped F1-S3 (908/908 full baseline)

# 4. Architecture fitness (NEW: test-no-clerk-organizations + 11 ratchet tests)
cd vitalia/frontend && npx vitest run src/__tests__/architecture/                # 12/12 (55 cases)

# 5. E2E Playwright smoke (workers=1 determinístico)
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
  npx playwright test e2e/regression/vitalia-fase1-tenant-switcher/ \
  --project=smoke --workers=1
# Expected: 26 passed, 1 skipped (SC-03), 0 failed

# 6. Visual regression goldens (comparativa vs snapshots)
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
  npx playwright test e2e/regression/vitalia-fase1-tenant-switcher/tenant-switcher-visual.smoke.spec.ts \
  --project=smoke --workers=1
# Expected: 8 specs · 7 goldens PASS · visual-05 conditional (no PNG by design)
```

**Expected:** todos los comandos retornan exit code 0.

**Manual ratify pendiente (next session):** Chris compara los 7 PNG goldens en `vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/tenant-switcher-visual.smoke.spec.ts-snapshots/` side-by-side con los mockups ratificados:
- `vitalia/docs/archive/2026/stories/vitalia-fase1-tenant-switcher/mockups/tenant-switcher-closed.html`
- `vitalia/docs/archive/2026/stories/vitalia-fase1-tenant-switcher/mockups/tenant-switcher-open.html`

Si OK → `pending_chris_visual_ratify: false` en `capabilities/platform/tenant-switcher.yaml`. Si diff estructural → CHANGES_REQUESTED retroactive (re-open vía /auditor iter 3 dentro cap 3/3).

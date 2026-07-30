# 07-merge — vitalia-bugfix-shell-nav-scroll-errors

> **Merge by:** `/pm-vitalia` · **Date:** 2026-06-03 · **type:** bugfix (lite, ADR-011) · **cap_change_type:** fix
> **Verdicts:** técnico `/auditor` APPROVED (re-audit confirmado bug#2 delta) · negocio `demo_signoff` Chris APPROVED (6/6 live dev-app)
> **state:** reviewing → done

Bugfix de 6 bugs del shell-organism reportados por Chris ejerciendo dev-app.vitalialat.com.
Los 6 corregidos + verificados LIVE en dev-app. **2 over-claims del "6/6" heredado fueron
descubiertos y corregidos esta sesión** (bug#1 "build artifact" era falso → Next 16 soft-nav;
bug#2 e2e enmascaraba → /api/tenants 404).

## § 1 — Gherkin / business-rules verification matrix (Phase D)

| Regla | Scenario | Test | Estado |
|---|---|---|---|
| RN-1 routing valid landing | bug1_routing_lands_valid | `e2e/regression/shell-nav-scroll/bug1-routing-lands-valid.spec.ts` + `src/lib/shell-routes.test.ts` | ✅ PASS |
| RN-1 negative (agente inválido → 404) | bug1 negative | bug1 spec (gate OFF) | ✅ PASS |
| RN-2 tenant selector ≥1 visible | bug2_tenant_selector_visible_single_tenant | `bug2-tenant-selector-visible.spec.ts` (cold-start honesto) | ✅ PASS |
| RN-2 negative (0 tenants oculto) | empty_state_no_tenants | `fe_unit_shell` (Vitest) | ✅ PASS |
| RN-3 sin título-eco | bug3_no_redundant_sheet_title | `bug3-no-redundant-title.spec.ts` + `fe_unit_lisa_marca` | ✅ PASS |
| RN-4 contenido scrolleable | bug4_content_scrolls | `bug4-content-scrolls.spec.ts` | ✅ PASS |
| RN-5 sin banner landing | bug5_no_landing_placeholder_presencia | `bug5-no-landing-placeholder.spec.ts` (scoped gate) + `fe_knip`(env-gap) | ✅ PASS |
| RN-6 error aislado, nav viva | bug7_error_isolated_nav_alive | `bug7-error-isolated-nav-alive.spec.ts` (fault-injection) | ✅ PASS |

**0 MISSING.** Re-audit Phase D confirmó la matriz. Detalle: `CHECKPOINTS.md` + `T-review.md`.

## § 2 — Playwright E2E run

```bash
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
  npx playwright test e2e/regression/shell-nav-scroll/ --project=smoke --workers=1
# → 15 passed (6 bug specs real-backend + _live-verify dod-evidence)
```
Gate anti-burbuja REAL (specs importan `fixtures/base.ts` vía `real-backend-forward.fixture`, NO `@playwright/test` directo). Veredicto: **15/15 PASS** (re-corrido por orchestrator + auditor).

## § 3 — Capabilities updated (cap_change_type: fix → change_log append)

- `vitalia/docs/product/capabilities/shell-organism/shell-vitalia.yaml` — change_log `type: fix` (#1 routing, #2 selector, #3 dispatcher, #4 scroll, #7 error-boundary)
- `vitalia/docs/product/capabilities/brand_studio/lisa-marca.yaml` — change_log `type: fix` (#3 h2-eco, #5 banner landing)
- `vitalia/docs/product/capabilities/iam/luana-core-adoption.yaml` — change_log `type: fix` (#2 useTenants → `/api/v1/iam/users/me/tenants`)

No se crean caps nuevas ni scenarios nuevos (bugfix corrige comportamiento existente).

## § 4 — Modules MD

Sin cambios de superficie nueva → `modules/*.md` auto-list no cambia (bugfix). `make portfolio` regenera BACKLOG.

## § 5 — Cómo verificar (reproducible)

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/frontend
npx tsc --noEmit                              # 0 errores
npx eslint src/ e2e/ --cache --max-warnings 0 # 0
npx vitest run                                # 2502/2502
npx vitest run src/__tests__/architecture/    # 171/171
E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/shell-nav-scroll/ --project=smoke --workers=1  # 15/15
# Live (dev-app): make dev-app-vitalia → https://dev-app.vitalialat.com (dr.demo@vitalialat.com)
#   bug#1: recargar /{tenant} varias veces → siempre /mateo/agenda, sin "Rendered more hooks"
#   bug#2: clear localStorage vitalia-tenant-state → reload → GET /me/tenants 200 → selector "Sanaré LATAM"
```

## § Verificación live (DoD #37 · ADR-vitalia-008)

`dod_live_verified: true`. Ejercido contra **dev-app.vitalialat.com** (Cloudflare tunnel → stack real, Clerk real `dr.demo@vitalialat.com`, BE real :8002) vía Chrome DevTools MCP + docker logs + network panel:

- **#1** bare `/{tenant}` → `…/mateo/agenda` (edge-redirect proxy.ts), 0 pageerror "Rendered more hooks" (antes flake ~40%).
- **#2** cold-start (clear activeTenant → reload): `GET /api/v1/iam/users/me/tenants` **200** → selector **"Sanaré LATAM"** visible. Único call de tenants = `/me/tenants` (cero `/api/tenants`). Screenshot capturado.
- **#3** `lucas/lanzar` + marca views sin `subtab-header-*` eco.
- **#4** `app-panel-slot` content `overflow-y: auto`.
- **#5** Presencia sin "Editor de landing pública".
- **#7** e2e fault-injection (marca→500) → fallback en panel + ribbon/sub-tabs vivos.

Backend logs limpios (404/422 residuales = gaps de contrato FE↔BE pre-existentes de OTRA story: telemetry `growth-studio-event` 404, agenda `grid` 422 — NO de este bugfix).

## Notas / follow-ups (separados, NO esta story)

- **Sistémico FE↔BE / tenant-resolution:** `POST /api/telemetry/growth-studio-event` → 404 + `GET /api/v1/scheduling/agenda/grid` → 422 en dev-app. Familia [[no-clerk-organizations]] "onboarding aún LEE org". Candidato a story de contrato FE↔BE / IAM.
- **Bug de framework Next 16.2.3** (soft-nav intra-route-group → "Rendered more hooks"): el edge-redirect es un *workaround* del trigger del landing, no un fix del framework. Soft-navs profundas dentro de Agenda podrían reaparecer. Candidato a learning cross-brand (nicolify/comunify usan shells `ssr:false`).
- **Env churn** (vite/vitest version-skew del lockfile-regen + Docker file-watcher): ver `estabilizar-harness-e2e-lisa-marca/OBSERVED-env-vite-vitest-skew.md`.

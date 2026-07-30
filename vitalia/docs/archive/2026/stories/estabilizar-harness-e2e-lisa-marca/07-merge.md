<!-- voseo-allowed: doc interno de merge -->
# 07-merge — vitalia/estabilizar-harness-e2e-lisa-marca

> /pm-vitalia · Fase F · 2026-06-03 · state reviewing → done
> Tipo: bugfix-lite (harness e2e honesto + determinista + logo R2 + 5 demo-bug fixes)
> Auditor: APPROVED (CHECKPOINTS C1-C5) · demo_signoff: Chris APPROVED 2026-06-03

## § 1 — Gherkin verification matrix

Copia: `06-audit/gherkin-matrix.md`. SC-1..SC-8 sin MISSING. SC-1 (suite determinista) = PASS-con-retries
(94% ×3; 2 residuales large-dataset/voice-warning = throttle Clerk dev-FAPI, aceptado por Chris + HB-28).
Demo-bug fixes (logo 3 capas + DELETE + autosave-on-load + badge página + preview tipografía) = PASS live-verified.

## § 2 — Playwright / verificación E2E run

- Suite `e2e/regression/vitalia-fase2-lisa-marca/ ×3` contra backend real: 94% determinista (9/11 specs 100%).
- de-mock genuino (auditor-fe verificó: 0 route.fulfill sobre identity/visuals/personality, base.ts anti-burbuja, POMs web-first).
- **Live-verify REAL (curl contra :8002, no GET-200):**
  - `POST /logos → 201` → `GET /visuals` persiste logo_url → fetch URL R2 → `200 image/png`.
  - `DELETE /logos → 204` → `GET /visuals` logo_url `None` (CLEARED) → `DELETE` sin rol → `403` (RBAC).
  - `GET /visuals → 200` (colores/tipografía) + BE integration `test_marca_visuals_missing_attr 5/5` vs DB real.
- gate-runner (test-vitalia): 7/7 gates PASS (ruff, format, arch 335, brand_studio, tsc, eslint, vitest 2525).

## § 3 — Capabilities updated/created

- `vitalia/docs/product/capabilities/brand_studio/lisa-marca.yaml` (cap_change_type: **fix**):
  - change_log entry `estabilizar-harness-e2e-lisa-marca` (type=fix) · merge_sha al cerrar.
  - `admin-configura-identidad-clinica` → `verified_real` (nombre/colores/tipografía/logo).
  - `admin-configura-presencia-web` → `status: partial` (sin spec happy-path honesto).
  - 2 flaky (voice-warning, large-dataset) → `verified_real` con caveat retry.
  - bidirectional HARD cross-check 3 → 96/96.

## § 4 — Modules MD refreshed

- `vitalia/docs/product/modules/brand_studio.md` — sin cambio narrativo (bugfix, no nueva sub-tab).

## § 5 — How to verify (reproducible)

```bash
WS=$(git rev-parse --show-toplevel); cd ${WS}/vitalia/backend
set -a; source ${WS}/vitalia/.env.dev; set +a
export POSTGRES_DSN="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:5435/${POSTGRES_DB}"
${WS}/.venv/bin/pytest tests/modules/vitalia/brand_studio/test_marca_service.py -q   # 14 passed
${WS}/.venv/bin/pytest tests/architecture/ -q                                        # 335 passed
cd ${WS}/vitalia/frontend && npx vitest run src/features/lisa/                        # 371 passed

# Live (stack UP — make dev-app-vitalia):
TENANT=e69a691d-070e-5caf-a053-6e74642ec100
H=(-H "X-Tenant-ID: $TENANT" -H "X-User-ID: 11111111-1111-1111-1111-111111111111" -H "X-User-Role: owner")
curl -s -X POST localhost:8002/api/v1/lisa/marca/logos "${H[@]}" -F "file=@logo.png;type=image/png"   # 201
curl -s -X DELETE localhost:8002/api/v1/lisa/marca/logos "${H[@]}" -w "%{http_code}"                   # 204
```

## § Verificación live (rule #37)

```yaml
dod_live_verified: true
dev_app_verified: true   # ADR-vitalia-008
demo_signoff: {signed_by: Chris, date: '2026-06-03', result: APPROVED}
```

## WARNs no-bloqueantes (radar /pm-vitalia + /pm-luana)
- get_trust_signals mypy arg-type (pre-existente, runtime-safe).
- user_resolver async `get_by_clerk_id` → promotion candidate `/pm-luana`.
- **Cross-story:** avatares lisa-doctores usan mismo `AssetsService.upload_asset` → mismo FK 500 latente (mockeado) → abrir bugfix story.

## Merge note
- Squash-merge `wip/vitalia → main` DIFERIDO (single-hub con stories paralelas adrian/inbox no-auditadas). El cierre done + archive se aplica sobre wip/vitalia; el push a main se hace cuando todas las stories del hub estén listas.

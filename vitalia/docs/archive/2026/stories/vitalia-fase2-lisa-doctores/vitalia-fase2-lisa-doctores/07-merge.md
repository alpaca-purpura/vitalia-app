<!-- voseo-allowed: doc interno de proceso -->
# 07-merge — vitalia/vitalia-fase2-lisa-doctores

> Fase F (story-closure-gate). Auditor APPROVED · chris_verify.signoff SATISFIED · reconciled · state reviewing→done.
> Alcance del cierre: story completa (delta v3 mergeado 06-12 + bug7 rounds 4-6 cerrados 06-15). Este 07-merge cubre el cierre final tras los rounds bug7 de G-verify.

## § 1 — Gherkin verification matrix
Copia: `06-audit/gherkin-matrix.md` (bug7 rounds 4-6). Sin MISSING, sin FAIL. Ground truth real-backend = DB (ISODOW / excluded_dates / end_date) + geometría DOM. Delta-v3 matrix verificada en el merge 06-12 (histórico).

## § 2 — Playwright E2E run
```bash
cd vitalia/frontend
E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase2-lisa-doctores/bug7-r5-dow.spec.ts --project=smoke --workers=1   # 8/8
E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase2-lisa-doctores/bug7-r4-dow.spec.ts --project=smoke --workers=1   # 22 casos
E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase2-lisa-doctores/bug7-r3-*.spec.ts --project=smoke --workers=1     # regresión 16
```
Verdict: GREEN (r5 8/8 · r4 22 · r3 16, 1 flaky retry-OK). Real-backend, cero mocks del surface availability.

## § 3 — Capabilities updated
- `vitalia/docs/product/capabilities/clinics/lisa-doctores.yaml` (status: live · ya live desde 06-12):
  - change_log += entry 2026-06-15 type=fix (bug7 rounds 4-6).
  - scenarios += `dia-de-semana-tz-paint`, `borrar-recurrente-scope`, `no-crear-en-pasado`, `occurrences-ciclos-completos` (status verified_real).
  - business_rules += `RN-D3F-4` (día-de-semana TZ), `RN-D3G-1` (delete scope), `RN-D3G-2` (no-crear-pasado); `RN-D3F-2` reescrita (N ciclos completos).
  - scenario `recurrencia-google-editor` corregido (8 repeticiones = 16 ocurrencias).
  - `make cap-doctor BRAND=vitalia` → ✅ SANO 0 deriva.

## § 4 — Modules MD refreshed
- `vitalia/docs/product/modules/clinics.md` — auto-list regenera via `make portfolio` post-merge (R3, no editar manual).

## § 5 — How to verify
```bash
# BE: semántica + scoped delete + past guard
cd vitalia/backend && ${WS}/.venv/bin/pytest tests/modules/vitalia/clinics/ -q   # 457
# FE unit
cd vitalia/frontend && npx vitest run src/features/lisa/ src/lib/format/   # 525
# Migración aplicada
docker exec luana-dev-vitalia_backend_dev-1 bash -c "cd /workspace/vitalia/backend && /workspace/.venv/bin/alembic current"  # 044_vitalia
# Live (dev-app): Lisa → doctor → Horarios → crear weekly lunes (pinta Lun) · borrar recurrente (diálogo scope) · Mar+Jue ×3 (6 turnos)
```

## Trazabilidad
- Commits bug7: `8d211f8f` (r4 día-de-semana) · `e3c79f3a` (r5 FE) · `fe8786d4` (r5 BE migr 044) · `3c75252b` (r5 e2e) · `2ba3852d` (r6 ciclos) · `486701fa` (R reconcile) · `a2c243cb` (audit).
- chris_verify.signoff: SATISFIED (Chris, 2026-06-15, rounds 1-6).
- Auditor: CHECKPOINTS.md APPROVED (C1-C5, 0 bloqueantes) · T-bug7-{be,fe}-review.md APPROVED.
- Result docs: T-FIX-bug7-round{4,5,6}-result.md + T-FIX-bug7-round5-{BE,FE}-result.md.

## Open items (NO bloquean · ruteados a CIL)
- Bloques multi-día creados pre-round6 no auto-corrigen (editar/recrear) — open_item registrado.
- WARN CIL: repo-mock service tests (L3) · test guard-strength (L3) · docstring stale orgId (quick-win) · pre-existente pgcrypto `treatment_plans.notes` TEXT módulo CRM (L4, otra story).

## Integración a main
⏸ **PENDIENTE OK de Chris.** El squash-merge `wip/vitalia → main` (integración + staging deploy MANUAL per git-safety) NO se ejecuta sin ratificación explícita. El cierre a `done` + archive vive en `wip/vitalia`.

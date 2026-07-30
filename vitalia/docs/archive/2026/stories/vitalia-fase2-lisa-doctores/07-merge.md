# 07-merge — vitalia/vitalia-fase2-lisa-doctores (DELTA v3 → done)

> /pm-vitalia · 2026-06-12 · Verdict auditor: APPROVED (CHECKPOINTS C1-C5 26/26) · autonomous run completo (mandato Chris 2026-06-12 01:40)

## § 1 — Gherkin verification matrix
Copia congelada: `06-audit/gherkin-matrix.md` — **41/41 SCs delta PASS** (BE 440/440 · FE 501+139 · e2e real-backend: switcher 6/6 · editor 4/4 · axe 2/2 · D3-E 4 · batería D3-C/F BE). Build mayo: matriz histórica T-E2E-result.md (sin regresión — suites superset verdes).

## § 2 — Playwright E2E run
`cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/specs/vitalia/pagina-publica-editor.spec.ts e2e/specs/vitalia/a11y/pagina-publica-axe.spec.ts` → **6/6 GREEN** (real-backend, anti-burbuja base.ts — el 422 residual del editor lo cazó este gate y se fixeó pre-merge). Delta specs por ticket corridos live durante build+audit.

## § 3 — Capabilities updated
- `vitalia/docs/product/capabilities/clinics/lisa-doctores.yaml` → **status: live** · F.3 **extend** (change_log delta v3 + 6 scenarios verified_real + business_rules RN-D3A-2/D3B-4/D3D-9/D3F-2 + access + dev_preview refresh con 4ª hoja/picker/mes/público) · `make cap-doctor BRAND=vitalia` = 0 deriva.

## § 4 — Modules MD refreshed
`vitalia/docs/product/modules/clinics.md` auto-list → regen vía `make portfolio` (R3 — post-commit).

## § 5 — How to verify (reproducible)
1. `make dev-vitalia` + migraciones: `docker exec luana-dev-vitalia_backend_dev-1 bash -c "cd /workspace/vitalia/backend && /workspace/.venv/bin/alembic upgrade head"` (head = 043_vitalia).
2. Login dr.demo → Lisa → Staff → doctor → **demo-script.md (14 pasos)**: switcher ▾ preserva hoja · bloque ×2 reps pinta EXACTAMENTE 2 · vista Mes · editor Google con resumen humano · hoja Página: subir PDF real + generar perfil + Publicar + abrir `/d/{clinica}/{doctor}` en incógnito (Doctoralia + og + anti-enum).
3. Suites: `pytest tests/modules/vitalia/clinics/` (440) · `npx vitest run src/features/lisa` (501) · e2e §2.

## Residuales (no bloquean — registrados)
- **Followups Chris (signoff pre-autorizado chris-input 01:40):** self-test live + ratificar goldens V-VIS-1..4 (ADR-003). Hallazgo del self-test → bugfix follow-up, no reabre.
- **CIL:** HB-42 contract-test FE↔BE (**prio 1** — 10 instancias esta story) · HB-71 (capturado) · W2 jscpd scoped · W5 e2e-mock D3-C/E · 4 WARNs BE mayo menores · EntityPicker contrast token (core, pin en spec).
- **Integración a main:** squash wip/vitalia→main = acción de integración estándar separada (no parte del done de story).

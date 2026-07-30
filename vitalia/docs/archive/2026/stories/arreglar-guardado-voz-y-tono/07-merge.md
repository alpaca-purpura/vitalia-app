# 07-merge — vitalia/arreglar-guardado-voz-y-tono

> Type: bugfix (lite) · Merged by: /pm-vitalia · Date: 2026-05-31 · Verdict auditor: APPROVED

## § 1 — Gherkin verification matrix

Ver `06-audit/gherkin-matrix.md`. Resumen: 6/8 scenarios determinísticos verde (los 2 núcleos del bug
reportado + secundario 422 + PHI redaction + cross-tenant + enum-inválido); 2 quarantined (error-UX + a11y)
con pointer a `estabilizar-harness-e2e-lisa-marca` (race auth-readiness Clerk pre-existente del harness).

## § 2 — Playwright E2E run

```bash
cd vitalia/frontend
E2E_TENANT_ID=e69a691d-070e-5caf-a053-6e74642ec100 VITALIA_PE_TENANT_ID=e69a691d-070e-5caf-a053-6e74642ec100 \
  E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/arreglar-guardado-voz-y-tono/ --project=smoke
```
Verdict: **6 passed, 5 skipped (quarantined), 0 failed/flaky** — determinista (2 corridas). Real backend
(arquetipo autosave 3.8s · bloque no-422 11.9s confirmado `--reporter=list --workers=1`).

## § 3 — Capabilities updated/created

- `vitalia/docs/product/capabilities/brand_studio/lisa-marca.yaml` — change_log entry type=fix (arreglar-guardado-voz-y-tono)
  · scenario `admin-define-voz-y-tono` e2e_test: null → `voz-arquetipo-autosave.spec.ts` · last_modified 2026-05-31.
  (cap_change_type=fix → sin scenarios nuevos.)

## § 4 — Modules MD refreshed

- `vitalia/docs/product/modules/brand_studio.md` — auto-list regenera vía reconcile (sin cambio manual).

## § 5 — How to verify (reproducible)

```bash
WS=$(git rev-parse --show-toplevel)
# 1. BE — sanitize + DTO + telemetry tests
cd $WS/vitalia/backend && $WS/.venv/bin/pytest tests/modules/vitalia/audit/test_audit_writer_sanitize.py tests/modules/vitalia/brand_studio/test_patch_personality_audit.py -v
# 2. Live (stack make dev-vitalia) — el bug reportado ya no ocurre:
curl -s -o /dev/null -w "%{http_code}\n" -X PATCH http://127.0.0.1:8002/api/v1/lisa/marca/personality \
  -H "X-Tenant-ID: e69a691d-070e-5caf-a053-6e74642ec100" -H "X-User-ID: 00000000-0000-0000-0000-000000000000" \
  -H "X-User-Role: owner" -H "Content-Type: application/json" -d '{"archetype":"sage"}'   # → 200 (era 500)
# 3. E2E (ver § 2)
```

## Commits

`38aa5c8b` `98a903a5` `a0060e7a` `81b13787` `2b12924e` `560a5f54` `f19a21c3` `24331331` `a0e6373f` `38a45c4e`

## Follow-up

`estabilizar-harness-e2e-lisa-marca` (creada, state=idea): race auth-readiness Clerk (re-habilita quarantined) +
de-mock specs lisa-marca restantes + prohibited-phrases X-User-ID + audit-actor X-User-ID + contraste WCAG.

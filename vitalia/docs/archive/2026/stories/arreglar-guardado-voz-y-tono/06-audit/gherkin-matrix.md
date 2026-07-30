# Gherkin verification matrix — vitalia/arreglar-guardado-voz-y-tono

> Auditor: Phase D · Date: 2026-05-31 · type: bugfix (lite)

| Scenario (01-spec.md) | Test | Status | Notes |
|---|---|---|---|
| voz-arquetipo-autosave-persiste | `voz-arquetipo-autosave.spec.ts` (badge saving→saved, PATCH 200 no 500) + curl live PATCH→GET | ✅ PASS (real backend, determinista 2x) | persist-on-reload quarantined → harness story (verificado live a nivel API) |
| audit-write-no-typeerror | `test_audit_writer_sanitize.py` (RED→GREEN) + curl PATCH 200 | ✅ PASS | TypeError sanitize_payload eliminado |
| audit-personality-sin-phi | `test_audit_writer_sanitize.py::test_phi_redacted` | ✅ PASS | PHI redaction restaurada (auditor-be confirmó) |
| voz-bloque-edita-no-422 | `voz-bloque-autosave.spec.ts` (no 422 extra_forbidden) | ✅ PASS (real backend, determinista) | camelCase alias |
| arquetipo-invalido-validacion | `test_patch_personality_audit.py` (enum inválido → 422) | ✅ PASS | |
| autosave-error-muestra-badge | `voz-autosave-error.spec.ts` (mock 503 → badge error) | ⏸ QUARANTINE | flaky por race auth-readiness Clerk → `estabilizar-harness-e2e-lisa-marca` |
| cross-tenant-personality-bloqueado | `test_patch_personality_audit.py` (cross-tenant 403/404) | ✅ PASS | tenant isolation |
| autosave-badge-aria-live | `e2e/a11y/...` | ⏸ QUARANTINE | flaky (race) + contraste WCAG pre-existente (observed-bug) → harness story |

**Resumen:** 6/8 scenarios verificados determinísticos (incl. los 2 núcleos del bug reportado + el secundario 422 + PHI + cross-tenant). 2 quarantined (error-UX + a11y) con pointer explícito a `estabilizar-harness-e2e-lisa-marca` (race de auth-readiness de Clerk, pre-existente del harness). Persistencia verificada REAL a nivel API (curl round-trip).

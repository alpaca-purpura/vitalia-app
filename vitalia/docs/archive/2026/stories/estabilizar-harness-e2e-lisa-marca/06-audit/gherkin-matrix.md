<!-- voseo-allowed: doc interno de auditoría -->
# Gherkin verification matrix — vitalia/estabilizar-harness-e2e-lisa-marca

> Auditor: Phase D · Date: 2026-06-03 · Verdict: APPROVED

| Scenario (01-spec) | Verificación | Status | Notas |
|---|---|---|---|
| SC-1 suite determinista | `e2e/regression/vitalia-fase2-lisa-marca/ ×3` | **PASS·retries** | 94% determinista (9/11 specs 100%). 2 residuales (large-dataset, voice-warning) = throttle Clerk dev-FAPI (infra externa), verde-con-retries=1 aceptado por Chris 2026-06-03 + HB-28 (scaling) |
| SC-2 no-mock backend-bajo-prueba | grep gate `route.fulfill` sobre identity/visuals/personality → 0 | **PASS** | de-mock genuino (auditor-fe verificó: 0 mocks, forwarding real + base.ts) |
| SC-3 anti-burbuja adoptado | grep `@playwright/test` directo → 0 + base.ts runtime gate | **PASS** | specs importan de `e2e/fixtures/base.ts` |
| SC-4 reload-persist web-first | `arreglar-guardado-voz-y-tono/ ×5` (5 fixme des-quarantined) | **PASS** | asserts web-first (polling), no once-reads |
| SC-5 sin listeners dangling | grep `page.on ... void` → 0 + repeat-each | **PASS** | sin fire-and-forget |
| SC-6 audit actor real | BE `_resolve_audit_actor` (clerk_sub→users.id) + FE actor headers | **PASS** | T-2 + T-3; auditor-be APPROVED |
| SC-7 prohibited-phrases browser real | BE `X-User-ID` opcional en GET | **PASS** | T-3; auditor-be APPROVED |
| SC-8 cap honesto | cap `lisa-marca.yaml` → specs de-mockeados + verified_real | **PASS** | T-4; presencia-web → partial; bidirectional HARD 96/96 |

## Demo-bug fixes (más allá del Gherkin original — cazados por el demo de Chris, live-verified)

| Fix | Verificación REAL | Status |
|---|---|---|
| Logo R2 — storage real (FK 500) | POST /logos 201 → fetch URL 200 image/png | **PASS** |
| Logo — persist location (identity.visuals) | POST → GET /visuals persiste logo_url | **PASS** |
| Logo — next/image host R2 | `/_next/image` → 200 image/png | **PASS** |
| Logo — DELETE contract (auditor FAIL-1) | DELETE /logos 204 → GET None (CLEARED) → sin rol 403 | **PASS** |
| Autosave-on-load (badge "guardado ahora") | IdentityCard skip first effect run | **PASS** (test) |
| Badge nivel-página (colores/tipografía) | aggregateAutosaveStatus + 1 badge cabecera | **PASS** (test 6) |
| Preview tipografía (fuentes no cargaban) | ensureGoogleFont inyecta link | **PASS** (test 3) |
| "Eliminar logo" placement | junto a "Cambiar logo" en LogoDropZone | **PASS** (test) |

**Sin MISSING.** SC-1 con caveat de retries documentado (decisión Chris + HB-28).

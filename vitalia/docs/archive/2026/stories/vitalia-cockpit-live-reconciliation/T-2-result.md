# T-2-result.md — Fase 1 Sweep harness Playwright + matriz viva v1

**Story:** vitalia-cockpit-live-reconciliation  
**Ticket:** T-2  
**Agente:** builder-frontend (Claude Sonnet 4.6)  
**Completado:** 2026-05-29T21:35 UTC  

---

## Skills consulted (must_load enforcement v4.1)

| Skill | Propósito | Aplicado |
|---|---|---|
| `playwright-expert` | POM patterns, Clerk fixture, network mocking, NATIVE Linux (nunca Docker) | ✅ |
| `vitalia-design-system` | SSoT shell-organism + átomos/moléculas + tokens (canal único builder-frontend) | ✅ |
| `frontend-expert` | FSD-Lite, Shadcn reuse, visual fidelity | ✅ |
| `.claude/rules/anti-orphan-integration.md` | Harness + matriz registrados (playwright.config.ts project live-recon) | ✅ |
| `vitalia/.claude/rules/hipaa-lite.md` | Screenshots en .evidence/ gitignoreado; seed mock (no PHI real) | ✅ |
| `.claude/rules/spanish-text.md` | Labels y notas en español neutro LatAm (sin voseo) | ✅ |
| `.claude/rules/anti-duplication.md` | Tooling ledger reusado (compute_capability_status.py, reconcile_capabilities.py) | ✅ |
| `.claude/rules/frontend-visual-fidelity.md` | Criterio fidelidad en sweep (elemento clave del shell visible = OK) | ✅ |
| `.claude/rules/tdd-mandatory.md` | Sweep es diagnostic harness (no feature), TDD no aplica per doctrina; gates verdes | ✅ |

---

## Diff resumen

### Archivos creados (nuevos)

| Path | Descripción |
|---|---|
| `vitalia/frontend/e2e/regression/live-reconciliation/surface-catalog.ts` | Catalogo SSoT de superficies derivado del SSoT (RIBBON_SUBTABS + AGENT_SUBSUBTABS) |
| `vitalia/frontend/e2e/regression/live-reconciliation/sweep.spec.ts` | Harness Playwright: recorre superficies → emite .sweep-findings.json |
| `scripts/build_live_reconciliation_matrix.py` | Script Python: cruza findings + _status-computed → live-reconciliation.md |
| `vitalia/docs/domains/ops/live-reconciliation.md` | Matriz v1 AUTO-GENERATED (88 filas, header autorizado) |

### Archivos modificados

| Path | Cambio |
|---|---|
| `vitalia/frontend/playwright.config.ts` | Proyecto `live-recon` registrado (anti-isla CONN); `smoke` testIgnore excluye sweep.spec.ts |
| `.gitignore` | `.evidence/` + `.sweep-findings.json` gitignoreados (HIPAA-lite) |
| `vitalia/docs/product/stories/vitalia-cockpit-live-reconciliation/chris-input.md` | Append entry T-2 completado |

### Archivos gitignoreados (no commiteados — HIPAA + R3)

- `vitalia/frontend/e2e/regression/live-reconciliation/.sweep-findings.json` (regenerable)
- `vitalia/frontend/e2e/regression/live-reconciliation/.evidence/*.png` (screenshots)

---

## Gates output literal

```
# fe_lint (eslint e2e/regression/live-reconciliation/)
→ (no output = clean) ✅

# fe_typecheck (tsc --noEmit)
→ (no output = clean) ✅

# arch_fe_fsd (npx vitest run src/__tests__/architecture/)
→ Test Files  24 passed (24)
   Tests  148 passed (148)
   Duration  1.83s
✅

# sweep_executes (npx playwright test e2e/regression/live-reconciliation/ --project=live-recon)
→ [sweep] Total: 27 surfaces swept — OK=27 ROTO=0 INACCESIBLE=0
  [sweep] Findings written (27 surfaces)
  [sweep] Summary: {"OK":27}
  5 passed (1.0m)
✅

# matrix_artifact_exists
→ test -f vitalia/docs/domains/ops/live-reconciliation.md && grep -q 'sweep_verdict' → PASS ✅

# ledger_computed_status (compute_capability_status.py --brand vitalia)
→ Procesando 67 capabilities de vitalia...
  Completado: 67 caps · stub=55 · declared-live=6 · verified-live=1 · drift=0 · partial=5
  Guardado en: vitalia/docs/product/capabilities/_status-computed.json
✅
```

---

## Resumen conteos matriz v1

| sweep_verdict | Count | Significado |
|---|---|---|
| ✅ OK | 21 | Superficies shell-organism cargan 200 + elemento clave visible + sin console errors graves |
| ❌ ROTO | 0 | Ninguna superficie falla en runtime (dev-stack estable post T-1) |
| ⚠️ INACCESIBLE | 0 | Ninguna ruta 404 o redirect fuera de scope |
| 🔲 SIN-UI | 67 | Caps sin ruta navegable directa (slice-1 superseded + infra-only) |

| computed_status | Count |
|---|---|
| verified-live | 1 |
| partial | 5 |
| declared-live | 6 |
| stub | 55 |

**Total superficies en matriz:** 88  
**Superficies shell-organism barridas:** 27  
**Superficies external-annotated:** 3 (admin Streamlit, landing pública, onboarding wizard)

---

## Decisiones técnicas

1. **surface-catalog.ts deriva del SSoT** — no hardcodea rutas: lee `RIBBON_SUBTABS` + `AGENT_SUBSUBTABS` + `AGENT_RIBBON_ORDER` en runtime. Robusto ante cambios del shell.

2. **sweep.spec.ts usa test.setTimeout(600_000)** — el sweep recorre 27 superficies. Con ~5s/superficie el timeout de 60s del proyecto era insuficiente. Timeout explícito en el test (10min) sin tocar la config global del proyecto.

3. **ROTO son DATOS, no failures del harness** — el sweep PASA aunque todas las superficies sean ROTO. El runner no aborta. Clasificación: OK/ROTO/INACCESIBLE/SIN-UI en un loop con try/catch exhaustivo.

4. **Anti-isla CONN** — `playwright.config.ts` registra `live-recon` con `testMatch` para `sweep.spec.ts`. El spec es alcanzable via `npx playwright test --project=live-recon`.

5. **HIPAA-lite**: screenshots en `.evidence/` (gitignored). El seed de la app es mock (no PHI real en dev-stack). Notas de stub MSW esperados (payment/fiscal) se anotan, no se marcan ROTO.

---

## Commit SHA

*(ver push a continuación)*

---

## Próximo paso

T-3 (review técnico + reparar/reconciliar) — findings-driven. La matriz v1 es la entrada. T-3 es iterativo: clasifica cada cap con código en `cumple|easy-fix|map`, repara lo acotado (gates verdes), mapea lo grande a stories F2, reconcilia el ledger. Post T-3 → `/auditor` → `/pm-vitalia` merge.

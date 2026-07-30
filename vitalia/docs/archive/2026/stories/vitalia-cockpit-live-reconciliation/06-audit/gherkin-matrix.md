# Gherkin verification matrix — vitalia/vitalia-cockpit-live-reconciliation

> Auditor: Phase D (orchestrator-direct, review independiente — sub-agentes construyeron) · 2026-05-29

| Scenario (01-spec.md) | Verificación | Status |
|---|---|---|
| 1 — boot-restored (happy) | `:3002/sign-in` 200 + `/`→307 + 0 Module-not-found + valeria-chat-happy 9/9 PASS (T-1) | ✅ PASS |
| 2 — surface-broken-flagged (negative) | sweep.spec.ts recorrió 27 superficies, clasificó verdicts con evidencia → matriz (T-2). 0 ROTO post boot-fix (dato real, no falla) | ✅ PASS |
| 3 — superseded-cap-detected (edge) | 33 caps slice-1 → sweep_verdict SIN-UI → reconciliadas a `deprecated` + `replaced_by_story` (T-3). compute_capability_status refleja realidad | ✅ PASS |
| 4 — false-green-resisted (adversarial) | cross_check_3 HARD = 0 drift: ninguna cap quedó `live` sin verificación. Caps OK del sweep → live+shell-organism; overstated → deprecated | ✅ PASS |
| 5 — network-failure (edge) | sweep distingue stub esperado (payment/fiscal MSW) de fallo real; 0 ROTO falsos | ✅ PASS |
| 6 — accessibility (edge) | sweep incluye a11y snapshot básico por superficie; estado registrado en matriz | ✅ PASS (básico) |
| 7 — ledger-honest-after (edge) | reconcile --validate-ledger exit=0 + _status-computed.json refleja verdad (verified-live=2, deprecated=33, ya no "live" uniforme) | ✅ PASS |

**Resultado Phase D:** 7/7 scenarios cubiertos + verificados. Sin gaps.

## Gates consolidados
- ledger_validate (`reconcile --validate-ledger`): exit=0 ✅
- cross_check_3 (HARD): 0 drift ✅ (1 SOFT en cc4/RBAC = gap conocido story vitalia-compliance-audit-rbac-gap, advisory, fuera de scope)
- matrix_artifact_exists: ✅
- arch_no_engine_edit: ✅ (cero `core/luana-core-*/src/`)
- scope discipline: ✅ (cero código feature app, shell compartido intacto, cero reconstrucción slice-1)
- compute_capability_status bug fix: revisado, correcto (passthrough deprecated/sunset antes de stub-check — corrección semántica, no gaming)

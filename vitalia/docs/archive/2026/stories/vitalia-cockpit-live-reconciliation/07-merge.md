# 07-merge — vitalia-cockpit-live-reconciliation

> Story technical-story. Merge Fase F · 2026-05-29. Verdict auditor: APPROVED (CHECKPOINTS C1-C5).

## § 1 — Gherkin verification matrix
Copia: `06-audit/gherkin-matrix.md`. 7/7 scenarios verificados:
boot-restored ✅ · surface-broken-flagged ✅ · superseded-cap-detected ✅ · false-green-resisted ✅ · network-failure ✅ · accessibility ✅ · ledger-honest-after ✅.

## § 2 — Playwright E2E run
- `vitalia/frontend/e2e/shell-organism/valeria-chat-happy.spec.ts` → 9/9 PASS (17.9s) — confirma boot + shell-organism render (T-1).
- `vitalia/frontend/e2e/regression/live-reconciliation/sweep.spec.ts` (project `live-recon`) → 27 superficies barridas, runner PASS, verdicts emitidos (T-2). Resultado: **OK=27, ROTO=0, INACCESIBLE=0, SIN-UI=67**.

## § 3 — Capabilities updated/created (Fase F.3 · cap_change_type: new + mantenimiento)
- **NUEVA:** `vitalia/docs/product/capabilities/ops/live-reconciliation-sweep.yaml` (status live, scenario + e2e → sweep.spec.ts, cross_check_3 pass).
- **RECONCILIADAS (67):** status honesto + `ui_paradigm` + `replaced_by_story`:
  - 33 → `deprecated` + `slice-1-superseded` + `replaced_by_story` (mapeadas a 20 stories F2)
  - 11 → `live` + `shell-organism` (navegables verificadas por sweep)
  - 10 → `infra-only` · 5 → `admin-panel` · 1 → `public-landing` · 7 → `planned` (sin cambio)
- **Foto del ledger antes → después:** 67 caps (verified-live=1, stub=55, deprecated=0) → 68 caps (verified-live=2, deprecated=33, stub=27). El cockpit ahora dice la VERDAD.
- **Tooling fix:** `scripts/compute_capability_status.py` — passthrough deprecated/sunset antes del stub-check (corrección semántica).

## § 4 — Artefacto vivo + backlog mapeado
- `vitalia/docs/domains/ops/live-reconciliation.md` — matriz SSoT cap↔realidad (88 filas) + sección "Backlog mapeado" (33 caps slice-1 → 20 stories F2-S2..S22 priorizadas con evidencia). Es la cap `ops.live-reconciliation-sweep`, **promotable cross-brand**.

## § 5 — How to verify (reproducible)
```bash
WS=$(git rev-parse --show-toplevel); cd $WS
# Boot OK
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3002/sign-in   # 200
# Ledger honesto
.venv/bin/python scripts/compute_capability_status.py --brand vitalia      # verified-live=2 deprecated=33
.venv/bin/python scripts/reconcile_capabilities.py --brand vitalia --validate-ledger; echo exit=$?  # exit=0
.venv/bin/python scripts/validate_code_cap_bidirectional.py --brand vitalia | grep "in HARD checks"  # 0
# Sweep
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/live-reconciliation/ --reporter=line
# Matriz
cat vitalia/docs/domains/ops/live-reconciliation.md
```

## § 6 — Commits del story
- `8e3015dd` T-1 boot fix (remount core/)
- `02977169` T-2 sweep harness + matriz v1
- `5b85b869` T-3 ledger honesto (68 caps + backlog F2)
- `7bb98f83` audit APPROVED (CHECKPOINTS + Phase D)
- (lateral) `2f63b70f` fix registro builder-* + `81c3fa0b` learning tooling

## § 7 — Pendiente Chris (merge-a-main gated)
El squash-merge `wip/vitalia → main` queda **gated a Chris** (no autonomous): hay sesión paralela activa en wip/vitalia + main es integración con staging deploy MANUAL. Cuando Chris lo decida, se hace desde el worktree main per `git-safety.md § triple-branch`.

## Resultado net
- ✅ El 500 que veía Chris al entrar: RESUELTO (boot fix, causa raíz cerrada).
- ✅ Nada navegable roto (0 ROTO) — los "errores" eran 100% el drift de boot.
- ✅ Cockpit honesto: 67 caps reconciliadas, ya no sobre-declara `live`.
- ✅ Backlog F2 priorizado con evidencia (lo "faltante" = 20 stories Fase 2, no bugs).

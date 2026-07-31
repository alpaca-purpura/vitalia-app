# Definition of Done — Live Verification contra dev-app (ninguna story es `done` sin que Claude la ejerza en el stack real)

> **Slim stub (W1 harness-refactor 2026-06-08).** Detalle operativo completo (infra + política de credenciales + las dos herramientas + el bar honesto + anti-masking + DoD endurecida §1-6 + obligación por skill + registro + troubleshoot + 11 enforcement layers) en `docs/rules-detail/definition-of-done-live-verify.md` — load on-demand. **Origen:** sesión 2026-05-31 (caso histórico nicolify-r0-shell `done` sin live-verify + caso lisa-marca). **Critical Rule #37.** **Cement-date:** 2026-05-31. URLs/creds/ports/dev-app/`mutation_gate.py` → seam `live_verify_infra` en `project.config.yaml`.

## Regla cardinal

Ninguna story con UI o endpoint alcanza `state: done` hasta que **Claude la haya ejercido contra el stack de desarrollo real de la marca, leído los logs, y confirmado el efecto** — y lo haya **registrado** con `dod_evidence`. Se ejerce **la acción real (sobre todo writes: POST/PATCH/PUT/DELETE)** contra `dev-app.vitalialat.com` (o `localhost:3002` fallback) con Clerk real + usuario de prueba, observando el efecto (fila DB / cambio de estado / log). Claude **NUNCA declara `done` / "funciona" / "verificado" / "shipped"** por suite verde, build OK, o `GET 200`.

> El verde de los gates (tsc/eslint/vitest/pytest/playwright) es **necesario pero nunca suficiente**. La DoD se cierra **ejerciendo la acción real del usuario en la app corriendo + leyendo logs + confirmando el efecto**. Una e2e que **mockea el backend del surface bajo prueba** NO cuenta (falso verde — caso lisa-marca).

## Naturaleza + gates (resumen — detalle §1-6 en el detail)

- **`verification_nature`** (key **top-level** en `04-validators.yaml` · D-X4) ∈ `técnica | funcional | ambas` — lo declara `/architect`. Los gates se keyean por naturaleza, NUNCA por el WT label.
- **técnica** → gates automáticos (tsc/mypy → ruff/eslint → arch-fitness → unit/integration) + **verificación-por-efecto** (leer el efecto/logs). Sin demo, sin anti-burbuja. **Opt-in por naturaleza** (architect activa en `04-validators technical_gates`): Schemathesis (endpoints nuevos) · Hypothesis (invariantes) · **MUTATION GATE diff-scoped** `scripts/mutation_gate.py` (mutmut BE / Stryker FE · HB-54 · esta §2 lo aloja): 100% mutantes muertos sobre líneas NUEVAS; survivor líneas-nuevas → CHANGES_REQUESTED; survivor heredado → CIL L4; **DEGRADA advisory** si el tool falta (no rompe ci-parity).
- **funcional** → además: **gate anti-burbuja** (`vitalia/frontend/e2e/fixtures/base.ts` — pageerror/console-error/`/api` ≥400/Next overlay; specs importan `base.ts`, NO `@playwright/test`) + cobertura de **cada regla de negocio** (gherkin `@rule-ID` matrix) + **demo manual** (Chris firma en G).
- **Demo / signoff = UN solo campo `chris_verify.signoff`** (proceso v5: se ejerce en **G** `AWAIT_CHRIS_VERIFY`, ANTES del auditor — el viejo `demo_signoff` está RETIRADO, no se duplica). `result ∈ {SATISFIED, SATISFIED_WITH_FOLLOWUPS(sev≤medium), REJECTED}`.
- **★ Cobertura = colaborador real, no mock (seam testing · HB-94):** un test que mockea el colaborador del otro lado de la costura (seam) bajo prueba NO cuenta como cobertura de esa costura (`test-design-doctrine.md § Cobertura = colaborador real, no mock`). La costura **código↔Clerk/auth** (session timing `isLoaded`, JWT expiry 60s, refresh) NO es unit-testeable con mock → **la live-verify de esta regla (#37) es su ÚNICA cobertura** — por eso es backstop no-opcional, no un lujo. `/architect` declara la costura + el `test_type` por escenario en `04-validators § test_construction_plan.seam_coverage`; Phase D rechaza cobertura mock-only de escenarios de costura.

## Registro obligatorio (evidencia, no palabra)

```yaml
dod_live_verified: true
dod_env: "make dev-app-vitalia → dev-app.vitalialat.com (Chrome DevTools MCP)"   # o "localhost:300X" fallback
dod_evidence:
  - action: "PATCH personality voz/arquetipo + guardar (autenticado dr.demo@vitalialat.com)"
    observed: "toast OK + badge 'guardado', valor persiste al recargar"
    backend_log: "PATCH /personality 200 · DB personality_profiles.updated_at actualizado · sin traceback"
verified_at: 2026-05-31
```

Sin `dod_live_verified: true` + `dod_evidence` (writes ejercidos + efecto observado) → la story NO pasa a `done`. Funcional (`demo_required: true`) → además `chris_verify.signoff` (en G).

## Cuándo carga el detalle

- Vas a ejercer una live-verify (cómo levantar dev-app, qué credenciales) → infra + política de usuarios/claves.
- `/architect` declara `04-validators` (verification_nature/technical_gates/business_rules/demo_required/regression_guard) → DoD endurecida §1-6.
- `/auditor` Phase D o `/pm-vitalia` Fase F → obligación por skill + enforcement layers.
- Una live-verify "verde" parece sospechosa → § Anti-masking (slug≠UUID · cold-start · orphan-mount).

## Anti-patterns (top 4 — lista completa en el detalle)

- ❌ Declarar `done`/"funciona"/"shipped" con suite verde sin ejercer la acción real en el stack corriendo
- ❌ "Verificado" porque un `GET` dio 200 (sin write ni leer logs); o e2e que mockea el backend presentada como live-verify
- ❌ `07-merge.md` con `state: done` y el box de DoD live **sin tildar** (caso origen nicolify-r0-shell)
- ❌ `/pm-vitalia` mergeando a `done` sin `dod_live_verified: true` + `dod_evidence` (+ `chris_verify.signoff` si funcional)

## Enforcement (gates · detalle = 11 layers en el detail)

Pre-commit MECÁNICO `scripts/git/dod-evidence-gate.sh` (bloquea transición a `developed|done` funcional sin `dod_live_verified`+`dod_evidence`; presence-enforcement, fail-OPEN + `DOD_GATE_ACK=1`) · `/dev-team` developed-boundary HARD gate · `/auditor` auto-FAIL `LIVE_VERIFY_MISSING` + ejerce ≥1 write live · `/pm-vitalia` Fase F REFUSE merge. La **verdad** la dan `chris_verify.signoff` (humano, G) + auditor live; el hook solo verifica presencia.

## Referencias

- `docs/rules-detail/definition-of-done-live-verify.md` — **detalle completo** (infra, creds, herramientas, bar, anti-masking, §1-6, obligación por skill, 11 layers)
- `.claude/rules/test-design-doctrine.md § Verificación REAL ≠ HTTP 200` — la doctrina + el bar honesto
- `.claude/rules/story-closure-gate.md § Fase G/F` — G (chris_verify.signoff) + F (merge→done)
- `.claude/skills/{chrome-devtools-verify,playwright-expert}/SKILL.md` — mecanismos de live-verify
- `vitalia/docs/architecture/ADR-vitalia-008-dev-app-live-verification-gate.md` — el GATE concreto en vitalia
- `MEMORY.md` → `dod-live-verify` · `verification-real-not-200`

<!-- voseo-allowed: doc interno de proceso, no user-facing -->

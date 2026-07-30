# 07-merge-template.md — Story closure merge artifact

> Owner: `/pm-{brand}`. Escrito SOLO tras `/auditor` CHECKPOINTS.md verdict=APPROVED + Phase D gherkin matrix all PASS.
> Cementa los cambios al producto + reproduce verificación. `/pm-{brand}` REHÚSA transition `reviewing → done` si missing alguna de las 5 secciones obligatorias.
>
> **Cement-date:** 2026-05-18 (story-closure-gate). Stories transitioned a reviewing pre-2026-05-18 quedan exentas del schema estricto.
>
> SSoT: `.claude/rules/story-closure-gate.md` § Contrato `07-merge.md` + `docs/process/story-closure-gate.md`.

---
story_id: STORY_ID
brand: BRAND_SLUG                     # vitalia | nicolify | comunify | lupulo | platform
release: PARENT_RELEASE_ID            # release del brand (contenedor temporal)
merged_at: 2026-05-18T20:00Z
merged_by: /pm-{brand}
commit_squash_sha: abcd1234            # SHA del squash-merge wip/* → main
checkpoints_path: "../CHECKPOINTS.md"
gherkin_matrix_path: "../06-audit/gherkin-matrix.md"
---

## § 1 — Gherkin verification matrix

> Copia de `06-audit/gherkin-matrix.md` producida por `/auditor` Phase D. Cada scenario de `01-spec.md` mapeado a test path con verdict PASS.

| Scenario (Gherkin) | Test path | Status | Notes |
|---|---|---|---|
| SC-01 "Wizard finaliza con tenant_id válido" | `{brand}/backend/tests/modules/{brand}/onboarding/test_wizard_complete.py::test_creates_tenant` | ✅ PASS | |
| SC-02 "Wizard rechaza email duplicado" | `{brand}/backend/tests/modules/{brand}/onboarding/test_wizard_complete.py::test_duplicate_email_rejected` | ✅ PASS | |
| SC-03 "Wizard genera onboarding event para Lucas" | `{brand}/backend/tests/modules/{brand}/onboarding/test_event_emission.py::test_event_emitted` | ✅ PASS | |
| ... | ... | ✅ PASS | |

**Coverage:** N/N scenarios PASS. Cero NO_COVERAGE. Cero FAIL.

## § 2 — Playwright E2E run

> Última corrida E2E targeted a rutas afectadas por la story. Comando + output verdict.

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/{brand}/frontend && E2E_BASE_URL=http://localhost:300X npx playwright test --grep "{story-id}"
```

- Specs run: N
- Passed: N
- Failed: 0
- Skipped: 0
- Duration: M.M minutes
- Trace report: `{brand}/frontend/playwright-report/index.html`
- Storage state: `{brand}/frontend/playwright/.clerk/user.json` (Clerk fresh, 60-min TTL respected)

**E2E verdict:** ✅ ALL GREEN.

> Si story NO toca UI: documentar `gherkin_coverage_note: "Story service-only, sin E2E targeted"` en CHECKPOINTS.md y omitir esta sección (excepción documentada).

## § 3 — Capabilities updated/created

> Inventory enforcement (R32). Paths exactos. Cada capability YAML incluye `verification.commands` + `verification.gherkin_evidence` post-cement-date.

### NEW capabilities
- `{brand}/docs/product/capabilities/{module-a}/{cap-x}.yaml` — status: `live`
  - `verification.commands`: comandos reproducibles para re-verificar (ver § 5)
  - `verification.gherkin_evidence`: SC-01..SC-N (cita matrix)
  - `verification.playwright_specs`: `{brand}/frontend/e2e/.../{story-id}.spec.ts` (si aplica)

### UPDATED capabilities
- `{brand}/docs/product/capabilities/{module-b}/{cap-y}.yaml` — status: `planned → live`
- `{brand}/docs/product/capabilities/{module-c}/{cap-z}.yaml` — added scenarios SC-04..SC-06

### Capability YAML schema addition (post 2026-05-18)

```yaml
# {brand}/docs/product/capabilities/{module}/{cap}.yaml
---
capability_id: {cap-x}
module: {module-a}
slug: {cap-x}
status: live
date_introduced: 2026-05-18
story_introduced: {story-id}
package_version: ...
package_path: ...
license: proprietary
verification:                                              # ★ NEW post 2026-05-18
  commands:                                                # comandos canónicos reusables
    - "cd ${WS}/{brand}/backend && ${WS}/.venv/bin/pytest tests/modules/{brand}/{module-a}/ -v"
    - "cd ${WS}/{brand}/frontend && npx playwright test --grep '{capability-id}'"
  gherkin_evidence:                                        # scenarios trazables
    - scenario: "SC-01 ..."
      test_path: "{brand}/backend/tests/.../test_x.py::test_y"
    - scenario: "SC-02 ..."
      test_path: "{brand}/frontend/e2e/.../{story-id}.spec.ts::scenario-02"
  playwright_specs:                                        # opcional, si UI
    - "{brand}/frontend/e2e/{module-a}/{capability-id}.spec.ts"
  story_merge_artifact: "{brand}/docs/product/stories/{story-id}/07-merge.md"
---
```

## § 4 — Modules MD refreshed

> Auto-list marker regenera. Paths exactos.

- `{brand}/docs/product/modules/{module-a}.md` — auto-list incluye `{cap-x}` (post-merge)
- `{brand}/docs/product/modules/{module-b}.md` — auto-list incluye `{cap-y}` (post-merge)

Regen ejecutado:
```bash
cd ${WS} && make portfolio          # regenera {brand}/docs/product/BACKLOG.md + auto-list en modules MD
```

## § 5 — How to verify (reproducible commands)

> Comandos copy-paste para reproducir la verificación de la funcionalidad. Owner futuro de auditoría / promotion candidate scan corre estos comandos para re-validar.

```bash
WS=$(git rev-parse --show-toplevel)
BRAND={brand}
STORY_ID={story-id}

# 0. Setup: stack {brand} corriendo
make dev-${BRAND}                     # postgres + backend + frontend

# 1. Unit tests módulo afectado (BE)
cd ${WS}/${BRAND}/backend && ${WS}/.venv/bin/pytest tests/modules/${BRAND}/{module-a}/ -v

# 2. Architecture fitness (DDD + tenant isolation + anti-duplication)
cd ${WS}/${BRAND}/backend && ${WS}/.venv/bin/pytest tests/architecture/ -v

# 3. Frontend tests (TS + Vitest)
cd ${WS}/${BRAND}/frontend && npx tsc --noEmit && npx vitest run src/features/{module-a}/

# 4. E2E Playwright targeted
cd ${WS}/${BRAND}/frontend && E2E_BASE_URL=http://localhost:300X npx playwright test --grep "${STORY_ID}"

# 5. (Si agentic) Eval goldens
cd ${WS}/${BRAND}/backend && ${WS}/.venv/bin/pytest tests/agentic_evals/ --trials=3
```

**Expected:** todos los comandos retornan exit code 0. Si alguno falla post-merge → regression, abrir hot-fix ticket per `.claude/rules/hotfix-repro-mandatory.md`.

## § 6 — Verificación live — Definition of Done (Critical Rule #37 · `definition-of-done-live-verify.md`)

> Ninguna story con UI o endpoint pasa a `state: done` sin que Claude la haya **ejercido contra el stack dev real** de la marca (`dev-app.{brand}lat.com` vía Cloudflare Tunnel, o `localhost:300X`), **leído los logs** y **confirmado el efecto**. Suite verde / build OK / `GET 200` son necesarios pero NUNCA suficientes.

```yaml
dod_live_verified: true
dod_env: "make dev-app-{brand} → dev-app.{brand}lat.com (Chrome DevTools MCP)"   # o "localhost:300X"
dod_evidence:
  - action: "<acción real del usuario, incluido el write POST/PATCH/PUT/DELETE>"
    observed: "<toast OK + fila aparece + valor persiste al recargar>"
    backend_log: "<status correcto + sin traceback + efecto en DB confirmado>"
dod_verified_at: <YYYY-MM-DD>
```

**REFUSE gate (`/pm-{brand}` Fase F):** si `dod_live_verified != true` o falta `dod_evidence` (writes ejercidos + efecto observado) → **NO** escribir `state: done`. Única excepción: tickets config/docs/tooling puro → `dod_live_verified_skip_reason`.

## Cross-references

- `01-spec.md` § Gherkin scenarios — origen de la matrix § 1
- `03-arch.md` — decisiones técnicas honored
- `04-validators.yaml` — validators ejecutados durante /dev-team build
- `06-tickets.yaml` — `gherkin_coverage` fields mapped a § 1
- `CHECKPOINTS.md` — C1-C5 grid auditor verdict
- `06-audit/gherkin-matrix.md` — output verbatim Phase D auditor
- `.claude/rules/story-closure-gate.md` — hard rule SSoT
- `docs/process/story-closure-gate.md` — rationale + case study

## Story → archive

- `{brand}/docs/product/stories/{story-id}/` → `{brand}/docs/archive/{year}/stories/{story-id}/` (snapshot inmutable post-merge)
- Release padre actualiza `stories[]` marcando esta story `done` (recomputa su state machine)

## Output al user (Chris) post-merge

```
✅ Story {brand}/{story-id} MERGED a main (squash-merge: {SHA})
   - Phase D gherkin matrix: N/N scenarios PASS
   - Playwright E2E: N specs all green
   - Capabilities updated: {cap-x} (NEW live), {cap-y} (planned→live)
   - Modules refreshed: {module-a}.md, {module-b}.md auto-list
   - Story archived: {brand}/docs/archive/{year}/stories/{story-id}/
   - Release {parent-release} updated (1 story → done)

   State transition: reviewing → done.
   WIP cap status: reviewing (was 1) → 0; done (rolling 90d) +1.
```

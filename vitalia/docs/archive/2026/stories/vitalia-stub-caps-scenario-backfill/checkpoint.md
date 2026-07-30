---
story_id: vitalia-stub-caps-scenario-backfill
type: technical-story
agent_owner: config
module: platform
cap_target: multi-cap-backfill            # 20 caps existentes — extend (append scenario+e2e); NO crea caps nuevas
cap_change_type: extend                    # agrega scenarios a caps live existentes (cross_check_3 → verified-live)
state: done                            # ⬅ ROLLBACK refined→refining 2026-05-29: DONE cambió (bar deployed-visible de Chris)
release: F2
architecture_pattern: ADR-vitalia-004
adr_004_compliance: n/a-with-rationale    # no es story sub-tab/feature; es backfill de verificación (como cockpit-live-reconciliation)
priority: medium
ratified_by_chris: true  # v2 ratificado-por-extensión (decisiones pre-ratificadas 2026-05-29 + AskUserQuestion 2026-05-30)                   # spec v1 ratificado, pero DONE en revisión v2 (bar deployed-visible)
parallel_safe: false                       # toca 20 cap YAMLs + tests cross-módulo
last_modified: 2026-05-30
phase: DONE_MERGED           # esperando decisiones Chris (verificación deployed + política caps rotos)
prior_art_scan_done: true                  # 2026-05-29 — ver § Prior art scan (sección abajo)
prior_story: vitalia-cockpit-live-reconciliation   # esta nace del hallazgo de aquella (done 2026-05-29)
last_artifact: 06-tickets.yaml                  # architect parcial (solo 03-arch.md) — pausado al cambiar DONE
next_action: "DONE. Backfill honesto cerrado (14 v-l + 6 partial + 1 bug fixed). Follow-up: 3 stories de hardening. Próximo: Slice 2 PHI."

# Autonomous mode — PAUSADO 2026-05-29 (DONE cambió post-ratify · bar deployed-visible)
autonomous_mode: false                     # ⬅ era true; pausado porque la definición de DONE cambió materialmente
autonomous_mode_paused_reason: "Chris fijó bar nuevo: funcionalidades verificadas deben ser visibles en dev-app.vitalialat.com (salvo netamente backend justificado). Cambia DONE + estrategia de verificación → re-refinar spec antes de reanudar autónomo."
autonomous_mode_chain: [architect, dev-team, auditor, pm-merge]
autonomous_mode_ratified_by: chris
autonomous_mode_ratified_at: 2026-05-29T18:35:00-05:00
autonomous_mode_caps:
  max_iterations_per_ticket: 10
  max_audit_iterations: 3
  max_total_cost_usd: 6.00
  max_wall_clock_minutes: 120
  on_cap_exceeded: "state=blocked + escalate Chris"
autonomous_mode_notes: >
  Technical-story no-agentic, ~4 tickets (T-0 gate-extension + T-A/T-B/T-C baterías).
  HARD-false conditions OK: no toca core/luana-core, no agentic prod, no cross-brand, validators must_pass claros (no pass_k).
  CAVEAT scope: T-0 toca scripts/*.py (cross-cutting tooling, NO engine core) → builder commitea con SCOPE_GATE_SKIP=1 + razón (fase solo-bootstrap permitida). Cambio ADITIVO (reconoce pytest sin romper .ts). Anti-teatro: correr-verde + relevancia por cada e2e_test cableado.
---

# Backfill de scenarios+e2e para los 20 caps `stub` (declarados live sin verificación)

> **Origen:** sesión 2026-05-29, post `vitalia-cockpit-live-reconciliation` (done). Chris: "Crea la historia con todo lo aprendido para los stub, para aclararlas, agregarles el escenario real de lo que hace su código." Al reconciliar el ledger quedó claro que ~20 caps declaran `status: live` pero computan `stub`/`declared-live` — tienen código + claim live, pero **sin scenario+e2e formal** (cross_check_3). El cockpit las muestra como drift (honesto: "no puedo probarlo"). Esta story las lleva a `verified-live` agregando el escenario real de lo que su código hace + el test que lo verifica.

## Intent de Chris

Por cada cap `stub` declarada live: **(1) aclararla** (escribir el scenario Gherkin real = qué hace su código hoy), **(2) agregar/cablear el e2e/test** que lo verifica, de modo que `compute_capability_status` la suba a `verified-live` (cross_check_3 deja de marcar drift). Resultado: el conteo "verde real" del cockpit sube y `/drift` se limpia honestamente.

## Hallazgo clave heredado (de la story previa)

- El sweep (T-2 de cockpit-live-reconciliation) confirmó que estas superficies **renderizan OK (0 ROTO)**. El problema NO es que estén rotas — es que **"renderiza OK" ≠ "verified-live"**: les falta el scenario+e2e formal por-cap.
- **Mucho de esto es CABLEAR tests existentes, no escribir nuevos:** varias ya tienen e2e en `vitalia/frontend/e2e/` (topbar.spec.ts, theme-toggle.spec.ts, sign-in specs, admin-*.spec.ts) — solo falta que el `scenario.e2e_test` del cap YAML apunte a ellos. Otras (infra/BE) necesitan un integration/contract test, NO un e2e de UI.
- Matriz de realidad como input: `vitalia/docs/domains/ops/live-reconciliation.md`.

## Worklist — 20 caps target (agrupados por naturaleza del test)

### A. UI / foundation (shell-organism · render OK por sweep · mayormente CABLEAR e2e existente)
- `design-tokens-foundation` · `design-tokens-theme` (→ e2e theme-toggle.spec.ts existe)
- `topbar-global` (→ e2e topbar.spec.ts existe)
- `sign-in-sign-up-pages` (→ e2e auth/sign-in-*.spec.ts existe)
- `shell-foundation-shadcn-tailwind-v4` · `iam-scaffold-slice-1` · `playwright-smoke-suite` · `public-clinic-landing`

### B. Admin Streamlit (e2e admin ya existe · CABLEAR scenario → spec)
- `admin-streamlit-service` · `clinics-crud` · `tenants-crud` · `users-crud` · `streamlit-tenants-users`
- (e2e existentes: admin-login, admin-users-crud, admin-tenants-crud, admin-clinics-extension, admin-hipaa-dual-filter)

### C. Infra / BE (NO UI e2e → integration/contract test; scenario describe comportamiento BE)
- `api-health-endpoint` · `audit-writer-ssot` · `hipaa-dual-filter-decorator` · `migrations-slice-1-schema`
- `otel-sentry-graceful-degradation` · `vitalia-callback-subclasses` · `idempotent-cron-arq-scaffold`

## Excluidos explícitamente (NO esta story)
8 caps `planned` (futuros, sin código aún) — son Fase 2, no backfill: `3-clinic-fixture-latam`, `fiscal-emission-pe`, `medical-pdf-extractors`, `medical-services-offer-preset`, `patient-records-medical-history`, `re-engagement`, `registries-medical-vertical`, `vertical-medical-extension-sdk`.
Y las 33 `deprecated` (slice-1 superseded) — se reconstruyen en Fase 2, no se backfillean.

## Definición de DONE
- Cada uno de los 20 caps: scenario Gherkin real (qué hace el código) + `e2e_test`/`test` que existe y pasa.
- `compute_capability_status --brand vitalia`: los 20 suben de `stub`/`declared-live` → `verified-live` (o `partial` justificado si la verificación es parcial honesta).
- `validate_code_cap_bidirectional` cross_check_3: 0 drift (HARD) y conteo verified-live sube de 2 → ~22.
- `/drift` del cockpit: se limpia (deja de mostrar estos 20 como drift).
- Disciplina: cero código de feature nuevo (solo scenarios + tests + wiring); cero reconstrucción; cero engine edit. Caben fixes inline triviales si un test revela algo, con gates verdes.

## Prior art scan (formalizado /pm-vitalia 2026-05-29)

> Ejecutado per `.claude/rules/anti-duplication-refining.md` Step prior-art-scan. KW: `capability scenario backfill verified-live cross_check_3 e2e wiring`.

| Fuente | Hallazgo | Decisión |
|---|---|---|
| **Engine `core/luana-core-*/`** | Ningún package backfillea scenarios de caps (es tooling de proceso SDD, no runtime). | **net-new tooling-work** — sin import de engine |
| **vitalia propio** | `scripts/compute_capability_status.py` + `validate_code_cap_bidirectional.py` ya existen (gates objetivos). `vitalia/docs/domains/ops/live-reconciliation.md` = matriz cap↔realidad (input directo). | **reuse** scripts como gate; consume matriz |
| **vitalia e2e existentes** | Confirmados specs a CABLEAR (no escribir): `e2e/visual|a11y/topbar-global/topbar.spec.ts`, `.../design-tokens-theme/theme-toggle.spec.ts`, `e2e/auth/sign-in-*.spec.ts`, `e2e/admin/admin-{login,users-crud,tenants-crud,clinics-extension,hipaa-dual-filter}.spec.ts`, `tenants-users.spec.ts`. | **wire-existing** (batería A+B) |
| **comunify live** | Sin pattern paralelo de backfill (comunify aún no llegó a reconciliación de ledger). | **no aplica** |
| **story madre** | `vitalia-cockpit-live-reconciliation` (done 2026-05-29) produjo la matriz + reveló los 20 stub. | **input directo** |
| **`docs/process/lifecycle.md` § Fase 2** | "backfill de scenarios" es exactamente el proceso que esta story ejecuta. | **esta story ES eso** |

**Conclusión:** cero duplicación engine/cross-brand. Es tooling-work interno vitalia: cablear e2e existentes (A/B) + escribir integration/contract tests donde no hay UI (C) + poblar `scenarios[]` en 20 cap YAMLs. `cap_change_type: extend` coherente (agrega scenarios a caps live, NO crea caps).

## next_action
- `/pm-vitalia` refinemos → `/po` (technical-story) produce 01-spec con: scenario real por cap (3 baterías A/B/C) + criterio wiring-vs-writing + gate cross_check_3. Luego `/architect` (tickets por grupo A/B/C) → `/dev-team` → `/auditor` → merge.

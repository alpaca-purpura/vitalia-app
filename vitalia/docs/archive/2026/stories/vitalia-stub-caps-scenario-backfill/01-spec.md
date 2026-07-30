---
story_id: vitalia-stub-caps-scenario-backfill
brand: vitalia
type: technical-story
state: refining
po_version: 2
cap_target: multi-cap-backfill
cap_change_type: extend
architecture_pattern: ADR-vitalia-004
adr_004_compliance: n/a-with-rationale   # backfill de verificación, no sub-tab/feature UI nueva
ratified_by_chris: false                 # v2 pendiente de re-ratificación
prior_story: vitalia-cockpit-live-reconciliation
slice2_phi_dependency: false             # ★ v2: MEDIDO — ninguno de los 20 caps requiere el decoder PHI (Slice 2)
last_modified: 2026-05-30
---

# 01-spec v2 — Backfill de scenarios+e2e para los 20 caps `stub` declarados live

## Context

**Origen:** post `vitalia-cockpit-live-reconciliation` (done 2026-05-29). El sweep + el ledger honesto revelaron que ~20 caps declaran `status: live` pero `compute_capability_status.py` los computa `stub`/`declared-live`: tienen **código + claim live**, pero **sin `scenarios[]` formal con `e2e_test`** que el gate pueda verificar. El cockpit los pinta como drift honesto ("no puedo probarlo"). Esta story los lleva a `verified-live` agregando **el escenario real de lo que su código hace hoy** + cableando/escribiendo **el test que lo verifica** + **ejerciéndolos de verdad** (bar deployed-visible, abajo).

**No es código de feature nuevo.** Es: (1) *aclarar* cada cap con un scenario Gherkin que describe lo que su código YA hace, (2) cablear el `e2e_test` al test que lo verifica (mayormente tests existentes), (3) donde no exista, escribir un integration/contract test honesto, (4) **ejercer la acción real** y confirmar el efecto.

### Estado medido al arrancar v2 (anti-teatro aplicado a la planificación · 2026-05-30)

Corrí los dos gates ANTES de refinar (no asumí):
- `validate_code_cap_bidirectional.py --brand vitalia --strict` → `cross_check_3 drift=0, exit 0`. **El HARD gate YA está verde.** Esta story NO arregla un fallo — sube el conteo `verified-live` (hoy 2 → ~22) y limpia el `/drift` del cockpit honestamente.
- `compute_capability_status.py --brand vitalia` → de los 20 target, 19 son `stub` (0 scenarios), 1 (`public-clinic-landing`) es `declared-live` (2 scenarios sin e2e_test).
- Los tests candidatos **existen** (batería A/B Playwright specs ✓ + batería C pytest ✓: `test_phi_dual_filter.py`, `test_audit_log_row_per_phi_endpoint.py`, `test_audit_log_sync_write.py`, `test_migrations_idempotent.py`, `test_cron_envelope_used.py`, `workers/test_arq_settings.py`, etc.).
- **🔑 Ninguno de los 20 caps requiere el decoder PHI (Slice 2).** Batería A = UI shell/pública + sign-in no-autenticado. Batería B = admin Streamlit (auth aparte). Batería C = pytest sin auth live; `hipaa-dual-filter-decorator` se verifica con un pytest **estático** de arch-fitness, no con un request PHI live. → `slice2_phi_dependency: false`. (Slice 2 PHI es deuda arquitectónica real pero SEPARADA — story propia post-merge.)

### Mecánica de los gates objetivo (decodificada — SSoT de la aceptación)

Dos scripts definen el resultado computado. El spec se ata a su comportamiento real:

**`scripts/compute_capability_status.py`** (state-machine, declared = frontmatter `status`):
- `stub` → 0 scenarios. `declared-live` → `live` + scenarios sin ningún `e2e_test`. `partial` → `live` + algunos scenarios verificados pero no todos. `drift` → `live` + hay `e2e_test` declarados que **no existen** en disco.
- **`verified-live` → `live` + TODOS los scenarios tienen `e2e_test` que EXISTE en disco** (`exist == scenarios_total`). Chequea **existencia del archivo, NO que el test pase**.

**`scripts/validate_code_cap_bidirectional.py` cross_check_3 (HARD, pre-push block):**
- Por cada `scenarios[*].e2e_test`: el archivo debe **existir** AND **contener el substring `test(` o `test.describe(`**.
- `.spec.ts` (Playwright) y `.test.ts(x)` (Vitest) satisfacen. **pytest (`def test_…(`) NO** → motiva T-0.

### El gate solo chequea existencia + patrón — por eso el bar de Chris es superior (anti-teatro)

El gate mecánico NO corre los tests ni verifica que el cap funcione en deploy. Eso lo hace **teatro-vulnerable** (un cap podría apuntar a un spec passing no-relacionado y "pasar" — SC-4). Por eso esta story NO se cierra solo con el gate verde: aplica el **bar deployed-visible** (§ siguiente). El gate verde es necesario (ledger honesto) pero **nunca suficiente**.

## ★ Bar de verificación — DEPLOYED-VISIBLE (ratificado Chris 2026-05-29)

> SSoT doctrina: `.claude/rules/test-design-doctrine.md` § "Verificación REAL ≠ HTTP 200". Caso origen: lisa-marca shippeó "LIVE" pero rota en deploy (suite mockeada = falso verde).

Un cap se declara `verified-live` SOLO cuando se cumplen **las tres**:
1. **Gate verde** — su `scenario.e2e_test` existe + matchea patrón (cross_check_3 = 0 drift para ese cap).
2. **Test corre verde + es relevante** — el builder corre el test cableado y confirma (a) pasa, (b) **genuinamente ejercita** el `given/when/then` del scenario (no un proxy). El auditor verifica relevancia (CHANGES_REQUESTED si el test no cubre).
3. **Ejercido de verdad según su naturaleza** (la pieza que el gate NO captura):

| Grupo de cap | "Ejercido de verdad" significa |
|---|---|
| **UI-visible (app principal)** | Ejercer la acción real en **dev-app.vitalialat.com** (toggle tema, navegar topbar, cargar sign-in, abrir /config/avanzado, abrir landing pública) → resultado esperado **visible** + **logs del backend sin 4xx/5xx inesperado**. NO basta `GET 200` ni render de placeholder. |
| **Admin panel** | Ejercer la acción real en el **panel admin Streamlit deployed** (login, listar/crear tenant/clinic/user) → efecto visible + persistido. |
| **Infra-foundation (sin página)** | Ejercer el endpoint/suite real en deploy (`curl https://dev-app.vitalialat.com/api/health` → 200 + body esperado; la smoke suite corre verde contra dev-app). |
| **Netamente-backend** | **pytest verde es la verificación honesta** (justificado: no hay superficie dev-app que ejercer — son decoradores/migraciones/callbacks/crons). Se documenta el rationale "netamente-backend" en el cap YAML. |

**fix-to-green dentro de la story (ratificado):** si al ejercer un cap en deploy aparece roto (como lisa-marca: 500 por venv stale / tabla no migrada), se **arregla acá** (fix quirúrgico + gates verdes). Si genuinamente no se puede llevar a verde honesto en esta story → queda `partial` con rationale documentado en el cap YAML (NUNCA se fuerza `verified-live` falso).

## Estratificación de los 20 caps (4 grupos por método de verificación honesto)

> Cada cap declara su `verification_method` en el scenario (campo informativo) + el reporte por-cap (§ Deliverable) registra la evidencia.

### G1 · UI-visible — app principal (ejercer en dev-app + Playwright) · 7 caps

| cap | YAML | e2e_test (WIRE) | ejercicio dev-app |
|---|---|---|---|
| `design-tokens-theme` | `platform/` | `e2e/regression/design-tokens-theme/theme-toggle-interaction.smoke.spec.ts` | toggle claro/oscuro → CSS vars cambian, visible |
| `design-tokens-foundation` | `platform/` | `e2e/visual/design-tokens-theme/theme-toggle.spec.ts` | tokens aplicados en toda pantalla |
| `topbar-global` | `platform/` | `e2e/regression/topbar-global/topbar-interaction.smoke.spec.ts` | topbar renderiza + interacción |
| `sign-in-sign-up-pages` | `auth/` | `e2e/auth/sign-in-form.spec.ts` (+ `sign-in-redirect.spec.ts`) | página sign-in carga + form |
| `iam-scaffold-slice-1` | `iam/` | `e2e/regression/vitalia-fase1-routing-shell/happy-navigation.spec.ts` | ruta /config/avanzado navegable |
| `shell-foundation-shadcn-tailwind-v4` | `platform/` | `e2e/regression/shell-visual-check/shell-visual-check.spec.ts` | primitivas shadcn renderizan en shell |
| `public-clinic-landing` | `public_landing/` | ruta `/public/{slug}` — confirmar spec público o WRITE-thin | landing pública carga (sin auth) |

### G2 · Admin panel — Streamlit deployed (ejercer en panel + Playwright admin) · 5 caps

| cap | YAML | e2e_test (WIRE) | ejercicio |
|---|---|---|---|
| `admin-streamlit-service` | `admin/` | `e2e/admin/admin-login.spec.ts` | login admin panel |
| `clinics-crud` | `admin/` | `e2e/admin/admin-clinics-extension.spec.ts` | crear/listar clínica |
| `tenants-crud` | `admin/` | `e2e/admin/admin-tenants-crud.spec.ts` | crear/listar tenant |
| `users-crud` | `admin/` | `e2e/admin/admin-users-crud.spec.ts` | crear/listar user |
| `streamlit-tenants-users` | `admin/` | `e2e/admin/tenants-users.spec.ts` | flujo tenants↔users |

> Nota G2: los admin specs corren contra Streamlit (:8502). El builder confirma que corren verde en el entorno e2e; si están skip/quarantine → escala (no se cablea un test que no corre).

### G3 · Infra-foundation — sin página dedicada (endpoint/suite en deploy) · 2 caps

| cap | YAML | test | ejercicio |
|---|---|---|---|
| `api-health-endpoint` | `observability/` | contract test `/api/health` (pytest o Playwright API request) | `curl https://dev-app.vitalialat.com/api/health` → 200 + body |
| `playwright-smoke-suite` | `tests/` | un smoke representativo `e2e/specs/smoke/*.smoke.spec.ts` (la suite ES el comportamiento) | la smoke suite corre verde |

### G4 · Netamente-backend — pytest = verificación honesta (justificado, sin dev-app) · 6 caps

| cap | YAML | test candidato (pytest) | acción |
|---|---|---|---|
| `hipaa-dual-filter-decorator` | `clinics/` | `vitalia/backend/tests/architecture/test_phi_dual_filter.py` | WIRE (existe) |
| `audit-writer-ssot` | `audit/` | `test_audit_log_row_per_phi_endpoint.py` + `test_audit_log_sync_write.py` | WIRE (existen) |
| `migrations-slice-1-schema` | `platform/` | `test_migrations_idempotent.py` | WIRE (existe) |
| `idempotent-cron-arq-scaffold` | `workers/` | `test_cron_envelope_used.py` + `workers/test_arq_settings.py` | WIRE (existen) |
| `otel-sentry-graceful-degradation` | `observability/` | degradación graciosa OTEL/Sentry no disponible | WIRE-or-WRITE-thin |
| `vitalia-callback-subclasses` | `observability/` | subclases observabilidad heredan base | WIRE (`test_no_observability_mirror*.py`) or WRITE-thin |

> Justificación G4 (netamente-backend, no dev-app): son decoradores estáticos / migraciones / crons / callbacks / degradación de telemetría — no tienen superficie de usuario que ejercer en dev-app. El pytest que ejercita su comportamiento ES la verificación honesta (alineado con `test-design-doctrine` § matriz: infra → integration/contract test, NO UI e2e). Cada uno documenta `verification_method: pytest-backend-justified` + rationale en el cap YAML.

**Reparto:** G1=7 + G2=5 + G3=2 + G4=6 = **20** ✓.

## Definición de DONE (v2)

1. Cada uno de los 20 caps tiene ≥1 `scenario` (schema golden, § Recipe) con `given/when/then` que describe lo que su **código hace hoy** + `e2e_test` apuntando a un test que **existe, pasa y cubre** ese comportamiento.
2. **Bar deployed-visible cumplido por grupo** (§ Bar): G1/G2 ejercidos en dev-app/admin con efecto visible + logs limpios; G3 endpoint/suite verde en deploy; G4 pytest verde + rationale netamente-backend.
3. `compute_capability_status.py --brand vitalia`: los 20 suben a `verified-live` (o `partial` justificado, documentado por-cap). `verified-live` total sube de **2 → ~22**.
4. `validate_code_cap_bidirectional.py --brand vitalia --strict`: `cross_check_3` **drift = 0** (HARD), verdict `CLEAN` o `SOFT_DRIFT` (nunca `HARD_FAIL`). Regression: cross_check_3 sigue 0 tras T-0 para los `.ts` actuales.
5. **Reporte de verificación por-cap** (§ Deliverable) escrito y commiteado.
6. `/drift` del cockpit deja de mostrar estos 20.
7. Disciplina: **cero código de feature nuevo**, cero reconstrucción, **cero engine edit** (`core/luana-core-*`). Permitido: scenarios + tests + wiring + T-0 (`scripts/`) + fixes inline quirúrgicos (con gates verdes) si ejercer revela algo roto.

## Deliverable nuevo (v2) — Reporte de verificación por-cap

Archivo `vitalia/docs/product/stories/vitalia-stub-caps-scenario-backfill/VERIFICATION-REPORT.md` (lo escribe `/dev-team` durante el build, lo valida `/auditor`). Una fila por cap:

```markdown
| cap | grupo | método | qué se ejerció | evidencia (cmd/log/screenshot) | resultado | computed_status |
|-----|-------|--------|----------------|--------------------------------|-----------|-----------------|
| topbar-global | G1 | dev-app + playwright | navegación a dev-app, topbar visible, click en logo | `playwright ... exit 0` + log `200 GET /` | ✅ visible | verified-live |
| api-health-endpoint | G3 | curl deploy | GET /api/health | `curl https://dev-app... → 200 {"status":"ok"}` | ✅ | verified-live |
| hipaa-dual-filter-decorator | G4 | pytest (backend-justified) | arch-fitness decoradores PHI | `pytest test_phi_dual_filter.py → exit 0` | ✅ | verified-live |
```

Regla: una fila NO puede decir "✅ verified-live" con evidencia que sea solo "GET 200" para G1/G2 (debe haber ejercicio real + log). G4 acepta "pytest verde" como evidencia honesta.

## Recipe por-cap (schema golden — de `auth/clerk-middleware.yaml`)

Append al cap YAML un bloque `scenarios:` (unidad atómica de comportamiento v4):

```yaml
scenarios:
  - id: <kebab-id-comportamiento>
    name: "Descripción legible de lo que hace el código"
    actor: doctor | admin_clinic | sistema | infra
    status: live
    given: "Precondición concreta del comportamiento real"
    when: "Acción / disparador exacto"
    then: "Efecto medible observable (lo que el test verifica)"
    e2e_test: "vitalia/frontend/e2e/...spec.ts  |  vitalia/backend/tests/...test_*.py"
    verification_method: dev-app | admin-panel | deploy-endpoint | pytest-backend-justified   # ★ v2
    story_spec_ref: "vitalia/docs/.../01-spec.md  (story que introdujo el código)"
    atomic_ref: null
    added_in_story: vitalia-stub-caps-scenario-backfill
    added_date: 2026-05-30
```

Y un entry en `change_log` (`type: extend`, `summary: "backfill scenario+e2e → verified-live (deployed-visible)"`, `added_in_story: vitalia-stub-caps-scenario-backfill`).

## T-0 — Extensión del gate a pytest (prerequisito de G4 · ratificado Chris)

`scripts/validate_code_cap_bidirectional.py` cross_check_3: para paths `.py`, aceptar patrón pytest (`\bdef test`) además de `test(`/`test.describe(`. Para `.ts/.tsx`, **comportamiento idéntico al actual** (cero impacto JS). `compute_capability_status.py`: SIN cambio (ya cuenta por existencia del path).

**Scope:** `scripts/*.py` (cross-cutting · afecta todas las brands). Cambio **aditivo** (reconoce MÁS patrones). Bajo fase solo-bootstrap permitido con `SCOPE_GATE_SKIP=1` + razón en commit body. Requiere tests del propio script: (a) `.py` con `def test_` → pass; (b) `.py` sin `def test` → drift `no_test_pattern`; (c) `.ts` sigue igual (regression). **Regression obligatoria:** re-correr sobre los caps `.ts` actuales da verdict idéntico.

## Scenarios (de la OPERACIÓN de backfill — acceptance del story · 4/4 obligatorios)

### SC-1 · happy — cap stub con spec existente verde + ejercido en dev-app → verified-live
- **given:** `topbar-global` declara `live`, computa `stub` (0 scenarios); existe `topbar-interaction.smoke.spec.ts` verde que ejercita el TopBar; el TopBar renderiza en dev-app.
- **when:** se appendea 1 scenario con `e2e_test` apuntando a ese spec + `verification_method: dev-app`; se corre el spec; se ejerce el TopBar en dev-app y se leen los logs.
- **then:** spec verde + TopBar visible en dev-app + logs sin 4xx/5xx; `compute_capability_status` reporta `topbar-global` = `verified-live`; `cross_check_3` para ese cap = 0 drift; fila en VERIFICATION-REPORT con evidencia (no "200 a secas").
- **graders:**
  - `{ type: shell_command, cmd: "cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/topbar-global/", expect: "exit 0" }`
  - `{ type: shell_command, cmd: "python3 scripts/compute_capability_status.py --brand vitalia", expect: "topbar-global computed_status == verified-live" }`
  - `{ type: state_check, target: "_status-computed.json", expect: "capabilities['topbar-global'].computed_status == 'verified-live'" }`
  - `{ type: manual_audit, who: claude-dev-app, expect: "topbar visible en dev-app.vitalialat.com + log backend sin error durante el ejercicio" }`

### SC-2 · negative — e2e_test a path inexistente → drift detectado (gate protege)
- **given:** por error de tipeo, un scenario apunta `e2e_test` a un archivo que no existe.
- **when:** se corre `validate_code_cap_bidirectional.py --strict`.
- **then:** `cross_check_3` reporta `drift > 0` con `status: missing_file`; el script sale 1 (HARD); el pre-push bloquea. El builder corrige el path antes de cerrar.
- **graders:**
  - `{ type: shell_command, cmd: "python3 scripts/validate_code_cap_bidirectional.py --brand vitalia --strict", expect: "exit 0 (drift_in_hard == 0) tras corregir todos los paths" }`
  - `{ type: state_check, target: "_bidirectional-validation.json", expect: "cross_check_3.drift == 0" }`

### SC-3 · edge — cap netamente-backend vía pytest (post T-0) + partial honesto
- **given:** `hipaa-dual-filter-decorator` (G4, sin superficie dev-app); su verificador honesto es pytest (`test_phi_dual_filter.py`).
- **when:** post-T-0, se cablea `e2e_test` al pytest con `verification_method: pytest-backend-justified`; se corre el pytest.
- **then:** pytest verde; `cross_check_3` acepta el `.py` (patrón `def test_`) = 0 drift; `compute_capability_status` = `verified-live`. Si un cap solo verifica parte honesta → `partial` con rationale en el cap YAML (NO se fuerza verified-live falso).
- **graders:**
  - `{ type: shell_command, cmd: "cd vitalia/backend && ${WS}/.venv/bin/pytest tests/architecture/test_phi_dual_filter.py -q", expect: "exit 0" }`
  - `{ type: shell_command, cmd: "python3 scripts/validate_code_cap_bidirectional.py --brand vitalia --strict", expect: "exit 0" }`
  - `{ type: state_check, target: "_status-computed.json", expect: "hipaa-dual-filter-decorator ∈ {verified-live, partial-con-rationale}" }`

### SC-4 · adversarial — anti-teatro: e2e_test a spec passing NO relacionado
- **given:** un cap apunta su `e2e_test` a un spec que pasa pero NO ejercita el comportamiento del cap (gaming del gate, que solo checa existencia + patrón).
- **when:** auditor revisa relevancia scenario↔test + el VERIFICATION-REPORT.
- **then:** el gate mecánico pasaría (verde falso), PERO la disciplina del story lo rechaza: el builder DEBE confirmar que el test cubre el given/when/then + dejar evidencia de ejercicio real en el reporte; el auditor marca **CHANGES_REQUESTED** si el test cited no es relevante o si la evidencia es "200 a secas" para G1/G2. Verified-live honesto = test existe **+ pasa + cubre + ejercido de verdad**.
- **graders:**
  - `{ type: llm_rubric, rubric: "relevancia scenario↔test", assertions: ["el given/when/then del scenario corresponde a lo que el test cited assert-ea", "el test ejercita el código del cap (no un proxy)", "la evidencia del reporte NO es solo GET 200 para G1/G2"], threshold: 1.0 }`
  - `{ type: manual_audit, who: auditor, expect: "rechaza cualquier e2e_test no-relevante o evidencia-200-a-secas aunque el gate mecánico pase" }`

## Acceptance gates (resumen ejecutable)

```bash
WS=$(git rev-parse --show-toplevel); cd ${WS}
# 1. Status sube (2 → ~22 verified-live)
python3 scripts/compute_capability_status.py --brand vitalia

# 2. Bidireccional HARD limpio (sigue 0 tras T-0)
python3 scripts/validate_code_cap_bidirectional.py --brand vitalia --strict   # exit 0

# 3. Tests cableados verdes (muestra)
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression e2e/admin e2e/auth
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/architecture tests/integration tests/workers -q

# 4. Bar deployed-visible (G1/G2/G3): ejercer en dev-app + curl health
curl -s -w '\n%{http_code}\n' https://dev-app.vitalialat.com/api/health
docker logs luana-dev-vitalia_backend_dev-1 --tail 60 | grep -iE '4..|5..|traceback|error' || echo "logs limpios"

# 5. Regen matriz + /drift limpio
python3 scripts/build_live_reconciliation_matrix.py --brand vitalia
```

## Prior art applied (anti-duplication-refining)

- **Reuse (gates objetivo):** `scripts/compute_capability_status.py` + `scripts/validate_code_cap_bidirectional.py` — NO se recrean; se consumen como SSoT de aceptación y se **extienden** aditivamente (T-0) para pytest.
- **Reuse (template):** schema `scenarios[]` verbatim de `vitalia/docs/product/capabilities/auth/clerk-middleware.yaml` (golden verified-live).
- **Reuse (tests existentes):** G1/G2 cablean specs Playwright ya en `vitalia/frontend/e2e/**`; G4 cabla pytest arch-fitness ya en `vitalia/backend/tests/architecture/**` + `tests/workers/**` (confirmados por filesystem scan 2026-05-30). NO se escriben tests nuevos donde hay cobertura verde.
- **Input directo:** `vitalia/docs/domains/ops/live-reconciliation.md` (matriz) + story madre `vitalia-cockpit-live-reconciliation` (done).
- **Doctrina:** `docs/process/lifecycle.md` § Fase 2 (backfill de scenarios) + `.claude/rules/test-design-doctrine.md` (§ Verificación REAL ≠ HTTP 200 → motiva el bar deployed-visible; § matriz → motiva T-0 pytest).
- **Engine / cross-brand:** cero. Ningún engine package backfillea scenarios. comunify aún no llegó a reconciliación. `cap_change_type: extend` coherente (agrega scenarios a caps live, no crea caps).
- **Slice 2 PHI:** desacoplado — MEDIDO que ningún cap de los 20 lo requiere (`slice2_phi_dependency: false`). Slice 2 = story propia post-merge.

## Open questions (resueltas)

- **Q1 batería C / gate pytest** → RESUELTA: extender el gate a pytest (T-0). Honesto + alineado con test-design-doctrine.
- **Q2 integridad anti-teatro** → RESUELTA: correr-verde + relevancia + **bar deployed-visible** (no solo existencia).
- **Q3 verificación dev-app vs local** → RESUELTA v2: G1/G2 ejercidos en dev-app (deployed-visible); G3 endpoint/suite en deploy; G4 pytest justificado backend.
- **Q4 política caps rotos** → RESUELTA v2: fix-to-green dentro de la story; si no se puede honesto → `partial` con rationale (NUNCA verified-live falso).
- **Q5 Slice 2 dependencia** → RESUELTA v2: NO es prerequisito (medido). Story propia post-merge.

## Excluidos explícitamente (NO esta story)

- 8 caps `planned` (futuros sin código = Fase 2): `3-clinic-fixture-latam`, `fiscal-emission-pe`, `medical-pdf-extractors`, `medical-services-offer-preset`, `patient-records-medical-history`, `re-engagement`, `registries-medical-vertical`, `vertical-medical-extension-sdk`.
- 33 caps `deprecated` (slice-1 superseded · se reconstruyen en Fase 2).
- **Slice 2 PHI** (desentubar JWKS real + rol desde `user_tenants` + repos reales): deuda real PERO story propia — ninguno de los 20 caps la requiere.

## Próximo paso

`/architect vitalia vitalia-stub-caps-scenario-backfill` → ready package. Tickets esperados: **T-0** gate-extension (scripts/ + tests del script), **T-A** G1 UI-visible (7 caps wire + dev-app), **T-B** G2 admin (5 caps wire), **T-C** G3+G4 infra/backend (8 caps pytest/endpoint, depende de T-0) + **VERIFICATION-REPORT.md**. DAG: `T-0 → T-C` ; `T-A`, `T-B` paralelos.

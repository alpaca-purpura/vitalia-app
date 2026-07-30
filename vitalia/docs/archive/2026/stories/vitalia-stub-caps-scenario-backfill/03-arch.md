---
story_id: vitalia-stub-caps-scenario-backfill
brand: vitalia
arch_version: 2
schema_version: v4.1
architecture_pattern: ADR-vitalia-004
adr_004_compliance: n/a-with-rationale   # backfill de verificación, no sub-tab UI nueva (igual que cockpit-live-reconciliation)
authored_by: architect (direct, no orchestrator spawn — ver § Surfaces)
slice2_phi_dependency: false             # ★ v2: medido — ninguno de los 20 caps requiere el decoder PHI (Slice 2)
last_modified: 2026-05-30
---

# 03-arch — Backfill scenarios+e2e para 20 caps stub

## ★ v2 update (2026-05-30 — alineado con 01-spec v2)

Cambios sobre v1: (1) **bar DEPLOYED-VISIBLE** — `verified-live` honesto requiere ejercicio real según naturaleza (ver § TESTS arch); (2) **estratificación en 4 grupos** G1 UI-visible / G2 admin / G3 infra-foundation / G4 netamente-backend (las baterías A/B/C de v1 mapean: A→G1, B→G2, C→G3+G4); (3) **deliverable nuevo** `VERIFICATION-REPORT.md` (evidencia por-cap); (4) **fix-to-green** dentro de la story; (5) **Slice 2 PHI desacoplado** (`slice2_phi_dependency: false` — medido que ningún cap de los 20 lo requiere). El resto del arch v1 (T-0 gate-extension preciso, DOCS scenarios[], CONN integration) se mantiene.

### Estratificación 4 grupos (verificación honesta por grupo)

| Grupo | Caps | Método "ejercido de verdad" |
|---|---|---|
| **G1 · UI-visible (app principal)** | design-tokens-theme, design-tokens-foundation, topbar-global, sign-in-sign-up-pages, iam-scaffold-slice-1, shell-foundation-shadcn-tailwind-v4, public-clinic-landing (7) | ejercer en dev-app.vitalialat.com (visible) + log limpio + Playwright verde |
| **G2 · Admin panel** | admin-streamlit-service, clinics-crud, tenants-crud, users-crud, streamlit-tenants-users (5) | ejercer en admin Streamlit deployed + Playwright admin verde |
| **G3 · Infra-foundation (sin página)** | api-health-endpoint, playwright-smoke-suite (2) | endpoint/suite verde en deploy (`curl dev-app /api/health`; smoke corre verde) |
| **G4 · Netamente-backend** | hipaa-dual-filter-decorator, audit-writer-ssot, migrations-slice-1-schema, idempotent-cron-arq-scaffold, otel-sentry-graceful-degradation, vitalia-callback-subclasses (6) | pytest verde = verificación honesta (justificado: sin superficie dev-app) |

### VERIFICATION-REPORT.md (deliverable T-A/T-B/T-C)

`/dev-team` escribe `vitalia/docs/product/stories/vitalia-stub-caps-scenario-backfill/VERIFICATION-REPORT.md` (1 fila por cap: grupo · método · qué se ejerció · evidencia cmd/log · resultado · computed_status). Regla anti-teatro: evidencia "GET 200 a secas" PROHIBIDA para G1/G2 (debe haber ejercicio real + log). G4 acepta "pytest verde". `/auditor` valida relevancia + que la evidencia cumpla el bar.

## Surfaces involved

| Surface | Toca | Detalle |
|---|---|---|
| **TOOLING** (`scripts/*.py`) | sí | T-0: extender `validate_code_cap_bidirectional.py` cross_check_3 para reconocer pytest en paths `.py` + extender su test en `scripts/tests/`. |
| **DOCS / cap YAMLs** (`vitalia/docs/product/capabilities/`) | sí | Append `scenarios[]` + `change_log` entry a 20 cap YAMLs (baterías A/B/C). |
| **TESTS — FE Playwright** (`vitalia/frontend/e2e/`) | sí (wire) | Baterías A/B: cablear specs EXISTENTES (correr verde + confirmar relevancia). WRITE-thin solo si falta cobertura (public-clinic-landing). |
| **TESTS — BE pytest** (`vitalia/backend/tests/`) | sí (wire) | Batería C: cablear pytest EXISTENTES (arch fitness confirmados) + WRITE-thin donde falte (api-health). |
| BE/FE feature code | **NO** | Cero código de feature nuevo. |
| AGENTIC | **NO** | — |
| Engine `core/luana-core-*` | **NO** | Boundary respetado. |

### Por qué authored directo (sin spawn architect-orchestrator)

El `architect-orchestrator` está diseñado para feature code BE/FE/AGENTIC (POMs, visual goldens, RHF forms, migrations). Esta story NO construye feature: extiende una herramienta (`scripts/`), edita data (cap YAMLs) y **cablea tests existentes**. El template estándar (test_construction_plan con POMs/fixtures, playwright_visual_scope con goldens) mis-fittearía. El architect (Opus) con el contexto de gate-mechanics completo produce un package más preciso para esta naturaleza meta/tooling. Decisión consistente con `test-design-doctrine` (la batería de tests se diseña según la naturaleza del ticket).

## TOOLING arch — T-0 (gate extension)

**Problema:** `validate_code_cap_bidirectional.py` cross_check_3 (HARD) exige que el `e2e_test` file contenga `test(` o `test.describe(` (línea 66 `E2E_TEST_PATTERNS`, línea 185 `has_pattern`). Pytest usa `def test_…(` → no matchea → batería C HARD-failaría.

**Solución (aditiva, path-aware):** en `cross_check_3`, al validar el patrón, decidir el set según extensión del path:
- path `.py` → aceptar patrón pytest: `def test_` **o** `def test(` (regex `\bdef test`).
- path `.ts` / `.tsx` / otros → patrón JS actual (`test(` / `test.describe(`) — **sin cambio de comportamiento**.

Pseudo-edit (builder confirma forma final):
```python
# scripts/validate_code_cap_bidirectional.py
E2E_TEST_PATTERNS_JS = ("test(", "test.describe(")
PYTEST_PATTERN = re.compile(r"\bdef test", re.MULTILINE)   # def test_ / def test(

# en cross_check_3, reemplazar:
#   has_pattern = any(p in content for p in E2E_TEST_PATTERNS)
# por:
if full_path.suffix == ".py":
    has_pattern = bool(PYTEST_PATTERN.search(content))
else:
    has_pattern = any(p in content for p in E2E_TEST_PATTERNS_JS)
```

**`compute_capability_status.py`: SIN cambio.** Ya cuenta verificación por **existencia** del path `e2e_test` (no chequea patrón). Un `.py` que existe ya cuenta para `verified-live`. (Confirmado leyendo `_compute_status`.)

**Regression obligatoria:** correr el set actual de caps `.ts` antes/después de T-0 → verdict idéntico (cero impacto JS). Test del script (`scripts/tests/test_validate_code_cap_bidirectional.py`) extendido con: (a) caso `.py` con `def test_` → pass; (b) caso `.py` sin `def test` → drift `no_test_pattern`; (c) caso `.ts` sigue igual.

**Scope:** `scripts/` es cross-cutting (afecta todas las brands). Commit con `SCOPE_GATE_SKIP=1` + razón (fase solo-bootstrap permitida, `git-safety.md`). Cambio aditivo, bajo riesgo.

## DOCS arch — backfill scenarios[] (schema golden)

Por cap: append bloque `scenarios:` (schema verbatim de `auth/clerk-middleware.yaml`, único verified-live actual) + entry `change_log` (`type: extend`). Cada scenario: `id`, `name`, `actor`, `status: live`, `given/when/then` (describe lo que el código **hace hoy**), `e2e_test` (path al test que lo verifica), `story_spec_ref`, `atomic_ref: null`, `added_in_story: vitalia-stub-caps-scenario-backfill`, `added_date: 2026-05-29`.

`last_modified: 2026-05-29` del cap. NO se toca `status` (sigue `live`) — solo cambia el `computed_status` derivado.

## TESTS arch — wiring (baterías) + write-thin

| Batería | Caps | Test surface | Estado |
|---|---|---|---|
| A (UI/foundation) | 8 | Playwright `.spec.ts` existentes | WIRE (1 WRITE-thin: public-clinic-landing si no hay spec público) |
| B (admin Streamlit) | 5 | Playwright admin `.spec.ts` existentes | WIRE (confirmar corren verde vs Streamlit :8502) |
| C (infra/BE) | 7 | pytest existentes (arch fitness) | WIRE (confirmados: phi_dual_filter, audit_log_row, pgcrypto, no_phi_in_url) + WRITE-thin (api-health, otel-sentry, callback-subclasses, cron, migrations donde falte) |

**Confirmados existentes (WIRE):**
- `hipaa-dual-filter-decorator` → `vitalia/backend/tests/architecture/test_phi_dual_filter.py`
- `audit-writer-ssot` → `vitalia/backend/tests/architecture/test_audit_log_row_per_phi_endpoint.py`
- batería A: `topbar-interaction.smoke.spec.ts`, `theme-toggle-interaction.smoke.spec.ts`, `sign-in-*.spec.ts`, etc.
- batería B: `e2e/admin/admin-*.spec.ts`

**Anti-teatro (ratificado):** por cada `e2e_test` cableado, el builder DEBE: (1) correr el test → verde; (2) confirmar que el test ejercita el given/when/then del scenario (no un proxy no relacionado). Si un cap solo se puede verificar parcialmente honesto → queda `partial` con rationale en el cap YAML (NO se fuerza verified-live falso). El auditor verifica relevancia (categoría anti-teatro).

## Cross-cutting decisions

- **Tenant isolation / PII:** N/A directo (no se tocan queries ni response models). Los tests de batería C que se cablean (phi_dual_filter, audit_log, pgcrypto, no_phi_in_url) SON los guardianes PII/tenant — wiring los pone como verificación formal del cap. Refuerza HIPAA-lite, no lo debilita.
- **Spanish neutro:** los `given/when/then` + `name` de scenarios son texto técnico interno del cap YAML (no user-facing UI) → glosario voseo no aplica estrictamente, pero se redactan en español neutro por consistencia.
- **Master-data / currency:** N/A.

## Integration design (CONN) — no es isla

| Contención | Cómo se cumple |
|---|---|
| **Consumed** | Los `scenarios[]` de los cap YAMLs son consumidos por `compute_capability_status.py` (deriva status) + el cockpit (`/functionality`, `/drift` leen `_status-computed.json`). La extensión de gate (T-0) es consumida por `validate_code_cap_bidirectional.py` en cada run + pre-push hook + cockpit `/drift`. |
| **On the map** | Cada scenario vive en su cap YAML (hogar permanente). cap_target=multi-cap-backfill, cap_change_type=extend. |
| **Navigable** | El resultado es navegable en el cockpit: `/functionality` muestra los caps como verified-live; `/drift` deja de listarlos. Reachability: `cockpit → /drift → 0 de estos 20`. |
| **Notarized** | Sin registro nuevo: `scripts/` ya está cableado en pre-commit/pre-push + cockpit. T-0 es aditivo a tooling ya registrado. Los tests cableados ya corren en la suite e2e/pytest existente. |

> Reachability path: `dev corre compute_capability_status.py + validate --strict` → 20 caps verified-live + cross_check_3 drift=0 → `cockpit /drift` limpio. Cero superficie huérfana: no se crea código sin consumidor.

## Prior art audit (re-ejecutado por architect)

- **Engine consumed via import:** ninguno (es tooling de proceso SDD, no runtime). Confirmado: ningún `core/luana-core-*` backfillea scenarios.
- **Reused (tooling):** `scripts/compute_capability_status.py` (SIN cambio) + `scripts/validate_code_cap_bidirectional.py` (extendido aditivo T-0) + sus tests en `scripts/tests/`.
- **Reused (template):** `vitalia/docs/product/capabilities/auth/clerk-middleware.yaml` (golden scenarios[] schema).
- **Reused (tests):** Playwright `vitalia/frontend/e2e/**` (baterías A/B) + pytest arch-fitness `vitalia/backend/tests/architecture/**` (batería C) — confirmados por filesystem scan. NO se escriben tests nuevos donde hay cobertura verde.
- **Lift candidates:** ninguno. La extensión pytest del gate beneficia a todas las brands pero vive en `scripts/` compartido (no es per-brand mirror) → no requiere promotion proposal; es edición directa del tooling compartido (cross-cutting, SCOPE_GATE_SKIP).
- **Net-new justificado:** WRITE-thin pytest para api-health/otel-sentry/callback-subclasses/cron donde no exista un test que cubra el comportamiento (mínimo, honesto, no feature).
- **Cross-brand mirror:** cero. comunify no tiene pattern paralelo.
- **cap_change_type coherence:** `extend` ✓ — agrega scenarios a caps `live` existentes, no crea caps. 03-arch cita caps existentes (no crea). Coherente.

## Tickets (resumen — detalle en 06-tickets.yaml)

- **T-0** — Gate extension pytest (`scripts/`) + script test. builder-backend/sonnet. blocks T-C.
- **T-A** — Batería A: 8 caps wire Playwright/Vitest. builder-frontend/sonnet.
- **T-B** — Batería B: 5 caps admin wire. builder-frontend/sonnet.
- **T-C** — Batería C: 7 caps pytest wire + write-thin. builder-backend/sonnet. depends T-0.

DAG: `T-0 → T-C` ; `T-A`, `T-B` independientes (paralelos). Ninguno agentic → cero Opus.

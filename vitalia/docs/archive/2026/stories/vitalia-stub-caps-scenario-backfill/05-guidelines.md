# 05-guidelines — vitalia-stub-caps-scenario-backfill (v2)

> Naturaleza: tooling + docs (cap YAMLs) + test-wiring. NO feature code.

## Patterns required

- **Scenarios append-only**: en cada cap YAML, APPEND bloque `scenarios:` (no reescribir el cap). Schema verbatim del golden `vitalia/docs/product/capabilities/auth/clerk-middleware.yaml`.
- **change_log entry**: por cada cap tocado, append entry `type: extend`, `summary: "backfill scenario+e2e → verified-live (deployed-visible)"`, `added_in_story: vitalia-stub-caps-scenario-backfill`, `added_date: 2026-05-30`. Update `last_modified: 2026-05-30`.
- **`e2e_test` apunta a test que EXISTE + el builder lo corrió verde + es relevante** (cubre el given/when/then). Confirmar existencia con `ls` ANTES de declararlo.
- **`verification_method` field** por scenario: `dev-app` (G1) | `admin-panel` (G2) | `deploy-endpoint` (G3) | `pytest-backend-justified` (G4).
- **T-0 cambio aditivo**: cross_check_3 path-aware — `.py` → patrón `\bdef test`; `.ts/.tsx/otros` → patrón JS actual (`test(` / `test.describe(`) SIN cambio. Cero impacto en los `.ts` existentes (regression obligatoria).
- **T-0 tests del script** RED→GREEN antes del cambio (TDD): caso `.py`-con-`def test_` pass · caso `.py`-sin-`def test` drift · caso `.ts` igual.
- **fix-to-green quirúrgico**: si ejercer un cap revela algo roto en deploy (ej. venv stale / tabla no migrada como lisa-marca), arreglarlo con el mínimo cambio + gates verdes + documentar root cause en VERIFICATION-REPORT.
- **partial honesto**: si un cap no llega a verde honesto → `computed_status` queda `partial` con rationale en el cap YAML. NUNCA forzar `verified-live` falso.
- Spanish neutro en `name`/`given`/`when`/`then` (texto técnico del cap; voseo no aplica estricto pero se redacta neutro por consistencia).

## Patterns forbidden

- ❌ Engine edit (`core/luana-core-*/src/`) — boundary HARD.
- ❌ Código de feature nuevo (`vitalia/backend/src/modules/vitalia/**` no-test, `vitalia/frontend/src/{features,components,app}/**`) — salvo fix-to-green quirúrgico documentado.
- ❌ Reescribir specs Playwright existentes para "ajustar" a un cap (se CABLEA el que cubre; si ninguno cubre → WRITE-thin honesto nuevo).
- ❌ `e2e_test` apuntando a un spec passing NO relacionado (gaming del gate — SC-4 adversarial). El test debe ejercitar el comportamiento del cap.
- ❌ Declarar `verified-live` con evidencia "GET 200 a secas" para G1/G2 en el VERIFICATION-REPORT.
- ❌ Cablear un admin spec que está `skip`/`quarantine` (no corre = no verifica) — escalar.
- ❌ Cross-brand edit (`{other_brand}/`) o tocar otra story.
- ❌ Tocar `compute_capability_status.py` (NO necesita cambio — ya cuenta por existencia).

## Files in scope

- `scripts/validate_code_cap_bidirectional.py` (T-0 — cross-cutting, commit con `SCOPE_GATE_SKIP=1` + razón)
- `scripts/tests/test_validate_code_cap_bidirectional.py` (T-0 — tests del script)
- `vitalia/docs/product/capabilities/{platform,auth,iam,public_landing,admin,observability,clinics,audit,workers,tests}/{cap}.yaml` × 20 (append scenarios[] + change_log)
- `vitalia/frontend/e2e/**` SOLO si WRITE-thin honesto (public-clinic-landing si no hay spec público)
- `vitalia/backend/tests/**` SOLO si WRITE-thin honesto (otel-sentry / vitalia-callback si no hay cobertura)
- `vitalia/docs/product/stories/vitalia-stub-caps-scenario-backfill/VERIFICATION-REPORT.md` (deliverable)

## Files NEVER touched (escalate)

- `core/luana-core-*/src/**` (engine — lift via /pm-luana)
- `vitalia/frontend/src/components/ui/**` + `app/layout.tsx` (shell/primitivas — un cambio rompe otras pantallas)
- `scripts/compute_capability_status.py` (NO necesita cambio)
- `{other_brand}/**` · `.claude/**`

## must_load_skills (builder cita verbatim + reporta "Skills consulted")

required:
  - id: ".claude/rules/test-design-doctrine.md"
    purpose: "§ Verificación REAL ≠ HTTP 200 — el bar deployed-visible de esta story"
  - id: ".claude/rules/anti-duplication.md"
    purpose: "cero recreación de gates / engine"
  - id: ".claude/rules/tdd-mandatory.md"
    purpose: "T-0 tests del script RED→GREEN"
  - id: ".claude/rules/spanish-text.md"
    purpose: "neutro en scenarios text"
  - id: "playwright-expert"
    when: "G1/G2 — correr specs cableados verde + WRITE-thin public-landing"
    purpose: "preflight + E2E_BASE_URL + Clerk auth + admin Streamlit specs"
  - id: "backend-expert"
    when: "T-0 + G4 — pytest wiring + WRITE-thin"
    purpose: "arch-fitness, pytest patterns"
  - id: ".claude/rules/git-safety.md § Fase solo-bootstrap"
    purpose: "T-0 toca scripts/ cross-cutting → SCOPE_GATE_SKIP=1 + razón en commit body"

reference_artifacts:
  - "vitalia/docs/product/stories/vitalia-stub-caps-scenario-backfill/01-spec.md (estratificación 4 grupos + bar)"
  - "vitalia/docs/product/stories/vitalia-stub-caps-scenario-backfill/03-arch.md (T-0 design preciso + grupos)"
  - "vitalia/docs/product/capabilities/auth/clerk-middleware.yaml (golden scenarios[] schema)"
  - "vitalia/docs/domains/ops/live-reconciliation.md (matriz cap↔realidad)"

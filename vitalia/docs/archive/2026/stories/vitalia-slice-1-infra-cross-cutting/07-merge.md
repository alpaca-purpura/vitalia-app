# Merge artifact — vitalia/vitalia-slice-1-infra-cross-cutting

> Brand: vitalia
> Merged: 2026-05-18 (squash-merge pending — see § 5 commands)
> Commit (squash-merge): _pending_ (will fill upon Step 11 squash-merge to main)
> Auditor verdict: APPROVED (CHECKPOINTS.md 27/27 ✅, 10 T-{n}-review.md APPROVED)
> Phase D verdict: EXEMPT (infra enabler — see 06-audit/gherkin-matrix.md)

## § 1 — Gherkin verification matrix

> Copia de `06-audit/gherkin-matrix.md` — Phase D EXEMPT por ser infra enabler sub-story.

| Scenario (Gherkin) | Test path | Status |
|---|---|---|
| N/A — infra enabler | (no Gherkin scenarios del padre `vitalia-ux-discovery` directos) | EXEMPT |

**Razón exención:** Esta sub-story aporta plumbing (migrations, registries, observability, AppShell, IAM/CRM scaffold, workers) que las 6 sub-stories consumer (`onboarding-wizard`, `inbox`, `pipeline`, `agenda`, `fidelizacion`, `marketing`) usarán al construir sus Gherkin scenarios. La verificación equivalente para esta story vive en 264 arch fitness + 1410 BE unit + 38 FE arch tests todos GREEN.

Detalle completo: `vitalia/docs/product/stories/vitalia-slice-1-infra-cross-cutting/06-audit/gherkin-matrix.md`.

## § 2 — Playwright E2E run

> N/A — infra enabler sin UI features propias. Shell + components scaffold solamente (sin rutas user-facing).

```bash
# Cuando las 6 sub-stories consumer entren a Phase F merge, cada una correrá su Playwright targeted.
# Ejemplo formato esperado para sub-stories consumer:
# cd /home/chalreme/Proyectos/luana-vitalia/vitalia/frontend && \
#   E2E_BASE_URL=http://localhost:3002 npx playwright test --grep "{story-id}"
```

- Specs run: 0 (N/A esta story)
- Passed: N/A
- Failed: 0
- Trace: N/A

## § 3 — Capabilities updated/created

> Inventory enforcement (R32). Paths exactos.

8 NEW capability YAMLs combined (granularidad agregada en lugar de 20 micro-cap files — más mantenible):

- `vitalia/docs/product/capabilities/compliance/hipaa-lite-defensive-stack.yaml` — NEW (status: live)
- `vitalia/docs/product/capabilities/iam/iam-scaffold-slice-1.yaml` — NEW (status: live)
- `vitalia/docs/product/capabilities/crm/crm-scaffold-slice-1.yaml` — NEW (status: live)
- `vitalia/docs/product/capabilities/observability/otel-sentry-graceful-degradation.yaml` — NEW (status: live)
- `vitalia/docs/product/capabilities/workers/idempotent-cron-arq-scaffold.yaml` — NEW (status: live)
- `vitalia/docs/product/capabilities/connections/registries-medical-vertical.yaml` — NEW (status: live)
- `vitalia/docs/product/capabilities/platform/design-tokens-foundation.yaml` — NEW (status: live)
- `vitalia/docs/product/capabilities/platform/migrations-slice-1-schema.yaml` — NEW (status: live)

## § 4 — Modules MD refreshed

> Auto-list marker regenera. Paths:

- `vitalia/docs/product/modules/compliance.md` — auto-list incluye `hipaa-lite-defensive-stack` post-merge
- `vitalia/docs/product/modules/iam.md` — NEW module (auto-list refresh)
- `vitalia/docs/product/modules/crm.md` — auto-list incluye `crm-scaffold-slice-1` post-merge
- `vitalia/docs/product/modules/observability.md` — NEW module (auto-list refresh)
- `vitalia/docs/product/modules/workers.md` — NEW module (auto-list refresh)
- `vitalia/docs/product/modules/connections.md` — auto-list incluye `registries-medical-vertical` post-merge
- `vitalia/docs/product/modules/platform.md` — auto-list incluye `design-tokens-foundation` + `migrations-slice-1-schema`

(Auto-list refresh ejecuta `scripts/reconcile_capabilities.py --brand vitalia` post-squash-merge.)

## § 5 — How to verify (reproducible commands)

> Comandos copy-paste para reproducir la verificación de la funcionalidad.

```bash
# Setup (asumiendo stack vitalia corriendo via make dev-vitalia):
WS=$(git rev-parse --show-toplevel)

# 1. BE arch fitness (226 tests — incluye HIPAA-lite dual filter, audit_log sync, pgcrypto, migrations idempotent)
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/architecture/ -v

# 2. BE full unit suite (1410 tests — IAM 42 + CRM 64 + compliance 28 + observability 23/8skip + workers 73 + extensions 29 + migrations smoke 93 + Story 11 carryover)
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/ -v --ignore=tests/integration

# 3. BE lint + format
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/ruff check src/ tests/ && ${WS}/.venv/bin/ruff format --check src/ tests/

# 4. FE typecheck + lint + arch fitness (38 tests in 9 files — incluye test_no_hardcoded_colors GREEN post-4545c22)
cd ${WS}/vitalia/frontend && npx tsc --noEmit && npx eslint src/ --cache --max-warnings=0
cd ${WS}/vitalia/frontend && npx vitest run src/__tests__/architecture/ --reporter=default

# 5. FE component tests (245 tests — 64.19% coverage ≥20% threshold)
cd ${WS}/vitalia/frontend && npx vitest run src/components/

# 6. FE Storybook build (sanity check 12 component stories renderan sin error)
cd ${WS}/vitalia/frontend && npx storybook build

# 7. Migrations idempotency (apply twice, no errors)
docker exec -t luana-vitalia-backend-dev bash -c "cd /app && alembic upgrade head && alembic upgrade head"
```

**Expected:** todos los comandos retornan exit code 0.

**Validators GREEN snapshot (gate-output.json post 4545c22):**
- be_ruff_check: PASS
- be_ruff_format_check: PASS (400 files already formatted)
- be_pytest_arch: PASS (226 passed)
- be_pytest_unit: PASS (1410 passed, 8 skipped, 50 deselected)
- fe_tsc: PASS (0 errors)
- fe_eslint: PASS (0 warnings, --max-warnings=0)
- fe_vitest_arch: PASS (9 test files, 38 tests)
- overall.any_fail: false / all_pass: true (19s duration)

## Notes for `/pm-vitalia` post-merge

### Promotion candidates → `/pm-luana`

2 patterns brand-specific con potencial cross-brand:

1. **PhiRepositoryBase + AuditLogRepository** (HIPAA-lite defensive stack)
   - Target core: `core/luana-core-compliance/` extend
   - Applies to other brands potentially: fitflow (gym waivers + medical history), inmoflow (broker contracts con PII regulated), guestly (guest data hotel regulated)
   - Learning to write: `vitalia/docs/learnings/2026-05-18-hipaa-lite-defensive-architecture.md` con `promotable: candidate`

2. **idempotent_cron decorator** (wraps engine IdempotentStore + OTel cron_span + structlog + Sentry)
   - Target core: nuevo package `core/luana-core-workers/` o extender `core/luana-core-platform/workers/`
   - Applies to other brands potentially: ALL (todas las brands eventualmente tendrán cron jobs)
   - Learning to write: `vitalia/docs/learnings/2026-05-18-idempotent-cron-decorator.md` con `promotable: candidate`

### Squash-merge guidance (CRITICAL)

El branch `wip/vitalia-infra-cross-cutting` (HEAD 4545c22) contiene los commits de DOS stories mezclados (porque el branch original `wip/vitalia-slice-1-shipping` hospedaba ambas pre-decreto story-closure-gate):

**Commits infra-cross-cutting (mantener):**
- dc35339, d6f01b6 — T-arch-1
- 1194941 — T-infra-1
- 4d1dca2, 9cf8548 — T-infra-2
- eee11fa — T-infra-3
- e9ad00e — T-infra-4
- 616bfe1 — T-infra-5
- ad69231 — T-infra-6
- 347672c — T-infra-7
- 088a7ee — T-infra-8
- 600f6c3 — T-infra-9
- 4545c22 — fix FE colors post-defer-audit
- + commits capability YAMLs + 07-merge.md (los que se generarán antes del squash)

**Commits copilot-tools-impl (NO traer a main — quedan en wip/vitalia-slice-1-shipping):**
- 3adea2c, fe0fbad — T-be-migrations-1 copilot-tools
- 55dd313 — T-be-services-1
- 032807a — T-be-services-2
- 476a755, 21f57a4 — T-be-services-3
- e6d59c9, fed4675, de159f7, 123de15, 5a0c643, b9881ba, 2c5de90, 01acc78 — story-closure-gate cement commits (PLATFORM cross-brand, ya en main? verificar)

**Estrategia recomendada para squash-merge selectivo:**
```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}  # principal worktree

# Opción A — Cherry-pick selectivo (preserva atomicidad por ticket):
git checkout main
git cherry-pick dc35339 d6f01b6 1194941 4d1dca2 9cf8548 eee11fa e9ad00e 616bfe1 ad69231 347672c 088a7ee 600f6c3 4545c22 <capability-commit-sha>
# (este enfoque crea 13 commits en main — historia detallada)

# Opción B — Squash todo en 1 commit + verify no copilot-tools files:
git checkout main
git merge --squash wip/vitalia-infra-cross-cutting
# Reset cualquier file copilot-tools que NO debería estar:
#   vitalia/backend/src/modules/vitalia/copilot/persistence/models/* (de T-be-migrations-1 copilot)
#   vitalia/backend/src/modules/vitalia/{copilot,sales_agent}/application/* (de T-be-services-{1,2,3})
git reset HEAD vitalia/backend/src/modules/vitalia/copilot/persistence/models/
git reset HEAD vitalia/backend/src/modules/vitalia/copilot/application/
git reset HEAD vitalia/backend/src/modules/vitalia/sales_agent/
git checkout -- vitalia/backend/src/modules/vitalia/copilot/persistence/models/
git checkout -- vitalia/backend/src/modules/vitalia/copilot/application/
git checkout -- vitalia/backend/src/modules/vitalia/sales_agent/
# Verify story-closure-gate commits ya en main (e6d59c9 etc), si no — cherry-pick aparte
git commit -m "feat(vitalia/infra): slice 1 infra-cross-cutting (10 tickets + FE color fix)"
git push origin main
```

**Recomendación auditor:** Opción B (squash + selective reset) si historia detallada no es crítica. Opción A (cherry-pick) si queremos preserva atomicidad por ticket.

### Cleanup post-merge

```bash
cd /home/chalreme/Proyectos/luana-platform
git worktree remove /home/chalreme/Proyectos/luana-vitalia-infra-cross-cutting
git branch -d wip/vitalia-infra-cross-cutting
# wip/vitalia-slice-1-shipping queda (hospeda copilot-tools-impl deferred, blocks_on resuelto)
```

### Update copilot-tools-impl checkpoint

`vitalia/docs/product/stories/vitalia-copilot-tools-impl/checkpoint.md` debe actualizarse para reflejar:
- `defer_audit_blocks_on:` → null (infra-cross-cutting ya merged a main)
- `next_action:` → "infra-cross-cutting MERGED. Chris decide: (a) retomar dev de los 6 tickets restantes en worktree nuevo wip/vitalia-copilot-tools-impl, o (b) re-evaluar scope post infra changes."

### Story archive

`vitalia/docs/product/stories/vitalia-slice-1-infra-cross-cutting/` → `vitalia/docs/archive/2026/stories/vitalia-slice-1-infra-cross-cutting/` (snapshot inmutable post squash-merge).

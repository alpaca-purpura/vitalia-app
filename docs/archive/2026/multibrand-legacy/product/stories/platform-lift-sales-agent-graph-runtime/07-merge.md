# 07-merge.md — platform-lift-sales-agent-graph-runtime (Phase 1)

> technical-story engine lift · `/pm-luana` merge. Las 5 secciones adaptadas (Gherkin N/A → arch tests por ESC; cap N/A → `cap_change_type: fix`).

## § 1 — Verificación (arch tests por ESC · reemplaza Gherkin matrix)

technical-story: no hay Gherkin de comportamiento. El contrato = arch tests RED-first por ESC, re-corridos independientemente por orchestrator + auditor.

| ESC | Test | RED (sin fix) | GREEN (con fix) |
|---|---|---|---|
| ESC-4 | `test_esc4_relationship_module_qualified.py` (subproceso) | `InvalidRequestError: Multiple classes found for path "MessageModel"` | 1 passed |
| ESC-5 | `test_esc5_templates_cwd_independent.py` | `TemplateNotFound` cwd ajeno | 3 passed |
| ESC-6 | `test_esc6_prompt_version_tenant_id.py` | `AttributeError no attribute tenant_id` | 2 passed |
| T-DEBT1 | suite_collects | `ModuleNotFoundError tests.modules` | colecta 476, 0 errores |

## § 2 — Downstream regression (reemplaza Playwright E2E)

- **platform suite: 294 passed / 0 failed** (auditor-run, PYTHONPATH override) — ESC-4 downstream limpio.
- **No-regresión probada por el auditor** (revirtió los 3 prod files → subset idéntico: pre-lift 24F/40P vs post-lift 22F/42P → +2 passes, 0 fallas nuevas).
- Full sales-agent suite = flaky en worktree (configure_mappers global + conftest synthetic AppointmentModel = stub Story-8 + sqlite gaps) — documentado en 03-arch § Realidad del entorno; NO es regresión. Gate canónico real = ci-parity + Postgres post-merge.

## § 3 — Capabilities

`cap_change_type: fix` → N/A (engine-hardening, sin cap nueva). map_zone: infraestructura → motor-agentico. Gate HB-34: fix no exige cap YAML.

## § 4 — Modules / engine packages tocados

- `core/luana-core-platform` — `infrastructure/models/crm.py` (LeadModel.messages module-qualified). semver: minor (bugfix additivo).
- `core/luana-core-sales-agent` — `infrastructure/prompts/base.py` (templates engine-relative) + `infrastructure/models/prompt_version_model.py` (+tenant_id) + `tests/architecture/test_esc{4,5,6}_*.py` (new) + `tests/orchestrator/test_chat_orchestrator_snapshot.py` (import fix). semver: minor.

## § 5 — How to verify (reproducible)

```bash
WS=$(git rev-parse --show-toplevel)
PP=$WS/core/luana-core-sales-agent/src:$WS/core/luana-core-platform/src
PP4=$PP:$WS/core/luana-core-scheduling/src:$WS/core/luana-core-iam/src:$WS/core/luana-core-offer-studio/src
# Post-merge en main / canónico (uv editable) NO necesita PYTHONPATH override; in-worktree sí.
PYTHONPATH=$PP4 $WS/.venv/bin/pytest core/luana-core-sales-agent/tests/architecture/ -q
cd $WS/core/luana-core-platform && PYTHONPATH=$PP $WS/.venv/bin/pytest -q   # 294 passed
```

**Bar runtime real (post-merge, Chris):** sync vitalia → aplicar migración ESC-6 (migration_notes.md) → levantar stack vitalia → mensaje Telegram → reply de Adrián + fila conversación/trace/costo en DB.

## Merge governance

- **Audit:** APPROVED (T-ALL-review.md, 8/8 checks, auditor-executed evidence).
- **chris_verify.signoff:** SATISFIED (2026-06-22).
- **Proposal:** `docs/promotion-protocol/proposals/2026-06-22-sales-agent-multibrand-graph-runtime.md` (vive en `wip/vitalia`, no en main) → marcar `migrated` cuando vitalia mergee, o por separado. El lift NO se bloquea por esto.
- **Propagación:** `make sync-all` (main → 4 wip/{brand}) tras merge.
- **ESC-6 brand-migration:** NO corre en el lift — cada brand la autorea en su worktree (migration_notes.md); vitalia prioritaria post-sync.
- **Phase 2 (ESC-1/2/3):** package separado, brand-first desde vitalia (cablear tool real → promover el cableado EP-3).

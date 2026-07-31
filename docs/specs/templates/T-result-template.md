# T-{n}-result.md — Template (developer output post-build)

> Owner: developer ASIGNADO. Escrito UNA VEZ post-build, antes de pushear y handoff a /auditor.
> El auditor consume ESTE archivo + gate-output.json + diff. NO re-corre tests desde cero (consume JSON).
>
> ★ v4.1 cement 2026-05-19 — sección "Skills consulted (must_load enforcement)" obligatoria.

---
ticket_id: T-1
story_id: STORY_ID
brand: BRAND_SLUG                                 # ★ v4.1
state: pushed
finished_by: qwen-opencode
finished_at: 2026-05-04T17:00Z
push_commit_sha: abc1234
push_branch: story/{story-id}                     # trunk-based — squash-merge a main, luego borrar
schema_version: v4.1
---

## Skills consulted (must_load enforcement v4.1) ★

> Builder MUST entregar esta tabla. Si missing → auditor CHANGES_REQUESTED automático.

| Skill / Rule | Status | When consulted |
|---|---|---|
| backend-expert | ✅ loaded | Step 0 — DDD pattern check + SQLA 2.0 invariantes |
| copilot-expert | ✅ loaded | Step 0 — module-specific invariantes |
| .claude/rules/tenant-isolation.md | ✅ loaded | mid-build — verify query filter tenant_id |
| .claude/rules/backend-ddd.md | ✅ loaded | Step 0 — layer boundaries |
| .claude/rules/backend-migrations.md | ✅ loaded | mid-build — idempotent IF NOT EXISTS pattern |
| .claude/rules/spanish-text.md | ✅ loaded | pre-commit — Spanish neutro check (`grep voseo`) |
| .claude/rules/auditor-self-fix-policy.md | ✅ loaded | Step 0 — saber qué auditor self-fix vs spawn dev-team |
| .claude/rules/tdd-mandatory.md | ✅ loaded | Step 0 — TDD RED→GREEN discipline |
| FastAPI canonical patterns | ✅ loaded | endpoint nuevo |
| pytest async testing patterns | ✅ loaded | endpoint test patterns |
| frontend-expert | n/a | surface=BE only |
| playwright-expert | n/a | playwright_required=false (este ticket no toca FE) |

## Resumen 1-frase

[Qué se construyó, en qué archivos, qué quedó listo.]

## Acceptance criteria — auto-verificación

| ID | Criterio | Verifier output | Estado |
|---|---|---|---|
| A1 | POST /api/v1/{path} happy → 200 | `tests/modules/{m}/test_{name}_endpoint.py::test_happy_path PASSED` | ✅ |
| A2 | Cross-tenant → 403 | `... test_tenant_isolation PASSED` | ✅ |
| A3 | Migration idempotente | `alembic upgrade head` corrido 2x sin error | ✅ |
| A4 | Coverage no baja | 48% (baseline 47%) | ✅ |
| A5 | Spanish neutro | `grep -E '\b(podés|tenés|...)\b' src/` → 0 matches | ✅ |

## Diff resumen

```
backend/src/modules/{m}/api/dtos.py                    +28 lines
backend/src/modules/{m}/api/routes.py                  +18 lines
backend/src/modules/{m}/application/services/...       +45 lines (new)
backend/src/modules/{m}/infrastructure/repositories/.. +30 lines (new)
alembic/versions/XXXX_add_...py                        +22 lines (new)
backend/tests/modules/{m}/test_{name}_service.py       +60 lines (new)
backend/tests/modules/{m}/test_{name}_endpoint.py      +40 lines (new)

7 files changed, 243 insertions
```

## Quality gates output (paste literal)

```
$ /test-backend

── Ruff check ─────────
[OK] No issues found

── Ruff format ────────
[OK] All files formatted

── Arch fitness ───────
[OK] tests/architecture passed (15 tests)

── Pytest ─────────────
247 passed, 0 failed
backend/tests/modules/{m}/                    --- 12 tests passed
backend/tests/integration/                    --- N tests passed

── Coverage ───────────
TOTAL                                          48% (>= 43%, baseline 47%)
src/modules/{m}/                               87%

── Mypy strict (módulo) ─
[OK] mypy src/modules/{m} --strict

── Migration idempotency ─
[OK] make verify-migration-idempotency

[OK] All gates passed
```

## Commits

```
$ git log --oneline -3
def5678 feat({m}): tenant isolation + cross-tenant guard
abc1234 feat({m}): endpoint POST /{action} + DTOs + service stub
```

Push status:
```
$ git push origin "$(git branch --show-current)"      # story/{story-id} — trunk-based (NUNCA branches permanentes fuera de main)
To github.com:...
   abc1234..def5678  story/{story-id} -> story/{story-id}
```

## Notas para /auditor

- Decisión `idempotency-key` header vs natural-key — documentada en service docstring + impl-log
- Coverage del módulo subió de 81% a 87% (+6%)
- 1 ratchet allowlist `KNOWN_ARCHITECTURE_VIOLATIONS` se REDUJO en 2 entries
- Sin TODOs / `# noqa` introducidos

## Riesgos conocidos / deuda

- ⚠️ Pendiente: implementar rate-limiting per tenant (es T-{n+1}, no este ticket)
- ⚠️ Pendiente: telemetría detallada (es T-{n+2})

## Output al orchestrator

```
done -> {brand}/docs/product/stories/{story-id}/T-{n}-result.md
state: pushed (commit def5678)
ready for /auditor
```

## Verificación live (Critical Rule #37 · `definition-of-done-live-verify.md`)

Los scenarios user-reachable de este ticket se ejercieron contra el stack dev real (`make dev-app-{brand}` / `localhost:300X`), no solo tests verdes:

```yaml
dod_live_verified: true|false
dod_env: "<make dev-app-{brand} → dev-app.{brand}lat.com (Chrome DevTools MCP) | localhost:300X>"
dod_evidence:
  - action: "<write/flujo real ejercido>"
    observed: "<efecto visible>"
    backend_log: "<status + sin traceback + efecto DB>"
```
> Un `GET 200` sobre un placeholder NO es verificación. Una e2e que mockea el backend del surface = falso verde.

<!-- voseo-allowed: doc interno / buzón conversacional, no user-facing -->

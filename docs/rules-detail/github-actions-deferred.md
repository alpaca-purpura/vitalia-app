# GitHub Actions Deferred — detail (moved from .claude/rules/ 2026-05-30, load on-demand)

**Origen:** conversación 2026-05-27 — Chris explicitó que no se necesita GitHub Actions activo hasta que haya deploy a servidor real. Mientras tanto, calidad se enforce vía `scripts/git-hooks/pre-commit` + `pre-push` (native Linux) que ya están instalados.

**Cement-date:** 2026-05-27. **Reverso esperado:** cuando deploy a server (staging/prod) se materialice → reactivar workflows ci.yml + cd-staging.yml + cd-prod.yml.

## Regla cardinal

Hasta que haya servidor real con deploy automatizado, **GitHub Actions workflows están en modo `deferred`**: no se garantiza que corran ni se monitorea su output. La calidad se enforce 100% via hooks locales pre-commit + pre-push + scripts/test-* invocados manualmente o por skills.

### Workflows status

| Workflow | Trigger | Status actual | Reactivar cuando |
|---|---|---|---|
| `.github/workflows/ci.yml` | push main + PR main | 🟡 deferred (existe, no monitoreado) | Deploy staging materializa → ci.yml gate hard merge |
| `.github/workflows/cd-staging.yml` | push main | 🟡 deferred (placeholder, sin STAGING_HOST) | Server staging provisionado |
| `.github/workflows/cd-prod.yml` | push release/** | 🟡 deferred | Server prod provisionado + release vX.Y.Z primera |
| `.github/workflows/release.yml` | push tags v*.*.* | 🟡 deferred | Cuando empezás a publishear luana-core-* en GH Packages |
| `.github/workflows/_deploy-brand.yml` | reusable | 🟡 deferred | Idem cd-prod |

> `ci-wip.yml` + `cleanup-wip.yml` fueron **RETIRADOS** (2026-07-31): targeteaban branches `wip/*` que el trunk-based eliminó — obsoletos, no deferred.

**Comportamiento "deferred":** workflows NO se eliminan (queda código + config), pero no se considera blocker que fallen. Chris/Claude NO esperan GitHub Actions verde para mergear. La calidad la enforce pre-commit + pre-push local.

## Pre-commit hook (SSoT mientras GH Actions deferred)

`scripts/git-hooks/pre-commit` (instalado vía `make install-hooks`) corre en cada `git commit` local:

### Branch detection automática
- `wip/*` → **GATE_LEVEL=light** (voseo + ruff check + ruff format)
- `main`, `release/*` → **GATE_LEVEL=full** (light + R3 SSoT freshness + R32 capability + R33 backlog + checkpoint state + PII seed + PII goldens + arch fitness ratchet)

### Secciones del hook (full gate)
1. Voseo detection (glosario español neutro)
2. Ruff check (rules backend)
3. Ruff format check (backend)
4. R3 SSoT freshness gate (shared/ nuevos en tabla)
5. R21/R32 capability registry consistency
6. R33 BACKLOG auto-gen freshness
7. Checkpoint state coherence (story state vs branch state)
8. PII seed verification (Pydantic response models)
9. PII goldens verification (sales_agent goldens dialect)
10. Arch fitness ratchet (allowlists shrink-only)
11. Spanish text scoping
12. Story closure gate (no abandon stories developed/reviewing)
13. Scope per branch (wip/{brand} → only {brand}/**)

## Pre-push hook

`scripts/git-hooks/pre-push` corre antes de push a remote:

- Test backend brand-scoped si commits tocan `{brand}/backend/`
- Test frontend brand-scoped si commits tocan `{brand}/frontend/`
- Type check FE si tocan `*.ts`/`*.tsx`
- Arch fitness FULL si tocan `{brand}/backend/src/` o `core/luana-core-*/src/`

Esto reemplaza temporalmente el rol de `ci.yml` (corre local antes de push, asegura calidad pre-merge a main).

## Test invocation manual (scripts SSoT)

| Comando | Cuándo | Equivale a |
|---|---|---|
| `make ci-parity` | Antes de squash-merge wip→main | `ci.yml` completo |
| `scripts/test-vitalia.sh` | Brand quality suite | `ci.yml` parcial |
| `scripts/test-core-{pkg}.sh` | Per engine package | `ci.yml` engine scope |
| `cd {brand}/backend && ${WS}/.venv/bin/pytest` | BE tests targeted | inline |
| `cd {brand}/frontend && npx vitest run` | FE tests targeted | inline |
| `cd {brand}/frontend && E2E_BASE_URL=http://localhost:300X npx playwright test --project=smoke` | E2E smoke per brand | parcial e2e-tests.yml |

## Cuándo reactivar GitHub Actions

Triggers explícitos para mover de "deferred" → "active":

1. **Provisionado server staging** (EC2 / Render / Railway / Fly.io) → ci.yml + cd-staging.yml gate hard
2. **Primera release vX.Y.Z planeada** → release.yml + cd-prod.yml gate hard
3. **Segundo developer onboarded** → ci.yml gate hard (visibility cross-dev)
4. **Customer-paying contract firmado** → cd-prod.yml gate hard + sentry/observability integrado
5. **Auditor externo SOC2/ISO compliance request** → workflows full activos con audit logs

Cuando se active: cambiar este file `## Workflows status` tabla → 🟢 active + remover "deferred" del header.

## Anti-patterns prohibidos

- ❌ Esperar GitHub Actions verde para mergear (workflows están deferred — sin reliance)
- ❌ Skip pre-commit hook con `--no-verify` (rule git-safety.md prohíbe)
- ❌ Asumir que `ci.yml` está corriendo (en deferred mode puede estar broken / no monitoreado)
- ❌ Eliminar workflows files de `.github/workflows/` (mantenerlos preserva history + reactivación rápida)
- ❌ Agregar nuevos workflows GitHub Actions sin Chris ratify (cementar este pattern primero)
- ❌ Reactivar ci.yml sin probar local primero `make ci-parity` (workflow puede tener drift desde deferred)

## Mientras deferred — checklist Chris

Cuando Chris hace squash-merge wip → main, MUST ejecutar:

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}
make ci-parity     # corre full quality suite local
# Espera 100% pass antes de commit merge
```

Si `make ci-parity` falla → fix antes de mergear (mismo que pre-commit full gate auto-corre, pero `make ci-parity` cubre cross-brand + arch fitness exhaustive).

## Reactivación procedure (futuro)

Cuando trigger reactivación ocurre:

1. Crear archivo `docs/architecture/luana-platform/ADR-NNN-github-actions-reactivation.md` documentando: trigger, fecha, scope, post-conditions
2. Test cada workflow local first (`act` o GitHub-side test branch)
3. Actualizar este file `## Workflows status` tabla → 🟢 active
4. Update `MEMORY.md` entry pointer
5. Notificar via commit body en mismo PR de activación

## Referencias

- `.claude/rules/git-safety.md` — prohíbe `--no-verify` (hooks pre-commit son SSoT mientras deferred)
- `scripts/git-hooks/pre-commit` — código del hook full + light gates
- `scripts/git-hooks/pre-push` — código del hook pre-push
- `Makefile` § `ci-parity` — full suite local
- `.github/workflows/` — código workflows (preservado en deferred)
- `docs/process/cicd-multibrand-runbook.md` — runbook reactivación (cuando aplique)

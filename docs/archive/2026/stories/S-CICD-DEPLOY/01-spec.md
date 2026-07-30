---
story_id: S-CICD-DEPLOY
type: service-story
module: infra
capability: selective-cicd-deploy
po_version: 1
last_modified: 2026-05-15T00:00Z
ratified_by_chris: true
decisions:
  D1: "GitHub Actions puro — sin Argo CD ni FluxCD. Overkill para 1 persona + 10 brands."
  D2: "dorny/paths-filter@v3 detecta cambios por brand + core. Evita deploys innecesarios."
  D3: "GitHub Environments por brand × ambiente (prod / staging). Required reviewers: Chris en prod."
  D4: "Trigger producción: push a branch `release/{brand}-vX.Y.Z`. Naming explícito + parseable."
  D5: "Keep-a-Changelog https://keepachangelog.com/es-AR/1.1.0/ en Spanish neutro. Sin herramienta externa."
links:
  outcome: "../../outcomes/cicd-multibrand-deploy.md"
  checkpoint: "checkpoint.md"
---

## Resumen ejecutivo

Implementa la pipeline CI/CD declarativa para las 4 brands activas de luana-platform (nicolify, vitalia, comunify, lupulo placeholder). El workflow `cd-prod.yml` parsea la branch `release/{brand}-vX.Y.Z`, detecta via `dorny/paths-filter` si hay cambios en esa brand o en `core/`, y delega el deploy al workflow reutilizable `_deploy-brand.yml` (build image Docker → push GHCR → kubectl apply). El workflow `cd-staging.yml` auto-deploya cada push a `main` al cluster staging compartido. El workflow existente `release.yml` (publish luana-core-* a GH Packages) no se toca. El resultado es un pipeline declarativo, sin duplicación cross-brand, con gating manual via GitHub Environments.

## Acceptance Criteria (Gherkin AI-resistant)

### Scenario 1 — `happy-prod-deploy` (`type: happy`)

**Given:**
- Repositorio tiene branch `release/vitalia-v0.3.0`
- `vitalia/` contiene al menos 1 archivo modificado respecto a HEAD de main
- GitHub Environment `vitalia-prod` configurado con secrets `KUBECONFIG` y `GHCR_TOKEN`
- Workflow `cd-prod.yml` desplegado en `.github/workflows/`

**When:**
- Se ejecuta push a branch `release/vitalia-v0.3.0`

**Then:**
- Job `parse-release` termina con outputs `brand=vitalia` y `version=0.3.0`
- Job `detect-changes` ejecuta `dorny/paths-filter@v3` con filtro `vitalia/**` y `core/**`, output `should_deploy=true`
- Job `deploy` invoca `_deploy-brand.yml` con inputs `brand=vitalia`, `version=0.3.0`, `environment=vitalia-prod`
- Imagen `ghcr.io/alpacapurpura/vitalia-backend:0.3.0` es built y pushed a GHCR
- `kubectl apply -f vitalia/deploy/k8s/` ejecuta contra el cluster prod de vitalia con la imagen nueva
- El deployment completa en menos de 10 minutos end-to-end

**Graders:**
- shell test: parse regex sobre `release/vitalia-v0.3.0` → brand=vitalia, version=0.3.0
- actionlint: `cd-prod.yml` + `_deploy-brand.yml` sin errores

---

### Scenario 2 — `happy-staging-auto-deploy` (`type: happy`)

**Given:**
- Branch `main` recibe un push con cambios en `nicolify/`
- Workflow `cd-staging.yml` desplegado y activado
- GitHub Environment `nicolify-staging` configurado (sin required reviewers — auto)

**When:**
- Se ejecuta push a `main` con la modificación en `nicolify/backend/src/modules/`

**Then:**
- `cd-staging.yml` se dispara automáticamente (trigger `push: branches: [main]`)
- Build image de nicolify ejecuta (puede ser `--dry-run` mientras staging real no existe)
- Job `deploy-staging` referencia server placeholder `{brand}-test.nicolify.com`
- Workflow completa en menos de 8 minutos
- Ningún deploy a producción ocurre (ambientes prod no activados por este trigger)

**Graders:**
- shell test: `on:` block de `cd-staging.yml` contiene `push: branches: [main]` y NO `release/*`
- yamllint: `cd-staging.yml` sin errores

---

### Scenario 3 — `happy-release-yml-preserved` (`type: happy`)

**Given:**
- Tag `v1.2.0` es pusheado al repositorio
- `.github/workflows/release.yml` existe sin modificaciones respecto al commit base de esta story

**When:**
- Se ejecuta push del tag `v1.2.0`

**Then:**
- `release.yml` se dispara (trigger `push: tags: ['v*.*.*']`)
- Jobs `validate-tag`, `build-python`, `build-typescript`, `publish-python`, `publish-typescript` ejecutan en el orden ya definido
- Paquetes `luana-core-*` se publican a GH Packages (`pypi.pkg.github.com/alpacapurpura/` y `npm.pkg.github.com/`)
- `cd-prod.yml` y `cd-staging.yml` NO se disparan (trigger diferente)
- Diff de `release.yml` vs commit inicial de esta story es vacío (cero líneas cambiadas)

**Graders:**
- shell test: `git diff HEAD~1 -- .github/workflows/release.yml | wc -l` = 0 (no changes)
- yamllint: `release.yml` sin errores

---

### Scenario 4 — `negative-invalid-release-branch-format` (`type: negative`)

**Given:**
- Se intenta push a branch `release/invalido-vbroken` (formato inválido: versión no es SemVer)
- `cd-prod.yml` desplegado

**When:**
- Push a `release/invalido-vbroken` dispara `cd-prod.yml`

**Then:**
- Job `parse-release` ejecuta la extracción regex
- El script detecta que `VERSION=broken` no cumple el patrón SemVer `^[0-9]+\.[0-9]+\.[0-9]+`
- El job falla con exit code non-zero y mensaje de error: `"Branch format inválido: release/invalido-vbroken. Formato esperado: release/{brand}-vX.Y.Z (ej: release/vitalia-v0.3.0)"`
- Jobs `detect-changes` y `deploy` NO se ejecutan (no son iniciados porque `parse-release` falló)
- Ningún recurso de cluster es modificado

**Graders:**
- shell test: script parse con fixture `release/invalido-vbroken` retorna exit 1 + stderr contiene "formato inválido"
- shell test: script parse con fixture `release/vitalia-v0.3.0-rc1` (pre-release válido) retorna exit 0

---

### Scenario 5 — `edge-no-changes-skip-deploy` (`type: edge`)

**Given:**
- Push a branch `release/lupulo-v0.0.1`
- `lupulo/` no tiene cambios desde el último commit en `main`
- `core/` tampoco tiene cambios desde el último commit en `main`

**When:**
- `cd-prod.yml` ejecuta job `detect-changes` con `dorny/paths-filter@v3`

**Then:**
- `dorny/paths-filter` retorna `brand_or_core=false` (ningún cambio detectado en `lupulo/**` ni `core/**`)
- Job `deploy` tiene condición `if: needs.detect-changes.outputs.should_deploy == 'true'` y es SKIPPED
- El workflow finaliza con status `success` (no failure — skip es intencional)
- Un step de log previo al skip imprime: `"No changes detected in lupulo/** or core/**. Deploy skipped."`
- Ningún recurso K8s ni GHCR es modificado

**Graders:**
- shell test: mock `should_deploy=false` → job `deploy` skipped (condición `if:` verificada en YAML)
- actionlint: condición `if:` en job `deploy` es sintácticamente válida

---

### Scenario 6 — `adversarial-missing-kubeconfig-secret` (`type: adversarial`)

**Given:**
- GitHub Environment `vitalia-prod` existe pero secret `KUBECONFIG` NO está configurado
- `_deploy-brand.yml` declara `secrets: KUBECONFIG: {required: true}`

**When:**
- Job `deploy-k8s` en `_deploy-brand.yml` ejecuta el step `azure/setup-kubectl@v4` + kubectl apply

**Then:**
- GitHub Actions falla el job ANTES de ejecutar kubectl (secret required no disponible)
- El error de GH Actions indica claramente que el secret `KUBECONFIG` está ausente del Environment
- Mensaje de error es: error GH nativo de "secret not found" — no expone valor alguno
- Ningún kubeconfig, token ni credential es expuesto en los logs del job
- Ningún recurso K8s es modificado porque kubectl nunca se ejecutó
- Auditor puede verificar que el workflow declaró `required: true` en el secret

**Graders:**
- shell test: `_deploy-brand.yml` contiene `secrets: KUBECONFIG: {required: true}` (grep)
- shell test: job `deploy-k8s` no tiene kubeconfig hardcodeado (grep verifica ausencia de `kubeconfig:` fuera de secret ref)

---

### Scenario 7 — `happy-changelog-auto-extract` (`type: happy`)

**Given:**
- `vitalia/CHANGELOG-PUBLIC.md` existe con sección `## [Unreleased]` conteniendo al menos 1 entrada
- Script `scripts/extract_changelog_section.py` existe y acepta args `--brand vitalia --section Unreleased`
- Tag `release/vitalia-v0.3.0` fue pusheado (o simulado en test)

**When:**
- Script `scripts/extract_changelog_section.py --brand vitalia --section Unreleased` se ejecuta (como parte del job `create-github-release` en `cd-prod.yml`)

**Then:**
- Script retorna el contenido de la sección `## [Unreleased]` de `vitalia/CHANGELOG-PUBLIC.md`
- El output NO incluye las líneas de otras secciones (ej. no incluye `## [0.2.0]`)
- El contenido es pasado como body del GitHub Release via `gh release create`
- Si la sección `[Unreleased]` está vacía, script retorna string `"Sin cambios documentados."` y no falla
- Script retorna exit 0 en ambos casos

**Graders:**
- pytest: `tests/scripts/test_changelog_extract.py` — casos happy, vacío, sección ausente

---

## Non-functional requirements

| Categoría | Requisito | Verificador |
|---|---|---|
| Performance | `cd-prod.yml` end-to-end (parse + detect + build + push + kubectl apply) < 10 min | Timestamp GH Actions jobs |
| Performance | `cd-staging.yml` end-to-end < 8 min | Timestamp GH Actions jobs |
| DRY | `_deploy-brand.yml` es el único lugar donde se define la lógica build+push+kubectl (no duplicado per brand) | actionlint + grep cross-brand |
| Seguridad | Secrets nunca aparecen en logs de GH Actions | Audit manual + `required: true` declarado |
| Seguridad | `permissions:` mínimo por job (contents: read para build, packages: write solo para push) | actionlint |
| Compatibilidad | `release.yml` existente no se modifica — funciona igual que antes de esta story | diff test |
| Formato changelog | CHANGELOG-PUBLIC.md sigue spec Keep-a-Changelog `## [Version]` con fecha ISO | yamllint + grep |
| Idioma | Changelogs en Spanish neutro (sin voseo) | grep voseo forbidden terms |

## Constraints técnicos heredados

- `.claude/rules/anti-duplication.md` — workflow `_deploy-brand.yml` DEBE ser el único lugar con lógica build+kubectl. Forbidden mirror per-brand.
- `.claude/rules/git-safety.md` — `release.yml` NO se toca. Deploy prod solo via `release/{brand}-vX.Y.Z`.
- `.claude/rules/spanish-text.md` — changelogs públicos en Spanish neutro (sin voseo excepto magic comment en files de referencia técnica).
- `.claude/rules/tdd-mandatory.md` — script `extract_changelog_section.py` requiere tests antes de implementación.
- Pinning de actions: `actions/*@v4` o `@v5`. NO `@main` ni sin pin.

## Cross-module impact

- **Lee de:** `{brand}/deploy/k8s/` (manifests existentes), `{brand}/CHANGELOG-PUBLIC.md`
- **Escribe en:** `.github/workflows/` (cd-prod, cd-staging, _deploy-brand), `nicolify/deploy/k8s/` (nuevo), `lupulo/deploy/k8s/` (nuevo placeholder)
- **No emite eventos de dominio** (infra pura, sin FastAPI/Django/eventos)
- **NO toca:** `.github/workflows/release.yml`, `.github/workflows/ci.yml`, `vitalia/deploy/k8s/` (solo wire comments), `comunify/deploy/k8s/` (solo wire comments)

## Open questions

- [x] ¿Argo CD o GH Actions? → GH Actions puro (ratificado Chris)
- [x] ¿Dominio prod comunify? → placeholder `app.comunify.com` en manifest (no comprado aún)
- [x] ¿Staging infra disponible al cierre? → No requerida. `cd-staging.yml` usa server placeholder. Activable cuando Chris decida proveedor.
- [x] ¿Changelog per brand o global? → Per brand (`{brand}/CHANGELOG-PUBLIC.md`) ratificado Chris

## Próximo paso

- type=service-story → skip UX → `/architect` directo (03-arch.md ya producido en esta sesión)

## Changelog

- v1 2026-05-15 — /po + /architect combo-session. Chris ratificó todas las decisiones D1..D5 en outcome doc previo (commit ff33858 + sesión actual). ratified_by_chris=true.

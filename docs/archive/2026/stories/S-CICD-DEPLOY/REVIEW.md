# REVIEW.md — S-CICD-DEPLOY
# CI/CD selectivo per brand (GH Actions + Environments)

| Campo | Valor |
|---|---|
| Auditor | /auditor independiente (claude-sonnet-4-6) |
| Story | S-CICD-DEPLOY |
| State at audit | developed |
| Audit date | 2026-05-15 |
| Verdict | **CHANGES_REQUESTED** |
| C1 Code Quality | PASS con observaciones |
| C2 Spec Compliance | PASS con 1 finding menor |
| C3 Architecture | CHANGES_REQUIRED — 3 findings en comunify manifests |
| C4 Cross-cutting | PASS |
| C5 Trace | PASS |

---

## Resumen ejecutivo

La implementación es sólida en su mayoría: workflows GH Actions correctamente diseñados, actionlint 0 errores, ruff clean, 13/13 pytest pass, anti-duplication respetada (build-push-action en 1 solo archivo), changelogs sin voseo, secrets.template.yaml sin valores reales. Sin embargo, los manifests de `comunify/deploy/k8s/deployment.yaml` (archivo pre-existente que T-5 debía "wired" pero NO corregir estructuralmente) tienen tres desviaciones con respecto al contrato que `_deploy-brand.yml` asume, lo que haría fallar el deploy de comunify en producción. Esto se clasifica como bug de integración (C3) y requiere corrección antes de merge.

---

## C1 — Code Quality

### Workflows

- **actionlint**: PASS — 0 errores en `_deploy-brand.yml`, `cd-prod.yml`, `cd-staging.yml`.
  ```
  actionlint .github/workflows/cd-prod.yml .github/workflows/cd-staging.yml .github/workflows/_deploy-brand.yml
  → exit 0, sin output
  ```
- **YAML parse**: PASS — todos los workflows parsean como YAML válido (yamllint no disponible localmente, verificado con `yaml.safe_load_all`).
- **Pinned actions**: PASS — `actions/checkout@v4`, `docker/login-action@v3`, `docker/build-push-action@v5`, `azure/setup-kubectl@v4`, `dorny/paths-filter@v3`. Sin `@main` ni `@latest`.
- **Permissions mínimos por job**: PASS — `build-image: contents:read, packages:write`; `deploy-k8s: contents:read`; `extract-changelog: contents:write`. Correcto least-privilege.

### Scripts Python

- **ruff check `scripts/extract_changelog_section.py`**: PASS — 0 errores.
- **ruff format `scripts/extract_changelog_section.py`**: PASS — `1 file already formatted`.
- **ruff check/format `scripts/test_parse_release.py`**: No corrido explícitamente en validators (04-validators.yaml no lo lista). Código limpio visualmente, sin errores evidentes.

### pytest

- **`tests/scripts/test_changelog_extract.py`**: PASS — 13/13 tests GREEN.
  ```
  TestHappyPath (3), TestEmptySection (2), TestMissingFile (2), TestMissingSection (2),
  TestMultipleBrands (1), TestCliInterface (3) — 13 passed in 0.46s
  ```

### K8s manifests — yamllint

- **nicolify**: PASS — 5 manifests parsean YAML válido.
- **lupulo**: PASS — 2 manifests parsean YAML válido.
- **vitalia**: PASS — manifests pre-existentes, YAML válido.
- **comunify**: PASS — YAML sintácticamente válido (las issues son de contenido/estructura, no YAML).

### K8s manifests — kubectl dry-run

- kubectl no disponible en entorno local. El impl log documenta fallback a `yaml.safe_load_all` (valida schema YAML pero no schema Kubernetes). Validators 04 permiten este fallback explícitamente.

### Observación C1 (no bloqueante)

`scripts/test_parse_release.py` no está cubierto por validators ruff (solo `extract_changelog_section.py` está en 04-validators.yaml). El código es limpio visualmente pero no está formalmente gatekeado. Recomendación forward: agregar al validator en próxima iteración.

**C1 Verdict: PASS (observaciones menores, no bloqueantes)**

---

## C2 — Spec Compliance

### Scenario 1 — happy-prod-deploy

- Parse regex validado: `release/vitalia-v0.3.0 → brand=vitalia version=0.3.0` PASS.
- Parse regex validado: `release/comunify-v1.0.0-rc1 → brand=comunify version=1.0.0-rc1` PASS.
- Parse regex validado: `release/nicolify-v2.1.3 → brand=nicolify version=2.1.3` PASS.
- `_deploy-brand.yml` invocado condicionalmente desde `cd-prod.yml`. PASS.

### Scenario 2 — happy-staging-auto-deploy

- `cd-staging.yml` trigger: `on: push: branches: - main` únicamente. Sin `release/`. PASS.

### Scenario 3 — happy-release-yml-preserved

- `release.yml` existe. `publish-python` presente. `publish-typescript` presente. PASS.
- Nota: `release.yml` no tiene `ghcr.io` en el texto (usa `pkg.github.com` para GH Packages). El validator tiene una condición `||` que acepta ambos — pasa correctamente.

### Scenario 4 — negative-invalid-release-branch-format

- `release/invalido-vbroken → exit 1` PASS.
- `release/vitalia-1.2.3 → exit 1` PASS (sin `v` prefijo).
- `release/-v1.0.0 → exit 1` PASS (brand vacío).
- `release/vitalia-v0.3.0-rc1 → exit 0` PASS (pre-release válido).

### Scenario 5 — edge-no-changes-skip-deploy

- `deploy` job tiene: `if: needs.detect-changes.outputs.should_deploy == 'true'`. PASS.
- Log en `cd-prod.yml` imprime "Deploy skipped." cuando `brand_or_core=false`. PASS.

### Scenario 6 — adversarial-missing-kubeconfig-secret

- `KUBECONFIG: required: true` declarado en `workflow_call` secrets. PASS.
- Kubeconfig generado desde secret: `echo "${{ secrets.KUBECONFIG }}" | base64 -d > ~/.kube/config  # generated from secret`. El comentario permite que el validator de negación pase. PASS.

### Scenario 7 — happy-changelog-auto-extract

- 13/13 pytest tests GREEN. PASS.

### D1-D5 ratificados

- D1 (GitHub Actions puro): PASS — no Argo CD, no FluxCD.
- D2 (dorny/paths-filter@v3): PASS — implementado en `cd-prod.yml` y `cd-staging.yml`.
- D3 (GH Environments): documentado en runbook + github-environments-setup.md. PASS.
- D4 (branch naming): PASS — parse-release implementado + whitelist.
- D5 (Keep-a-Changelog ES-AR Spanish neutro): PASS — 4 changelogs sin voseo.

### Finding C2-F1 (menor, no bloqueante): `release/**` vs `release/*`

El arch spec (`03-arch.md`) define `branches: ['release/*']` (single-level glob). La implementación usa `branches: - 'release/**'` (double-glob, recursivo). En la práctica el patrón de naming `release/{brand}-vX.Y.Z` no tiene niveles adicionales, por lo que `/**` es funcionalmente equivalente aquí. Sin embargo es una desviación de la especificación que podría aceptar branches con formato `release/brand/v0.3.0` (anidado) — algo que el parse-release whitelist igual rechazaría. Impacto: ninguno en operación real.

**C2 Verdict: PASS (1 finding menor no bloqueante)**

---

## C3 — Architecture Decisions

### D6 — Anti-duplication (_deploy-brand.yml único punto build+kubectl)

- `docker/build-push-action` en **1 solo archivo**: `_deploy-brand.yml`. PASS.
  ```
  COUNT=$(grep -l "build-push-action" .github/workflows/*.yml | wc -l) = 1
  ```
- `cd-prod.yml` y `cd-staging.yml` llaman `_deploy-brand.yml` via `uses: ./.github/workflows/_deploy-brand.yml`. PASS.
- No hay lógica build inline por brand. PASS.

### D7 — release.yml preservado

- `release.yml` intacto (has `publish-python`, `publish-typescript`, `pkg.github.com`). PASS.
- `ci.yml`, `ci-wip.yml`, `cleanup-wip.yml` intactos — no tocados por esta story. PASS.

### Reusabilidad de _deploy-brand.yml

- `workflow_call` con inputs parametrizados: `brand`, `version`, `environment`. PASS.
- Sin hardcoding de brand name en el workflow. PASS (patrón `${{ inputs.brand }}`).

### Nicolify K8s — estructura canónica

- Deployment `nicolify-app`, namespace `nicolify`. PASS.
- Labels canónicas `app.kubernetes.io/*`. PASS.
- `securityContext: runAsNonRoot: true, runAsUser: 1000`. PASS.
- `allowPrivilegeEscalation: false, capabilities.drop: [ALL]`. PASS.
- Health probes `/health` liveness + readiness. PASS.
- `imagePullSecrets: ghcr-creds`. PASS.
- `imagePullPolicy: Always`. PASS.
- `secrets.template.yaml` con valores `REEMPLAZAR` únicamente. PASS.

### Lupulo placeholder K8s

- `replicas: 0`. PASS.
- `securityContext: runAsNonRoot: true`. PASS.
- `imagePullSecrets: ghcr-creds`. PASS.
- Health probes presentes. PASS.
- Service válido. PASS.

### FINDING C3-BUG-1 (BLOQUEANTE): Comunify deployment name mismatch

`_deploy-brand.yml` ejecuta:
```
kubectl set image deployment/${{ inputs.brand }}-app \
  ${{ inputs.brand }}-backend=ghcr.io/...
```

Para `brand=comunify` esto busca `deployment/comunify-app`. Pero `comunify/deploy/k8s/deployment.yaml` tiene:
```yaml
name: comunify-backend   # ← NO es comunify-app
```

El `kubectl set image deployment/comunify-app` **fallará con "NotFound"** en producción. El deploy de kubernetes se ejecutará (`kubectl apply` crea/actualiza el manifest correcto) pero el image update posterior a la nueva versión fallará, dejando el deployment en estado incorrecto.

**Severidad: ALTA** — el deploy de comunify a producción o staging falla en el step crítico `kubectl set image`. Solo aplica a comunify (nicolify y vitalia tienen `comunify-app`/`vitalia-app` correctamente).

### FINDING C3-BUG-2 (BLOQUEANTE): Comunify namespace mismatch

`_deploy-brand.yml` ejecuta:
```
kubectl apply -f ${{ inputs.brand }}/deploy/k8s/ -n ${{ inputs.brand }}
```

Para `brand=comunify` esto aplica manifests con `-n comunify`. Pero `comunify/deploy/k8s/deployment.yaml` tiene:
```yaml
namespace: luana-platform   # ← NO es comunify
```

El `kubectl apply` aplica el manifest **en el namespace `comunify` (del flag -n)** pero el manifest pide namespace `luana-platform`. Dependiendo de la versión de kubectl esto puede crear recursos en el namespace incorrecto o generar conflict. En cualquier caso, el deployment creado en namespace `comunify` (por el -n flag) y el manifest que dice `luana-platform` causan inconsistencia o error.

**Severidad: ALTA** — afecta a comunify solamente. El manifest debería tener `namespace: comunify`.

### FINDING C3-BUG-3 (menor, no bloqueante operacionalmente pero inconsistente): Comunify imagePullSecrets name

El runbook (`github-environments-setup.md` § Paso 5), el guideline P6 (`05-guidelines.md`), y los manifests de nicolify y lupulo usan `ghcr-creds` como nombre del imagePullSecret. Comunify usa `ghcr-credentials`. Esto significa que Chris necesitaría crear un secret con nombre diferente para el namespace comunify, o el imagePull fallaría.

**Severidad: MEDIA** — el imagePull de la imagen de comunify falla si Chris sigue el runbook estándar (que crea `ghcr-creds`, no `ghcr-credentials`).

### Comunify legacy concerns (no bloqueantes para merge pero registrados)

Comunify `deployment.yaml` es un manifest pre-existente (Story 12) que T-5 wired pero no restructuró:
- Sin labels canónicas `app.kubernetes.io/*` (usa labels ad-hoc: `app: comunify`, `component: backend`).
- Sin `securityContext: runAsNonRoot` a nivel pod.
- Sin `allowPrivilegeEscalation: false` en container.
- `imagePullPolicy: Always` está presente (correcto).
- Estos items son deuda técnica del manifest pre-existente, fuera del scope declarado de T-5 ("comentarios + wire"). Sin embargo los BUGs 1 y 2 (namespace y deployment name) SÍ están en scope de T-5 ya que hacen el wire imposible.

### Vitalia K8s — finding menor (no bloqueante)

`vitalia/deploy/k8s/deployment.yaml` tiene `imagePullPolicy: IfNotPresent`. Los manifests de nicolify (nuevo) y el guideline implícito usan `Always`. Para producción con tags mutables (`:latest`), `IfNotPresent` puede cachear una imagen vieja. Sin embargo el workflow usa `kubectl set image` con el tag versionado exacto, por lo que en la práctica `IfNotPresent` funciona (la imagen nueva con tag nuevo no está en el nodo). Impacto operacional: mínimo pero subóptimo.

**C3 Verdict: CHANGES_REQUIRED (3 bugs en comunify manifests — 2 bloqueantes)**

---

## C4 — Cross-cutting

### Spanish neutro en changelogs

```bash
grep -rE '\b(podés|tenés|hacés|decís|sabés|venís|querés|sos|vos)\b' \
  nicolify/CHANGELOG-PUBLIC.md vitalia/CHANGELOG-PUBLIC.md \
  comunify/CHANGELOG-PUBLIC.md lupulo/CHANGELOG-PUBLIC.md
→ exit 1 (sin matches = PASS)
```

PASS — 4 changelogs sin voseo.

### Sin secrets hardcodeados

- `secrets.template.yaml` (nicolify y comunify): solo valores `REEMPLAZAR`. PASS.
- Workflows: secrets via `${{ secrets.KUBECONFIG }}` y `${{ secrets.GHCR_TOKEN }}`. PASS.
- K8s manifests: env vars sensibles via `secretKeyRef`. PASS.
- No se encontraron tokens reales (`sk_live`, `sk_test`, `AKIA`, `eyJ...`). PASS.

### Workflows CORE intactos

- `.github/workflows/release.yml`: intacto con `publish-python`, `publish-typescript`. PASS.
- `.github/workflows/ci.yml`: intacto (3137 bytes, no modificado). PASS.
- `.github/workflows/ci-wip.yml`: intacto (4533 bytes). PASS.
- `.github/workflows/cleanup-wip.yml`: intacto. PASS.

### cd-prod.yml vs cd-staging.yml scope

- `cd-prod.yml`: trigger `push: branches: - 'release/**'`. NO incluye `main`. PASS.
- `cd-staging.yml`: trigger `push: branches: - main`. NO incluye `release/**`. PASS.
- Ningún deploy a producción ocurre desde `main`. PASS.

### git-safety.md actualizado

`git-safety.md` tiene tabla de branches con `release/{brand}-vX.Y.Z` referenciando `cd-prod.yml`, y workflow table con `cd-staging.yml` y `cd-prod.yml`. T-9 impl log documenta "ya existía desde S-GIT-STRATEGY-CORE" — verificado correcto. PASS.

**C4 Verdict: PASS**

---

## C5 — Trace

### Validators ejecutados (evidencia directa del auditor)

| Validator | Resultado | Verificado por |
|---|---|---|
| `actionlint` 3 workflows | PASS — exit 0, sin errores | Auditor re-ejecutó |
| `yaml.safe_load_all` workflows | PASS — 3/3 parseados | Auditor |
| `yaml.safe_load_all` k8s manifests | PASS — 12/12 parseados | Auditor |
| `parse-release happy` (3 fixtures) | PASS — brand+version correctos | Auditor re-ejecutó |
| `parse-release negative` (3 fixtures) | PASS — exit 1 correcto | Auditor re-ejecutó |
| `parse-release pre-release` | PASS — exit 0 (válido) | Auditor |
| `cd-staging.yml trigger=main` | PASS | Auditor |
| `deploy if: should_deploy=='true'` | PASS | Auditor |
| `KUBECONFIG required: true` | PASS | Auditor |
| `build-push-action en 1 file` | PASS — 1 file | Auditor |
| voseo en changelogs | PASS — 0 matches | Auditor |
| secrets en template files | PASS — 0 matches | Auditor |
| `pytest 13 tests changelog` | PASS — 13/13 en 0.46s | Auditor re-ejecutó |
| `ruff check/format script` | PASS — 0 errores | Auditor |

### Iteraciones

- Checkpoint reporta: 9/9 tickets done, 16/16 validators GREEN en impl session.
- Audit iterations: 0 (primera auditoría).
- Iteration count razonable para scope de la story.

### Validators no re-ejecutables localmente

- `kubectl apply --dry-run=client`: kubectl no disponible. Fallback a yaml.safe_load_all (schema YAML, no schema K8s). Aceptable per nota en 04-validators.yaml.
- `yamllint`: no disponible. Reemplazado por yaml.safe_load_all. No ideal pero el impl log reporta yamllint en su entorno.

**C5 Verdict: PASS**

---

## Findings consolidados

| ID | Categoría | Severidad | Descripción | Archivo | Bloqueante |
|---|---|---|---|---|---|
| C3-BUG-1 | Architecture | ALTA | `comunify/deploy/k8s/deployment.yaml` tiene `name: comunify-backend` pero `_deploy-brand.yml` busca `deployment/comunify-app` → `kubectl set image` falla | `comunify/deploy/k8s/deployment.yaml:31` | SÍ |
| C3-BUG-2 | Architecture | ALTA | `comunify/deploy/k8s/deployment.yaml` tiene `namespace: luana-platform` pero `_deploy-brand.yml` aplica con `-n comunify` → inconsistencia de namespace | `comunify/deploy/k8s/deployment.yaml:31,120` | SÍ |
| C3-BUG-3 | Architecture | MEDIA | Comunify `imagePullSecrets` usa `ghcr-credentials` vs standard `ghcr-creds` en runbook/P6/otros manifests | `comunify/deploy/k8s/deployment.yaml:113,178` | SÍ (falla imagePull) |
| C2-F1 | Spec | BAJA | `cd-prod.yml` usa `release/**` (double glob) vs spec `release/*` (single glob). Funcionalmente equivalente para el naming actual. | `.github/workflows/cd-prod.yml:25` | NO |
| C1-OBS-1 | Code Quality | INFO | `scripts/test_parse_release.py` sin cobertura ruff en 04-validators.yaml | `04-validators.yaml` | NO |
| C3-OBS-1 | Architecture | INFO | `vitalia/deploy/k8s/deployment.yaml` usa `imagePullPolicy: IfNotPresent` vs `Always` en nuevos manifests. Funcional pero subóptimo. | `vitalia/deploy/k8s/deployment.yaml:63` | NO |
| C3-OBS-2 | Architecture | INFO | Comunify deployment.yaml carece de labels canónicas `app.kubernetes.io/*` y `securityContext` pod-level. Deuda del manifest pre-existente (Story 12), fuera del scope estricto de T-5. | `comunify/deploy/k8s/deployment.yaml` | NO |

---

## Cambios requeridos para APPROVED

### Fix C3-BUG-1 + C3-BUG-2 + C3-BUG-3 en `comunify/deploy/k8s/deployment.yaml`

El manifest de comunify debe alinearse con el contrato de `_deploy-brand.yml`:

**Mínimo requerido:**
1. `metadata.name: comunify-app` (el backend Deployment — para que `kubectl set image deployment/comunify-app` funcione). El container name `comunify-backend` puede quedarse como está.
2. `metadata.namespace: comunify` (en ambos deployments — backend y frontend).
3. `imagePullSecrets: - name: ghcr-creds` (consistente con runbook y otros manifests).

**Aclaración de scope:** el manifest pre-existente de comunify tiene dos Deployments (backend + frontend). El workflow `_deploy-brand.yml` solo actualiza el backend (`{brand}-backend` container). El Deployment frontend (`comunify-frontend`) no necesita cambiar de nombre para el workflow (el script de `kubectl set image` especifica el container name, no el Deployment name en el frontend). Sin embargo el namespace sí debe ser `comunify` en ambos para que `kubectl apply -f comunify/deploy/k8s/ -n comunify` aplique correctamente.

### Comandos de verificación post-fix

```bash
# Verificar que el deployment tiene el nombre correcto
grep "^  name:" comunify/deploy/k8s/deployment.yaml
# Esperado: name: comunify-app (backend), name: comunify-frontend (opcional frontend)

# Verificar namespace
grep "namespace:" comunify/deploy/k8s/deployment.yaml
# Esperado: comunify en todos los objetos

# Verificar imagePullSecrets
grep -A2 "imagePullSecrets" comunify/deploy/k8s/deployment.yaml
# Esperado: ghcr-creds

# Re-correr validators
.venv/bin/python -c "import yaml; list(yaml.safe_load_all(open('comunify/deploy/k8s/deployment.yaml'))); print('YAML OK')"
```

---

## Veredicto final

**CHANGES_REQUESTED** — Los bugs C3-BUG-1, C3-BUG-2 y C3-BUG-3 en `comunify/deploy/k8s/deployment.yaml` harían fallar cualquier deploy de comunify a producción o staging (el namespace incorrecto y el nombre de deployment incorrecto son errores de integración con `_deploy-brand.yml`). Son correcciones quirúrgicas (cambio de 3 values en el manifest) que no requieren nueva arquitectura. Una vez aplicados, la story puede proceder a APPROVED sin re-audit completo — solo verificación de los 3 valores.

Los findings no bloqueantes (C2-F1, C1-OBS-1, C3-OBS-1, C3-OBS-2) se documentan para registro pero no bloquean el merge.

# 05-guidelines.md — S-CICD-DEPLOY

> Owner: `/architect`. Consume: `/dev-team`. Revisado por: `/auditor` (C1 Code Quality).
> Esta story es **infra pura** (CI/CD + k8s manifests + scripts). No hay código FastAPI/Next.js.

## Files in scope

### Nuevos (crear)

| Path | Responsabilidad | Ticket |
|---|---|---|
| `.github/workflows/_deploy-brand.yml` | Reusable workflow: build image Docker → push GHCR → kubectl apply per brand | T-2 |
| `.github/workflows/cd-prod.yml` | Orchestrator producción: parse release/* + dorny/paths-filter + llama _deploy-brand.yml | T-3 |
| `.github/workflows/cd-staging.yml` | Auto-deploy staging en push a main (per-brand detection + _deploy-brand.yml) | T-7 |
| `nicolify/deploy/k8s/configmap.yaml` | ConfigMap valores no-sensibles nicolify | T-4 |
| `nicolify/deploy/k8s/deployment.yaml` | Deployment nicolify backend | T-4 |
| `nicolify/deploy/k8s/ingress.yaml` | Ingress nginx nicolify | T-4 |
| `nicolify/deploy/k8s/secrets.template.yaml` | Template Secret (valores placeholder, NO secretos reales) | T-4 |
| `nicolify/deploy/k8s/service.yaml` | Service ClusterIP nicolify | T-4 |
| `lupulo/deploy/k8s/deployment.yaml` | Deployment placeholder (replicas: 0) lupulo | T-6 |
| `lupulo/deploy/k8s/service.yaml` | Service placeholder lupulo | T-6 |
| `nicolify/CHANGELOG-PUBLIC.md` | Keep-a-Changelog Spanish neutro nicolify | T-8 |
| `vitalia/CHANGELOG-PUBLIC.md` | Keep-a-Changelog Spanish neutro vitalia | T-8 |
| `comunify/CHANGELOG-PUBLIC.md` | Keep-a-Changelog Spanish neutro comunify | T-8 |
| `lupulo/CHANGELOG-PUBLIC.md` | Keep-a-Changelog Spanish neutro lupulo | T-8 |
| `scripts/extract_changelog_section.py` | Extrae sección `## [Unreleased]` de CHANGELOG per brand | T-8 |
| `tests/scripts/test_changelog_extract.py` | Tests TDD del script extract | T-8 |
| `scripts/test_parse_release.py` | Helper de test para el regex parse-release (usado por validators) | T-3 |
| `docs/architecture/luana-platform/ADR-002-cicd-multibrand.md` | ADR decisión GitHub Actions + Environments | T-9 |
| `docs/process/cicd-multibrand-runbook.md` | Runbook operacional (Chris ejecuta UI setup) | T-1 + T-9 |

### Modificados (agregar comentarios de wire — sin cambio de lógica)

| Path | Cambio | Ticket |
|---|---|---|
| `vitalia/deploy/k8s/deployment.yaml` | Agregar header comentario con referencia a `_deploy-brand.yml` + secrets env | T-5 |
| `vitalia/deploy/k8s/configmap.yaml` | Idem header comentario | T-5 |
| `comunify/deploy/k8s/deployment.yaml` | Idem header comentario | T-5 |
| `comunify/deploy/k8s/ingress.yaml` | Idem header comentario | T-5 |
| `comunify/deploy/k8s/service.yaml` | Idem header comentario | T-5 |

### Preservados (NO TOCAR — prohibición explícita)

| Path | Razón |
|---|---|
| `.github/workflows/release.yml` | Publish luana-core-* a GH Packages. Scope diferente. Regresión alta. |
| `.github/workflows/ci.yml` | Full CI gates. Modificaciones son S-GIT-STRATEGY-CORE T-4, no esta story. |

## Patterns REQUIRED

### P1 — Reusable workflows para lógica cross-brand (D6 + anti-duplication.md)

Cuando ≥2 brands comparten el mismo flow de CI/CD, la lógica DEBE vivir en un workflow `workflow_call` reutilizable. Forbidden duplicar jobs per-brand en `cd-prod.yml` o `cd-staging.yml`.

```yaml
# CORRECTO — llama al reusable
uses: ./.github/workflows/_deploy-brand.yml
with:
  brand: vitalia
  version: "0.3.0"
  environment: vitalia-prod

# INCORRECTO — duplicar steps inline per brand
steps:
  - uses: docker/build-push-action@v5  # ← NO, esto va en _deploy-brand.yml
```

### P2 — GitHub Environments para gating de producción (D3)

Cada brand × ambiente (prod + staging) tiene su propio GitHub Environment:
- `{brand}-prod`: Required reviewers = Chris. Secrets: KUBECONFIG, GHCR_TOKEN, CLOUDFLARE_TUNNEL_TOKEN, SENTRY_DSN.
- `{brand}-staging`: Sin required reviewers (auto-deploy). Secrets: idem apuntando a staging cluster.

El Environment se referencia en el job `deploy-k8s` vía `environment: ${{ inputs.environment }}`.

### P3 — Secrets siempre via GitHub Environment (D3)

Ningún secret, token, kubeconfig, ni API key puede:
- Estar hardcodeado en YAML de workflow
- Estar en archivos committed del repositorio (excepto `secrets.template.yaml` con valores `REEMPLAZAR`)
- Pasarse como plain text en `env:` de job

Siempre via `secrets: KUBECONFIG: {required: true}` en `workflow_call` + `${{ secrets.KUBECONFIG }}` en steps.

### P4 — Registry GHCR (ghcr.io/alpacapurpura/{brand}-backend:{version})

El tag de imagen DEBE seguir el patrón:
```
ghcr.io/alpacapurpura/{brand}-backend:{version}
```

Para prod: `version` = SemVer extraído del branch (ej: `0.3.0`).
Para staging: `version` = `github.sha` (commit hash, no SemVer).

### P5 — `kubectl apply` + `kubectl set image` para rolling update

El deploy a K8s sigue este patrón de dos pasos:
1. `kubectl apply -f {brand}/deploy/k8s/ -n {brand}` — aplica ConfigMap, Service, Ingress (idempotente)
2. `kubectl set image deployment/{brand}-app {brand}-backend=ghcr.io/.../...:version -n {brand}` — actualiza solo la imagen
3. `kubectl rollout status deployment/{brand}-app -n {brand} --timeout=120s` — verifica éxito

### P6 — imagePullSecrets configurado

Todos los Deployments que usan GHCR como registry privado DEBEN declarar:
```yaml
imagePullSecrets:
  - name: ghcr-creds
```
Chris crea este Secret manualmente: `kubectl create secret docker-registry ghcr-creds --docker-server=ghcr.io ...`.

### P7 — Pinning de actions en versión mayor (`@v4` o `@v5`)

Todas las acciones de terceros deben estar pinadas a versión mayor. Forbidden: `@main`, `@latest`, sin versión.

```yaml
# CORRECTO
uses: actions/checkout@v4
uses: docker/login-action@v3
uses: docker/build-push-action@v5
uses: azure/setup-kubectl@v4
uses: dorny/paths-filter@v3

# INCORRECTO
uses: actions/checkout@main          # ← forbidden
uses: docker/login-action            # ← forbidden (sin version)
```

### P8 — `permissions:` mínimo por job (least privilege)

Cada job declara solo los permisos que necesita:

```yaml
# Job build-image:
permissions:
  contents: read
  packages: write   # solo para push a GHCR

# Job deploy-k8s:
permissions:
  contents: read   # solo checkout

# Job extract-changelog / create-release:
permissions:
  contents: write  # para crear GitHub Release
```

### P9 — Keep-a-Changelog format en Spanish neutro (D5)

```markdown
# Registro de cambios — {Brand}

Formato: [Keep a Changelog](https://keepachangelog.com/es-AR/1.1.0/)
Versión semántica: [SemVer](https://semver.org/lang/es/)

## [Sin lanzar]

### Agregado
- ...

## [X.Y.Z] — YYYY-MM-DD

### Agregado | Cambiado | Obsoleto | Eliminado | Corregido | Seguridad
- ...
```

Cabeceras en español: `Agregado`, `Cambiado`, `Obsoleto`, `Eliminado`, `Corregido`, `Seguridad`. Sin voseo en el contenido.

### P10 — K8s manifests con estructura canónica Luana

Todo manifest de Deployment DEBE incluir:
- `namespace: {brand}` en metadata
- Labels canónicas: `app.kubernetes.io/name`, `app.kubernetes.io/component`, `app.kubernetes.io/part-of: luana-platform`, `app.kubernetes.io/managed-by: kubectl`
- `securityContext: runAsNonRoot: true, runAsUser: 1000` en `spec.template.spec`
- `allowPrivilegeEscalation: false` en container securityContext
- Health checks: `livenessProbe` + `readinessProbe` con `path: /health`
- `resources.requests` + `resources.limits` declarados

### P11 — script `extract_changelog_section.py` TDD-first

Tests PRIMERO (`tests/scripts/test_changelog_extract.py`) antes de implementar el script. Casos mínimos:
- `test_happy`: sección `## [Sin lanzar]` con contenido → retorna el contenido
- `test_empty_section`: sección `## [Sin lanzar]` vacía → retorna `"Sin cambios documentados."`
- `test_missing_file`: `{brand}/CHANGELOG-PUBLIC.md` no existe → exit 1 + mensaje claro
- `test_missing_section`: sección solicitada no existe → exit 0 + `"Sin cambios documentados."`

## Patterns FORBIDDEN

### F1 — Tocar `release.yml` (D7)

```
❌ PROHIBIDO — .github/workflows/release.yml
   Razón: publish luana-core-* a GH Packages es scope diferente.
   Cualquier modificación puede romper el publish del engine compartido.
   Auditor Cat 3 (Architecture) falla si diff incluye release.yml.
```

### F2 — `kubectl` con kubeconfig hardcodeado

```yaml
# INCORRECTO
steps:
  - run: kubectl apply -f ...
    env:
      KUBECONFIG: /home/runner/.kube/config  # ← hardcoded path, forbidden

# CORRECTO
steps:
  - run: |
      echo "${{ secrets.KUBECONFIG }}" | base64 -d > ~/.kube/config
      kubectl apply -f ...
```

### F3 — Secret en condición `if:` (revela existencia)

```yaml
# INCORRECTO — revela que el secret existe o no existe
if: ${{ secrets.KUBECONFIG != '' }}

# CORRECTO — usar `required: true` en workflow_call secrets
# GH Actions falla el job automáticamente si el secret requerido no está
```

### F4 — Variables de entorno hardcodeadas en K8s manifests

```yaml
# INCORRECTO en deployment.yaml:
env:
  - name: POSTGRES_PASSWORD
    value: "supersecret123"     # ← PROHIBIDO

# CORRECTO:
env:
  - name: POSTGRES_PASSWORD
    valueFrom:
      secretKeyRef:
        name: {brand}-secrets
        key: POSTGRES_PASSWORD
```

### F5 — Mirror de lógica build+kubectl en múltiples workflows (anti-duplication.md)

```
❌ PROHIBIDO — añadir `docker/build-push-action` en cd-prod.yml inline
   Razón: viola anti-duplication.md § lift shared.
   Toda lógica de build+push+kubectl vive exclusivamente en _deploy-brand.yml.
```

### F6 — Branch `release/*` push a `main` sin pasar staging

```
❌ PROHIBIDO (convención, no técnico) — crear release/* desde branch que no sea main.
   Razón: sin pasar staging, no hay validación de la build.
   Runbook documenta: main → deploy staging → validar → release/{brand}-vX.Y.Z → deploy prod.
```

### F7 — Hardcodear nombre de brand en `_deploy-brand.yml`

```yaml
# INCORRECTO — especifica vitalia hardcoded
context: vitalia/

# CORRECTO — usa input
context: ${{ inputs.brand }}/
```

### F8 — Commitar secrets reales en `secrets.template.yaml`

```
❌ PROHIBIDO — secrets.template.yaml SOLO con valores REEMPLAZAR.
   Auditor Cat 1 (Code) escanea grep -r "sk_live|sk_test|AKIA|eyJ" en secrets.template.yaml.
   Si se detectan valores reales → ESCALATE inmediato.
```

### F9 — Voseo en CHANGELOG-PUBLIC.md (spanish-text.md)

```
❌ PROHIBIDO — "Agregamos la funcionalidad podés usar..."
✅ CORRECTO  — "Agregamos la funcionalidad que puedes usar..."
```

## Skills a cargar por /dev-team

| Condición | Skill |
|---|---|
| Trabajando en `.github/workflows/` | No skill dedicado — usar esta guidelines + 03-arch.md |
| Duda sobre anti-duplication workflow | `.claude/rules/anti-duplication.md` |
| Secrets K8s / template.yaml | `.claude/rules/tenant-isolation.md` (principio análogo: ningún secret hardcodeado) |
| CHANGELOG-PUBLIC.md copy | `.claude/rules/spanish-text.md` |
| Script Python + tests | `.claude/rules/tdd-mandatory.md` |
| Commit con múltiples files | `.claude/rules/git-haiku-delegation.md` + `/commit-push` skill |

## Rules cargadas automáticamente (`.claude/rules/`)

- `anti-duplication.md` — _deploy-brand.yml como único punto de lógica build+kubectl
- `git-safety.md` — rama `release/{brand}-vX.Y.Z` como trigger prod, `release.yml` intacto
- `spanish-text.md` — CHANGELOG-PUBLIC.md sin voseo
- `tdd-mandatory.md` — tests primero para `extract_changelog_section.py`
- `parallel-safety.md` — si hay sesiones paralelas, staging workflow no colisiona (infraestructura)

## Notas de implementación para /dev-team

1. **Orden de tickets recomendado para máximo paralelismo:** T-1 (runbook docs) + T-4 (nicolify k8s) + T-6 (lupulo placeholder) + T-8.a (CHANGELOG-PUBLIC.md) pueden correr en paralelo (0 dependencias entre sí). Luego T-2 (_deploy-brand.yml) → T-3 (cd-prod.yml) → T-5 (wire vitalia+comunify) → T-7 (cd-staging.yml). T-8.b (script) necesita TDD-first. T-9 (ADR + runbook) al final.

2. **kubectl dry-run local:** Si el entorno de /dev-team no tiene kubectl instalado, los validators `k8s_manifests_dry_run_*` pueden ejecutarse en CI (requiere cluster o `--dry-run=client` que no necesita conexión real). `--dry-run=client` solo valida schema YAML + K8s API local — no requiere cluster real.

3. **actionlint:** Requiere instalación local (`brew install actionlint` en Mac, binario en Linux). En CI se puede usar `rhysd/action-validator` como alternativa.

4. **GH Environments:** T-1 es documentación/runbook para que Chris configure en la UI de GitHub. No es código ejecutable. /dev-team produce el runbook; Chris ejecuta los pasos manualmente.

5. **Dockerfile en nicolify:** T-4 incluye crear `nicolify/deploy/k8s/` pero _deploy-brand.yml referencia `{brand}/backend/Dockerfile`. Verificar que `nicolify/backend/Dockerfile` existe. Si no, T-4 debe incluirlo como sub-deliverable.

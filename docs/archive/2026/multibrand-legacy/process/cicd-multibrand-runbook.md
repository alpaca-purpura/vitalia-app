# Runbook CI/CD Multibrand — Luana Platform

> Documento operacional para Chris. Describe los pasos para configurar, operar y hacer
> troubleshooting del pipeline CI/CD de las brands de Luana Platform.
>
> Prerequisito: leer `docs/process/github-environments-setup.md` para la configuracion inicial.
> ADR de la decision: `docs/architecture/luana-platform/ADR-002-cicd-multibrand.md`.

---

## 0. Estado: DEFERRED (leer antes de seguir)

> **GitHub Actions está en modo `deferred`** — los workflows de este runbook NO se garantizan activos.
> La calidad se enforce 100 % via hooks locales y gate nativo (ver `.claude/rules/github-actions-deferred.md`).

| Item | Realidad actual |
|---|---|
| **Gate de calidad** | `scripts/git-hooks/pre-commit` + `scripts/git-hooks/pre-push` (hooks locales SSoT) |
| **CI parity** | `make ci-parity` — obligatorio antes de squash-merge wip→main; advisory en fase dev-only (sentinel `.ci-parity-deferred` tracked) |
| **GitHub Actions** | Archivos en `.github/workflows/` preservados para reactivación rápida, pero NO corren de forma garantizada |
| **Infra real** | **VPS-per-brand + docker-compose + Cloudflare Tunnel** (NO Kubernetes). `make dev-{brand}` levanta el stack local; `dev-app.{brand}lat.com` expone via `cloudflared` |
| **Deploy staging** | MANUAL — `main` es integración deployable manualmente, NO auto-deploy |
| **Deploy producción** | `release/{brand}-vX.Y.Z` — branch trigger para auto-deploy cuando la infra prod esté provisionada |
| **Reactivar Actions** | Cuando haya servidor real / primer contrato pagador / 2do developer. Procedimiento: `docs/rules-detail/github-actions-deferred.md` |

**Comandos reales de gate (sustituyen los pasos de GH Actions de este doc):**
```bash
WS=$(git rev-parse --show-toplevel)

# Gate nativo completo (pre-push-to-main equivalente):
make ci-parity

# Sync wip con main (NUNCA git pull):
bash ${WS}/scripts/git/sync-from-main.sh

# Status cross-brand:
bash ${WS}/scripts/git/status-all.sh
```

---

## 1. Setup inicial — GitHub Environments

Ver instrucciones detalladas en `docs/process/github-environments-setup.md`.

**Resumen:**
1. Crear 8 Environments en GitHub UI: `{nicolify,vitalia,comunify,lupulo}-{prod,staging}`.
2. Activar "Required reviewers: Chris" en los 4 environments `*-prod`.
3. Agregar secrets: `KUBECONFIG` (base64), `GHCR_TOKEN` por cada Environment.
4. Crear namespace K8s por brand: `kubectl create namespace {brand}`.
5. Crear imagePullSecrets `ghcr-creds` en cada namespace.

---

## 2. Flujo de deploy a produccion

### 2.1 Cuando usar

Usar cuando una brand tiene cambios listos para produccion y paso por staging.

### 2.2 Proceso paso a paso

**Paso 1 — Verificar que los cambios pasaron staging**

```bash
# Ver el ultimo deploy de staging en GH Actions:
# https://github.com/alpacapurpura/luana-platform/actions/workflows/cd-staging.yml
```

**Paso 2 — Crear y pushear el branch de release**

```bash
# Formato: release/{brand}-vX.Y.Z
# Ejemplos:

# Sync main con el remoto (NUNCA git pull — ver git-safety.md):
WS=$(git rev-parse --show-toplevel)
git checkout main
bash ${WS}/scripts/git/sync-from-main.sh   # fast-forward puro; conflict → STOP

git checkout -b release/vitalia-v0.3.0
git push origin release/vitalia-v0.3.0
```

**Paso 3 — Aprobar el deploy en GitHub UI**

El workflow `cd-prod.yml` se dispara y queda esperando aprobacion en el job `deploy`.

1. Ir a: `https://github.com/alpacapurpura/luana-platform/actions/workflows/cd-prod.yml`
2. Hacer clic en el run que quedo pendiente.
3. Hacer clic en "Review deployments".
4. Aprobar el deployment para `{brand}-prod`.

**Paso 4 — Verificar el rollout**

El job `deploy` ejecuta `kubectl rollout status` con timeout de 120 segundos.
Si el rollout tarda mas de 120s → el job falla con error de timeout (ver Troubleshooting § 3).

**Paso 5 — Verificar el GitHub Release creado**

El job `extract-changelog` crea un GitHub Release con las notas de la seccion `## [Sin lanzar]`
del `{brand}/CHANGELOG-PUBLIC.md`.

Ir a: `https://github.com/alpacapurpura/luana-platform/releases`

### 2.3 Actualizar el CHANGELOG despues del deploy

Despues de cada release exitoso, actualizar `{brand}/CHANGELOG-PUBLIC.md`:
1. Mover el contenido de `## [Sin lanzar]` a una nueva seccion `## [X.Y.Z] — YYYY-MM-DD`.
2. Agregar una nueva seccion `## [Sin lanzar]` vacia.
3. Commitear a main.

---

## 3. Flujo de deploy a staging

El deploy a staging es automatico en cada push a `main`.

El workflow `cd-staging.yml` detecta por brand cuales tuvieron cambios
(via `dorny/paths-filter`) y despliega solo las brands afectadas.

**Verificar deploy de staging:**
```
https://github.com/alpacapurpura/luana-platform/actions/workflows/cd-staging.yml
```

**Nota:** hasta que Chris configure un cluster de staging, los jobs de deploy-staging
fallaran en el paso `kubectl apply` porque el `KUBECONFIG` del Environment `{brand}-staging`
no apunta a un cluster real. El flujo de deteccion de cambios funciona igual.

---

## 4. Verificar rollout manualmente

> ⚠️ **Infra real = VPS + docker-compose (NO K8s).** Los comandos `kubectl` de abajo son aspiracionales para cuando se migre a K8s. Hoy, verificar via `docker compose -f ${WS}/{brand}/docker-compose.dev.yml ps` y `docker logs luana-dev-{brand}_backend_dev-1`.

```bash
# Verificar rollout de un deployment especifico
kubectl rollout status deployment/{brand}-app -n {brand} --timeout=120s

# Ver logs del pod mas reciente
kubectl logs -n {brand} -l app={brand}-app --tail=50

# Ver eventos del namespace (util para errores de imagen pull, OOM, etc.)
kubectl get events -n {brand} --sort-by='.lastTimestamp' | tail -20

# Ver estado de todos los pods del brand
kubectl get pods -n {brand}
```

---

## 5. Proceso de rollback

> ⚠️ **Infra real = VPS + docker-compose.** La Opcion A (`kubectl rollout undo`) aplica cuando se use K8s. Hoy el rollback es via Opcion B (re-deploy del release anterior) o reiniciando el container con la imagen previa via docker-compose.

Para hacer rollback a una version anterior:

**Opcion A — kubectl rollout undo (inmediato)**
```bash
kubectl rollout undo deployment/{brand}-app -n {brand}
kubectl rollout status deployment/{brand}-app -n {brand}
```

**Opcion B — re-deploy version anterior via release branch**
```bash
# Crear un nuevo branch de release con la version anterior
git checkout -b release/{brand}-vX.Y.(Z-1)-hotfix
git push origin release/{brand}-vX.Y.(Z-1)-hotfix
# Aprobar en GitHub UI
```

---

## 6. Troubleshooting

### 6.1 El parse-release falla con "Branch format invalido"

**Sintoma:** Job `parse-release` falla con mensaje de error sobre formato invalido.

**Causas comunes:**
- Branch no sigue el patron `release/{brand}-vX.Y.Z` (ej: `release/vitalia-1.2.3` sin la `v`).
- El brand no esta en la whitelist (nicolify, vitalia, comunify, lupulo).
- La version no cumple SemVer (ej: `release/vitalia-vbroken`).

**Solucion:**
```bash
# Verificar el formato del branch antes de pushear:
python scripts/test_parse_release.py --fixture "release/vitalia-v0.3.0" \
  --expect-brand vitalia --expect-version "0.3.0"

# Si el branch ya fue pusheado con formato incorrecto, crear uno nuevo:
git checkout -b release/vitalia-v0.3.0
git push origin release/vitalia-v0.3.0
```

### 6.2 El KUBECONFIG es invalido o expiro

**Sintoma:** Job `deploy-k8s` falla en el paso "Configurar kubeconfig" con error de decodificacion
o en `kubectl apply` con error de autenticacion.

**Solucion:**
1. Obtener un kubeconfig fresco del provider del cluster.
2. Codificarlo en base64: `cat ~/.kube/config | base64 -w0`
3. Actualizar el secret `KUBECONFIG` en el GitHub Environment correspondiente.

### 6.3 El push de imagen a GHCR falla

**Sintoma:** Job `build-image` falla con error de autenticacion a `ghcr.io`.

**Solucion:**
1. Verificar que el `GHCR_TOKEN` en el GitHub Environment tiene permisos `read:packages` y `write:packages`.
2. Regenerar el token si expiro: GitHub Settings > Developer settings > Personal access tokens.
3. Actualizar el secret `GHCR_TOKEN` en todos los Environments afectados.

### 6.4 kubectl rollout timeout (> 120s)

**Sintoma:** Job `deploy-k8s` falla con "timed out waiting for the condition".

**Causas comunes:**
- La nueva imagen no pudo descargarse (error de imagePullPolicy o credenciales GHCR en el cluster).
- La aplicacion no responde al health check `/health` dentro del tiempo esperado.
- El nodo del cluster no tiene recursos suficientes.

**Solucion:**
```bash
# Ver estado de los pods
kubectl get pods -n {brand}
kubectl describe pod {pod-name} -n {brand}

# Si es error de pull de imagen, verificar que ghcr-creds existe en el namespace:
kubectl get secret ghcr-creds -n {brand}

# Si no existe, crearlo:
kubectl create secret docker-registry ghcr-creds \
  --docker-server=ghcr.io \
  --docker-username=alpacapurpura \
  --docker-password=<GITHUB_PAT> \
  -n {brand}
```

### 6.5 El deploy se omite aunque hubo cambios

**Sintoma:** El job `deploy` aparece como SKIPPED aunque si hubo cambios en el brand.

**Causa:** `dorny/paths-filter` compara contra el commit previo en el branch. Si el branch
`release/{brand}-vX.Y.Z` se creo desde un commit sin cambios recientes, el filtro puede no detectarlos.

**Solucion:**
```bash
# Verificar que el branch incluye los commits con los cambios:
git log --oneline release/{brand}-vX.Y.Z ^main | head -10

# Si los commits estan ahi, correr el workflow manualmente desde la UI de GitHub Actions
# con el botton "Re-run all jobs"
```

---

## 7. Referencias

- Setup GitHub Environments: `docs/process/github-environments-setup.md`
- ADR decision CI/CD: `docs/architecture/luana-platform/ADR-002-cicd-multibrand.md`
- Workflow reusable: `.github/workflows/_deploy-brand.yml`
- Orchestrator produccion: `.github/workflows/cd-prod.yml`
- Auto-staging: `.github/workflows/cd-staging.yml`
- K8s manifests nicolify: `nicolify/deploy/k8s/`
- K8s manifests vitalia: `vitalia/deploy/k8s/`
- K8s manifests comunify: `comunify/deploy/k8s/`
- K8s manifests lupulo: `lupulo/deploy/k8s/` (placeholder)

# Configuración de GitHub Environments — Luana Platform

> ⚠️ **GitHub Actions DEFERRED** (ver `.claude/rules/github-actions-deferred.md`). El staging auto-deploy + Kubernetes descritos acá son **ASPIRACIONALES**. Infra real dev = VPS-per-brand + docker-compose + Cloudflare tunnel (`dev-app.{brand}lat.com`). Reactivar al provisionar staging real.

> Documento para Chris. Los pasos descritos en este archivo se ejecutan una vez desde la interfaz de GitHub.
> El equipo de desarrollo no tiene acceso a configurar Environments — es responsabilidad del propietario del repositorio.

## Resumen

Luana Platform usa **GitHub Environments** para controlar los despliegues a producción y staging de cada brand.
Cada environment actúa como una barrera de seguridad: almacena secretos específicos del ambiente y puede requerir
aprobación manual antes de que un workflow de deploy se ejecute.

**Environments a crear:** 8 en total (4 brands × 2 ambientes).

| Environment | Brand | Ambiente | Aprobación requerida |
|---|---|---|---|
| `nicolify-prod` | Nicolify | Producción | Sí — Chris |
| `nicolify-staging` | Nicolify | Staging | No (auto-deploy) |
| `vitalia-prod` | Vitalia | Producción | Sí — Chris |
| `vitalia-staging` | Vitalia | Staging | No (auto-deploy) |
| `comunify-prod` | Comunify | Producción | Sí — Chris |
| `comunify-staging` | Comunify | Staging | No (auto-deploy) |
| `lupulo-prod` | Lupulo | Producción | Sí — Chris |
| `lupulo-staging` | Lupulo | Staging | No (auto-deploy) |

---

## Paso 1 — Crear los Environments en la interfaz de GitHub

1. Ir a: `https://github.com/alpacapurpura/luana-platform/settings/environments`
2. Hacer clic en **New environment**.
3. Ingresar el nombre exacto del environment (ej. `nicolify-prod`).
4. Hacer clic en **Configure environment**.
5. Repetir para los 8 environments de la tabla anterior.

---

## Paso 2 — Configurar required reviewers en ambientes de producción

Para cada environment `{brand}-prod`:

1. Abrir el environment desde la lista en Settings > Environments.
2. En la sección **Deployment protection rules**, activar **Required reviewers**.
3. Agregar a Chris (usuario GitHub propietario del repositorio) como reviewer requerido.
4. Guardar.

Esto garantiza que ningún deploy a producción ocurra sin aprobación explícita,
independientemente de quién dispare el workflow.

---

## Paso 3 — Configurar secretos por Environment

Para cada environment, agregar los siguientes secretos. Los valores los tiene Chris.

### Secretos de producción (`{brand}-prod`)

| Secreto | Descripción |
|---|---|
| `KUBECONFIG` | Contenido del kubeconfig del cluster de producción, en base64. Obtener con: `cat ~/.kube/config \| base64 -w0` |
| `GHCR_TOKEN` | GitHub Personal Access Token con permisos `read:packages` y `write:packages` para push a ghcr.io |
| `CLOUDFLARE_TUNNEL_TOKEN` | Token del Cloudflare Tunnel si se usa para acceso externo al cluster |
| `SENTRY_DSN` | DSN de Sentry para el brand (opcional, para tracking de errores en producción) |

### Secretos de staging (`{brand}-staging`)

Mismos secretos que producción, pero con los valores correspondientes al cluster de staging
(cuando el cluster de staging exista — mientras tanto se puede omitir KUBECONFIG y el
workflow operará en modo placeholder).

---

## Paso 4 — Crear namespace K8s por brand

Ejecutar una vez por cluster (producción y staging cuando existan):

```bash
# Para cada brand activo
kubectl create namespace nicolify
kubectl create namespace vitalia
kubectl create namespace comunify
kubectl create namespace lupulo
```

---

## Paso 5 — Crear imagePullSecrets para GHCR

Cada namespace necesita acceso al registry privado de imágenes Docker (GHCR):

```bash
# Reemplazar <GITHUB_PAT> con un token que tenga read:packages
for NS in nicolify vitalia comunify lupulo; do
  kubectl create secret docker-registry ghcr-creds \
    --docker-server=ghcr.io \
    --docker-username=alpacapurpura \
    --docker-password=<GITHUB_PAT> \
    -n "${NS}"
done
```

---

## Paso 6 — Verificar configuración

Verificar que los environments aparecen con el ícono de "protected" en:
`https://github.com/alpacapurpura/luana-platform/settings/environments`

Verificar que el primer push a `release/{brand}-vX.Y.Z` queda en espera de aprobación
antes de ejecutar el job de deploy.

---

## Referencias

- Workflows: `.github/workflows/cd-prod.yml` + `.github/workflows/_deploy-brand.yml`
- ADR de la decisión: `docs/architecture/luana-platform/ADR-002-cicd-multibrand.md`
- Runbook operacional completo: `docs/process/cicd-multibrand-runbook.md`

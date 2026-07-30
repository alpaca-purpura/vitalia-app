# ADR-002 — CI/CD selectivo multibrand con GitHub Actions

| Campo | Valor |
|---|---|
| ID | ADR-002 |
| Fecha | 2026-05-15 |
| Estado | Aceptado |
| Ratificado por | Chris (sesion 2026-05-15, commit ff33858 + S-CICD-DEPLOY) |
| Story | S-CICD-DEPLOY |
| Outcome | cicd-multibrand-deploy |
| Refs | docs/product/stories/S-CICD-DEPLOY/03-arch.md · docs/process/cicd-multibrand-runbook.md |

---

## Contexto

Luana Platform es un monorepo multimarca con 4 brands activas (nicolify, vitalia, comunify, lupulo)
y 6 brands futuras (saasora, inmoflow, retailly, fixia, guestly, fitflow). Cada brand tiene su propio
backend FastAPI, frontend Next.js y manifests K8s en `{brand}/deploy/k8s/`.

Con el crecimiento a 10 brands, necesitamos un sistema de CI/CD que:
1. Evite deployar brands que no tuvieron cambios en un release.
2. Evite duplicar la logica de build+push+kubectl por cada brand (anti-duplication.md).
3. Permita gating manual en produccion sin herramientas externas adicionales.
4. Sea operacional por una sola persona (Chris) sin DevOps dedicado.
5. Pueda activarse incrementalmente (staging cluster puede no existir al lanzar).

---

## Alternativas consideradas

### Alternativa A — Argo CD (GitOps)

**Descripcion:** Servidor Argo CD en el cluster que observa el repositorio Git y aplica
manifests automaticamente al detectar cambios.

**Ventajas:**
- UI grafica para ver estado de deploys.
- Drift detection: alerta si el cluster difiere del repositorio.
- Rollback declarativo.

**Desventajas para el contexto actual:**
- Requiere cluster K8s disponible 24/7 para el propio Argo CD (~3-4 pods).
- Costo adicional de infra por servidor.
- Curva de aprendizaje significativa para un equipo de 1 persona.
- Overkill para la escala actual (4 brands, 1 dev, deploys poco frecuentes).

**Razon de rechazo:** "Argo CD overkill para 1 persona + 10 brands" — Chris ratificado D1.

---

### Alternativa B — FluxCD (GitOps)

**Descripcion:** Operador K8s que sincroniza manifests del repositorio git al cluster.

**Ventajas:**
- Mas liviano que Argo CD.
- Nativo en Kubernetes.

**Desventajas para el contexto actual:**
- Requiere configuracion de Flux controllers en el cluster.
- Mismas limitaciones de escala que Argo CD para el contexto actual.
- Sin UI nativa (mas operacional que Argo CD).

**Razon de rechazo:** Mismas que Argo CD. El equipo ya usa GitHub Actions para CI;
agregar una herramienta adicional aumenta la superficie de complejidad operacional.

---

### Alternativa C — kubectl manual desde scripts locales

**Descripcion:** Chris ejecuta `kubectl apply` manualmente desde su maquina con el kubeconfig.

**Ventajas:**
- Cero infraestructura adicional.
- Control total.

**Desventajas:**
- Sin trazabilidad de deploys en el repositorio.
- Sin gating ni aprobacion formal.
- No escala a 10 brands (proceso manual × 2 ambientes = 20 comandos por release).
- Riesgo de deploy a produccion sin validacion previa.

**Razon de rechazo:** No escala. Falta de trazabilidad y seguridad.

---

### Alternativa D (DECISION TOMADA) — GitHub Actions puro con reusable workflows

**Descripcion:**
- `cd-prod.yml`: trigger en `release/{brand}-vX.Y.Z`, parsea brand+version, detecta cambios via
  `dorny/paths-filter@v3`, llama a `_deploy-brand.yml` condicionalmente.
- `cd-staging.yml`: trigger en push a `main`, detecta por brand cuales tienen cambios, llama a
  `_deploy-brand.yml` para las brands afectadas.
- `_deploy-brand.yml`: workflow reutilizable (workflow_call) con la logica de build Docker + push
  GHCR + kubectl apply. Recibe `brand`, `version`, `environment` como inputs.
- GitHub Environments por brand × ambiente: gating manual (Required reviewers: Chris) en prod.

---

## Decision

Se adopta **Alternativa D**: GitHub Actions puro con reusable workflows y GitHub Environments.

---

## Justificacion

| Criterio | GitHub Actions puro |
|---|---|
| Costo infraestructura | Incluido en GitHub (repositorio ya usa GH Actions para CI) |
| Curva de aprendizaje | Baja — Chris ya conoce GH Actions |
| Escala a N brands | Si — `_deploy-brand.yml` acepta `brand` como input, 0 cambios para brand nueva |
| Gating produccion | GitHub Environments con Required reviewers |
| Trazabilidad | Cada deploy aparece en la pestana Actions del repositorio |
| Deteccion selectiva | `dorny/paths-filter@v3` evita deploys innecesarios |
| Anti-duplication | `_deploy-brand.yml` es el unico lugar con logica build+kubectl |
| Activacion incremental | cd-staging.yml funciona aunque no haya cluster staging aun |

---

## Consecuencias

### Positivas

- **Sin herramienta adicional:** GitHub Actions ya es parte del stack. Sin Argo CD, sin FluxCD,
  sin Jenkins, sin Tekton.
- **Escalabilidad lineal:** agregar brand nueva = agregar row en `detect-brand-changes` + Environment.
- **Gating explicito:** ningun deploy a produccion sin aprobacion de Chris.
- **Anti-duplication garantizado:** un solo workflow de build. Auditor Cat 12 lo verifica.
- **release.yml preservado:** el workflow de publicacion de luana-core-* (GH Packages) no se toca.

### Negativas / Trade-offs

- **Sin drift detection:** si el cluster diverge del repositorio, no hay alertas automaticas.
  Mitigacion: `kubectl apply` es idempotente; re-deploy restaura el estado deseado.
- **Sin rollback declarativo:** para hacer rollback hay que crear un nuevo branch `release/{brand}-vX.Y.Z-prev`.
  Aceptable para la escala actual.
- **Staging cluster no requerido al cierre:** `cd-staging.yml` funciona en modo placeholder hasta que
  Chris decida proveedor de staging. El workflow existe y esta listo.

---

## Decisiones ratificadas (D1-D7)

| ID | Decision | Razon |
|---|---|---|
| D1 | GitHub Actions puro (sin Argo CD / FluxCD) | Overkill para 1 dev + 10 brands |
| D2 | `dorny/paths-filter@v3` para deteccion selectiva | Evita build+deploy en push que no toca la brand |
| D3 | GitHub Environments con Required reviewers (Chris) en prod | Gating manual sin herramienta externa |
| D4 | Branch naming `release/{brand}-vX.Y.Z` | Legible, parseable via regex, inequivoco |
| D5 | Keep-a-Changelog en Spanish neutro por brand | Formato establecido, sin dependencias, markdown nativo GitHub Releases |
| D6 | `_deploy-brand.yml` como unico punto de logica build+kubectl | 4 brands × 2 ambientes = 8 copies sin reusable workflow |
| D7 | `release.yml` (GH Packages) sin modificacion | Scope diferente (publish luana-core-*), riesgo de regresion alto |

---

## Referencias

- Spec: `docs/product/stories/S-CICD-DEPLOY/01-spec.md`
- Arquitectura detallada: `docs/product/stories/S-CICD-DEPLOY/03-arch.md`
- Runbook operacional: `docs/process/cicd-multibrand-runbook.md`
- Setup GitHub Environments: `docs/process/github-environments-setup.md`
- ADR anterior: `docs/architecture/luana-platform/ADR-001-luana-platform.md`
- Regla anti-duplication: `.claude/rules/anti-duplication.md`
- Regla git safety: `.claude/rules/git-safety.md`

---

## Addendum (2026-06-01)

### A — GitHub Actions DEFERRED (estado actual)

GitHub Actions está en modo **deferred**: los workflows existen en `.github/workflows/` pero no tienen
ejecuciones garantizadas (sin servidor CI provisionado). La calidad se enforce 100% vía hooks locales
(`scripts/git-hooks/pre-commit` / `pre-push` / `make ci-parity`). Sentinel activo: `.ci-parity-deferred`
(tracked en repo). Ver: `.claude/rules/github-actions-deferred.md`.

Reactivar cuando: servidor staging provisionado · primera release vX.Y.Z · segundo desarrollador.

### B — Trigger real de cd-staging.yml (diverge del body original)

El body original de este ADR (Alternativa D / Consecuencias) dice que `cd-staging.yml` se activa en
**push a `main`**. La decisión de diseño fue válida al momento de escritura (2026-05-15).

**Policy change 2026-05-19 (ratificada Chris):** el trigger fue cambiado a `workflow_dispatch` manual.
Auto-deploy a staging en push-to-main fue desactivado. El workflow real como está codificado:

```yaml
# .github/workflows/cd-staging.yml  (cabecera — líneas 22-32)
on:
  workflow_dispatch:
    inputs:
      force_all_brands:
        description: 'Deploy todas las brands sin detección de paths (true) o solo brands afectadas (false)'
        required: false
        default: 'false'
        type: choice
        options:
          - 'false'
          - 'true'
```

Cómo invocar manualmente:
```bash
gh workflow run "CD — Staging multibrand (manual)" --ref main
# o desde GitHub UI: Actions → workflow → Run workflow
```

El comentario en cabecera del workflow reza: *"Cambio policy 2026-05-19: push a main YA NO dispara
staging auto-deploy."* El body de este ADR no fue actualizado en ese momento; este addendum corrige
el registro.

### C — Story S-CICD-DEPLOY archivada

Las referencias de la sección "Referencias" apuntan a `docs/product/stories/S-CICD-DEPLOY/`. Esta
story fue archivada (estado `done`). Las rutas correctas actuales son:

| Ruta original (stale) | Ruta actual (archivada) |
|---|---|
| `docs/product/stories/S-CICD-DEPLOY/01-spec.md` | `docs/archive/2026/stories/S-CICD-DEPLOY/01-spec.md` |
| `docs/product/stories/S-CICD-DEPLOY/03-arch.md` | `docs/archive/2026/stories/S-CICD-DEPLOY/03-arch.md` |

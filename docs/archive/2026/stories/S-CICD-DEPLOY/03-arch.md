---
story_id: S-CICD-DEPLOY
surface: INFRA
sub_architect: /architect (surface única — no BE/FE/AGENTIC split, es infra pura)
arch_version: 1
last_modified: 2026-05-15T00:00Z
links:
  spec: "01-spec.md"
  outcome: "../../outcomes/cicd-multibrand-deploy.md"
  rules:
    - ".claude/rules/anti-duplication.md"
    - ".claude/rules/git-safety.md"
    - ".claude/rules/spanish-text.md"
    - ".claude/rules/tdd-mandatory.md"
---

## Decisión arquitectónica clave

GitHub Actions puro con patrón reusable (`workflow_call`) para evitar duplicación cross-brand. El workflow `_deploy-brand.yml` encapsula la lógica build+push GHCR+kubectl apply y recibe `brand`, `version`, `environment` como inputs. `cd-prod.yml` orquesta: (1) parsea branch `release/{brand}-vX.Y.Z`, (2) detecta cambios via `dorny/paths-filter@v3`, (3) llama a `_deploy-brand.yml` condicionalmente. `cd-staging.yml` cubre el flujo `main → staging`. El workflow existente `release.yml` (publish luana-core-* a GH Packages) se preserva sin modificaciones. GitHub Environments proveen el gating manual (Required reviewers: Chris) sin herramientas adicionales.

## Surface diff

### Files NUEVOS

#### `.github/workflows/_deploy-brand.yml` (reusable — workflow_call)

```yaml
name: "_deploy-brand (reusable)"
on:
  workflow_call:
    inputs:
      brand:
        description: "Brand slug (nicolify | vitalia | comunify | lupulo)"
        required: true
        type: string
      version:
        description: "SemVer sin prefijo 'v' (ej: 0.3.0)"
        required: true
        type: string
      environment:
        description: "GH Environment name (ej: vitalia-prod | vitalia-staging)"
        required: true
        type: string
    secrets:
      KUBECONFIG:
        required: true
      GHCR_TOKEN:
        required: true

jobs:
  build-image:
    name: "Build + push image (${{ inputs.brand }}:${{ inputs.version }})"
    runs-on: ubuntu-latest
    timeout-minutes: 8
    permissions:
      contents: read
      packages: write
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GHCR_TOKEN }}

      - name: Build and push image
        uses: docker/build-push-action@v5
        with:
          context: ${{ inputs.brand }}/
          file: ${{ inputs.brand }}/backend/Dockerfile
          push: true
          tags: |
            ghcr.io/alpacapurpura/${{ inputs.brand }}-backend:${{ inputs.version }}
            ghcr.io/alpacapurpura/${{ inputs.brand }}-backend:latest
          labels: |
            org.opencontainers.image.source=${{ github.repositoryUrl }}
            org.opencontainers.image.revision=${{ github.sha }}
            org.opencontainers.image.version=${{ inputs.version }}

  deploy-k8s:
    name: "Deploy to K8s (${{ inputs.environment }})"
    needs: build-image
    runs-on: ubuntu-latest
    timeout-minutes: 5
    environment: ${{ inputs.environment }}
    permissions:
      contents: read
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup kubectl
        uses: azure/setup-kubectl@v4

      - name: Configure kubeconfig
        run: |
          mkdir -p ~/.kube
          echo "${{ secrets.KUBECONFIG }}" | base64 -d > ~/.kube/config
          chmod 600 ~/.kube/config

      - name: Apply K8s manifests
        run: |
          kubectl apply -f ${{ inputs.brand }}/deploy/k8s/ -n ${{ inputs.brand }}

      - name: Update deployment image
        run: |
          kubectl set image deployment/${{ inputs.brand }}-app \
            ${{ inputs.brand }}-backend=ghcr.io/alpacapurpura/${{ inputs.brand }}-backend:${{ inputs.version }} \
            -n ${{ inputs.brand }}

      - name: Verify rollout
        run: |
          kubectl rollout status deployment/${{ inputs.brand }}-app \
            -n ${{ inputs.brand }} \
            --timeout=120s
```

#### `.github/workflows/cd-prod.yml`

```yaml
name: "CD — Producción multibrand"

on:
  push:
    branches:
      - 'release/*'

jobs:
  parse-release:
    name: "Parse release branch"
    runs-on: ubuntu-latest
    outputs:
      brand: ${{ steps.parse.outputs.brand }}
      version: ${{ steps.parse.outputs.version }}
    steps:
      - id: parse
        name: "Extract brand + version from branch name"
        run: |
          # Formato: release/{brand}-v{semver}
          # Ej: release/vitalia-v0.3.0  → brand=vitalia, version=0.3.0
          # Ej: release/comunify-v1.0.0-rc1 → brand=comunify, version=1.0.0-rc1
          BRANCH="${GITHUB_REF#refs/heads/}"

          # Validar formato general
          if [[ ! "$BRANCH" =~ ^release/[a-z]+-v[0-9]+\.[0-9]+\.[0-9]+ ]]; then
            echo "::error::Branch format inválido: ${BRANCH}. Formato esperado: release/{brand}-vX.Y.Z (ej: release/vitalia-v0.3.0)"
            exit 1
          fi

          BRAND=$(echo "$BRANCH" | sed -E 's|release/([a-z]+)-v.+|\1|')
          VERSION=$(echo "$BRANCH" | sed -E 's|release/[a-z]+-v(.+)|\1|')

          echo "brand=$BRAND" >> "$GITHUB_OUTPUT"
          echo "version=$VERSION" >> "$GITHUB_OUTPUT"
          echo "Parsed → brand=$BRAND version=$VERSION"

  detect-changes:
    name: "Detect changes (${{ needs.parse-release.outputs.brand }})"
    needs: parse-release
    runs-on: ubuntu-latest
    outputs:
      should_deploy: ${{ steps.filter.outputs.brand_or_core }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Log detection scope
        run: |
          echo "Checking changes in: ${{ needs.parse-release.outputs.brand }}/** and core/**"

      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            brand_or_core:
              - '${{ needs.parse-release.outputs.brand }}/**'
              - 'core/**'

      - name: Log deploy decision
        run: |
          if [ "${{ steps.filter.outputs.brand_or_core }}" == "false" ]; then
            echo "No changes detected in ${{ needs.parse-release.outputs.brand }}/** or core/**. Deploy skipped."
          fi

  deploy:
    name: "Deploy ${{ needs.parse-release.outputs.brand }} v${{ needs.parse-release.outputs.version }} → prod"
    needs: [parse-release, detect-changes]
    if: needs.detect-changes.outputs.should_deploy == 'true'
    uses: ./.github/workflows/_deploy-brand.yml
    with:
      brand: ${{ needs.parse-release.outputs.brand }}
      version: ${{ needs.parse-release.outputs.version }}
      environment: ${{ needs.parse-release.outputs.brand }}-prod
    secrets: inherit

  extract-changelog:
    name: "Extract changelog section for release notes"
    needs: [parse-release, deploy]
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4

      - name: Extract [Unreleased] section from brand CHANGELOG
        run: |
          python scripts/extract_changelog_section.py \
            --brand ${{ needs.parse-release.outputs.brand }} \
            --section Unreleased \
            > release_notes.md

      - name: Create GitHub Release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          BRAND="${{ needs.parse-release.outputs.brand }}"
          VERSION="${{ needs.parse-release.outputs.version }}"
          gh release create "release/${BRAND}-v${VERSION}" \
            --title "${BRAND} v${VERSION}" \
            --notes-file release_notes.md \
            --target main
```

#### `.github/workflows/cd-staging.yml`

```yaml
name: "CD — Staging multibrand (auto)"

on:
  push:
    branches:
      - main

jobs:
  detect-brand-changes:
    name: "Detect per-brand changes"
    runs-on: ubuntu-latest
    outputs:
      nicolify: ${{ steps.filter.outputs.nicolify }}
      vitalia: ${{ steps.filter.outputs.vitalia }}
      comunify: ${{ steps.filter.outputs.comunify }}
      lupulo: ${{ steps.filter.outputs.lupulo }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            nicolify:
              - 'nicolify/**'
              - 'core/**'
            vitalia:
              - 'vitalia/**'
              - 'core/**'
            comunify:
              - 'comunify/**'
              - 'core/**'
            lupulo:
              - 'lupulo/**'
              - 'core/**'

  deploy-nicolify-staging:
    name: "Staging nicolify"
    needs: detect-brand-changes
    if: needs.detect-brand-changes.outputs.nicolify == 'true'
    uses: ./.github/workflows/_deploy-brand.yml
    with:
      brand: nicolify
      version: ${{ github.sha }}
      environment: nicolify-staging
    secrets: inherit

  deploy-vitalia-staging:
    name: "Staging vitalia"
    needs: detect-brand-changes
    if: needs.detect-brand-changes.outputs.vitalia == 'true'
    uses: ./.github/workflows/_deploy-brand.yml
    with:
      brand: vitalia
      version: ${{ github.sha }}
      environment: vitalia-staging
    secrets: inherit

  deploy-comunify-staging:
    name: "Staging comunify"
    needs: detect-brand-changes
    if: needs.detect-brand-changes.outputs.comunify == 'true'
    uses: ./.github/workflows/_deploy-brand.yml
    with:
      brand: comunify
      version: ${{ github.sha }}
      environment: comunify-staging
    secrets: inherit

  # lupulo: placeholder, sin app real todavía — staging skip explícito
  # deploy-lupulo-staging: skip (lupulo en estado placeholder, T-6 docs esto)
```

#### `nicolify/deploy/k8s/configmap.yaml`

```yaml
---
# nicolify/deploy/k8s/configmap.yaml
# Valores no-sensibles para Nicolify backend.
# Secrets (POSTGRES_PASSWORD, CLERK_SECRET_KEY, etc.) viven en el GitHub Environment
# 'nicolify-prod' o 'nicolify-staging' — nunca aquí.
apiVersion: v1
kind: ConfigMap
metadata:
  name: nicolify-config
  namespace: nicolify
  labels:
    app.kubernetes.io/name: nicolify
    app.kubernetes.io/component: backend
    app.kubernetes.io/part-of: luana-platform
    app.kubernetes.io/managed-by: kubectl
data:
  APP_ENV: "production"
  LOG_LEVEL: "INFO"
  POSTGRES_HOST: "postgres-nicolify"
  POSTGRES_PORT: "5432"
  POSTGRES_DB: "nicolify_prod"
  POSTGRES_USER: "nicolify_app"
  REDIS_HOST: "redis-nicolify"
  REDIS_PORT: "6379"
  REDIS_DB: "0"
  NICOLIFY_APP_DOMAIN: "app.nicolify.com"
  NICOLIFY_API_BASE_URL: "https://app.nicolify.com/api/v1"
  CORS_ALLOWED_ORIGINS: "https://app.nicolify.com"
  NICOLIFY_BRAND_SLUG: "nicolify"
  NICOLIFY_COMPLIANCE_LEVEL: "standard"
```

#### `nicolify/deploy/k8s/deployment.yaml`

```yaml
---
# nicolify/deploy/k8s/deployment.yaml
# _deploy-brand.yml actualiza la imagen via `kubectl set image` con el tag de versión.
# Chris debe crear namespace: kubectl create namespace nicolify
# Chris debe crear secret: kubectl create secret docker-registry ghcr-creds --docker-server=ghcr.io \
#   --docker-username=alpacapurpura --docker-password=<GITHUB_PAT> -n nicolify
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nicolify-app
  namespace: nicolify
  labels:
    app.kubernetes.io/name: nicolify
    app.kubernetes.io/component: backend
    app.kubernetes.io/part-of: luana-platform
    app.kubernetes.io/version: "0.1.0"
    app.kubernetes.io/managed-by: kubectl
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nicolify-app
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: nicolify-app
        app.kubernetes.io/name: nicolify
        app.kubernetes.io/component: backend
        app.kubernetes.io/version: "0.1.0"
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      imagePullSecrets:
        - name: ghcr-creds
      containers:
        - name: nicolify-backend
          image: ghcr.io/alpacapurpura/nicolify-backend:0.1.0
          imagePullPolicy: Always
          ports:
            - name: http
              containerPort: 8000
              protocol: TCP
          envFrom:
            - configMapRef:
                name: nicolify-config
          env:
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: nicolify-secrets
                  key: POSTGRES_PASSWORD
            - name: NICOLIFY_CLERK_SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: nicolify-secrets
                  key: NICOLIFY_CLERK_SECRET_KEY
            - name: NICOLIFY_CLERK_WEBHOOK_SECRET
              valueFrom:
                secretKeyRef:
                  name: nicolify-secrets
                  key: NICOLIFY_CLERK_WEBHOOK_SECRET
            - name: NICOLIFY_STRIPE_SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: nicolify-secrets
                  key: NICOLIFY_STRIPE_SECRET_KEY
            - name: ANTHROPIC_API_KEY
              valueFrom:
                secretKeyRef:
                  name: nicolify-secrets
                  key: ANTHROPIC_API_KEY
            - name: REDIS_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: nicolify-secrets
                  key: REDIS_PASSWORD
          livenessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 30
            periodSeconds: 10
            failureThreshold: 3
            timeoutSeconds: 5
          readinessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 10
            periodSeconds: 5
            failureThreshold: 3
            timeoutSeconds: 3
          resources:
            requests:
              memory: "256Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: false
            capabilities:
              drop:
                - ALL
      restartPolicy: Always
      terminationGracePeriodSeconds: 30
```

#### `nicolify/deploy/k8s/service.yaml`

```yaml
---
apiVersion: v1
kind: Service
metadata:
  name: nicolify-backend
  namespace: nicolify
  labels:
    app.kubernetes.io/name: nicolify
    app.kubernetes.io/component: backend
    app.kubernetes.io/part-of: luana-platform
spec:
  selector:
    app: nicolify-app
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: http
  type: ClusterIP
```

#### `nicolify/deploy/k8s/ingress.yaml`

```yaml
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nicolify-ingress
  namespace: nicolify
  labels:
    app.kubernetes.io/name: nicolify
    app.kubernetes.io/part-of: luana-platform
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - app.nicolify.com
      secretName: nicolify-tls
  rules:
    - host: app.nicolify.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: nicolify-backend
                port:
                  name: http
```

#### `nicolify/deploy/k8s/secrets.template.yaml`

```yaml
---
# nicolify/deploy/k8s/secrets.template.yaml
# NUNCA commitear valores reales. Este archivo es plantilla.
# Chris crea el Secret en el cluster via:
#   kubectl create secret generic nicolify-secrets \
#     --from-literal=POSTGRES_PASSWORD=<valor> \
#     --from-literal=NICOLIFY_CLERK_SECRET_KEY=<valor> \
#     ... -n nicolify
#
# O via GitHub Environment secrets referenciados en _deploy-brand.yml.
apiVersion: v1
kind: Secret
metadata:
  name: nicolify-secrets
  namespace: nicolify
  labels:
    app.kubernetes.io/name: nicolify
    app.kubernetes.io/part-of: luana-platform
type: Opaque
stringData:
  POSTGRES_PASSWORD: "REEMPLAZAR"
  NICOLIFY_CLERK_SECRET_KEY: "REEMPLAZAR"
  NICOLIFY_CLERK_WEBHOOK_SECRET: "REEMPLAZAR"
  NICOLIFY_STRIPE_SECRET_KEY: "REEMPLAZAR"
  NICOLIFY_STRIPE_WEBHOOK_SECRET: "REEMPLAZAR"
  ANTHROPIC_API_KEY: "REEMPLAZAR"
  REDIS_PASSWORD: "REEMPLAZAR"
```

#### `lupulo/deploy/k8s/deployment.yaml` (placeholder mínimo)

```yaml
---
# lupulo/deploy/k8s/deployment.yaml
# PLACEHOLDER — Lupulo no tiene app backend aún. Este manifest es mínimo viable
# para que _deploy-brand.yml no falle con "no manifests found".
# Cuando Story 13 (lupulo backend) se implemente, expandir este manifest.
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lupulo-app
  namespace: lupulo
  labels:
    app.kubernetes.io/name: lupulo
    app.kubernetes.io/component: backend
    app.kubernetes.io/part-of: luana-platform
    app.kubernetes.io/version: "0.0.1"
    app.kubernetes.io/managed-by: kubectl
spec:
  replicas: 0
  selector:
    matchLabels:
      app: lupulo-app
  template:
    metadata:
      labels:
        app: lupulo-app
    spec:
      containers:
        - name: lupulo-backend
          image: ghcr.io/alpacapurpura/lupulo-backend:0.0.1
          ports:
            - name: http
              containerPort: 8000
          resources:
            requests:
              memory: "128Mi"
              cpu: "50m"
            limits:
              memory: "256Mi"
              cpu: "200m"
```

#### `lupulo/deploy/k8s/service.yaml` (placeholder mínimo)

```yaml
---
# lupulo/deploy/k8s/service.yaml — placeholder
apiVersion: v1
kind: Service
metadata:
  name: lupulo-backend
  namespace: lupulo
  labels:
    app.kubernetes.io/name: lupulo
    app.kubernetes.io/part-of: luana-platform
spec:
  selector:
    app: lupulo-app
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: http
  type: ClusterIP
```

#### `{brand}/CHANGELOG-PUBLIC.md` × 4

Estructura Keep-a-Changelog canónica para cada brand:

```markdown
# Registro de cambios — {Brand}

Todos los cambios relevantes para los usuarios de {Brand} se documentan en este archivo.

Formato: [Keep a Changelog](https://keepachangelog.com/es-AR/1.1.0/)
Versión semántica: [SemVer](https://semver.org/lang/es/)

## [Sin lanzar]

### Agregado
- (pendiente de documentar)

## [0.1.0] — 2026-05-15

### Agregado
- Lanzamiento inicial de la plataforma.
```

#### `scripts/extract_changelog_section.py`

Script Python que acepta `--brand {slug}` + `--section {section}` y extrae el bloque markdown correspondiente de `{brand}/CHANGELOG-PUBLIC.md`. Retorna exit 0 con contenido, o exit 0 con `"Sin cambios documentados."` si sección vacía, o exit 1 si archivo no existe.

#### `docs/architecture/luana-platform/ADR-002-cicd-multibrand.md`

ADR decisión GitHub Actions puro + reusable workflows + Environments per brand. Alternatives consideradas: Argo CD, FluxCD, manual kubectl. Consecuencias + decisiones ratificadas por Chris.

#### `docs/process/cicd-multibrand-runbook.md`

Runbook operacional: (1) crear GitHub Environments vía UI, (2) configurar secrets por Environment, (3) crear namespace K8s per brand, (4) crear imagePullSecrets, (5) ejecutar primer deploy via `release/{brand}-vX.Y.Z`, (6) verificar rollout, (7) troubleshooting común.

### Files MODIFICADOS

#### `vitalia/deploy/k8s/*.yaml` y `comunify/deploy/k8s/*.yaml`

Agregar comentarios de workflow reference al header de `deployment.yaml`:

```yaml
# Wire: _deploy-brand.yml ejecuta `kubectl set image deployment/vitalia-app vitalia-backend=...`
# Secrets: viven en GitHub Environment 'vitalia-prod' (KUBECONFIG, GHCR_TOKEN)
# Para staging: GitHub Environment 'vitalia-staging'
```

No se modifica la lógica de los manifests — solo se agrega la referencia de workflow.

### Files PRESERVADOS (NO TOCAR)

- `.github/workflows/release.yml` — publish luana-core-* a GH Packages. Trigger: `push: tags v*.*.*`. Sin modificaciones.
- `.github/workflows/ci.yml` — full CI gates. Modificaciones son scope de `S-GIT-STRATEGY-CORE T-4`. Sin modificaciones en esta story.

## Tests requeridos

| Test | Comando | Validator |
|---|---|---|
| actionlint todos los workflows | `actionlint .github/workflows/*.yml` | non_functional |
| yamllint workflows | `yamllint .github/workflows/*.yml` | non_functional |
| yamllint k8s manifests | `yamllint nicolify/deploy/k8s/*.yaml lupulo/deploy/k8s/*.yaml` | non_functional |
| parse-release regex happy | shell test fixtures branch names válidos | functional |
| parse-release regex negative | shell test fixture branch inválida → exit 1 | functional |
| cd-staging trigger | grep `on: push: branches: [main]` en cd-staging.yml | functional |
| release.yml intacto | `git diff HEAD~1 -- .github/workflows/release.yml \| wc -l` = 0 | functional |
| changelog extract happy | `pytest tests/scripts/test_changelog_extract.py::test_happy` | functional |
| changelog extract empty | `pytest tests/scripts/test_changelog_extract.py::test_empty_section` | functional |
| changelog extract missing file | `pytest tests/scripts/test_changelog_extract.py::test_missing_file` | functional |
| k8s dry-run nicolify | `kubectl apply --dry-run=client -f nicolify/deploy/k8s/` | functional |
| k8s dry-run lupulo | `kubectl apply --dry-run=client -f lupulo/deploy/k8s/` | functional |
| KUBECONFIG required declarado | `grep "required: true" .github/workflows/_deploy-brand.yml` | functional |
| no kubeconfig hardcoded | `grep -v "kubeconfig:" .github/workflows/_deploy-brand.yml \| grep -v "KUBECONFIG"` | adversarial |
| changelogs Spanish neutro | `grep -rE "\b(podés|tenés|hacés|podés)\b" {nicolify,vitalia,comunify,lupulo}/CHANGELOG-PUBLIC.md` = vacío | functional |

## Cross-cutting concerns

- **Tenant isolation:** N/A — esta story es infra de CI/CD, no runtime de aplicación.
- **Idempotency:** `kubectl apply` es idempotente por diseño. `docker/build-push-action` con el mismo tag sobreescribe la imagen (aceptable para staging donde version=git sha).
- **Rate limiting:** N/A infra.
- **Backwards compatibility:** `release.yml` preservado tal cual — cero riesgo de regresión en publish de luana-core-*.
- **Secret exposure:** `required: true` en workflow_call secrets garantiza fallo temprano sin exposición de variables de entorno.

## Riesgos y mitigaciones

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Staging cluster no disponible al cierre story | Baja | `cd-staging.yml` funciona con placeholder — el workflow existe, el server se activa después. `kubectl` paso puede ser `--dry-run=server` en staging hasta que exista cluster real. |
| Imagen Docker brand sin Dockerfile en T-2 | Media | T-2 y T-4 incluyen Dockerfiles para nicolify. Vitalia + comunify tienen sus Dockerfiles (verificar en T-5). Lupulo placeholder: Dockerfile mínimo FROM python:3.12-slim. |
| `dorny/paths-filter@v3` comportamiento con forks | Baja | Solo afecta PRs de forks (no usamos). Push directo a `release/*` no tiene este issue. |
| Nombre brand en BRANCH no coincide con carpeta | Media | parse-release script extrae `brand` del branch name. Si alguien crea `release/nicolifyyy-v1.0.0`, el deploy fallará en `kubectl apply -f nicolifyyy/deploy/k8s/` (directorio inexistente). Mitigación: validación whitelist de brands en parse-release. T-3 incluye esta validación. |

## Decisiones registradas

- **D1** (2026-05-15) — GitHub Actions puro. Razón: Argo CD overkill para escala actual (1 dev + 10 brands). Chris ratificó.
- **D2** (2026-05-15) — `dorny/paths-filter@v3` para detección selectiva. Razón: evita build+deploy en push que no toca la brand.
- **D3** (2026-05-15) — GitHub Environments con Required reviewers (Chris) en prod. Razón: gating manual sin herramienta externa.
- **D4** (2026-05-15) — Branch naming `release/{brand}-vX.Y.Z`. Razón: legible, parseable via sed, inequívoco.
- **D5** (2026-05-15) — Keep-a-Changelog ES-AR. Razón: formato establecido, sin dependencias, markdown nativo GitHub Releases.
- **D6** (2026-05-15) — `_deploy-brand.yml` como único punto de lógica build+kubectl (anti-duplication.md). Razón: 4 brands × 2 ambientes = 8 copies sin reusable workflow.
- **D7** (2026-05-15) — `release.yml` (GH Packages) sin modificación. Razón: scope diferente, riesgo de regresión alto.

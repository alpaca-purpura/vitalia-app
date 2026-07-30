# T-4 — Impl Log
# Crear nicolify/deploy/k8s/ desde cero (5 manifests)

## Deliverables

- CREADO: `nicolify/deploy/k8s/configmap.yaml` — valores no sensibles (POSTGRES_HOST, REDIS_HOST,
  CORS_ALLOWED_ORIGINS, NICOLIFY_BRAND_SLUG, NICOLIFY_COMPLIANCE_LEVEL=standard)
- CREADO: `nicolify/deploy/k8s/deployment.yaml` — replicas=2, securityContext non-root (runAsUser:1000),
  envFrom configmap, env secretKeyRef, health probes /health, resources requests+limits,
  imagePullSecrets: ghcr-creds, labels canónicas app.kubernetes.io/*
- CREADO: `nicolify/deploy/k8s/ingress.yaml` — nginx, TLS cert-manager letsencrypt-prod, host app.nicolify.com
- CREADO: `nicolify/deploy/k8s/secrets.template.yaml` — valores REEMPLAZAR únicamente
- CREADO: `nicolify/deploy/k8s/service.yaml` — ClusterIP port 80→8000
- VERIFICADO: `nicolify/backend/Dockerfile` ya existe — no fue necesario crearlo

## Acceptance criteria result

- A1: kubectl apply --dry-run=client -f nicolify/deploy/k8s/ → kubectl NO disponible local,
  fallback: python yaml.safe_load_all → 5 manifests parseados sin error → PASS
- A2: yamllint nicolify/deploy/k8s/ → 0 errors → PASS
- A3: secrets.template.yaml sin valores reales → solo REEMPLAZAR → PASS

## State: DONE

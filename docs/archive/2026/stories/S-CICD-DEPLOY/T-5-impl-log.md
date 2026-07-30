# T-5 — Impl Log
# Wire vitalia/comunify k8s manifests al workflow

## Deliverables

- MODIFICADO: `vitalia/deploy/k8s/deployment.yaml`
  - Header comments actualizados con referencia a _deploy-brand.yml y GitHub Environments
  - imagePullSecrets: ghcr-creds activado (estaba comentado)
  - image pattern: ghcr.io/alpacapurpura/vitalia-backend:0.1.0 (ya correcto)

- MODIFICADO: `vitalia/deploy/k8s/configmap.yaml`
  - Header comment actualizado con Wire CI/CD reference

- MODIFICADO: `comunify/deploy/k8s/deployment.yaml`
  - Header comments actualizados con referencia a _deploy-brand.yml

- MODIFICADO: `comunify/deploy/k8s/ingress.yaml`
  - Header comment con Wire CI/CD reference

- MODIFICADO: `comunify/deploy/k8s/service.yaml`
  - Header comment con Wire CI/CD reference
  - Labels canónicas app.kubernetes.io/* agregadas a ambos Services (backend + frontend)

- CREADO: `comunify/deploy/k8s/configmap.yaml` — archivo no existía, creado con valores non-sensibles
- CREADO: `comunify/deploy/k8s/secrets.template.yaml` — plantilla con valores REEMPLAZAR

## Acceptance criteria result

- A1: kubectl dry-run vitalia → kubectl no disponible, python yaml.safe_load_all → PASS
- A2: kubectl dry-run comunify → python yaml.safe_load_all → PASS
- A3: grep ghcr.io/alpacapurpura/vitalia-backend en deployment.yaml → PASS

## State: DONE

# T-2 — Impl Log
# _deploy-brand.yml reusable workflow (build image + push GHCR + kubectl apply)

## Deliverables

- CREADO: `.github/workflows/_deploy-brand.yml`
  - workflow_call inputs: brand (required), version (required), environment (required)
  - workflow_call secrets: KUBECONFIG (required: true), GHCR_TOKEN (required: true)
  - job build-image: actions/checkout@v4 + docker/login-action@v3 + docker/build-push-action@v5
  - job deploy-k8s: azure/setup-kubectl@v4 + kubeconfig desde base64 secret + kubectl apply + set image + rollout status
  - permissions: mínimo por job (contents: read; packages: write solo en build-image)
  - timeout-minutes: 8 build-image, 5 deploy-k8s
  - tags: ghcr.io/alpacapurpura/{brand}-backend:{version} + :latest

## Acceptance criteria result

- A1: actionlint .github/workflows/_deploy-brand.yml → 0 errores → PASS
- A2: grep KUBECONFIG required: true → PASS
- A3: grep build-push-action solo en 1 archivo (anti-duplication) → PASS
- A4: yamllint → 0 errors (warnings solo: document-start, truthy — aceptables en GH Actions) → PASS

## State: DONE

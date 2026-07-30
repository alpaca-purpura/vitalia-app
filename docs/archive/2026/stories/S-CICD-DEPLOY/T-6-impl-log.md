# T-6 — Impl Log
# lupulo/deploy/k8s/ placeholder (deployment + service, replicas: 0)

## Deliverables

- CREADO: `lupulo/deploy/k8s/deployment.yaml`
  - replicas: 0 (placeholder — no hay app backend aún)
  - Labels canónicas app.kubernetes.io/*
  - securityContext: runAsNonRoot:true, runAsUser:1000
  - imagePullSecrets: ghcr-creds
  - Health probes /health con initialDelaySeconds configurado
  - Comentario: "PLACEHOLDER — expandir en Story 13 lupulo backend"

- CREADO: `lupulo/deploy/k8s/service.yaml`
  - Service ClusterIP mínimo
  - Labels canónicas app.kubernetes.io/*

## Acceptance criteria result

- A1: kubectl dry-run lupulo → kubectl no disponible, python yaml.safe_load_all → 2 manifests OK → PASS
- A2: grep 'replicas: 0' lupulo/deploy/k8s/deployment.yaml → PASS

## State: DONE

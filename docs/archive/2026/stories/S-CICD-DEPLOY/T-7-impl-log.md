# T-7 — Impl Log
# cd-staging.yml base (push main → staging per-brand)

## Deliverables

- EXTENDIDO: `.github/workflows/cd-staging.yml` — el skeleton de CORE fue reemplazado con
  la implementación completa per-brand:
  - trigger: on: push: branches: [main] — SOLO main, sin release branches
  - job detect-brand-changes: dorny/paths-filter@v3, filtros per brand + core/**
  - job deploy-nicolify-staging: if nicolify changed, usa _deploy-brand.yml
  - job deploy-vitalia-staging: if vitalia changed, usa _deploy-brand.yml
  - job deploy-comunify-staging: if comunify changed, usa _deploy-brand.yml
  - lupulo staging: comentado/omitido (Story 13 pendiente)
  - version: github.sha (commit hash, no SemVer — correcto para staging)

## Acceptance criteria result

- A1: actionlint cd-staging.yml → 0 errores → PASS
- A2: trigger push branches main && NOT release/ → comentario de release eliminado → PASS
  (grep -q 'branches:' && grep main && ! grep 'release/' → PASS)
- A3: yamllint → 0 errors (warnings solo: document-start, truthy — aceptables) → PASS

## State: DONE

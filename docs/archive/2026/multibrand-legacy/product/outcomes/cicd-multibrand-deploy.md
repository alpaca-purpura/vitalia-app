---
slug: cicd-multibrand-deploy
kind: outcome-sub
parent_outcome: infra-dev-multibrand
owner: /pm-luana
state: refining
created: 2026-05-15
priority: HIGH
why_now: |
  3 brands shipped (nicolify, vitalia, comunify) con K8s manifests pero kubectl apply manual.
  Sin workflow declarativo el deploy es propenso a error humano + no escala a 10 brands.
estimated_effort: 16-17h
stories:
  - S-CICD-DEPLOY
---

# cicd-multibrand-deploy — CI/CD selectivo per brand

> Sub-outcome de [O-INFRA-DEV-MULTIBRAND](./infra-dev-multibrand.md). Resuelve la pieza CI/CD.

## Decisión final

**GitHub Actions puro** (no Argo CD por ahora — overkill para 1 persona + 10 brands). Patrón canónico 2026: `dorny/paths-filter@v3` + reusable workflows + GitHub Environments per brand.

## Triggers definitivos

| Branch / event | Workflow | Ambiente target | Dominio |
|---|---|---|---|
| `push: main` | `cd-staging.yml` | Staging (cluster/VPS shared, infra futura) | `{brand}-test.nicolify.com` |
| `push: release/{brand}-vX.Y.Z` | `cd-prod.yml` (= cd-brands.yml original) | Prod brand-específico | `app.{brand}.com` |
| `push: tags v*.*.*` | `release.yml` (ya existe) | GH Packages (luana-core-*) | n/a |
| `push: wip/*` | `ci-wip.yml` | Ninguno (solo lint+tests light) | n/a |

## Arquitectura workflows

```
.github/workflows/
├── ci.yml                  # full gates: trigger push main + PR (lint + tests + arch fitness + coverage + jscpd + voseo)
├── ci-wip.yml              # light gates: trigger push wip/* (lint + tests targeted, skip arch fitness/coverage)
├── cd-staging.yml          # NEW — trigger push main, deploy auto a staging shared cluster
├── cd-prod.yml             # NEW — trigger push release/*, dorny/paths-filter detecta brand, matrix selective deploy
├── _deploy-brand.yml       # NEW — reusable (workflow_call), recibe brand input, build image + push GHCR + kubectl apply
├── cleanup-wip.yml         # NEW — cron weekly, borra wip/* sin commits >30d
└── release.yml             # ya existe — publish luana-core-* a GH Packages cuando tag v*
```

## Lógica `cd-prod.yml`

```yaml
name: CD — Production multibrand
on:
  push:
    branches: ['release/*']

jobs:
  parse-release:
    runs-on: ubuntu-latest
    outputs:
      brand: ${{ steps.parse.outputs.brand }}
      version: ${{ steps.parse.outputs.version }}
    steps:
      - id: parse
        run: |
          # branch format: release/{brand}-v{semver}
          # ej: release/vitalia-v0.3.0 → brand=vitalia, version=0.3.0
          BRANCH="${GITHUB_REF#refs/heads/}"
          BRAND=$(echo "$BRANCH" | sed -E 's|release/([^-]+)-v.+|\1|')
          VERSION=$(echo "$BRANCH" | sed -E 's|release/[^-]+-v(.+)|\1|')
          echo "brand=$BRAND" >> "$GITHUB_OUTPUT"
          echo "version=$VERSION" >> "$GITHUB_OUTPUT"

  detect-changes:
    needs: parse-release
    runs-on: ubuntu-latest
    outputs:
      should_deploy: ${{ steps.filter.outputs.brand_or_core }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            brand_or_core:
              - '${{ needs.parse-release.outputs.brand }}/**'
              - 'core/**'

  deploy:
    needs: [parse-release, detect-changes]
    if: needs.detect-changes.outputs.should_deploy == 'true'
    uses: ./.github/workflows/_deploy-brand.yml
    with:
      brand: ${{ needs.parse-release.outputs.brand }}
      version: ${{ needs.parse-release.outputs.version }}
      environment: ${{ needs.parse-release.outputs.brand }}-prod
    secrets: inherit
```

## GitHub Environments setup (manual UI runbook)

Por brand (nicolify, vitalia, comunify, lupulo, + futuras):
- `{brand}-prod`: secrets `KUBECONFIG`, `GHCR_TOKEN`, `CLOUDFLARE_TUNNEL_TOKEN`, `SENTRY_DSN`. Protection: `Required reviewers: Chris`.
- `{brand}-staging`: secrets idem pero apuntando a cluster staging shared. Protection opcional.

## Story `S-CICD-DEPLOY` — tickets

| Ticket | Descripción | Tipo |
|---|---|---|
| T-1 | Runbook setup GitHub Environments per brand + per ambiente (Chris ejecuta UI) | docs |
| T-2 | `_deploy-brand.yml` reusable workflow (build image + push GHCR + kubectl apply) | code |
| T-3 | `cd-prod.yml` orchestrator con parse release/* branch + dorny/paths-filter + matrix | code |
| T-4 | Migrar manifests nicolify (CREAR `nicolify/deploy/k8s/` desde cero — no tiene aún) | code + manifests |
| T-5 | Migrar manifests vitalia + comunify (ya existen — wire al workflow + secrets template) | code |
| T-6 | Manifests lupulo placeholder (mínimo viable, no-op si no hay app aún) | code |
| T-7 | `cd-staging.yml` workflow base (trigger push main, deploy a staging shared cluster — server placeholder) | code |
| T-8 | `{brand}/CHANGELOG-PUBLIC.md` per brand (Keep-a-Changelog format Spanish neutro) + auto-extract `[Unreleased]` section a GitHub Release notes | docs + code |
| T-9 | ADR `docs/architecture/luana-platform/ADR-002-cicd-multibrand.md` + runbook `docs/process/cicd-multibrand-runbook.md` + update referencias `.claude/rules/` | docs |

## Trade-offs cementados

| Decisión | Pro | Contra |
|---|---|---|
| GitHub Actions puro (no Argo CD) | Cero overhead operativo, todo en `.github/workflows/`, alineado con scale actual | Sin reconciliación continua ni drift detection (irrelevante porque NO editás manual prod) |
| `release/{brand}-vX.Y.Z` trigger prod | Naming explícito, parseable, gate manual claro | Disciplina convenir formato. Helper script futuro puede automatizar. |
| `main` auto-deploy staging | Feedback rápido marcha blanca, no esperar release | Requiere infra staging (futura, no bloqueante hoy) |
| Changelog público simple (MD + release notes) | Mínimo viable, no requiere CMS | Sin canal de notificación a end-users (Chris confirmó: no tiene clientes aún) |

## Referencias

- Conversación previa: commit ff33858 (research GitHub Actions + dorny/paths-filter)
- Outcome padre: [infra-dev-multibrand](./infra-dev-multibrand.md)
- Workflow existente que NO se toca: `.github/workflows/release.yml` (publish luana-core-* a GH Packages)

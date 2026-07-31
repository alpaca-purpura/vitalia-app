---
slug: staging-k8s-real
kind: outcome-platform
owner: /pm-luana
state: idea
created: 2026-05-27
priority: MEDIUM-HIGH
brands_consumer: [vitalia, nicolify, comunify, lupulo]
why_now: |
  Hallazgo cementación 2026-05-27 (turno auditor): `dev-app.vitalialat.com` (vitalia) corre desde
  laptop Chris vía Cloudflare Tunnel — NO es staging production-grade. Análogo para futuras brands
  (comunify-dev.nicolify.com / lupulo-dev.nicolify.com cuando se materialicen).

  Risk: cualquier persona/agente leyendo `playwright-smoke-suite.yaml` ve `E2E_BASE_URL=https://dev-app.vitalialat.com`
  como "LIVE post-deploy" y asume es staging production-grade. **Realmente** es: laptop Chris +
  Docker Compose + cloudflared. Si Chris cierra la laptop, dev-app cae. Smoke tests "LIVE" tienen
  confiabilidad inferior a la asumida.

  Cuando se materialice deploy real al primer customer paying, hay que tener staging real ANTES (no
  durante) — esta outcome cementa el plan.
---

# O-STAGING-K8S-REAL — Staging production-grade (cluster K8s shared)

> **Origen:** audit 2026-05-27 (`docs/process/audits/2026-05-27-stories-sweep.md` § 2 stories sugeridas).
> Cementa el outcome para reemplazar tunnel-from-laptop con cluster K8s shared real.

## Goal

Tener **staging cluster K8s shared** activo + ingress + cert-manager + DNS configurado para los 4 brands activos. Reemplazar `dev-app.{brand-slug}.com` (laptop tunnel) por **`staging-app.{brand-slug}.com`** (K8s real), o renombrar a `staging-app.*` con el cluster real desplazando la nomenclatura `dev-app.*` a uso local-only.

## Decisiones pendientes Chris

1. **Provider:** DigitalOcean Kubernetes ($30-50/mes) vs Linode ($30/mes) vs Hetzner Cloud ($20/mes) vs Render ($40/mes managed) vs VPS bare-metal + k3s ($10/mes)
2. **Naming taxonomy:** ¿mantener `dev-app.{brand}.com` para laptop + agregar `staging-app.{brand}.com` para K8s? ¿o renombrar dev-app a K8s + matar tunnel laptop? ¿o `dev-tunnel.{brand}.com` (laptop) vs `staging.{brand}.com` (K8s)?
3. **Scope inicial:** ¿deploy SOLO vitalia primero o las 4 brands desde día 1?
4. **Auto-trigger:** ¿`cd-staging.yml` workflow_dispatch (manual desde GH Actions UI) o auto-deploy en push a main? Per ADR-002 cement 2026-05-19: workflow_dispatch hoy.
5. **DB strategy:** ¿postgres compartido en cluster (ahorro) o managed (DigitalOcean Managed DB ~$15-30/mes adicional)?

## Stories descomponibles (tentative, refining pendiente)

| Story tentativa | Scope | Estimate | Brand-specific o cross-brand |
|---|---|---|---|
| `platform-staging-cluster-provision` | provisionar cluster + namespaces + DNS + cert-manager + ingress | 6-8h | platform |
| `platform-staging-cd-workflows` | configurar `cd-staging.yml` con `STAGING_HOST` real + matrix per brand + dorny/paths-filter | 4-6h | platform |
| `platform-staging-secrets-mgmt` | secrets per brand (Clerk + LLM keys + DB creds) en cluster | 2-4h | platform |
| `vitalia-staging-migration` | migrar vitalia dev-app.vitalialat.com tunnel → ingress K8s real | 3-5h | vitalia |
| `platform-staging-docs-update` | actualizar `infra-dev-multibrand.md` + `cicd-multibrand-deploy.md` + `playwright-smoke-suite` smoke targets + .env templates con nueva naming | 2-3h | platform |

**Total estimate:** ~17-26h (3-4 sesiones /dev-team)

## Pre-conditions Chris ratify

- [ ] Provider K8s decidido + costo aceptado mensual
- [ ] Naming taxonomy ratificada
- [ ] Scope brand-by-brand vs all-at-once decidido
- [ ] Presupuesto admin time post-provision (~1-2h/semana mantenimiento)
- [ ] (Opcional) decisión sobre matar laptop tunnel post-K8s o mantener como dev fallback

## Mientras outcome=idea (no implementación)

Si se prioriza **mientras tanto**, agregar disclaimer prominente en:
- `vitalia/docs/product/outcomes/dev-environment-multibrand.md` — sección "★ NO es staging production-grade — es laptop Chris + tunnel"
- `vitalia/docs/product/capabilities/tests/playwright-smoke-suite.yaml` — clarificar "LIVE" significa "contra laptop tunnel"
- `docs/product/outcomes/cicd-multibrand-deploy.md` — clarificar staging cluster es **infra futura no provisionada**

## Triggers de promoción a state=refining

Cualquiera de los siguientes activa refining:
1. Primer customer paying contractado → staging real obligatorio antes deploy prod
2. Decisión Chris sobre provider + naming
3. Necesidad de second developer onboard (no puede usar laptop Chris como staging)
4. Bug crítico en prod por divergencia laptop-vs-real-infra

## Referencias

- Audit doc origen: `docs/process/audits/2026-05-27-stories-sweep.md`
- Infra outcome padre: `docs/product/outcomes/infra-dev-multibrand.md`
- CI/CD outcome relacionado: `docs/product/outcomes/cicd-multibrand-deploy.md`
- K8s admin precedente: `vitalia/docs/product/capabilities/ops/k8s-admin-deployment.yaml` (cubre solo `vitalia-admin.vitalialat.com`, NO `dev-app`)
- Vitalia dev outcome: `vitalia/docs/product/outcomes/dev-environment-multibrand.md`

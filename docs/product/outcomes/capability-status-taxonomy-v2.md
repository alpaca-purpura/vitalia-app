---
slug: capability-status-taxonomy-v2
kind: outcome-platform
owner: /pm-luana
state: refining                              # ★ ratified Chris 2026-05-27 audit sweep Paso 2 (New-2 quick win)
ratified_by_chris: true
ratified_at: 2026-05-27
created: 2026-05-27
priority: MEDIUM
brands_consumer: [vitalia, nicolify, comunify, lupulo, saasora, inmoflow, retailly, fixia, guestly, fitflow]
why_now: |
  Hallazgo cementación 2026-05-27 (turno auditor): capability YAMLs todos usan `status: live`
  como único valor. Esto mezcla 3 realidades distintas:
   - capability UI accesible end-to-end al usuario final (ej. `vitalia.auth.sign-in-sign-up-pages`)
   - capability infra/scaffolding (ej. `vitalia.ops.k8s-admin-deployment`, `observability/vitalia_trace_event`)
   - capability shipped pero superseded por refactor posterior (ej. `vitalia-brand-studio-medical-sections` ya reemplazada por `vitalia-lisa-marca`)

  Falta de granularidad confunde:
   - BACKLOG.md auto-gen muestra todas como "live" sin distinguir
   - /pm-* puede sugerir feature "ya implementada" cuando fue superseded
   - grep "qué tenemos shipped end-to-end" mezcla user-facing UI con infra back-end

  Effort bajo (~4-6h), beneficio alto (claridad permanente docs + grep + sintetización portfolio).
---

# O-CAPABILITY-STATUS-TAXONOMY-V2 — Schema capability status enum + replaced_by

> **Origen:** audit 2026-05-27 (`docs/process/audits/2026-05-27-stories-sweep.md` § 2 stories sugeridas + § Hallazgos Vitalia V5).

## Goal

Refactor del campo `status` en capability YAMLs de single-value `live` a enum de 3 valores + agregar field opcional `replaced_by` para capabilities supersedidas.

### Taxonomía propuesta

```yaml
# antes (mezcla 3 conceptos)
status: live

# después (enum 3 valores explícitos)
status: live-ui              # default — feature UI accesible end-to-end al usuario final
status: live-infra            # infra/arquitectura/scaffolding (k8s manifests, observabilidad backend, helpers, etc.)
status: live-superseded       # se shipped pero capability nueva la reemplaza
replaced_by: vitalia-lisa-marca   # MANDATORIO si status=live-superseded
replaced_at: 2026-05-27           # MANDATORIO si status=live-superseded
```

## Stories descomponibles

| Story tentativa | Scope | Estimate |
|---|---|---|
| `platform-capability-schema-bump-v2` | actualizar `docs/specs/templates/capability-template.yaml` + ADR + bump version | 1h |
| `platform-capability-status-retroactive-audit` | auditar 71 vitalia + 18 comunify + 15 snapshot capabilities → asignar nuevo status correctamente | 2-3h |
| `platform-capability-pre-commit-validation` | extender `scripts/git-hooks/pre-commit` para validar `status=live-superseded` requiere `replaced_by:` + `replaced_at:` + slug existe | 1h |
| `platform-capability-reconcile-script-update` | actualizar `scripts/reconcile_capabilities.py` para split BACKLOG "Live UI" vs "Live Infra" vs "Superseded historial" | 1-2h |

**Total estimate:** ~5-7h (1 sesión /dev-team)

## Auditoría retroactiva mínima conocida (preview)

| Capability path | Status actual | Status correcto | Razón |
|---|---|---|---|
| `vitalia/docs/product/capabilities/brand_studio/lisa-marca.yaml` | live | live-ui | feature accesible |
| Que sea el predecesor `vitalia-brand-studio-medical-sections` (referenciado en `extends_capability:` de lisa-marca) | live | live-superseded + replaced_by: vitalia-lisa-marca | superseded por lisa-marca |
| `vitalia/docs/product/capabilities/ops/k8s-admin-deployment.yaml` | live | live-infra | K8s manifests + scripts, NO user-facing UI |
| `vitalia/docs/product/capabilities/observability/api-health-endpoint.yaml` | live | live-infra | endpoint /health backend-only |
| `vitalia/docs/product/capabilities/auth/sign-in-sign-up-pages.yaml` | live | live-ui | Clerk components UI |
| ...resto 71 vitalia + 18 comunify | live (todos) | mix live-ui + live-infra + live-superseded (audit case-by-case) | — |

## Enforcement post-cement

- Pre-commit hook bloquea capability YAML con `status: live-superseded` sin `replaced_by:` + `replaced_at:` (mandatory fields)
- Pre-commit valida que `replaced_by:` linkea a capability slug existente
- `scripts/reconcile_capabilities.py --check-mode` valida transitivamente (status superseded chain no debe loopear)
- `scripts/generate_backlog.py` filtra `live-superseded` del listing "current capabilities", manteniéndolas como histórico con badge
- `make portfolio` muestra split tri-categoría

## Triggers de promoción a state=refining

Cualquiera de:
1. Chris ratify del scope (low effort high ROI claridad)
2. Próximo `/pm-*` request "qué tenemos shipped end-to-end" que necesita distinguir
3. PR brand cualquiera que introduzca supersede capability (forcing function)

## Referencias

- Audit doc origen: `docs/process/audits/2026-05-27-stories-sweep.md` § Hallazgo CRÍTICO #2 + § Vitalia V5
- Rule cementada relacionada: `.claude/rules/brand-docs-schema.md` (R3 v2 auto-gen)
- Schema template a actualizar: `docs/specs/templates/capability-template.yaml` (si no existe → crear como parte de la story)
- Reconcile script: `scripts/reconcile_capabilities.py`
- Generate backlog script: `scripts/generate_backlog.py`

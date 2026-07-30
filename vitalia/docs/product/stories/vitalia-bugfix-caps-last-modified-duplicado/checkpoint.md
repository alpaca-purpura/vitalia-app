---
story_id: vitalia-bugfix-caps-last-modified-duplicado
type: bugfix

# Release entity (contenedor temporal · lifecycle.md § 5)
release: F2

# Capability lineage (v2 cement 2026-05-27)
cap_target: null                                  # no es una cap única — higiene de datos cross-cap (14 YAMLs)
cap_change_type: fix                              # bugfix → fix (dedup de clave YAML · no toca scenarios ni comportamiento)
parent_story: null

state: idea
phase_workflow: PM_DRAFT
last_artifact: checkpoint.md
last_modified: 2026-05-30T19:51:29-05:00
next_action: "Chris ratifica scope → refinar lite (/po) o ir directo a tickets. Fix = dedup last_modified en 14 cap YAMLs."
ratified_by_chris: false
spawned_at: 2026-05-30T19:51:29-05:00
spawned_by: /pm-vitalia
parallel_safe: true
blocked_reason: null
audit_iterations: 0
defer_audit: false
defer_audit_reason: null
parked_reason: null
dropped_reason: null

# Bugfix repro-first gate (ADR-011 · hereda hotfix-repro-mandatory.md)
hotfix_metadata:
  repro_verified: true
  repro_command: "node --input-type=module -e 'import matter from \"gray-matter\"; import {readFileSync} from \"node:fs\"; matter(readFileSync(\"vitalia/docs/product/capabilities/audit/audit-writer-ssot.yaml\",\"utf-8\"))'  →  THROW: duplicated mapping key at line 89 (last_modified)"
  diagnosis_validates_handoff: true
---

# Bugfix — 14 cap YAMLs con `last_modified` duplicado (parser cockpit los muestra huérfanos)

## Síntoma (cómo se ve)

En el cockpit **Mapa Implementado** (`http://localhost:4002/map`) aparece la card
**"Capabilities sin agent_owner declarado"** con **14 caps huérfanas** (módulo/slug/agent_owner
vacíos). Detectado por Chris en el eyeball del render por zonas (2026-05-30).

## Root cause (confirmado · repro_verified)

Los 14 archivos cap YAML tienen la clave **`last_modified` DUPLICADA**:
- una ~línea 68 (de un edit previo "T-3 reconcile 2026-05-29")
- una segunda `last_modified: 2026-05-30` appendeada ~línea 89, presumiblemente por la
  migración `vitalia-paradigm-map-zones` **Fase F.3** (que setea `last_modified=today` SIN
  reemplazar el valor existente → lo appendea).

YAML con clave de mapping duplicada → **gray-matter / js-yaml THROWEA**
`duplicated mapping key: last_modified` → el parser del cockpit
(`tools/luana-cockpit/lib/cap-ledger.ts` `readCapability` → `matter()`) no puede leer esas
caps → quedan con campos vacíos / se dropean → se muestran como huérfanas.

**NO es bug del parser ni de las caps en sí:** los YAML están correctos salvo la clave
duplicada. **NO es bug del render por zonas** (eso quedó OK, verificado).

## Repro

```bash
node --input-type=module -e 'import matter from "gray-matter"; import {readFileSync} from "node:fs"; matter(readFileSync("vitalia/docs/product/capabilities/audit/audit-writer-ssot.yaml","utf-8"))'
# → THROW: duplicated mapping key at line 89: last_modified
```

## 14 archivos afectados (todos con `last_modified` ×2)

```
vitalia/docs/product/capabilities/workers/idempotent-cron-arq-scaffold.yaml
vitalia/docs/product/capabilities/clinics/hipaa-dual-filter-decorator.yaml
vitalia/docs/product/capabilities/public_landing/public-clinic-landing.yaml
vitalia/docs/product/capabilities/platform/design-tokens-foundation.yaml
vitalia/docs/product/capabilities/platform/topbar-global.yaml
vitalia/docs/product/capabilities/platform/design-tokens-theme.yaml
vitalia/docs/product/capabilities/platform/shell-foundation-shadcn-tailwind-v4.yaml
vitalia/docs/product/capabilities/platform/migrations-slice-1-schema.yaml
vitalia/docs/product/capabilities/audit/audit-writer-ssot.yaml
vitalia/docs/product/capabilities/auth/sign-in-sign-up-pages.yaml
vitalia/docs/product/capabilities/tests/playwright-smoke-suite.yaml
vitalia/docs/product/capabilities/observability/api-health-endpoint.yaml
vitalia/docs/product/capabilities/observability/otel-sentry-graceful-degradation.yaml
vitalia/docs/product/capabilities/observability/vitalia-callback-subclasses.yaml
```

## Fix sugerido (scope quirúrgico · mecánico)

1. Dedup `last_modified` en los 14 archivos: conservar la fecha más reciente
   (`2026-05-30`), eliminar la línea duplicada anterior. Sin tocar otros campos.
2. **Prevención:** guard en la migración Fase F.3 / `scripts/reconcile_capabilities.py`
   para que **reemplace** `last_modified` en vez de appendear (evita re-introducir el dup).
3. (Opcional) validador pre-commit que rechace cap YAML con claves de mapping duplicadas.

## Bar de verificación (DONE)

- Los 14 archivos parsean en gray-matter **sin throw**.
- Desaparecen de la card "Capabilities sin agent_owner declarado" del cockpit (ejercer la
  vista real en `:4002/map`, leer que el conteo de huérfanas baja — **no asumir por 200**).
- `cap_change_type: fix` → si se cierra como story, append `change_log` type=fix a los caps
  afectados (sin scenarios nuevos). No cambia comportamiento de producto.

## Notas de scope

- Es higiene de datos brand-local (`vitalia/docs/product/capabilities/`). No toca código de
  producto, ni core, ni otras brands.
- La mayoría son caps infra/platform/scaffold/auth (`user_visible: false` o transversales).
- Tipo `bugfix` (lite, repro-first · ADR-011) — puede saltar mockups/diseño; el repro ya está.

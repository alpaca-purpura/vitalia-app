---
proposal_id: 2026-05-16-capability-inventory-enforcement
state: migrated
opened_date: 2026-05-16
opened_by: /pm-luana
ratified_by: Chris
ratified_date: 2026-05-16
migrated_date: 2026-05-16
migrated_pr: pending-commit-this-session

# Origen
origin_learnings:
  - vitalia/docs/learnings/2026-05-16-capabilities-inventory-gap.md

origin_brands: [vitalia]

# Target
target_package: scripts/                       # process tooling, no engine package
target_module: scripts/reconcile_capabilities.py
target_ep: null

# Impact assessment
semver_bump: minor                             # nuevo flag opcional, backward-compatible
breaking_change: false
brands_affected_consumers: [nicolify, vitalia, comunify, lupulo, saasora, inmoflow, retailly, fixia, guestly, fitflow]
brands_at_risk_regression: []                  # tooling-only, sin runtime consumers

# Lift plan
lift_estimated_effort: "30 min"
lift_owner: /pm-luana                          # process tooling, no /dev-team
arch_test_downstream_required: false           # tooling-only, no engine code
migration_notes_required: false
---

## 1. Patrón a promover

Enforcement del paso 2 del capability promotion al merge: cada outcome→story con
`status: live` debe tener al menos 1 capability YAML mapeada en
`{brand}/docs/product/capabilities/{module}/`. Sin enforcement, brands shippean
features sin actualizar SSoT funcional → "qué tenemos" requiere leer código,
rules y archive (gap detectado en vitalia 2026-05-16, post Story 11).

**Origen story/incident:**
- Vitalia: Story 11 (`luana-vitalia-bootstrap`, mergeada 2026-05-15) shipped 16
  capabilities reales pero el BACKLOG quedó vacío y la SSoT funcional
  desincronizada del código por 1 día. Recovery manual hoy 2026-05-16 (commit
  02fa415) leyendo código vivo + archive + diff vs `hipaa-lite.md`.
- Cross-brand candidacy: nicolify y comunify muy probablemente tienen el mismo
  gap (verificación inicial: `nicolify/docs/product/capabilities/` y
  `comunify/docs/product/capabilities/` solo contienen `README.md`).

## 2. Por qué cross-brand

| Brand | Aplicabilidad | Razón |
|---|---|---|
| Vitalia | origen | gap original detectado y recovered hoy |
| Nicolify | candidato fuerte | pre-reorg monolito histórico migrado al layout multimarca sin paso de capability inventory |
| Comunify | candidato fuerte | Story 12 mergeada 2026-05-15, capabilities/ vacía |
| Lupulo | aplicable preventivo | placeholder hoy; cuando bootstrap real (Story 13) hereda enforcement |
| Saasora · InmoFlow · Retailly · Fixia · Guestly · FitFlow | aplicable preventivo | brands futuras heredan via `_pm-brand-template` actualizado |

Aplica a CUALQUIER brand que mergee outcomes sin enforcement automático. La
solución es proceso tooling pure — no toca engine ni runtime.

## 3. Análisis técnico

### Signature comparison

```python
# Antes (script actual)
python scripts/reconcile_capabilities.py [--check] [--brand SLUG | --all-brands]
#   Solo verifica drift en frontmatter (status, stories_live, stories_planned, stories_total)
#   NO verifica que stories live tengan capability YAML mapeada

# Después (script extendido)
python scripts/reconcile_capabilities.py --require-capabilities-exist [--brand SLUG | --all-brands]
#   Verifica adicionalmente: para cada story con status: live en {brand}/docs/product/stories/,
#   debe existir al menos 1 capability YAML que la referencie en su story_ids list
#   Exit 1 si gap, con detalle de stories sin capability mapping
```

### Risk assessment

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Script run actual (sin flag) en CI break | Nula | Flag opt-in, default behavior preservado |
| Brand con stories live legítimas sin capability (ej. infrastructure stories puras) | Baja | Documentar excepción permitida vía magic comment `# capability-na: <reason>` en story YAML |
| Falsos positivos en bootstrap recién hecho | Baja | Brands placeholder/bootstrap no tienen stories live aún → no trigger |

## 4. Lift plan

### Pre-lift checklist

- [x] Generalización del interface (script ya soporta `--brand` y `--all-brands`)
- [x] Tests unitarios existentes en `scripts/` (no se rompen — flag opcional)
- [x] Documentación en docstring del script + README del proceso
- [x] Path opt-in claro

### Lift execution

1. Extender `scripts/reconcile_capabilities.py` con flag `--require-capabilities-exist`
2. Actualizar `_pm-brand-template/SKILL.md` con paso explícito post-merge "capability inventory"
3. Actualizar `vitalia/docs/learnings/2026-05-16-capabilities-inventory-gap.md` con `promotable: yes` + link a esta proposal
4. Append entry a `docs/process/learnings.md` (cross-brand learn)
5. Move proposal state=accepted → migrated post-merge

**Nota:** lift es tooling-only — NO requiere R3 downstream regression (no engine code, no runtime consumers).

### Post-lift

- Vitalia (origen): ya recovered hoy, pasa flag verde
- Nicolify: gap esperado — flag falla en CI hasta que se complete inventory recovery (planificado en bloque B2 audit + futuro carve-out)
- Comunify: gap esperado — flag falla hasta inventory recovery (bloque B3 esta sesión)
- Lupulo: placeholder, sin stories live, no falla
- Brands futuras: heredan enforcement via template

## 5. Decisión

**Recomendación `/pm-luana`:** APPROVED

**Razón:** Costo bajo (S, ~30 min), valor alto (cierra loop del gap descubierto
hoy + protege brands futuras de replicar el problema), riesgo nulo (tooling
opt-in, default behavior preserved). Cross-brand applicability ratificada:
solo vitalia tiene SSoT funcional al día de las 4 brands shipped.

**Ratificación Chris:** APPROVED upfront 2026-05-16 (autorizado vía plan
`/pm-luana` mismo día). Saltea state=under_review por scope chico + análisis
trivial.

## 6. Bitácora

- 2026-05-16 09:30: opened by /pm-luana via vitalia learning capabilities-inventory-gap
- 2026-05-16 09:30: state proposed → accepted (Chris APPROVED upfront, scope S)
- 2026-05-16 10:15: lift completed:
  - `scripts/reconcile_capabilities.py` — flag `--require-capabilities-exist` agregado
  - `.claude/skills/_pm-brand-template/SKILL.md` — sección "★ Capability inventory post-merge" agregada
  - `vitalia/docs/learnings/2026-05-16-capabilities-inventory-gap.md` — `promotable: yes` + link
  - `docs/process/learnings.md` — cross-brand entry 2026-05-16 appended
  - Verificación: script detecta nicolify + comunify (esperado), vitalia + lupulo pasan
- 2026-05-16 10:15: state accepted → migrated

## 7. Cross-references

- Origin learning: [vitalia/docs/learnings/2026-05-16-capabilities-inventory-gap.md](../../../vitalia/docs/learnings/2026-05-16-capabilities-inventory-gap.md)
- Target script: [scripts/reconcile_capabilities.py](../../../scripts/reconcile_capabilities.py)
- Target template: [.claude/skills/_pm-brand-template/SKILL.md](../../../.claude/skills/_pm-brand-template/SKILL.md)
- Cross-brand learn entry: [docs/process/learnings.md](../../process/learnings.md) (entry 2026-05-16)
- Process docs: [docs/promotion-protocol/README.md](../README.md)

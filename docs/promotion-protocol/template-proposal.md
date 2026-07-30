# Promotion Proposal — template

> **Cómo usar:** copiar este file a `proposals/{YYYY-MM-DD}-{slug}.md` y rellenar frontmatter + secciones. Mantener pointer-first: enlazar `[[learning-name]]` y paths absolutos en lugar de duplicar contenido.

```yaml
---
proposal_id: {YYYY-MM-DD}-{slug}
state: proposed                # proposed | under_review | accepted | rejected | migrated
opened_date: YYYY-MM-DD
opened_by: /pm-luana
ratified_by: null              # Chris cuando ratifica APPROVED/REJECTED
ratified_date: null

# Origen
origin_learnings:
  - {brand-A}/docs/learnings/{date}-{slug}.md
  - {brand-B}/docs/learnings/{date}-{slug}.md  # si auto-detect agrupó ≥2 brands

origin_brands: [brand-a, brand-b]   # quién implementó el patrón hoy

# Target
target_package: core/luana-core-X
target_module: src/luana_core_X/{component}/  # path relativo dentro del package
target_ep: null                # EP-N si introduce nuevo extension point

# Impact assessment
semver_bump: minor             # patch | minor | major
breaking_change: false
brands_affected_consumers: []  # brands que opt-in eventualmente
brands_at_risk_regression: [brand-a, brand-b]  # brands con tests downstream que podrían romper

# Lift plan
lift_estimated_effort: "1-2 days"
lift_owner: /dev-team
arch_test_downstream_required: true   # always true (R3)
migration_notes_required: false       # true si breaking change
---
```

## 1. Patrón a promover

(1-2 párrafos describiendo qué es el patrón, qué problema resuelve, dónde nació)

**Origen story/incident:**
- Brand A: [[story-X]] (link a `{brand-A}/docs/product/stories/X/`)
- Brand B: [[story-Y]] (similar problem solved 2 weeks later)

## 2. Por qué cross-brand

(¿Por qué este patrón aplica a múltiples brands? Enumerar brands consumidoras potenciales con razón concreta)

| Brand | Aplicabilidad | Razón |
|---|---|---|
| Brand A | ya implementa | origen |
| Brand B | ya implementa | origen (similar pattern) |
| Brand C | candidato | tiene el mismo flow conceptualmente |
| Brand D | no aplica | vertical no necesita esto |

## 3. Análisis técnico

### Signature comparison

(Comparar las signatures actuales en cada brand. Mostrar qué se generaliza y qué se parametriza)

```python
# Brand A actual (en {brand-a}/backend/src/.../X.py)
class XHandler:
    def handle(self, ctx: BrandAContext) -> BrandAResult: ...

# Brand B actual (en {brand-b}/backend/src/.../X.py)
class XHandler:
    def handle(self, ctx: BrandBContext) -> BrandBResult: ...

# Propuesta core (en core/luana-core-X/src/luana_core_X/X.py)
class XHandler:
    def handle(self, ctx: CoreContext) -> CoreResult: ...
    # Brand-specific bits parametrizables via:
    # - dependency injection (BrandConfig)
    # - subclass + override
    # - extension point EP-N
```

### Risk assessment

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Brand C consume eventualmente y descubre límite del contract | Media | Documentar contract pública en `docs/core-modules/{package}.md` antes lift |
| Bump minor + brand existente no opt-in → ningún cambio | Baja | Default opt-in protege |
| Breaking change descubierto post-merge | Alta | R3 downstream regression mandatory |

## 4. Lift plan

### Pre-lift checklist

- [ ] Generalización del interface (sin refs hardcoded brand)
- [ ] Tests unitarios en `core/luana-core-X/tests/`
- [ ] Documentación contract en `docs/core-modules/{package}.md`
- [ ] CHANGELOG entry preparado

### Lift execution

1. Crear feature branch (per workspace git workflow)
2. Mover código brand → core con `git mv`
3. Generalizar interface
4. Bump semver minor en `core/luana-core-X/pyproject.toml`
5. Update `core/luana-core-X/CHANGELOG.md` con migration notes
6. Update `docs/core-modules/{package}.md` con promotion history entry
7. R3 arch test downstream — corre tests todos brands consumidores
8. Rollback path: revert lift, brand-X retiene patrón local

### Post-lift

- Brand A (origen): refactor para consumir `luana-core-X` package
- Brand B (origen): idem
- Otras brands: opt-in cuando decidan vía `{brand}/config/brand.yaml`

## 5. Decisión

**Recomendación `/pm-luana`:** APPROVED | REJECTED

**Razón:**

(...)

**Ratificación Chris:** _(pending hasta que pase a state=accepted o rejected)_

## 6. Bitácora

- YYYY-MM-DD: opened by /pm-luana (auto-detect via scan-promotables o manual)
- YYYY-MM-DD: state proposed → under_review
- YYYY-MM-DD: state → accepted/rejected
- YYYY-MM-DD: lift completed (si accepted) → state migrated

## 7. Cross-references

- Origin learnings: ver `origin_learnings` en frontmatter
- Target package contract: `docs/core-modules/{package}.md`
- Related EPs: ver `target_ep` en frontmatter (si aplica)
- Process docs: `docs/promotion-protocol/README.md`

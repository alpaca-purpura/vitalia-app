---
proposal_id: 2026-05-20-lift-tailwind-v4-postcss-scaffold
state: proposed
opened_date: 2026-05-20
opened_by: /pm-luana
ratified_by: null
ratified_date: null

# Origen
origin_learnings:
  - comunify/docs/learnings/2026-05-18-tailwind-v4-postcss-wiring-gap.md   # promotable=yes physical file

origin_brands: [comunify]

# Target
target_package: .claude/skills/_pm-brand-template/
target_module: scaffold FE bootstrap (postcss.config.mjs + package.json devDeps)
target_ep: null

# Impact assessment
semver_bump: n/a   # scaffold
breaking_change: false
brands_affected_consumers: [vitalia, lupulo, saasora, inmoflow, retailly, fixia, guestly, fitflow]
brands_at_risk_regression: [comunify]

# Lift plan
lift_estimated_effort: "1-2 horas"
lift_owner: /dev-team
arch_test_downstream_required: false
migration_notes_required: false

# Parent outcome
parent_outcome: docs/product/outcomes/bootstrap-brand-template-hardening.md
---

## 1. Patrón a promover

**Tailwind v4 PostCSS wiring** = scaffold mandatory para que Tailwind v4 emita utility classes en el CSS bundle. Sin esto, `@theme { --color-X }` declara las variables pero NO genera `.bg-X` / `.text-X` / etc. utilities — el CSS bundle se sirve sin classes funcionales y todos los `className="bg-X"` quedan como referencias dead.

### Componentes del scaffold (3 piezas obligatorias)

1. `{brand}/frontend/postcss.config.mjs` declarando `@tailwindcss/postcss` como único plugin
2. `{brand}/frontend/package.json` con `@tailwindcss/postcss ^4.1.0` en devDependencies
3. Documentation en `_pm-brand-template/SKILL.md` warning explícito

**Origen story:**
- Comunify: `comunify-design-system-tailwind-v4-tokens` v0.2.1 (mergeada 2026-05-20)
- Bug origen: cement v0.2.0 (Tailwind v4.1.0 + `@theme` block) shippeó "successfully" pero CSS bundle servía 467 líneas (solo vars, sin utilities)
- 2 días silent ship sin detectar bug visual
- Fix: agregar postcss.config.mjs + @tailwindcss/postcss devDep → bundle pasa a 1673 líneas con utilities

## 2. Por qué cross-brand

Todas las brands FE usan Tailwind v4 (post 2026 Tailwind v3 → v4 migration). Sin postcss config, todas tienen el mismo bug latente.

| Brand | Aplicabilidad | Razón |
|---|---|---|
| Comunify | ya implementa | origen — tailwind-v4-tokens v0.2.1 |
| Vitalia | **gap latente CONFIRMADO** | verified: NO `postcss.config.*` ni `@tailwindcss/postcss` devDep |
| Nicolify | ya implementa | nicolify es el "brand referencia" (verificado tiene setup completo) |
| Lupulo | gap preventivo probable | placeholder, mejor heredar correcto desde día 1 |
| 6 brands pendientes | aplicables al bootstrap | heredan template scaffold |

## 3. Análisis técnico

### Signature comparison

```
# Comunify (post-fix v0.2.1)
comunify/frontend/postcss.config.mjs                # EXISTS, declara @tailwindcss/postcss
comunify/frontend/package.json::devDependencies     # @tailwindcss/postcss ^4.1.0

# Vitalia (gap latente)
vitalia/frontend/postcss.config.{mjs,js,cjs}        # NO EXISTS
vitalia/frontend/package.json                       # NO @tailwindcss/postcss devDep

# Nicolify (referencia OK)
nicolify/frontend/postcss.config.mjs                # EXISTS
nicolify/frontend/package.json::devDependencies     # @tailwindcss/postcss instalado
```

### Risk assessment

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Vitalia sweep introduce regressions visuales | Media | Vitalia probablemente sirve CSS sin utilities también — fix solo activa lo que ya debería estar. Smoke test post-fix |
| Brand existente downgrade Tailwind v4 → v3 | Baja | Proposal asume v4 baseline; brands v3 no aplican |
| Conflict con setup PostCSS existente | Muy baja | Scaffold inspecciona si ya existe + integra, no sobreescribe |

## 4. Lift plan

### Pre-lift checklist

- [x] Learning physical file existe (`comunify/docs/learnings/2026-05-18-tailwind-v4-postcss-wiring-gap.md`)
- [ ] Verificar nicolify setup como reference impl
- [ ] Document scaffold en `_pm-brand-template/SKILL.md` § FE PostCSS bootstrap

### Lift execution

1. Actualizar `.claude/skills/_pm-brand-template/SKILL.md`:
   - Agregar § "FE PostCSS wiring (Tailwind v4 mandatory)"
   - Include verbatim `postcss.config.mjs` content
   - Include `@tailwindcss/postcss ^4.1.0` devDep line
   - Warning explícito: "Sin esto, utility classes NO emiten — CSS bundle queda con solo vars"
2. NO toca código brand directamente (sweep separada)

### Post-lift

- Comunify (origen): ya consume
- Vitalia: Story S1 sweep aplica `postcss.config.mjs` + agrega devDep
- Lupulo: idem
- Brands futuras: heredan automatic via template

## 5. Decisión

**Recomendación `/pm-luana`:** **APPROVED**

**Razón:**
- DRY threshold: 2 brands ya consumen (comunify + nicolify) — válido
- Gap latente CONFIRMADO en vitalia (verified empíricamente)
- Riesgo de lift es MUY BAJO: scaffold doc + verificación 2 archivos brand
- ROI alto: 6 brands futuras evitan 2 días silent ship bug

**Ratificación Chris:** _(pending)_

## 6. Bitácora

- 2026-05-20: opened by /pm-luana. state=proposed.

## 7. Cross-references

- Origin learning: `comunify/docs/learnings/2026-05-18-tailwind-v4-postcss-wiring-gap.md`
- Capability fix: `comunify/docs/product/capabilities/frontend_design_system/tailwind-v4-tokens.yaml`
- Parent outcome: `docs/product/outcomes/bootstrap-brand-template-hardening.md`
- Sister proposals: `2026-05-20-lift-camino-b-design-system.md`, `2026-05-20-lift-playwright-runner-scaffold.md`
- Reference impl: `nicolify/frontend/postcss.config.mjs` + `nicolify/frontend/package.json`

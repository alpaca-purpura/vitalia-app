---
proposal_id: 2026-05-20-lift-camino-b-design-system
state: proposed
opened_date: 2026-05-20
opened_by: /pm-luana
ratified_by: null
ratified_date: null

# Origen
origin_learnings:
  - comunify/docs/learnings/(pending-write)-camino-b-design-system-a11y.md   # /pm-comunify escribe physical file próxima sesión
  - comunify/docs/archive/2026/stories/comunify-design-system-a11y-contrast-cement/01-spec.md   # spec ratificada como referencia inmediata
  - comunify/docs/product/capabilities/frontend_design_system/a11y-contrast-cement.yaml   # capability v0.3.0

origin_brands: [comunify]

# Target
target_package: .claude/skills/_pm-brand-template/
target_module: scaffold design-system section (FE bootstrap files)
target_ep: null    # NO introduce extension point — es scaffold/recipe documentation

# Impact assessment
semver_bump: n/a   # scaffold (no package versionado)
breaking_change: false
brands_affected_consumers: [vitalia, lupulo, saasora, inmoflow, retailly, fixia, guestly, fitflow]
brands_at_risk_regression: [comunify]   # solo origen, ya consume

# Lift plan
lift_estimated_effort: "2-3 horas"
lift_owner: /dev-team (después de Chris APPROVED)
arch_test_downstream_required: false   # scaffold, no código compilado
migration_notes_required: false

# Parent outcome
parent_outcome: docs/product/outcomes/bootstrap-brand-template-hardening.md
---

## 1. Patrón a promover

**Camino B universal pattern** = recipe canónico para botones outline + badges + alerts + error labels con accesibilidad WCAG AA garantizada. Resuelve el problema combinatorio de pares foreground/background sin tocar los HSL de la paleta principal del brandbook.

```tsx
// Recipe verbatim (Camino B — outline pattern)
className="bg-{brand}-{X}/10 border border-{brand}-{X} text-{brand}-{X}-text hover:bg-{brand}-{X}/20"

// Donde {X} ∈ {warning, stable, accent, critical, blue}
// Y {brand}-{X}-text es el token foreground oscurecido (HSL lightness ~28-52%)
```

**Origen story:**
- Comunify: `comunify-design-system-a11y-contrast-cement` v0.3.0 (mergeada 2026-05-20)
- Bug origen: cement v0.2.0 shippeó con WARN auditor (`text-white` sobre `bg-warning` 1.80:1 fail WCAG AA)
- Audit expandido reveló 10 pares failing AA (6 críticos + 4 marginales)
- Solución: 5 tokens nuevos `*-text` + Camino B universal en botones moderation/dunning + arch fitness híbrido

## 2. Por qué cross-brand

Todas las brands con design system tokens semánticos (warning/stable/accent/critical/blue) sufren combinatorial WCAG AA failures si no cementan pares canónicos foreground/background.

| Brand | Aplicabilidad | Razón |
|---|---|---|
| Comunify | ya implementa | origen — a11y-contrast-cement v0.3.0 |
| Vitalia | candidato — gap latente | tiene design tokens similares, no audit a11y ejecutado |
| Lupulo | candidato — gap preventivo | placeholder, mejor heredar pattern desde día 1 |
| Saasora, Inmoflow, Retailly, Fixia, Guestly, FitFlow | aplicables al bootstrap | brands futuras heredan template scaffold |
| Nicolify | NO aplica directamente | usa paleta distinta (no semánticos compartidos comunify-style); puede beneficiarse opcional |

## 3. Análisis técnico

### Signature comparison

Comunify cementó el pattern + tokens. Vitalia/lupulo NO tienen ni tokens `-text` ni recipe.

```css
/* comunify/frontend/src/app/globals.css (cement v0.3.0 — origen) */
@theme {
  --color-comunify-warning-text: hsl(45 100% 28%);
  --color-comunify-stable-text: hsl(152 80% 28%);
  --color-comunify-accent-text: hsl(355 100% 45%);
  --color-comunify-critical-text: hsl(0 84% 49%);
  --color-comunify-blue-text: hsl(217 95% 52%);
}

/* Propuesta scaffold template — {brand}/frontend/src/app/globals.css */
@theme {
  /* Brand puede definir HSL principales custom + sus -text variants */
  --color-{brand}-warning: hsl(...);
  --color-{brand}-warning-text: hsl(...);  /* lightness 28-32% típico */
  /* ... (resto semánticos) */
}
```

```tsx
// scaffold _pm-brand-template/ pseudo-content recipe verbatim:
// "Para botones outline o badges WCAG AA, usar:
//  bg-{brand}-{X}/10 border border-{brand}-{X} text-{brand}-{X}-text hover:bg-{brand}-{X}/20"
```

### Risk assessment

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Brand existe sin tokens `-text` y no quiere migrar | Baja | Recipe es opcional; brand decide adoptar |
| Brand usa paleta distinta (Nicolify) | Baja | Recipe es generic — solo cambia prefix tokens |
| Sweep vitalia introduce regressions visuales | Media | Sweep ejecuta separate story (S1) con audit a11y previo |
| Brands futuras no implementan correctamente | Baja | Scaffold incluye check arch fitness anti-low-contrast (proposal #2 separada) |

## 4. Lift plan

### Pre-lift checklist

- [ ] /pm-comunify escribe `comunify/docs/learnings/(date)-camino-b-design-system-a11y.md` physical file con frontmatter promotable=yes (próxima sesión)
- [ ] Document recipe verbatim en `_pm-brand-template/SKILL.md` § FE design system bootstrap
- [ ] Incluir tabla "tokens `-text` requeridos cuando brand declara semánticos"
- [ ] Citar capability `comunify/docs/product/capabilities/frontend_design_system/a11y-contrast-cement.yaml` como reference impl

### Lift execution

1. Actualizar `.claude/skills/_pm-brand-template/SKILL.md`:
   - Agregar § "FE design system bootstrap" con Camino B recipe verbatim
   - Documentar contract `*-text` tokens (HSL lightness ~28-52% sobre bg light)
   - Incluir ejemplos `bg-{brand}-warning/10 border ... text-{brand}-warning-text`
2. NO toca código brand directamente (las brands existentes se actualizan via Story S1 sweep separadas)
3. Documentar promotion history entry en `_pm-brand-template/SKILL.md` § Cementado en 2026-05-20

### Post-lift

- Comunify (origen): ya consume — no acción
- Vitalia + lupulo: Story S1 sweep separada (después de proposals migrated)
- Saasora/inmoflow/retailly/fixia/guestly/fitflow: heredan via template automatic al bootstrap

## 5. Decisión

**Recomendación `/pm-luana`:** **APPROVED**

**Razón:**
- DRY threshold: ≥1 brand viable + 7 brands futuras consumidoras potenciales = válido
- Pattern es genuinamente cross-brand (cualquier design system con semánticos sufre el mismo bug latente)
- Riesgo de lift es BAJO: solo modifica scaffold doc (no código brand existente)
- ROI alto: 6 brands futuras evitan reinventar a11y compliance
- Validation de gap real en vitalia (verified: NO audit a11y ejecutado, gap latente probable)

**Ratificación Chris:** _(pending — Chris autorización "resolvamoslo todo de una vez" sugiere intent APPROVED, pero esperando explicit verdict)_

## 6. Bitácora

- 2026-05-20: opened by /pm-luana (autonomous Chris autorización). state=proposed.

## 7. Cross-references

- Origin learnings + capability:
  - `comunify/docs/learnings/INDEX-promotables.md` (queue index)
  - `comunify/docs/product/capabilities/frontend_design_system/a11y-contrast-cement.yaml` (capability v0.3.0)
  - `comunify/docs/archive/2026/stories/comunify-design-system-a11y-contrast-cement/01-spec.md` (spec)
- Parent outcome: `docs/product/outcomes/bootstrap-brand-template-hardening.md`
- Sister proposals (same outcome):
  - `2026-05-20-lift-tailwind-v4-postcss-scaffold.md`
  - `2026-05-20-lift-playwright-runner-scaffold.md`
- Target scaffold: `.claude/skills/_pm-brand-template/SKILL.md`
- Process docs: `docs/promotion-protocol/README.md`

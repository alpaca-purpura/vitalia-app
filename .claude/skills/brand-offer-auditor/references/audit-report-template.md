# Audit Report Template — Brand & Offer Studio

> Plantilla de salida del skill `brand-offer-auditor` (Step 7). Brand-agnostic: reemplazá `{brand}` por la marca detectada (`basename $(git rev-parse --show-toplevel)` o el arg `<brand>`). Guardar el resultado en `{brand}/docs/audits/{scope}-audit-{YYYY-MM-DD}.md` (o `docs/audits/` si es cross-brand/engine). Una fila por finding; severidad ordena la ejecución.

---

## Encabezado

```yaml
audit_scope: brand-studio | offer-studio | offer-type:{PRESET_KEY}   # qué se auditó
brand: {brand}
date: {YYYY-MM-DD}
auditor: brand-offer-auditor (skill)
sources_reviewed:                                                    # paths reales inspeccionados
  - core/luana-core-brand-studio/src/luana_core_brand_studio/domain/*.py
  - core/luana-core-offer-studio/src/luana_core_offer_studio/domain/*_catalog.py
  - {brand}/backend/src/modules/{brand}/{brand,offer}/...
  - {brand}/frontend/src/features/{brand-studio,offer-studio}/...
frameworks_applied: [Aaker, Keller, Gad, Neumeier, StoryBrand, Jung, ...]   # § Framework Knowledge
```

## Resumen ejecutivo

2-4 bullets: ¿el sistema captura la marca/oferta a profundidad suficiente para que el sales_agent cierre? Mayor brecha estructural. Conteo de findings por severidad.

| Severidad | Count |
|---|---|
| 🔴 CRITICAL | N |
| 🟠 HIGH | N |
| 🟡 MEDIUM | N |

## Findings (severity-ordered)

Cada finding usa este bloque. Severidad: **CRITICAL** = el sales_agent queda ciego / no puede vender; **HIGH** = degrada calidad o duplica; **MEDIUM** = mejora de profundidad.

```
### [SEV] {título corto del finding}
- **Lente:** Gap | Duplicate | Misalignment | Prompt Failure  (§ Core Audit Lenses)
- **Framework:** {framework que lo expone} (§ Framework Knowledge / overlap map)
- **Dónde:** {path:campo exacto — domain model / extraction prompt / UI form}
- **Evidencia:** {qué se observó — cita el campo/prompt/label real}
- **Por qué importa (SDR test):** {"si el SDR solo tuviera este campo, ¿podría cerrar?"}
- **Recomendación (ejecutable):** EXTEND {campo existente} | FIX {prompt/label} | UNIFY {campos duplicados} — NUNCA "add new field" si uno existente ya cubre el concepto (Key Principle: one concept, one field).
- **Owner sugerido:** /pm-luana (engine: core/luana-core-{brand,offer}-studio) | /pm-{brand} (brand extension EP-N)
```

## Cobertura por framework

| Framework | Cubierto | Gaps | Nota |
|---|---|---|---|
| {framework} | ✅/⚠️/❌ | {campos faltantes} | {profundidad} |

## Checklist ejecutable (para un agente)

Orden CRITICAL → HIGH → MEDIUM. Cada ítem mapea a un finding de arriba y debe ser accionable por `/architect` + `builder-*` o por una story de refinamiento.

- [ ] 🔴 {acción} — `{path}` — {finding ref}
- [ ] 🟠 {acción} — `{path}` — {finding ref}
- [ ] 🟡 {acción} — `{path}` — {finding ref}

## Anti-recomendaciones (qué NO hacer)

- No agregar campos redundantes (verificar overlap map § 11 antes de proponer "new field").
- No auditar un offer-type simple contra el framework completo (match framework depth to offer complexity).
- No tocar `core/luana-core-*` directo — cambios de engine van por `/pm-luana` promotion gate.

---

> **Recordatorio de principios** (§ Key Principles del skill): one concept/one field · plain language for users + methodology for machines · the SDR is the final consumer · improve existing before adding · depth over breadth · extraction prompts son el test real · the ladder must be connected.

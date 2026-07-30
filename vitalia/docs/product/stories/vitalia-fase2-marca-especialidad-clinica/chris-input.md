---
story_id: vitalia-fase2-marca-especialidad-clinica
created_at: 2026-06-07T01:20:00.000Z
last_modified: 2026-06-07T01:20:00.000Z
notes_count: 0
refs_count: 1
conversation_count: 1
---

# chris-input.md · vitalia-fase2-marca-especialidad-clinica

> **Qué es este archivo:** acá Chris escribe notas + referencias + Claude responde con verdicts. Es la cocina de la story (la conversación) — separada del spec/design/arch (los outputs ratificados).
>
> **3 secciones secuenciales:**
> - 💭 Notas — Chris escribe en lenguaje natural antes/durante refinement
> - 📎 Referencias — links, imágenes, story-refs, learning-refs, doc-refs
> - 💬 Conversación — turn-by-turn cronológico Chris ↔ Claude con verdicts
>
> Doc canónico: `docs/process/chris-input-protocol.md`.

## 💭 Notas

### 2026-06-07 01:20
Sin notas todavía · Chris escribe aquí cuando arranque el refinamiento con `/pm-vitalia`.

## 📎 Referencias

- **📖 story-ref** · `vitalia-fase2-lisa-servicios`
  > Origen: esta historia se capturó durante el round 3 de refinamiento de servicios (la especialidad de la clínica que servicios consume).
- **📖 story-ref** · `vitalia-fase2-onboarding-clinica` (surface de creación) · `vitalia-fase2-lisa-marca` (done · surface de edición)

## 💬 Conversación

> Append-only · turn-by-turn cronológico.
> Verdict labels: ✓ APLICADO · ⚠️ DUDA · ❌ REFUTADO · 💡 PROPONE.

### 2026-06-07 01:20 · 🤖 claude · `/po-ux` · ✓ APLICADO
**Story capturada** desde el refinamiento de `vitalia-fase2-lisa-servicios`. Decisión Chris 2026-06-07: la **especialidad de la clínica** (qué tipo de centro es) **se crea en el Onboarding** (set once) y **se edita en Lisa → Marca** — NO en Servicios (que la consume read-only).

Esta historia = **ampliar la marca** con ese atributo (a nivel tenant/brand) + el paso en onboarding + el consumo por servicios. Escribí `checkpoint.md` (state `idea`) con scope tentativo + AC + relaciones.

**Pendiente `/pm-vitalia`:** formalizar release/priority + cap lineage (`extend lisa.marca`) + **decidir si el paso de creación se implementa dentro de `vitalia-fase2-onboarding-clinica` o como parte de esta story** (evitar duplicar onboarding). Después `/po-ux` refina (mockup del campo en Lisa → Marca + el paso en onboarding).

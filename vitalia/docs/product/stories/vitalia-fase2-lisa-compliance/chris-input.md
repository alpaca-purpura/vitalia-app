---
story_id: vitalia-fase2-lisa-compliance
created_at: 2026-05-27T18:25:23-05:00
last_modified: 2026-05-27T18:25:23-05:00
notes_count: 0
refs_count: 0
conversation_count: 1
---

# chris-input.md · vitalia-fase2-lisa-compliance

> **Qué es este archivo:** acá Chris escribe notas + referencias + Claude responde con verdicts. Es la cocina de la story (la conversación) — separada del spec/design/arch (los outputs ratificados).
>
> **3 secciones secuenciales** (mantener el orden + emojis para que parser + cockpit funcionen):
> - 💭 Notas — Chris escribe en lenguaje natural antes/durante refinement
> - 📎 Referencias — links, imágenes, story-refs, learning-refs, doc-refs
> - 💬 Conversación — turn-by-turn cronológico Chris ↔ Claude con verdicts
>
> Doc canónico: `docs/process/chris-input-protocol.md`.

## 💭 Notas

> Chris: escribe acá tus notas en lenguaje natural. Cualquier cosa que te ayude a pensar la story.
>
> Cada entry abre con `### YYYY-MM-DD HH:MM` (timestamp).

### 2026-05-27 18:25
Sin notas todavía · Chris escribe aquí.

## 📎 Referencias

> Chris: pega links, sube imágenes (drag-drop o botón adjuntar), cita texto de buyer personas, referencia otras stories (`F2-S1`) o learnings (`2026-MM-DD-slug`).
>
> Tipos válidos: 🔗 link · 🖼 img · 💬 text · 📖 story-ref · 📚 learning-ref · 📄 doc.
>
> Formato: `- **(emoji) (tipo)** · (valor)` + opcional `  > (comentario)` en siguiente línea.

(sin referencias todavía)

## 💬 Conversación

> Append-only · turn-by-turn cronológico.
> Chris responde a Claude editando + agregando un entry nuevo.
> Claude appendea verdict al cierre de cada turn de su skill.
>
> Verdict labels: ✓ APLICADO · ⚠️ DUDA · ❌ REFUTADO · 💡 PROPONE.

### 2026-05-27 18:25 · 🤖 claude · `scripts/migrate_to_release_schema.py` · ✓ APLICADO
Story migrada al schema v2: `release=F2`, `cap_target=lisa.compliance`, `cap_change_type=new`. Legacy `outcome` + `phase` preservados durante deprecation gradual.

Cuando estés listo para refinar, llena 💭 Notas + 📎 Referencias arriba e invoca `/po-ux vitalia vitalia-fase2-lisa-compliance` (o `/po` si es service story, o `/ux-agentico` si es agentic).

### 2026-06-07 02:55 · 🤖 claude · `/pm-vitalia` · ⚠️ DUDA
Revisé LISA (marca done · doctores developing · servicios refining), el impacto en Adrián (canal-inbound refined consume el firewall PHI; outbound NO gatea opt-out aún), el sitemap deseado (`SYSTEM-MAP.yaml` v2) y la visión Vitalia. **Hallazgo:** la story fue scopeada bajo la visión vieja como una **consola pesada de compliance** (semáforo 7 checks + editor de retención + reportes técnicos) que **mezcla 3 concerns que el propio SYSTEM-MAP ya separó** — y hay inconsistencia de 3 vías (cap YAML `seguridad-cumplimiento`/user_visible:false ↔ story Lisa user-facing F2 ↔ mapa `lisa.compliance`=vista de confianza F3).

**Recomendación (detalle completo: `00-pm-recommendation.md`):** reencuadrar a una **vista de "Confianza y cumplimiento" del dueño** (slim, read-mostly, F3) — la capa que hace seguro delegar en agentes autónomos — y **sacar** a otras stories: editor de retención + checks técnicos → Configuración/Avanzado; cron de retención (hoy stub) → infra; **gate consentimiento/opt-out en outbound de Adrián** → dominio Adrián (HARD compliance). Cerrar `vitalia-compliance-audit-rbac-gap` (ya fixeado por hotfix `18e10822`).

**Necesito que elijas dirección (A/B/C)** antes de cerrar `refined` + invocar `/po-ux`. Mi recomendación = **A**.

### 2026-06-07 03:10 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
Chris eligió **A**. Reencuadre aplicado en 4 stories:
- `vitalia-fase2-lisa-compliance/checkpoint.md` → reescrito a vista "Confianza y cumplimiento" (slim, read-mostly), `release F2→F3`, `cap_target lisa.compliance` que `reads_cap seguridad-cumplimiento.compliance`, scope IN/OUT + spin-outs + AC draft. Sigue `state: refining`.
- `vitalia-fase2-config-avanzado` → el **editor de política de retención** se mueve acá (antes "edit en compliance").
- `vitalia-fase2-adrian-outbound` → nota: su gate opt-out/consent (§7) es el guardrail HARD de compliance (no se spawnea story aparte); la vista de confianza lee sus bloqueos.
- `vitalia-compliance-audit-rbac-gap` → **dropped** (ya fixeado por hotfix `18e10822`).

**Sequencing (observación PM):** la reframe BAJÓ la urgencia (F2→F3 + depende de que maduren datos de Adrián/consent). Lo urgente sigue siendo F2: `adrian-embudo` (developed · live-verify pendiente) + `lisa-doctores` (developing). NO encadeno `/po-ux` automático — la consulta era consultiva y la story es F3. Cuando quieras refinarla a fondo: `/po-ux vitalia vitalia-fase2-lisa-compliance` (incluirá gate mockup-per-component ADR-vitalia-003).

### 2026-06-07T03:35 · 🤖 claude · `/po-ux` · ⚠️ DUDA
Chris pidió frenar y revisar competidores (cero.ai, botclinico.cl, rendu.app, dentalink contact-center, doctocliq) vs visión, sospechando over-scope. **Confirmado — tenía razón.** Hallazgo: los 5 competidores lideran con el **agente IA de captación/agenda 24/7** (= H1 de la visión, #1 ROI) y **ninguno vende compliance como feature** (máximo: disclaimer legal + consentimiento informado como formulario — que Vitalia ya tiene shipped). La visión ubica compliance en H4/Q4 (mid-market Fernando), no en el MVP Q1 (Camila).

Reconozco que con (c)+(c) (consent-mgmt full + DSAR + access-log + alertas) armé una consola Q4 mientras el core que gana está a medias (canal-inbound/embudo/outbound/propuestas/Mateo). **Recomiendo cortar fuerte** y reorientar al core. Pregunté a Chris cuánto cortar (A parkear / B MVP mínimo de confianza / C seguir). Mi recomendación = **A** (parkear, focus core) con B como target liviano para más adelante.

### 2026-06-07T03:40 · 🤖 claude · `/po-ux` · ✓ APLICADO
Chris eligió **A**. `state: refining → parked` (`parked_reason` cementado: evidencia competidores + visión Q4 + core no construido + enforcement ya live en infra). El reframe A + el scope explorado quedan documentados en `00-pm-recommendation.md` + checkpoint para retomar sin re-investigar. `lisa/compliance` queda con su placeholder actual. Story diferida `vitalia-lisa-compliance-attestation` (idea) sigue dormida bajo la madre. **Refinamiento cerrado.** Próximo: reorientar al core agéntico (handoff a `/pm-vitalia` para elegir la siguiente story que gana).

### 2026-06-07T03:50 · 🤖 claude · `/po-ux` · ✓ APLICADO
Chris pidió dejar todo lo aprendido en un lugar reviewable para retomar el refinamiento en una conversación nueva. Consolidado en 3 lugares:
1. **`RESUME-refinement.md`** (★ punto de entrada) — cómo retomar en 3 pasos + decisiones Batch 1 tomadas + preguntas Batch 2 abiertas + evidencia competidores (tabla) + data sources shipped + scope IN/OUT/spun-out + precondiciones de unpark.
2. **`vitalia/docs/learnings/2026-06-07-compliance-not-marquee-scope-discipline.md`** — learning de marca (promotable: candidate).
3. **MEMORY pointer** (`compliance-overscope-parked-2026-06-07.md` + línea en MEMORY.md) — para que una sesión nueva lo descubra al cargar el índice.
El checkpoint ahora abre apuntando al RESUME. Nada se pierde; al volver no se re-investiga.

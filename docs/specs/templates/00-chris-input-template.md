---
story_id: STORY_ID
created_at: YYYY-MM-DDTHH:MM:SS-05:00
last_modified: YYYY-MM-DDTHH:MM:SS-05:00
notes_count: 0
refs_count: 0
conversation_count: 1
---

# chris-input.md · STORY_ID

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

### YYYY-MM-DD HH:MM
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

### YYYY-MM-DD HH:MM · 🤖 claude · `/pm-{sistema}` · ✓ APLICADO
Story creada en state=idea con cap_target=`CAP_TARGET` y cap_change_type=`CAP_CHANGE_TYPE`.

Cuando estés listo para refinar, llena 💭 Notas + 📎 Referencias arriba e invoca `/po-ux <sistema> <story-id>` (o `/po` si es service story, o `/ux-agentico` si es agentic).

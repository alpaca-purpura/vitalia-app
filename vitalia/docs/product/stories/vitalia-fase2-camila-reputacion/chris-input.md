---
story_id: vitalia-fase2-camila-reputacion
created_at: 2026-05-27T18:25:23-05:00
last_modified: 2026-06-18T19:45:00-05:00
notes_count: 0
refs_count: 0
conversation_count: 2
---

# chris-input.md · vitalia-fase2-camila-reputacion

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
Story migrada al schema v2: `release=F2`, `cap_target=camila.reputacion`, `cap_change_type=new`. Legacy `outcome` + `phase` preservados durante deprecation gradual.

Cuando estés listo para refinar, llena 💭 Notas + 📎 Referencias arriba e invoca `/po-ux vitalia vitalia-fase2-camila-reputacion` (o `/po` si es service story, o `/ux-agentico` si es agentic).

### 2026-06-18 · 🤖 claude · /pm-vitalia diagnóstico HB-82 · 💡 PROPONE
Inyecté un `§ Contexto heredado` corto al `checkpoint.md`: el único cruce de esta story con el diagnóstico re-engagement es **NPS**. El NPS ya tiene BE vivo en `fidelizacion` (`nps/summary` + `nps/submit`) → NO reconstruirlo acá si reputación lo necesita (consumir, anti-dup). Las reseñas externas (Google/IG/TikTok = el objetivo real) siguen sin BE → NEW. Las 5 mutations re-engagement NO viven acá — van a `vitalia-fase2-camila-reactivar`.

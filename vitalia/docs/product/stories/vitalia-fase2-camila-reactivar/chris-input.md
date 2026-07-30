---
story_id: vitalia-fase2-camila-reactivar
created_at: 2026-05-27T18:25:23-05:00
last_modified: 2026-06-18T19:45:00-05:00
notes_count: 0
refs_count: 2
conversation_count: 2
---

# chris-input.md · vitalia-fase2-camila-reactivar

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

- **📖 doc** · `docs/process/harness-backlog.md` HB-82 — SSoT del diagnóstico LIVE (re-engagement + los 9 gaps restantes). La story contenedor que lo originó fue borrada; el detalle re-engagement (contrato BE real + 2 decisiones /architect + qué FE es salvable) vive en el `§ Notas a considerar` de ESTE checkpoint.
- **🤖 code** · `vitalia/backend/src/modules/vitalia/fidelizacion/` (motor BE vivo a CONSUMIR) + `vitalia/frontend/src/features/fidelizacion/` (FE huérfano — cosechar modales/cards, reemplazar hooks) + `features/mateo/api/notify.ts` (patrón canónico headers PHI).

## 💬 Conversación

> Append-only · turn-by-turn cronológico.
> Chris responde a Claude editando + agregando un entry nuevo.
> Claude appendea verdict al cierre de cada turn de su skill.
>
> Verdict labels: ✓ APLICADO · ⚠️ DUDA · ❌ REFUTADO · 💡 PROPONE.

### 2026-05-27 18:25 · 🤖 claude · `scripts/migrate_to_release_schema.py` · ✓ APLICADO
Story migrada al schema v2: `release=F2`, `cap_target=camila.reactivar`, `cap_change_type=new`. Legacy `outcome` + `phase` preservados durante deprecation gradual.

Cuando estés listo para refinar, llena 💭 Notas + 📎 Referencias arriba e invoca `/po-ux vitalia vitalia-fase2-camila-reactivar` (o `/po` si es service story, o `/ux-agentico` si es agentic).

### 2026-06-18 · 🤖 claude · /pm-vitalia diagnóstico HB-82 · 💡 PROPONE
Inyecté `§ Notas a considerar` al `checkpoint.md` — **contexto, no mandato**: el refinamiento decide qué tomar. Resumen: el motor BE de re-engagement ya existe, vivo y cableado en `modules/vitalia/fidelizacion/` (10 rutas, openapi-verificado), así que vale evaluar consumirlo en vez de crear `reengagement` (posible mirror); el FE de las 5 mutations existe pero es scaffold huérfano (contrato imaginado, nunca cableado) — modales/cards podrían cosecharse, los 10 hooks son candidatos a reemplazar. El checkpoint trae el contrato BE real + las 2 sugerencias /architect (call_result enum propio · BE resuelve PHI por patient_id). **Regla anti-código-muerto añadida:** lo que el rediseño NO reuse, BORRARLO en esta story (features/fidelizacion + cap deprecada `patients.nps-tracking` + entradas de KNOWN_CONTRACT_GAPS). Esta es THE home de re-engagement; la story contenedor que originó esto fue BORRADA (Chris, 2026-06-18) — el detalle quedó acá, el resto de HB-82 en el backlog.

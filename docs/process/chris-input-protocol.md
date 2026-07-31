# chris-input.md Protocol — Conversación asíncrona Chris↔Claude (v2 cement 2026-05-28)

<!-- voseo-allowed: doc contains verbatim example conversations showing Chris's voseo notes + Claude tuteo responses · escape per spanish-text.md R25 -->

**Cement-date:** 2026-05-27. **v2 (nace con la idea):** 2026-05-28.
**Origen:** sesión 2026-05-27 — Phase 1.1.C (plan local). **v2:** sesión 2026-05-28 — Chris ratificó que el archivo nazca con la idea (buzón de inputs desde `state: idea`, no desde refining).

> **chris-input.md** es el artifact oficial donde Chris escribe notas + referencias + Claude responde con verdicts. **Nace junto con la idea** (`state: idea`) y vive 1 archivo per story a lo largo de toda su vida. Es el buzón donde Chris vuelca lo que desea / cree que necesita; Claude lo puede rebatir (verdict ❌ REFUTADO) durante el ciclo de vida y se refina en conjunto. Skills appendean al cierre de cada turno. Habilita loop conversacional asíncrono entre cockpit + Claude Code.

---

## Sección 1 · Por qué existe

**Problema:** desde que una idea nace (`state: idea`) y durante todo el refinement, Chris piensa cosas en lenguaje natural (notas), aporta refs (imágenes/links/learnings), conversa con Claude que responde + decide qué aplicar. Sin un archivo dedicado **desde el día cero**, esto se pierde, se mezcla con el spec, o las ideas crudas del periodo `idea` no tienen dónde acumularse.

**Solución:** `chris-input.md` **nace con la idea** y separa la conversación de los artifacts formales (spec/design/arch). El spec/design/arch son output ratificado · chris-input es la cocina + el buzón de inputs de Chris. Lo que Chris escribe es un **input** (lo que desea / cree que necesita), NO una orden: Claude lo puede rebatir durante el ciclo de vida y se refina en conjunto.

**Modelo de uso:**
1. Chris llena 💭 Notas + 📎 Refs en cockpit (UI visual)
2. Chris invoca skill correspondiente (`/po-ux`, `/po`, `/ux-agentico`, `/architect`)
3. Skill lee chris-input.md completo + procesa → produce/actualiza spec/design/arch
4. Skill appendea sección 💬 Conversación con verdict (✓ APLICADO · ⚠️ DUDA · ❌ REFUTADO · 💡 PROPONE)
5. Chris ve respuesta en cockpit (chokidar refresca automático) → puede responder → loop

---

## Sección 2 · 3 secciones secuenciales

| Sección | Orden | Editor | Contenido |
|---|---|---|---|
| 💭 Notas | 1 | Chris | Lenguaje natural · pensamientos · contexto · preferencias |
| 📎 Referencias | 2 | Chris | Links, imágenes (refs/*.png), texto citado, story-refs, learning-refs, doc-refs |
| 💬 Conversación | 3 | Chris + Claude | Turn-by-turn cronológico · cada Claude turn cierra con verdict |

**Por qué este orden:** Chris piensa primero (notas) → aporta material (refs) → Claude procesa (conversación + decide). Aunque las 3 secciones coexisten + se actualizan a lo largo de la vida de la story, el orden visual refleja el flujo cognitivo.

---

## Sección 3 · Schema markdown estructurado

```markdown
---
story_id: vitalia-fase2-valeria-pacientes
created_at: 2026-05-27T14:30:00-05:00
last_modified: 2026-05-27T14:52:00-05:00
notes_count: 2
refs_count: 5
conversation_count: 5
---

# chris-input.md · vitalia-fase2-valeria-pacientes

## 💭 Notas

### 2026-05-27 14:30
Necesito que el estado de pago se vea PROMINENTE en el directorio porque Valeria entra a la mañana y lo primero que mira es quién no pagó.

Filtros por etiqueta (VIP, primera vez, post-tratamiento) son importantes para Valeria.

### 2026-05-27 16:00
También me gustaría poder hacer quick-action de cobrar deuda desde el directorio sin entrar a la ficha. Pensemos esto.

## 📎 Referencias

- **🔗 link** · https://intercom.com/help/customer-segments
  > me gusta cómo segmentan acá
- **🖼 img** · refs/2026-05-27-mockup-directorio.png
  > boceto que hice anoche
- **📖 story-ref** · F2-S1
  > la integración con agenda debe ser fluida
- **💬 text** · Marta (buyer persona): "no me importa el detalle médico, importa quién tiene cita esta semana"
- **📚 learning-ref** · 2026-05-18-phi-repository-base
  > reusar el masking pattern

## 💬 Conversación

### 2026-05-27 14:30 · 🧑 chris
Ver mis notas + referencias arriba.

### 2026-05-27 14:42 · 🤖 claude · `/po-ux` · ✓ APLICADO
Apliqué tus inputs a draft 01-spec.md:
- SC-08: estado de pago como pill prominente en card directorio
- SC-09: filtros segmentos VIP / primera vez / post-tratamiento
- AC-12: quick-action "marcar pagado" desde directorio
- AC-13: integración con valeria.agenda

Reusé `BasePhiRepository` per tu learning-ref.

### 2026-05-27 14:43 · 🤖 claude · `/po-ux` · ⚠️ DUDA
La regla "no detalle médico" de Marta — ¿aplica solo al directorio o también a la ficha?

Mi propuesta: solo al directorio. La ficha sí muestra info médica bajo role doctor/nurse. ¿Confirmás?

### 2026-05-27 14:50 · 🧑 chris
Confirmado: solo directorio. Ficha mantiene full reveal bajo role doctor/nurse.

### 2026-05-27 14:52 · 🤖 claude · `/po-ux` · ✓ APLICADO
Actualizado SC-08:
- PHI masking SOLO en directorio (lista)
- Ficha full reveal bajo role doctor|nurse|admin

Spec listo para ratificación. Te dejo 01-spec.md draft completo.
```

**Frontmatter mandatory fields:** story_id, created_at, last_modified. Los `*_count` se autocalculan al guardar (cockpit/skill).

**Parsing regex** (para `lib/chris-input-parser.ts`):
- Sections: `^## 💭 Notas$`, `^## 📎 Referencias$`, `^## 💬 Conversación$`
- Note entries: `^### YYYY-MM-DD HH:MM$` + texto hasta siguiente `###`
- Ref entries: `^- \*\*(emoji) (type)\*\* · (value)$` + opcional next line `  > (comment)`
- Conv entries Chris: `^### YYYY-MM-DD HH:MM · 🧑 chris$`
- Conv entries Claude: `^### YYYY-MM-DD HH:MM · 🤖 claude · \`/(skill-name)\` · (emoji) (verdict)$`

---

## Sección 4 · Verdict labels (4 valores con emoji)

| Emoji | Label | Significado |
|---|---|---|
| ✓ | APLICADO | Cambios concretos aplicados al spec/design/arch/test referenciados explícitamente |
| ⚠️ | DUDA | Skill necesita respuesta de Chris antes de seguir. State queda esperando |
| ❌ | REFUTADO | Razón por la que NO aplica algo que Chris pidió (con justificación enforceable) |
| 💡 | PROPONE | Opción nueva que Claude sugiere · Chris ratifica o descarta |

**Regla:** cada turn Claude debe cerrar con UN verdict. No se permite múltiples verdicts mezclados (si hay 2 cosas para reportar, son 2 entries consecutivas).

---

## Sección 5 · Output protocol per skill (verbatim)

Cada skill de la pipeline SDD (po-ux, po, ux-agentico, architect, auditor, pm-{brand}, dev-team) MUST appendear sección Conversación al cierre de cada turn.

**Path target:**
- Story state ∈ {idea, refining, refined, ready, developing, developed, reviewing}: `{brand}/docs/product/stories/{story_id}/chris-input.md`
- Story state = done: `{brand}/docs/archive/{year}/stories/{story_id}/chris-input.md` (read-only post-merge)

**Cuándo appendear:** al terminar cada turn de la skill (no per-edit interno). Una invocación = 1 turn = típicamente 1-3 entries (verdict + sub-verdicts si hay).

**Formato verbatim del block markdown:**
```markdown
### {ISO date} · 🤖 claude · `/{skill-name}` · {emoji} {verdict-label}
{texto · 2-30 líneas · descripción de qué hizo + qué decisiones tomó + qué necesita Chris responder}
```

**Verdict logic:**
- `applied` (✓) → cambios concretos aplicados con paths/files mencionados
- `doubt` (⚠️) → pregunta que necesita respuesta Chris
- `refuted` (❌) → "No aplico X porque {razón}"
- `proposed` (💡) → "Sugiero alternativa Y, ¿confirmás?"

---

## Sección 6 · Lifecycle

| Fase | Trigger | Acción |
|---|---|---|
| Creación | `/pm-{brand}` **crea la story** (`state: idea`) — o cockpit `extend-cap`/`from-done` | Copia template `00-chris-input-template.md` a `{brand}/docs/product/stories/{id}/chris-input.md` con frontmatter inicial + 3 secciones vacías, **junto con `checkpoint.md`**. Nace con la idea. |
| Updates | Cada skill turn + Chris escribe inputs | Appendea entry a sección Conversación + Chris edita notas/refs vía cockpit (desde `idea` en adelante) |
| Archive | `/pm-{brand}` Fase F MERGE state `reviewing → done` | `git mv` chris-input.md junto con resto de stories al archive folder |

**chris-input.md nace con TODA story creada** (incluido `state: idea`). Una idea que se descarta sin refinar igual conserva su buzón (posiblemente vacío salvo el seed de creación). Override puntual para ideas efímeras: magic comment `# chris-input-skip: razón` en el checkpoint.

---

## Sección 7 · Reference types (6 tipos)

Tabla de tipos de referencia en sección 📎 Referencias:

| Emoji | Tipo | Valor | Ejemplo |
|---|---|---|---|
| 🔗 | link | URL absoluta | `https://intercom.com/...` |
| 🖼 | img | path relativo a `refs/{filename}` | `refs/2026-05-27-mockup.png` |
| 💬 | text | string citado (1-3 líneas) | `Marta: "no me importa..."` |
| 📖 | story-ref | story_id de otra story (mismo brand) | `F2-S1` o `vitalia-fase2-valeria-agenda` |
| 📚 | learning-ref | learning slug (date-slug.md) | `2026-05-18-phi-repository-base` |
| 📄 | doc | path relativo a doc del repo | `docs/process/capability-protocol.md` |

**Upload de imgs:** endpoint `/api/refs/upload` (cockpit Phase 5) recibe blob multipart, copia a `{brand}/docs/product/stories/{id}/refs/{filename}`, appendea entry. Tamaño max 10MB. Extensiones whitelist: png, jpg, jpeg, gif, webp, svg, pdf, md, txt.

**`.gitignore` rule:** `vitalia/docs/product/stories/**/refs/*` excepto `**/refs/*.md` y `**/refs/.gitkeep`. Chris-input.md sigue tracked (cita paths), binarios no inflan el repo. Si Chris necesita compartir refs cross-machine → mover a `refs-shared/` (tracked manual, opt-in).

---

## Sección 8 · Anti-patterns prohibidos

- ❌ Skill termina turn sin appendear (silent escape) — siempre appendear, aunque sea `verdict: applied · sin cambios sustantivos`
- ❌ Verdict sin texto sustantivo (`verdict: APLICADO` solo · 1 palabra no informa)
- ❌ Path hardcoded con brand fija — debe ser `{brand}` dinámico (skill detecta de checkpoint o args)
- ❌ Múltiples verdicts en un solo entry — si hay 2 cosas, son 2 entries consecutivas
- ❌ Entry Claude sin emoji + label de verdict (parser falla)
- ❌ Chris-input.md sin las 3 secciones (parser falla)
- ❌ Entry chris en sección Notas con timestamp futuro (relojes desincronizados)
- ❌ Ref `img` apuntando a archivo que no existe en `refs/` (cockpit muestra broken image)
- ❌ Story state ∈ {idea, refining...reviewing} sin chris-input.md (pre-commit hook bloquea checkpoint — el archivo nace con la idea)
- ❌ Editar entry Claude post-hoc (chris-input es append-only conceptualmente, salvo corrección obvia de typo)

---

## Sección 9 · Validations (auditor + hooks)

**Auditor Phase D extender:**
- Verificar que `chris-input.md` existe para stories `state ∈ {refining, refined, ready, developing, developed, reviewing}`
- Verificar que el último append es de Claude (no Chris esperando respuesta)
- Si último entry es Chris pero state ≠ refining, flag como WARN ("Chris dejó msg sin respuesta de Claude")
- Verificar que `notes_count`, `refs_count`, `conversation_count` en frontmatter matchea el actual count parseado

**Pre-commit hook (Section 16):**
- Si commit toca `{brand}/docs/product/stories/{id}/checkpoint.md` con `state ∈ {idea, refining, ...reviewing}` y NO existe `chris-input.md` en mismo dir → BLOQUEAR commit
- Escape: magic comment `# chris-input-skip: razón` en checkpoint frontmatter (uso típico: idea efímera que se descarta sin refinar)
- Validación de schema markdown (3 secciones presentes) opcional via `scripts/validate_chris_input.py`

---

## Sección 10 · Referencias

- `docs/specs/templates/00-chris-input-template.md` — template oficial nuevo
- `docs/process/capability-protocol.md` — chris-input ratifica `cap_change_type`
- `docs/process/release-protocol.md` — chris-input no toca release directamente (Chris edita via cockpit)
- `.claude/rules/brand-docs-schema.md` § R4 — chris-input.md nace con la idea (mandatory desde `state: idea`)
- `tools/luana-cockpit/lib/chris-input-parser.ts` — implementación parser markdown
- `tools/luana-cockpit/app/api/chris-input/[storyId]/route.ts` — CRUD endpoint cockpit
- `.claude/skills/{po-ux,po,ux-agentico,architect,auditor,pm-vitalia,dev-team}/SKILL.md` § Output protocol — cómo cada skill appendea

---
story_id: vitalia-bugfix-horarios-toolbar-sticky
created_at: 2026-06-15T00:00:00-05:00
last_modified: 2026-06-15T00:00:00-05:00
notes_count: 1
refs_count: 1
conversation_count: 2
---

# chris-input.md · vitalia-bugfix-horarios-toolbar-sticky

> **Qué es este archivo:** acá Chris escribe notas + referencias + Claude responde con verdicts. Es la cocina de la story (la conversación) — separada del spec/design/arch (los outputs ratificados).
>
> **3 secciones secuenciales** (mantener el orden + emojis para que parser + cockpit funcionen):
> - 💭 Notas — Chris escribe en lenguaje natural antes/durante refinement
> - 📎 Referencias — links, imágenes, story-refs, learning-refs, doc-refs
> - 💬 Conversación — turn-by-turn cronológico Chris ↔ Claude con verdicts
>
> Doc canónico: `docs/process/chris-input-protocol.md`.

## 💭 Notas

### 2026-06-15 00:00
Bugfix UI pequeño en Lisa STAFF cuando hay un doctor seleccionado
(ej. `…/lisa/staff/{doctorId}/horarios`):
1. Como se ve en `/tmp/1100.png`.
2. La barra de opciones debería ser "fixed", igual que el tab del módulo y los sub-tabs.

Pedido: resolverlo de preferencia directamente con el auditor con Opus, de forma sencilla,
sin pasar por toda la ceremonia (cambio mínimo).

## 📎 Referencias

- **🖼 img** · `/tmp/1100.png`
  > Lisa > Staff > Ana Garcia Mendoza > Horarios. Toolbar de la vista (Disponibilidad +
  > Semana/Mes + nav-semana + Mostrar 24 horas) que debería quedar fijo al scrollear.

## 💬 Conversación

> Append-only · turn-by-turn cronológico.
> Verdict labels: ✓ APLICADO · ⚠️ DUDA · ❌ REFUTADO · 💡 PROPONE.

### 2026-06-15 00:00 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
Carril ratificado por Chris: **bugfix-story lite + Opus** (sin /architect, sin /dev-team build).

Setup hecho:
- Step 0 GREEN (cero stories abiertas).
- Hallazgo de frontera: el toolbar que scrollea es **vitalia-local** (hoja Horarios), NO core.
  La N3 (`EntitySubNavBar` de `@luana/ui-kit`) ya queda fija. Diagnóstico: cadena
  flex/`min-h-0`/`h-full` rota → scrollea un contenedor externo en vez de la grilla interna.
- Story `vitalia-bugfix-horarios-toolbar-sticky` creada (`state=idea`, `type=bugfix`,
  `cap_target=clinics.lisa.doctores`, `cap_change_type=fix`).

Próximo: spawn Opus auditor-frontend (Carril R fix-and-own) para diagnosticar live + fijar +
regression-guard; luego /pm-vitalia live-verifica el scroll en dev-app (Chrome MCP) + merge a done.
Si el único fix correcto cae en core `@luana/ui-kit` → STOP + escalar (engine boundary).

### 2026-06-15 00:30 · 🤖 claude · `/pm-vitalia` · ⚠️ DUDA (cambio de scope — necesita tu ratificación)
El live-verify en dev-app **refutó** el PASS del subagente: el fix vitalia-local NO funciona
(el toolbar se va −836px al scrollear; el guard era estructural jsdom = verde-fantasma).

Root cause real (verificado live, ver `T-1-LIVE-VERIFY.md`): es **CORE**, no vitalia. El área de
contenido de `AppPanelSlot` (`@luana/ui-kit`) es un `<div overflow-y-auto>` **block**, pero
`EntityWorkspaceLayout` usa `flex-1` esperando padre flex → no clampa → el panel scrollea todo
(N3 sobrevive solo por su `sticky`). Afecta TODA marca que monte EWL en el shell (vitalia lisa+
adrián, nicolify embudo, comunify).

Fix CORE verificado live (1 línea): `AppPanelSlot.tsx:137` `flex-1 min-h-0 overflow-y-auto` →
**+`flex flex-col`**. EWL clampa, la grilla pasa a scroller interno, toolbars quedan FIJOS.

→ Lo que parecía bugfix UI minimal vitalia-local es un **fix core cross-brand** (sigue chico,
pero pasa por `/pm-luana` promotion gate + downstream regression per-marca). Te pregunto cómo
proceder antes de tocar core.

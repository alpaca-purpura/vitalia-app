<!-- voseo-allowed: buzón conversacional interno (notas Chris voseo + Claude tuteo) — escape per spanish-text.md R25 -->
---
story_id: vitalia-fase2-mateo-vista-semana
created_at: 2026-06-21T00:00:00Z
last_modified: 2026-06-21T00:00:00Z
notes_count: 1
refs_count: 1
conversation_count: 1
---

# chris-input.md · vitalia-fase2-mateo-vista-semana

> D12 de la live-QA de la agenda de Mateo. Rediseño de la grilla de la vista Semana.
>
> Cap target: `scheduling.mateo-agenda` · Cap change type: `extend`.

## 💭 Notas

### 2026-06-21
La vista "Semana" es una lista apilada por día: las columnas desbordan, no hay eje de horas a la izquierda, no hay leyenda de qué significa cada color, ni un resumen del día. Quiero que se lea de un vistazo.

## 📎 Referencias

- **📖 story-ref** · vitalia-scheduling-mateo-review (D12 en `LIVE-QA-2026-06-21.md` + checkpoint)
  > origen del defecto; ahí está el screenshot y la lectura de producto

## 💬 Conversación

### 2026-06-21 · 🧑 chris
D10/D11/D12 con diseño. 3 stories separadas. D12 (vista Semana) va después de D11.

### 2026-06-21 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
Creé esta story (idea) derivada de D12. Scope: eje horario + leyenda de colores + resumen del día, portando el wrapper del shell. Queda en backlog; se refina vía `/po-ux` después de D11.

### 2026-06-27 · 🧑 chris
Quiero refinar una historia de usuario chica. Elegí `mateo-vista-semana`.

### 2026-06-27 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
Subí `idea → refining` (cap refining 0/3 libre; las 2 en vuelo esperan tu gate G, no bloquean refining=bucket docs). `ui-story` + `ADR-vitalia-004` ya citado, 0 deps hard. Handoff inline a `/po-ux` (UI std). Scope de partida: grilla vista Semana legible de un vistazo (eje horario izq · leyenda colores estado-pago · resumen/conteos por día), owna solo `panel-content`, porta wrapper shell.

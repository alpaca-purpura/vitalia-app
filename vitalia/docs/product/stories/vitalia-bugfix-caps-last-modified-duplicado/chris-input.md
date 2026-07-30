---
story_id: vitalia-bugfix-caps-last-modified-duplicado
created_at: 2026-05-30T19:51:29-05:00
last_modified: 2026-05-30T19:51:29-05:00
notes_count: 0
refs_count: 1
conversation_count: 1
---

# chris-input.md · vitalia-bugfix-caps-last-modified-duplicado

> **Qué es este archivo:** acá Chris escribe notas + referencias + Claude responde con verdicts. Es la cocina de la story (la conversación) — separada del spec/design/arch (los outputs ratificados).

## 💭 Notas

### 2026-05-30 19:51
Sin notas todavía · Chris escribe aquí si quiere ajustar el scope.

## 📎 Referencias

- **🤖 doc** · vitalia/docs/observed-bugs/2026-05-30-mateo-agenda-hooks-crash-ssr422.md
  > (referencia tangencial: otro bug encontrado en la misma sesión de eyeball del cockpit — independiente de este)
- **📖 story-ref** · vitalia-paradigm-map-zones (story que migró + cuya Fase F.3 introdujo el `last_modified` duplicado)

## 💬 Conversación

> Append-only · turn-by-turn cronológico.
> Verdict labels: ✓ APLICADO · ⚠️ DUDA · ❌ REFUTADO · 💡 PROPONE.

### 2026-05-30 19:51 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
Story `bugfix` creada en `state: idea`. Origen: en el eyeball del Mapa Implementado del cockpit
(:4002/map, render por zonas) Chris vio una card de 14 caps huérfanas. Diagnostiqué la causa
en vivo: **14 cap YAMLs tienen `last_modified` duplicado** (un segundo `2026-05-30` appendeado
por la Fase F.3 de la migración map-zones, sin reemplazar el existente) → gray-matter throwea
`duplicated mapping key` → el cockpit no los parsea → aparecen como huérfanos.

`repro_verified: true` (comando + lista de 14 archivos + fix sugerido en el checkpoint.md).
`cap_change_type: fix` · cap_target null (es higiene de datos cross-cap, no una cap única).
Fix = dedup mecánico de `last_modified` + guard de prevención en la migración/reconcile.

**Próximo paso (cuando quieras):** como es un bugfix lite con repro hecho, puedes ir directo a
build — invoca `/po vitalia vitalia-bugfix-caps-last-modified-duplicado` para un spec corto de
regresión, o saltar a `/architect`/tickets si quieres arrancar el fix ya. ¿Lo dejamos anotado
en idea o lo refinamos ahora?

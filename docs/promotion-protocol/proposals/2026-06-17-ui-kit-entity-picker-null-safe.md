---
proposal_id: 2026-06-17-ui-kit-entity-picker-null-safe
status: accepted
date: 2026-06-17
accepted_at: 2026-06-17
proposed_by: /dev-team (vitalia-fase2-lisa-servicios G round 2 fix-loop)
accepted_by: Chris             # ratificado 2026-06-17 (G round 2 · AskUserQuestion "Ambos ahora (core + vitalia)" para F3)
target_package: core/@luana/ui-kit
origin_brand: vitalia
origin_story: vitalia-fase2-lisa-servicios (G round 2 · G2-F3)
risk: minimal (defensive null-guard · no API change · backward-compatible · added regression test)
---

# EntityPicker `deriveInitials` null-safe en @luana/ui-kit

**Qué:** `deriveInitials(name)` aceptaba `string` y hacía `name.trim()` directo. Un `value` cuyo `name`
es `undefined` (entrada de cache stale/parcial) crasheaba el picker entero
(`Cannot read properties of undefined (reading 'trim')`). Fix: la firma pasa a
`string | null | undefined` y normaliza `(name ?? "").trim()` → devuelve `"?"` cuando no hay nombre.
`triggerLabel`/`triggerInitials` ya tenían guard de `value`; el agujero era el `name` interno.
CERO cambio de API pública (la prop `value.name` sigue siendo `string` en el contrato; esto es defensa
en profundidad). Test de regresión agregado (`EntityPicker.test.tsx`: "does not crash when the selected
value has no name").

**Por qué core (cross-brand reuse):** `EntityPicker` es la primitiva canónica de selección de entidad
(canon §2.4) que TODAS las marcas consumen en list/detail. Un picker NUNCA debe crashear por un name
faltante — es una invariante de robustez del engine, no vitalia-specific. Chris ratificó en G round 2
(2026-06-17) hacer el hardening en core además del fix vitalia-side. Dejarlo brand-local sería imposible
(la primitiva vive en core); parchear solo el caller dejaría a las demás marcas expuestas al mismo crash.

**Motivación (caso origen · G2-F3):** en `lisa-servicios`, al marcar un especialista, los hooks
`useLinkSpecialist`/`useUnlinkSpecialist` hacían `setQueryData(detail, <SpecialistLinkDTO|204>)` —
sobrescribían el cache del workspace con un sub-DTO sin `public_name`. El `EntityProcessShell` pasaba
`value={{ name: servicio.public_name }}` → `deriveInitials(undefined)` → crash. El **root cause vitalia**
(los 7 hooks que corrompían el cache) se arregla en la misma story (invalidate detail en vez de
setQueryData de un sub-DTO). Este lift es el **safety net core**: aunque un consumidor futuro vuelva a
pasar un value con name faltante, el picker degrada a `"?"` en vez de tumbar la pantalla.

**Cambio (1 archivo + 1 test):**
- `core/@luana/ui-kit/src/EntityPicker.tsx` — `deriveInitials` firma + `(name ?? "")`.
- `core/@luana/ui-kit/src/__tests__/EntityPicker.test.tsx` — regression test.

**Gate:** ui-kit vitest EntityPicker 7/7 (incluye el nuevo) · vitalia tsc 0 · consumido vía pnpm workspace
(`@luana/ui-kit` → `src/index.ts`, sin build step).

**Downstream:** ningún consumidor existente depende de que `deriveInitials` rechace `undefined` (era un
crash, no un comportamiento). Backward-compatible al 100%.

---
proposal_id: 2026-06-12-ui-kit-entity-subnavbar-picker-slot
status: accepted
date: 2026-06-12
accepted_by: Chris (ratificación verbal 2026-06-11 — vitalia-fase2-lisa-doctores/chris-input.md entries 21:00 + 22:15: "Genérico en @luana/ui-kit")
target_package: core/@luana/ui-kit
origin_brand: vitalia
origin_story: vitalia-fase2-lisa-doctores (delta v3 · D3-A)
risk: low (aditivo, opt-in, backward-compatible)
---

# EntitySubNavBar · slot opcional EntityPicker (canon §6.3)

**Qué:** `EntitySubNavBar` gana prop OPCIONAL para montar `EntityPicker` (ya en ui-kit, canon §2.4) como identidad de entidad — chip estático actual = fallback cuando la prop no se pasa. Cero breaking: consumers existentes (vitalia staff, vitalia embudo, nicolify) sin cambios.

**Por qué core:** el canon §2.1-2.2 + §6.3 ya cementan "identidad = EntityPicker (▾, cambia sin volver)" para TODO workspace de entidad cross-brand. La composición quedó pendiente del build core-ds-foundation. Vitalia doctores = 1er consumidor real.

**Contrato:** prop `picker?: { fetcher: EntitySearchFetcher, onChange: (e) => void }` (naming final lo fija el builder alineado al API real de EntityPicker). Sin `picker` → chip estático actual.

**Verificación:** tests existentes EntitySubNavBar + EntityPicker siguen verdes (regression_guard) + test nuevo composición + downstream: vitalia embudo + nicolify shell sin regresión visual.

**Ejecutor:** ticket T-CORE-picker-slot (story vitalia-fase2-lisa-doctores delta) — worktree hub vitalia, edición scoped SOLO a EntitySubNavBar.tsx + test + index si hace falta.

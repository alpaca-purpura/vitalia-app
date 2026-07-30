# Audit UI Historias — vs. Patrón Showcase

**Fecha:** 2026-06-11. **Scope:** historias `refining|developing` con FE. **Enforcement:** checklist DESIGN-SYSTEM-ENFORCEMENT.md.

---

## vitalia-fase2-config-cuenta (refining)

**Estado actual:** spec ronda 1 draft, mockups sin ratificar Chris, NO completa checklist.

**Audit:**

| Ítem | Status | Acción |
|---|---|---|
| Zona declarada | ❌ `map_zone: null` | Fix checkpoint |
| Caja | ✅ `module: configuracion`, `agent_owner: configuracion` | OK |
| Patrón | 🟡 Forma sin N3 (es form, no lista/detalle) | OK por tipo |
| Components | 🟡 Falta `Group` autosave + `FloatingAutosaveIndicator` | Add spec mockup |
| Tokens | 🟡 Spec menciona `TenantLocale` + `timezone` pero NO especifica si son campos nuevos o existentes | Clarify en spec |
| Mockup | ❌ `mockup_final_signed: false` | Ronda 2 pendiente |
| Specs | 🟡 `input_spec_signed: false` (ronda 1 sin firmar) | Completar ronda 1 + firmar |
| Gherkin | ❌ No existe | Generar en ronda 2 |

**Fix plan:**
1. `/po-ux` finaliza ronda 1 spec (intención) + Chris firma
2. Mockup v2 con `Group` autosave + `FloatingAutosaveIndicator` flotante
3. Chris ratifica visual (FIRMA 2)
4. `/po-ux` transiciona refined

**Estimado:** 2-3 h `/po-ux` (ronda 1+2+mockup iterativo).

---

## vitalia-fase2-adrian-embudo (developed, dod_live_verified=true)

**Estado actual:** live-verified, código built pero pendiente auditor + demo Chris.

**Audit:**

| Ítem | Status | Acción |
|---|---|---|
| Zona | ✅ `map_zone: agentes`, `map_box: adrian` | OK |
| Caja | ✅ `module: crm` | OK |
| Patrón N3 | ✅ `EntityWorkspaceLayout` + `EntitySubNavBar` (migrado T-5) | CORRECTO |
| Components | ✅ Usa átomos @luana/ui-kit | OK |
| Tokens | ✅ Consume de `globals.css` (no copiar) | OK |
| Mockup | ✅ Ratificado Chris 2026-06-03 | OK |
| Specs | ✅ `01-spec` v3 + `input_spec_signed: true` + `mockup_final_signed: true` | OK |
| Gherkin | ✅ 4 base + 5 sub-categorías | OK |

**Status:** ✅ COMPLETA CHECKLIST. Sin fixes necesarios. Pendiente: `/auditor` review + demo Chris + merge.

---

## vitalia-fase2-lisa-servicios (parked)

**Estado:** parked por gate shell-core-hardening (libera slot refining). Ignorar por ahora.

---

## Resumen + Siguiente paso

| Historia | Patrón OK | Fixes | Prioridad |
|---|---|---|---|
| `config-cuenta` | 🟡 Form (OK tipo) | `/po-ux` ronda 2 + mockup + firmas | P0 (refining en curso) |
| `embudo` | ✅ Completo | NINGUNO | Waiting (auditor) |
| `lisa-servicios` | ⏸ Parked | N/A | Later |

**Historias en `idea` (~20):** aplicar ENFORCE.md desde apertura. Checksum pre-primer `/po-ux`.

---

## Plan paralelo

**HOY:**
1. ✅ Showcase done + ENFORCE.md written
2. 🔵 `/po-ux` refina `config-cuenta` ronda 2 (paralelo con audit)
3. 🔵 `/auditor` review `embudo` (paralelo)

**CUANDO LISTOS:**
- `config-cuenta` refined → `/architect` ready-package
- `embudo` audited → `/pm-vitalia` merge a main
- Nuevas historias (`idea`) cargan ENFORCE.md @ inception

---

## Comandos aplicar ENFORCE.md

```bash
# Para cada historia UI nueva (idea):
cp vitalia/docs/architecture/DESIGN-SYSTEM-ENFORCEMENT.md \
   vitalia/docs/product/stories/{story-id}/ENFORCE-CHECKLIST.md

# Verificar compliance (pre-commit hook, future):
# grep -c "✅" {story-id}/ENFORCE-CHECKLIST.md
```

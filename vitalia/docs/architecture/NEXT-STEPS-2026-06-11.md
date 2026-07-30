# Próximos pasos — Design System Homologación (vitalia, 2026-06-11)

**Status: 🟢 LISTO PARA EJECUTAR PARALELO**

---

## Qué está listo AHORA

| Artefacto | Status | Path |
|---|---|---|
| **Showcase ratificado Chris** | ✅ done | `vitalia/docs/product/stories/vitalia-ds-showcase/` |
| **ENFORCE checklist** | ✅ creado | `vitalia/docs/architecture/DESIGN-SYSTEM-ENFORCEMENT.md` |
| **Audit historias** | ✅ done | `vitalia/docs/architecture/AUDIT-HISTORIAS-2026-06-11.md` |
| **Patrón N3** | ✅ validado | `EntityWorkspaceLayout` (embudo implementado correcto) |
| **Patrón Autosave** | ✅ validado | `use-autosave` 600ms+coalesce + FloatingAutosaveIndicator |
| **Patrón Átomos** | ✅ validado | 21 átomos `@luana/ui-kit` en showcase |
| **Patrón Tokens** | ✅ validado | `globals.css` líneas 30-67 (derivados, no copia) |

---

## Próximas historias abierta

| Historia | Estado | Fix | Owner | ETA |
|---|---|---|---|---|
| **config-cuenta** | refining | `/po-ux` ronda 2 (mockup +firmas) | `/po-ux` | ~2-3h |
| **embudo** | developed | `/auditor` review + demo Chris | `/auditor` | 1h audit |
| **Nuevas ideas** | idea | Aplicar ENFORCE.md pre-refining | `/pm-vitalia` | N/A |

---

## Execución PARALELO (ahora mismo)

### Sesión 1: `/po-ux` refina `config-cuenta` ronda 2

**Instrucción concisa para `/po-ux` invocación:**
```
vitalia-fase2-config-cuenta: 
- Estado: spec draft ronda 1, NO firmada, mockups sin ratificar
- Tarea: Finalizar ronda 2 COMPLETA (mockup final + Gherkin + Matrix)
- Patrón: ADR-004 sub-tab + ADR-003 mockup-per-component + ENFORCE.md checklist
- Elementos: 4 sections Group autosave (600ms+coalesce+FloatingAutosaveIndicator) · fiscal_id validators · TenantLocale · timezone
- Tokens: derivados de globals.css verbatim (NO _shared.css)
- Mockup: ADR-003 shell wrapper + dark-mode + 3 splitter states
- Output: spec ronda 2 UNIFICADA + mockups ratificadas + chris-input 2 firmas + checkpoint refined
- Referencia: vitalia-ds-showcase HANDOFF picks showcase
```

**Duración estimada:** 2-3 horas (ronda 1 cierre + mockup iterativo + Chris ratificación).

---

### Sesión 2: `/auditor` review `embudo`

**Instrucción para `/auditor` invocación:**
```
vitalia-fase2-adrian-embudo (state: developed, dod_live_verified=true):
- Audit visual fidelity: EntityWorkspaceLayout OK (N3 patrón correcto) · átomos OK · tokens OK
- Verificar: Gherkin 4 base + 5 sub-categorías presentes · playwright_required: true · graders declarados
- Esperado: PASS (completa ENFORCE.md checklist)
- Pendiente humano: demo_signoff Chris + merge a main
```

**Duración estimada:** 1 hora audit.

---

## Nuevas historias — Instrucción para `/pm-vitalia`

**Cuando abras una nueva historia `ui-story` en `idea`:**

1. **Checklist pre-refining:** copia ENFORCE.md a la story folder como guía
2. **Comunica a Chris:** "La historia seguirá el patrón vitalia-ds-showcase (N3/Autosave/átomos/@luana/ui-kit/tokens). ¿OK?"
3. **Handoff a `/po-ux`:** incluye link a ENFORCE.md en el prompt

**Historias afectadas (~20 en idea):** no requieren acción ahora (aún no refinen). Cuando transi Idea→Refining, `/pm-vitalia` inyecta ENFORCE.md en checksum.

---

## Resultado esperado (fin de semana)

| Artefacto | Esperado |
|---|---|
| `vitalia-ds-showcase` | ✅ done (merged a main) |
| `vitalia-fase2-config-cuenta` | ✅ refined (ready para `/architect`) |
| `vitalia-fase2-adrian-embudo` | ✅ reviewed + merged a main |
| ENFORCE.md adoption | ✅ cargado en `/po-ux` gate + `/architect` skip + `/dev-team` lint |
| Nuevas historias UI | ✅ abietas con ENFORCE-CHECKLIST + patrones claros |

---

## Comandos (copiar-pegar cuando listos)

```bash
# Merge showcase a main (cuando Chris ratifica)
git add vitalia/docs/product/stories/vitalia-ds-showcase/
git commit -m "feat(vitalia-ds-showcase): done — design system showcase homologation merged"
git push origin wip/vitalia

# Copiar ENFORCE a nueva historia
cp vitalia/docs/architecture/DESIGN-SYSTEM-ENFORCEMENT.md \
   vitalia/docs/product/stories/{story-id}/ENFORCE-CHECKLIST.md

# Verificar adoption (future pre-commit)
echo "TODO: agregar gate lint ENFORCE.md presencia en refining→refined"
```

---

## Go-Live

**Señal verde:** cuando `config-cuenta` esté refined + `embudo` merged + 2+ historias nuevo abiertas con ENFORCE.md aplicado.

Entonces: `/pm-vitalia` escala a crear las ~15-18 historias restantes de Fase 2 con patrón claro + auditoría automática vía lint.

---

## Riesgos bloqueadores

| Riesgo | Mitigación |
|---|---|
| `/po-ux` no termina config-cuenta mockup a tiempo | Fallback: start `/architect` con spec draft + mockup v1 parcial (re-iterate con `/dev-team`) |
| Nuevas historias ignoran ENFORCE.md | Lint pre-commit bloquea (Stage 1 2026-06 futura) · `/pm-vitalia` audita cada inception |
| `embudo` tiene regresiones en audit | `/dev-team` fix-loop paralelo (max 2 iter per auditor-self-fix-policy.md v5) |

---

## Fin.

✅ Showcase cementado → `/pm-luana` lift gate disponible para core  
✅ ENFORCE.md puesto → todas las stories UI heredan patrón  
✅ Audit ejecutado → historias abiertas saben dónde divergen  
✅ Next steps claros → `/po-ux`, `/auditor`, `/pm-vitalia` saben qué hacer  

**Próxima acción:** Chris ratifica "adelante" → lanzar sesiones paralelo.

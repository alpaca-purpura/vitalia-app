# Master Prompt — Paralelo design-system homologation (vitalia 2026-06-11)

**USO:** Copia esto íntegro a nueva conversación. Ctx completo sin releer historia anterior.

---

## Context (2 min read)

**Qué pasó (2026-06-07..2026-06-11):**
- Chris ratificó `vitalia-ds-showcase` (mockup showcase, 12 decisiones). Historia ahora `state: done`.
- Patterns cementados: N3 `EntityWorkspaceLayout` · Autosave 600ms+coalesce+`FloatingAutosaveIndicator` · EntityInfoCard Opción B · 21 átomos `@luana/ui-kit` · tokens derivados `globals.css` (NO copia).
- Audit histórico: `embudo` (developed, built, OK patrón N3) · `config-cuenta` (refining, spec draft, needs ronda 2).
- Enforcement doc creado: `vitalia/docs/architecture/DESIGN-SYSTEM-ENFORCEMENT.md` (checklist obligatorio todas historias UI).

**Por qué paralelo:** 3 trabajos independientes, pueden correr 100% simultáneo. Histórico: `/po-ux` ronda 2 spec + `/auditor` review + `/pm-vitalia` carga nuevas historias.

**Estado ahora:** 2026-06-11 ~11 AM. Showcase merged a main (commit ready). Enforcement pack documentado. Listo ejecutar.

---

## 3 Sesiones paralelo (copiar prompts exactos)

### Sesión A: `/po-ux` refina `vitalia-fase2-config-cuenta` ronda 2

**Skill:** `/po-ux`  
**Brand:** `vitalia`  
**Duración estimada:** 2-3 horas  
**Precedente:** showcase ratificado + ENFORCE checklist

**COPIAR-PEGAR prompt:**

```
BRAND: vitalia
STORY: vitalia-fase2-config-cuenta (state: refining, spec ronda 1 DRAFT, mockups sin ratificar)

TAREA: Finalizar 01-spec ronda 2 COMPLETA + mockup ratificado Chris

PATRÓN: ADR-vitalia-004 sub-tab shell (forma simple, NO lista/detalle)
- Zona: plataforma (caja configuracion, área cuenta)
- Shell: Ribbon "Plataforma" → config tab → Mi cuenta sub-tab
- Ruta: /{tenantId}/config/cuenta
- Release: F4

ELEMENTOS:
- PageContainer + 4 secciones Group (nicolify contenedor + vitalia autosave)
- Autosave: use-autosave(600ms, coalesce=true) + FloatingAutosaveIndicator píldora única + barrita agente
- Campos: fiscal_id (country validators CUIT/RUC/RFC/NIT/RUT) · address (freetext) · idioma (TenantLocale pickup) · timezone (TenantLocale pickup)
- Tokens: derivados VERBATIM de vitalia/frontend/src/app/globals.css líneas 30-67 (NO copiar _shared.css)
- Átomos: Input/Textarea (vitalia mejorado de @luana/ui-kit) · Select (Shadcn) · Checkbox · Button

MOCKUP:
- ADR-003 mandatorio: mockup-per-component dentro shell-organism real
- Shell wrapper: portado VERBATIM de vitalia/docs/product/stories/vitalia-shell-organism/mockups/dual-mode-shell.html
- Dark mode: soportado (3 splitter states: collapsed/narrow/50-50)
- Datos LatAm realistas (dr.demo@vitalialat.com, Clínica Sanaré, CUIT 20-12345678-9)
- Spanish neutro LatAm (no voseo: NUNCA "tenés", SÍ "tienes")

GHERKIN scenarios (4 base + obligatorios):
- happy: llenar form → guardar automático (600ms trigger) + toast success
- negative: fiscal_id inválido → validación inline (rojo) + deshabilitado guardar automático
- edge: cambiar timezone en 2 tabs paralelos (race) → reconciliación sin crash
- adversarial: session timeout durante autosave → retry + recovery (no perder cambios)

ESPECIALES (W0.5-bis flow):
- RONDA 1 (FUNCIÓN): § Dónde vive + § Mapa funcional (viñetas, NO Gherkin) + § Pantallas tabla campos + § Dudas
- FIRMA 1 (Chris): "esto es lo que quiero" → checkpoint.input_spec_signed=true
- MOCKUP (CREATIVO): shell + hoja + todos campos conversados + átomos finales
- FIRMA 2 (Chris, ÚNICA): mockup final con states+validations → checkpoint.mockup_final_signed=true
- RONDA 2 (AUTO-GEN): Gherkin + Matriz cobertura + business rules (genera desde Firma 2)

OUTPUT obligatorio:
- 01-spec.md ronda 2 UNIFICADA (funcional + mockup + Gherkin + componentes + microcopy)
- mockups/config-cuenta-v1.html + mockups/config-cuenta-dark-mode.html (ADR-003 completo)
- chris-input.md: 2 firmas appended (FIRMA 1 ronda 1 + FIRMA 2 mockup final)
- checkpoint.md: input_spec_signed=true · mockup_final_signed=true · state refining→refined

CHECKLIST ENFORCE (vitalia/docs/architecture/DESIGN-SYSTEM-ENFORCEMENT.md):
- [ ] Zona declarada (map_zone=plataforma)
- [ ] Caja del mapa (agent_owner=configuracion, module=configuracion)
- [ ] Patrón shell (ADR-004 cita obligatorio)
- [ ] Componentes (Group+autosave+FloatingAutosaveIndicator, NO N3/EntityInfoCard)
- [ ] Page-primitives (PageContainer OK, NO <div> layout)
- [ ] Tokens (globals.css derivados verbatim, NO arbitraries)
- [ ] Mockup (ADR-003 shell wrapper + dark mode + datos LatAm + Spanish neutro)
- [ ] Specs (ronda 1 intención + ronda 2 Gherkin + 2 firmas)
- [ ] Prior art applied (scan nicolify/comunify/core para validadores fiscal country-specific)

REFERENCIA:
- vitalia/docs/product/stories/vitalia-ds-showcase/HANDOFF-next-session.md (picks showcase)
- vitalia/docs/architecture/DESIGN-SYSTEM-ENFORCEMENT.md (checklist de-referencia)
- vitalia/.claude/rules/shell-mockup-per-component.md (ADR-003 mockup gate)
- vitalia/.claude/rules/shell-feature-architecture-mandatory.md (ADR-004 enforcement)

TIPS:
- NO inventar componentes (si falta átomo → escala /dev-team o justifica lifto a core)
- Mockup = construcción, NO dibujo. Átomos + tokens reales del showcase MISMO
- Scenarios = ejercer acciones reales (writes, no GET 200)
- Shell wrapper = PORTADO verbatim, cambio = solo la sección panel-content (la hoja)

GO? Chris ratifica ronda 1 → genera ronda 2 auto. Cuando Chris ratifica ronda 2 mockup → transition refined.
```

---

### Sesión B: `/auditor` review `vitalia-fase2-adrian-embudo`

**Skill:** `/auditor`  
**Brand:** `vitalia`  
**Duración estimada:** 1 hora  
**Precedente:** story developed + dod_live_verified=true + n3 pattern OK (audit solo)

**COPIAR-PEGAR prompt:**

```
BRAND: vitalia
STORY: vitalia-fase2-adrian-embudo (state: developed, dod_live_verified=true, awaiting auditor)

TAREA: Audit visual fidelity + Gherkin coverage. Esperado: PASS (no fixes).

AUDIT checklist (vs DESIGN-SYSTEM-ENFORCEMENT.md):
- [ ] Zona declarada: map_zone=agentes, map_box=adrian ✅
- [ ] Caja: module=crm ✅
- [ ] Patrón N3: EntityWorkspaceLayout + EntitySubNavBar → OK MIGRADO @luana/ui-kit (T-5) ✅
- [ ] Componentes: átomos @luana/ui-kit (Button×7, Input, Badge, Select Shadcn, etc.) ✅
- [ ] Tokens: globals.css derivados (audit 3 colores random vs showcase) → SPOT-CHECK
- [ ] Mockup: ratificado Chris 2026-06-03 ✅
- [ ] Specs: 01-spec v3, input_spec_signed=true, mockup_final_signed=true ✅
- [ ] Gherkin: 4 base (happy/negative/edge/adversarial) + 5 sub-categorías (race/concurrent/network/empty/large/a11y/i18n) → VERIFY PRESENTES
- [ ] Playwright: cada scenario funcional FE tiene playwright_required=true
- [ ] Graders: e2e + state_check + visual_state declarados por scenario

ESPECÍFICO embudo:
- Visual golden (Playwright spec vs mockup final): ✅ board renderiza SIN crash post-live-verify (HB-44 resuelto)
- N3 patrón: master=embudo grilla EntityInfoCard + estado · detalle=lead detail workspace con EntitySubNavBar full-bleed 3er ribbon ✅
- Leaf tabs: Resumen / Historial (NO Shadcn Tabs body — anti-pattern vitalia) ✅
- Autosave: ResumenView tiene autosave 600ms? (spec menciona pero verify en code)

CONOCIDOS (NO fixes):
- Bug sistémico HB-42/HB-44: FE imaginó contrato (camelCase + fields inexistentes) → SOLUCIONADO en commit 41e2eecb (keysToCamel + board_dto)
- Lead detail tabs: sección Score NO es tab, es bloque del Resumen → CORRECTO
- Frozen subtab: /adrian/recuperar hermana de /embudo → CORRECTO patrón

EXPECTEDRESULT: PASS (no fixes necesarios)
- Scoring: cobertura Gherkin 100%, átomos reuse 100%, tokens OK, N3 patrón correcto
- Dictamen: APPROVED
- Handoff: `/pm-vitalia` merge a main (demo_signoff Chris + finalizar)

PENDIENTE HUMANO (out-of-scope auditor):
- demo_signoff Chris (Chris abre dev-app + ejerce flujo completo)
- `/pm-vitalia` merge cuándo→done + archive story a 2026/stories/{id}/

REFERENCIA:
- vitalia/docs/product/stories/vitalia-fase2-adrian-embudo/checkpoint.md (state+build_status+dod_live_verify)
- vitalia/docs/product/stories/vitalia-fase2-adrian-embudo/01-spec.md (spec v3 ratificado)
- vitalia/docs/architecture/AUDIT-HISTORIAS-2026-06-11.md (audit previo — embudo OK)

TIPS:
- NO re-auditear lo ya verificado live (dod_live_verified=true es gate #37 cerrado)
- Spot-check 3 colores random (agent-lisa, agent-mateo, primary) vs globals.css línea 30-67 del showcase
- Gherkin coverage = tabla "Covers:" por scenario → cada Bif-N/RN-N del spec debe mapear ≥1 SC

RESULTADO: "APPROVED · sin fixes necesarios · handoff /pm-vitalia merge"
```

---

### Sesión C: `/pm-vitalia` abre nuevas historias con ENFORCE

**Skill:** `/pm-vitalia`  
**Duración estimada:** 1-2 horas (setup + primeras 3-5 historias)  
**Precedente:** showcase done + ENFORCE.md creado

**COPIAR-PEGAR instrucción:**

```
TAREA: Abrir N historias UI nuevas (idea) con ENFORCE.md aplicado

CONTEXTO: showcase cementado, patrón claro, enforcement doc listo. Nuevas historias (idea ~20) deben cargar patrón desde inception.

FLUJO por historia:
1. `/pm-vitalia` abre story en `idea` (estado normal → checkpoint.md)
2. COPIA vitality/docs/architecture/DESIGN-SYSTEM-ENFORCEMENT.md → {story-id}/ENFORCE-CHECKLIST.md
3. ESCALA a Chris: "Historia {story-id} seguirá patrón vitalia-ds-showcase (N3 si lista/detalle · Autosave si form · átomos @luana/ui-kit · tokens globals.css). ¿OK?"
4. Si Chris ratifica: ROTA a `/po-ux` con instrucción: "Carga ENFORCE-CHECKLIST.md en los puntos de gate refining→refined"

HISTORIAS A ABRIR (Fase 2 remaining, ejemplo):
- vitalia-fase2-lisa-servicios (parked ahora, desparquear + ENFORCE)
- vitalia-fase2-lisa-landing-public (idea)
- vitalia-fase2-lucas-resultados (idea)
- vitalia-fase2-camila-multiplicar (idea)
- vitalia-fase2-camila-voz (idea)
- ... (rest ~15)

CHECKLIST por historia:
- [ ] Story tiene checkpoint.md con state=idea
- [ ] Copia ENFORCE-CHECKLIST.md al folder
- [ ] Chris ratifica patrón ("esos patrones OK")
- [ ] next_action → `/po-ux` refina + carga ENFORCE en gate

EXPECTEDRESULT: ~5 historias hoy abiertas con ENFORCE attached + Chris ratificación patrón

REFERENCIA:
- vitalia/docs/architecture/DESIGN-SYSTEM-ENFORCEMENT.md (la checklist)
- vitalia/docs/architecture/NEXT-STEPS-2026-06-11.md (timeline)

TIPS:
- NO esperar a que `/po-ux` cierre config-cuenta para abrir nuevas (paralelo independiente)
- ENFORCE.md = es una guía, NO una camisa de fuerza (exceptions ratificadas Chris are OK, pero raras)
- Cuando `/po-ux` gate refining→refined, debe checkear ENFORCE cumplido

OUTPUT: spreadsheet simple {story-id | idea-abierta | ENFORCE-attached | Chris-OK?}
```

---

## Medidas de éxito (meta)

| Session | Success criterion | Done? |
|---|---|---|
| A — config-cuenta | refined (input_spec_signed + mockup_final_signed + state=refined) | ⏳ 2-3h |
| B — embudo | APPROVED (no fixes, ready merge) | ⏳ 1h |
| C — nuevas historias | 5+ abierta con ENFORCE + Chris ratificación | ⏳ 1-2h |

**Fin línea:** sábado EOD vitalia tiene showcase done + config-cuenta ready + embudo merged + 5+ nuevas historias con patrones claros.

---

## Tips clave (evitar errores históricos)

### `/po-ux` (config-cuenta)
- ❌ NO dibujar mockup antes de firmar ronda 1 intención (inversión prohibida — W0.5-bis)
- ❌ NO escribir Gherkin a mano (se GENERA en ronda 2)
- ✅ Funcional PRIMERO (viñetas humanas Mapa funcional), mockup DESPUÉS
- ✅ Shell wrapper = PORTADO verbatim de dual-mode-shell.html (no reinventar)
- ✅ Tokens = verbatim de globals.css líneas 30-67 (no copiar _shared.css)
- ❌ NO inventar átomos (si falta → justifica o escala core)

### `/auditor` (embudo)
- ✅ Spot-check 3 tokens vs showcase (verificación real, no "asumir OK")
- ✅ Gherkin coverage = tabla "Covers:" vinculando scenarios a spec items
- ❌ NO re-auditear live-verify (dod_live_verified=true ya cerrado ese gate)
- ✅ Handoff explícito `/pm-vitalia` → merge criteria clear

### `/pm-vitalia` (nuevas historias)
- ✅ ENFORCE.md must-attach en inception (no wait para `/po-ux`)
- ✅ Chris ratifica patrón EARLY (idea.md, antes refining)
- ❌ NO skip ENFORCE gate si historia cita componentes nuevos (escala /architect)

---

## Comando rápido (go signal)

```bash
# Cuando Chris ratifica "adelante paralelo":

# A. Spawn /po-ux config-cuenta
# (copiar prompt SESSION A arriba → nueva conv)

# B. Spawn /auditor embudo (paralelo A)
# (copiar prompt SESSION B arriba → nueva conv)

# C. Spawn /pm-vitalia nuevas historias (paralelo A+B)
# (copiar instrucción SESSION C arriba → nueva conv)

# Todos 3 corren simultáneo. ETA: 4-5 horas total.
# Reportar: config-cuenta refined · embudo APPROVED · 5+ historias opened
```

---

## Si algo falla (contingency)

| Falla | Recuperación |
|---|---|
| config-cuenta mockup itera >3 rondas | Fallback: `/architect` comienza con spec draft + mockup v1 (re-iterate con /dev-team) |
| embudo audit descubre issue | Max 2 iter fix (auditor-self-fix-policy v5 Carril R) |
| Nuevas historias ignore ENFORCE | Lint future + `/pm-vitalia` audita cada inception ahora (manual) |
| Paralelo scheduling conflict | Las 3 sesiones son independientes; puede rearrancar una después |

---

## Fin prompt maestro.

✅ Contexto completo (sin releer hist anterior)  
✅ 3 prompts listos copiar-pegar  
✅ Tips + anti-patterns  
✅ Medidas éxito  
✅ Contingencies  

**Ir:** nueva conversación → copiar cada sesión prompt → ejecutar paralelo.

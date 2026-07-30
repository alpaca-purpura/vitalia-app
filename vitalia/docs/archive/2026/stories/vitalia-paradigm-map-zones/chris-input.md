<!-- voseo-allowed: buzón conversacional Chris↔Claude, no user-facing -->
# chris-input — vitalia-paradigm-map-zones

> Buzón de inputs de Chris (lo que desea y/o cree que necesita), desde la idea.
> Claude puede rebatir (❌ REFUTADO) o proponer (💡 PROPONE). Se refina en conjunto.

## 🎯 Lo que Chris pidió (origen)

Arrancar como story dedicada la **migración del mapa al nuevo paradigma** (3 zonas) + **re-planificar** dándole una **propuesta de organización que cumpla la nueva visión de producto** (trabajadores digitales sobre un sistema GTM). Revisar si el split de cajas del `SYSTEM-MAP.yaml` es el correcto o se mejora.

Scope que mencionó:
1. Migrar ~71 caps `config/infra` → cajas nuevas por zona.
2. Cockpit MapView render por zona + lentes.
3. Reasignar Valeria→supervisora / Mateo→Operar.
4. Índice de acciones (Plano 2) sin grep.

## 💬 Conversación

### 2026-05-30 · 🤖 claude · `/pm-vitalia` · 💡 PROPONE
Creé la story `vitalia-paradigm-map-zones` (state=idea) + escribí la propuesta de organización refinada en `00-research.md`. Hallazgo clave del prior-art scan: **todo el backlog Fase 2 (~20 idea-stories) está organizado por la taxonomía vieja** (`config-*` + Valeria como agente) → reorganizar el mapa reorganiza el backlog.

**Mejora principal sobre el draft del SYSTEM-MAP:** Valeria **no es una caja de valor** — es la **supervisora** (el chat sidebar, el conductor). La zona Agentes son 5 cajas de especialistas: **Lisa · Mateo · Adrián · Lucas · Camila**. "Mi Día" (agenda/bookings) pasa de Valeria a **Mateo (Operar)**. Esto alinea con el shell-organism ya shipped (Ribbon = especialistas, Valeria = chat sidebar).

Necesito que ratifiques (00-research.md § 5):
1. Valeria=supervisora (no caja) + Mateo=Operar — ¿confirmás?
2. `valeria-pacientes`: "pacientes del día"→Mateo vs caja clínica propia.
3. `lisa-compliance`: vista al cliente→Plataforma + enforcement→Infra, ¿OK?
4. ¿Renombramos las stories `config-*` a su caja nueva, o solo re-tag?
5. Cockpit (F3) es tool cross-brand: ¿misma tanda o tarea tool-scope aparte?

Tras tu ratificación → state=refining → `/architect` para el plan de migración (06-tickets).

### 2026-05-30 · 👤 chris · ✓ RATIFICA
Confirmo las 5 decisiones. Pasá a refining.

### 2026-05-30 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
Registré las 5 decisiones en `checkpoint.md::ratified_decisions`. state idea→refining. Resolución de las either/or: **d2** split — "pacientes del día"→Mateo, "historial médico" (config.patients-records)→Configuración/clínico · **d3** vista compliance→Plataforma·configuracion + enforcement→Infra·seguridad · **d4** renombrar `config-*` a su caja · **d5** cockpit (F3) misma tanda como tool-scope, índice de acciones (F4) puede diferir. Encadeno a `/po` para draft del 01-spec (spec de migración) usando `00-research.md` como plan base.

### 2026-05-30 · 🤖 claude · `/po` · ✓ APLICADO
Escribí `01-spec.md` v1 — spec de migración con 6 scenarios Gherkin verificables (happy F1+F2 re-tag/SYSTEM-MAP · happy Valeria→supervisora/Mateo→Operar · negative cap-sin-caja-STOP · edge idempotencia+user_visible derivado · adversarial box-inventado+cross-brand+render-no-rompe · happy F0 backlog Fase 2). Graders: reconcile_capabilities.py + validate_system_map.py + grep cero-config/infra + tests de migración. Scope boundary respetado (F3 cockpit = tool cross-brand; cap producto = F0+F1+F2). 3 open questions: Q1 bump ADR-vitalia-005 v2 vs ADR-006 · Q2 F4 índice acciones fuera de scope · Q3 cockpit MVP por-zona vs 2 lentes ya. Spec en refining hasta tu ratificación → luego /architect.

### 2026-05-30 · 👤 chris · ✓ RATIFICA (Q1-Q3)
Q1: bump ADR-vitalia-005 (+ revisá los previos por si hay updates). Q2: todo en esta sesión. Q3: los 2 lentes en una, todo aquí.

### 2026-05-30 · 🤖 claude · `/po` · 💡 PROPONE (shell UI boundary)
Apliqué Q1/Q2/Q3 al `01-spec.md` v2: F4 (índice de acciones) + 2 lentes ahora EN SCOPE; agregué SC-7. Revisé los 3 ADR previos (pedido Q1):
- **ADR-vitalia-005** → v2 (5ª dim zona + enum boxes nuevo + config/infra deprecados + Valeria=supervisor/Mateo=Operar + MapView por zona). `areas/` nunca se construyó (Fase D ⏳) → se redefine por zona o se descarta.
- **ADR-vitalia-004** → addendum (Ribbon ya no es "6 agentes con Valeria+Configurar"; es 5 especialistas Lisa·Mateo·Adrián·Lucas·Camila + Valeria sidebar). El patrón de 9 secciones NO cambia.
- **ADR-vitalia-003** → ref menor (lista de agentes).

★ **Decisión que necesito:** mover Valeria del Ribbon al sidebar + meter Mateo es **frontend shipped** y dispara **tu gate de mockups ADR-vitalia-003**. Propongo **(A)** hacer acá la reasignación a nivel taxonomía/datos+ADRs+cockpit+F4, y la **UI del shell** como story dependiente `vitalia-shell-ribbon-realign` con mockup-gate (limpio, respeta tu gate). Alternativa (B): meter la UI acá salteando el gate (no recomiendo). ¿A o B? Con eso ratifico spec → refined → /architect.

### 2026-05-30 · 👤 chris · ✓ RATIFICA (B)
La (b). Modifiquemos todo lo necesario para que quedemos bien y esta sea la nueva (y última) forma de los agentes. Revisá hasta el último detalle en qué impacta y actualizá todo.

### 2026-05-30 · 🤖 claude · `/po` · ✓ APLICADO (opción B · scan exhaustivo)
Scan exhaustivo (frontend + docs) → inventario completo en `02-impact.md` (SSoT del cambio, hasta el último archivo). Spec a v3 con scope (B): F0 backlog · F1 caps · F2 SYSTEM-MAP · F3 cockpit 2 lentes · F4 índice acciones · F5 docs/ADRs/rules/skills · F6 shell UI realineado (mockups ADR-003 primero) · F7 tests. Hallazgo: en `agent-catalog.ts` Mateo YA existe pero como "Tecnología" — tu d1 lo reescribe a "Operar/Mi Día". Resolví micro-mapeos: 3 ex-valeria→Mateo, shell-vitalia→Infra·plataforma-tecnica, Ribbon "Configurar"→tab "Plataforma". Impacto total: ~70 caps + ~13 docs/rules/skills/ADRs + ~8 archivos FE + 6 stories renombrar + mockups + tests. Falta tu OK final al spec → refined → /architect (que ticketea con mockup-gate para el shell).

### 2026-05-30 · 👤 chris · ✓ RATIFICA
Dala por refinada, continuá con architect hasta el done. Merge preservando historia. No generes mockup (cambio mínimo).

### 2026-05-30 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
Spec v3 ratificado → state=**refined**. Gate de mockups ADR-vitalia-003 **waived** por Chris (cambio mínimo Ribbon, documentado en checkpoint `mockup_gate_waived`). Arranco `/architect` (ready package F0-F7).

### 2026-05-30 · 🤖 claude · `/pm-vitalia` · ⚠️ DUDA (merge a main)
El merge wip/vitalia→main **NO es limpio**: main divergió (tiene `cockpit v0.6` + su propio `vitalia cap-model-v3` que wip no tiene); ~79 archivos cambiados en ambos lados (caps, SYSTEM-MAP, ADR-vitalia-005, cockpit). Bulldozear main puede romperlo/regresar cockpit v0.6 → NO lo hago a ciegas. Approach seguro: sync main→wip (resolver en wip favoreciendo cockpit v0.6 + caps nuevas), luego merge limpio. Espero tu OK al approach antes de tocar main.

### 2026-05-30 · 🤖 claude · `builder-backend` · ✓ APLICADO (T-1)
T-1 completado (F1+F4). **68 caps re-taggeadas** con `map_box` + `agent_owner` actualizado + `user_visible` alineado. **3 caps problemáticas normalizadas** (config.fiscal → configuracion, ops.reconciliation → plataforma-tecnica, camila.reactivacion → camila.reactivar). **validate_system_map.py** actualizado back-compat map_box-aware. **`_actions-index.json`** generado (69 caps). **`platform/product-map-zonas.yaml`** creado (cap nuevo schema v4). 9 tests escritos RED-first → GREEN. Todos los graders SC-1/SC-3/SC-4/SC-5/SC-7 + AV-2/AV-4 PASS. Awaiting gate-runner + auditor-backend.

### 2026-05-30 · 🤖 claude · `builder-backend` · ✓ APLICADO (T-3)
T-3 completado (F5 docs). **7 docs/rules/skills actualizados** con nueva taxonomía v1.2 (5 especialistas · Valeria=supervisora · Mateo=Operar · 12 cajas · config/infra deprecated). Deliverables: ADR-vitalia-005 v2.0 + ADR-vitalia-004 addendum v1.2 + ADR-vitalia-003 ref menor + SHELL-DESIGN-CONTRACT.md + vitalia/CLAUDE.md overlay + shell-mockup-per-component.md + shell-feature-architecture-mandatory.md + vitalia-design-system/SKILL.md. Acceptance validator `grep -rE "6 agentes|Valeria.*Operar|Mateo.*Tecnología"` en docs vitalia-scope: hits residuales son todos contexto histórico/changelog (CORRECTO). Ningún doc afirmando la taxonomía vieja como estado actual. Awaiting gate-runner + auditor-backend.

### 2026-05-30 · 🤖 claude · `builder-backend` · ✓ APLICADO (T-4)
T-4 completado (F0 rename backlog Fase 2 + map_box). **5 story dirs renombrados** via git mv: config-cuenta/conexiones/avanzado → configuracion-*, config-onboarding-clinica → onboarding-clinica, valeria-pacientes → mateo-pacientes. **22 checkpoints Fase 2 actualizados** con `map_zone:` + `map_box:` + story_id/agent_owner/cap_target coherentes con nueva taxonomía. F2.yaml + F4.yaml refs actualizadas. Acceptance validators: grep -L map_box → 0 / grep fase2-config- → 0 / grep cap_target:config./valeria. → 0 / reconcile_capabilities.py → exit 0. Todos GREEN.

### 2026-05-30 · 🤖 claude · `/dev-team` · ✓ APLICADO (T-5)
T-5 (F6 shell UI) completado. agent-catalog.ts: Ribbon = [lisa,mateo,adrian,lucas,camila], Mateo=Operar (agenda+pacientes ex-valeria), Valeria fuera del ribbon. **Valeria sidebar/chat/rail PRESERVADO** (supervisora). git mv routing valeria/→mateo/ + features/valeria→mateo. ConfigTab→Plataforma. El builder quedó a una falla (budget); cerré yo el bug (`PacientesPlaceholder` leía `RIBBON_SUBTABS.valeria` ahora vacío → `.mateo`, Carril A gate-verified). tsc 0 · eslint 0 · **vitest 2319/2319 PASS**. Falta T-6 (e2e) → auditor → merge.

### 2026-05-30 · 🤖 claude · `/dev-team` · ✓ APLICADO (T-6 · ÚLTIMO ticket)
T-6 (F7 tests) completado. 2 specs e2e nuevos (ribbon-realign: 5 tabs+Plataforma·Mateo·sin Valeria-tab · mateo-agenda-loads) + ~20 specs existentes actualizados (rutas valeria/agenda→mateo/agenda; tab Valeria→Mateo; sidebar Valeria preservado). Validators: migración idempotente GREEN · reconcile + validate_system_map(--brand vitalia) PASS · tsc 0 · eslint 0 · vitest 2319 sin regresión. e2e specs escritos+typecheckan (run real = CI, stack down). Builder paró por budget verificando; cerré yo. **BUILD COMPLETO 6/6** → transición developed → /auditor.

### 2026-05-30 · 🤖 claude · `/auditor` · ✓ APLICADO (APPROVED)
Audit Conv 3 completo. FE (T-5/T-6): APPROVED directo (Valeria sidebar preservado ✓, agent-catalog coherente, cross-brand mirror limpio). BE (T-1..T-4): el auditor cazó un bug REAL (F-1 Carril B): T-2 cambió SYSTEM-MAP a v2.0 (boxes dict) y rompió el script de migración de T-1 (crash en re-run; los 9 tests pasaban solo por fixture stale → SC-4 idempotencia falsa). Fix-loop iter 1: builder-backend actualizó script v2.0-aware + fixture v2.0; **idempotencia REAL verificada** (re-run = NO-OP 69 ok/0 updated, sin crash). CHECKPOINTS.md C1-C5 APPROVED. → auto-handoff /pm-vitalia merge → done.

### 2026-05-30 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO (DONE + merged a main)
Fase F MERGE completa. 07-merge.md (5 secciones) escrito · cap ledger Fase F.3 (product-map-zonas new) · story archivada a archive/2026/stories/ · **state reviewing→done**. Merge wip/vitalia→main **LIMPIO (0 conflictos)** — commit d12e4e0a. Verificado en main: SYSTEM-MAP v2.0 · cap nueva · Ribbon con Mateo · **cockpit v0.6 + nicolify intactos**. La migración de agentes (5 especialistas + Valeria supervisora + Mateo Operar) está en main. **STORY DONE.** Pendiente tool-scope (dispatch separado, NO esta story): cockpit MapView render por zona + capability-protocol §7. Promotion candidate (modelo zonas) → /pm-luana.

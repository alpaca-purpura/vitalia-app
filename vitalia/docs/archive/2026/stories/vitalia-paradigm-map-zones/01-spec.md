<!-- voseo-allowed: spec interno de migración, no user-facing -->
---
story_id: vitalia-paradigm-map-zones
brand: vitalia
type: service-story
subtype: infra-migration
state: refining
po_version: 3
architecture_pattern: ADR-010-orquestacion-agentica + ADR-vitalia-005 (extend → 5ª dim zona)
cap_target: platform.product-map-zonas
cap_change_type: new
ratified_by_chris: false
---

# 01-spec — Migración del mapa a 3 zonas (paradigma)

## Context

Materializa `PARADIGM.md` + `ADR-010` (cementados 2026-05-30) en el mapa del producto vitalia: migra de los pseudo-agentes `config`/`infra` a **3 zonas** (Agentes · Plataforma · Infraestructura), reorganiza el backlog Fase 2 y prepara el cockpit para render por zona. Plan + 5 decisiones ratificadas: `00-research.md` + `checkpoint.md::ratified_decisions`. **No** construye el motor agéntico real — solo la **taxonomía/mapa**.

**Prior art:** `ADR-vitalia-005` define las 4 dims actuales (esta story agrega la 5ª: zona, derivada). `SYSTEM-MAP.yaml::zones` ya tiene el draft. **Decisión:** extend ADR-vitalia-005 + new cap infra `platform.product-map-zonas`. Cero engine touch.

## Scope (frentes)

| Frente | Qué | Owner-scope |
|---|---|---|
| **F0** | Re-mapear/renombrar ~20 stories Fase 2 (`idea`) a su caja/zona nueva | vitalia product |
| **F1** | Re-tag ~71 caps `agent_owner` config/infra → caja nueva (mapping `absorbs`) · zona+`user_visible` derivados | vitalia product |
| **F2** | `SYSTEM-MAP.yaml`: promover `target_boxes` a boxes de 1er nivel · Valeria→supervisora · Mateo→Operar · deprecar `config`/`infra` · bump ADR | vitalia product |
| **F3** | Cockpit `MapView.tsx`: render por zona + 2 lentes + Valeria sidebar supervisor | ⚠️ tool cross-brand (`tools/luana-cockpit/`) |
| **F4** | Índice de acciones (Plano 2) generado del service layer (navegación agéntica sin grep) — **EN SCOPE** (Chris Q2) | vitalia + tool |
| **F5** | Actualizar ADRs/docs/rules/skills: **ADR-vitalia-005 → v2** · **ADR-vitalia-004 addendum** · ADR-003 + SHELL-DESIGN-CONTRACT + capability-protocol §7 + vitalia/CLAUDE.md + vitalia-design-system skill + shell-*.md rules (ver 02-impact §7) | vitalia product |
| **F6** | **Shell UI realineado** (opción B): `agent-catalog.ts` (Ribbon [lisa,mateo,adrian,lucas,camila] · Mateo=Operar · Valeria fuera) + Ribbon.tsx (Configurar→Plataforma) + routing `valeria/`→`mateo/` + `features/valeria`→`features/mateo` · **mockups ratificados ADR-003 primero** | vitalia product (FE) |
| **F7** | Tests: actualizar e2e Ribbon/Valeria + test de migración + reconcile/validate verdes | vitalia + tool |

> **Inventario completo (hasta el último archivo): `02-impact.md`** — SSoT del mapeo cap→caja (4 valeria · 22 config · 22 infra), frontend, cockpit, docs, backlog, regresiones. Es el blueprint.
>
> **Scope boundary (tool):** F3 (cockpit) vive en `tools/luana-cockpit/` (tool cross-brand). Misma tanda (fase solo-bootstrap), trackeado como tool-scope.
>
> **Gate ADR-003 (★):** F6 (shell UI) dispara tu gate de mockups → el plan `/architect` incluye ticket(s) de **mockups ratificados** del shell realineado ANTES de construir el FE.

## Taxonomía objetivo (resumen — detalle en 00-research § 3)

- **Agentes** (core, `user_visible:true`): 🏥 lisa · 🗓 **mateo (Operar/Mi Día)** · 💼 adrian · 📣 lucas · 🌟 camila. **Valeria = supervisora** (chat sidebar, NO caja de valor).
- **Plataforma** (supporting, `user_visible:true`): 🔐 acceso (auth+iam) · 🚀 onboarding · ⚙️ configuracion.
- **Infraestructura** (enabling, `user_visible:false`): 🛡️ seguridad-cumplimiento · 📊 observabilidad · 🔧 plataforma-tecnica · 🤖 motor-agentico.

## Acceptance criteria

1. Cero caps con `agent_owner ∈ {config, infra}` tras F1; cada cap tiene un `map_box` del registro y su zona deriva correctamente.
2. `SYSTEM-MAP.yaml` valida (`validate_system_map.py`) con boxes de 1er nivel por zona; `config`/`infra` marcados `deprecated`.
3. `reconcile_capabilities.py --brand vitalia` verde (cero huérfanos, ledger coherente).
4. Valeria NO aparece como caja en zona Agentes; agenda/bookings pertenecen a `mateo`.
5. Las stories `config-*` quedan renombradas a su caja; ningún story `idea` queda con caja inválida.
6. El cockpit muestra las 3 zonas; una cap sin zona cae en "huérfanas" **visible** (no silent).
7. Cero cambios a `core/luana-core-*` y cero caps de otras brands tocadas.
8. `ADR-vitalia-005` bumped a **v2** (5ª dim zona derivada + enum `agent_owner`/`map_box` nuevo + `config`/`infra` deprecados + Valeria=supervisor / Mateo=Operar + §2.6 MapView por zona); `ADR-vitalia-004` con **addendum** de taxonomía Ribbon; `ADR-vitalia-003` ref menor actualizada.
9. Índice de acciones (Plano 2) generado del service layer existe + es consumible (cockpit lo lee · agente lo navega sin grep) · gitignored (R3).
10. Cockpit MapView renderiza los **2 lentes** (trabajadores + proceso) sobre los mismos datos.

## Scenarios (Gherkin AI-resistant)

### SC-1 · happy · F1 re-tag de caps + F2 SYSTEM-MAP
```gherkin
Given los ~71 caps de vitalia con agent_owner ∈ {config, infra}
  And el mapping SYSTEM-MAP.yaml::zones.target_boxes[*].absorbs (ej. config.auth+config.iam → acceso)
When se corre el script de migración de caps + la promoción de SYSTEM-MAP
Then cada cap migrado tiene map_box ∈ {lisa,mateo,adrian,lucas,camila, acceso,onboarding,configuracion, seguridad-cumplimiento,observabilidad,plataforma-tecnica,motor-agentico}
  And su zona se deriva del registro (Agentes/Plataforma → user_visible:true · Infraestructura → false)
  And cero caps conservan agent_owner config/infra
  And SYSTEM-MAP tiene boxes de 1er nivel por zona con config/infra status:deprecated
  And validate_system_map.py + reconcile_capabilities.py --brand vitalia salen 0
```
**graders:**
- `{ type: state_check, target: shell, cmd: "grep -rlE 'agent_owner:\\s*(config|infra)\\b' vitalia/docs/product/capabilities/ | wc -l", expect: "0" }`
- `{ type: state_check, target: shell, cmd: ".venv/bin/python scripts/reconcile_capabilities.py --brand vitalia; echo $?", expect: "0" }`
- `{ type: state_check, target: shell, cmd: ".venv/bin/python scripts/validate_system_map.py; echo $?", expect: "0" }`

### SC-2 · happy · F2 Valeria→supervisora / Mateo→Operar
```gherkin
Given valeria.agenda, valeria.bookings, valeria.shell en SYSTEM-MAP + caps asociadas
When se aplica la reasignación ratificada (d1)
Then agenda y bookings pertenecen al box "mateo" (Operar/Mi Día)
  And "valeria" NO figura en zones.agentes.boxes (es la supervisora transversal)
  And el box motor-agentico documenta el supervisor graph (Valeria) como runtime
  And las caps re-tag de valeria.* → mateo.* o (shell) → plataforma-tecnica según corresponda
```
**graders:**
- `{ type: state_check, target: shell, cmd: "python -c \"import yaml;d=yaml.safe_load(open('vitalia/docs/architecture/SYSTEM-MAP.yaml'));print('valeria' in d['zones'][0]['boxes'])\"", expect: "False" }`
- `{ type: state_check, target: shell, cmd: "grep -rlE 'agent_owner:\\s*valeria' vitalia/docs/product/capabilities/booking vitalia/docs/product/capabilities/scheduling | wc -l", expect: "0" }`

### SC-3 · negative · cap/story sin caja válida → STOP, no silent
```gherkin
Given un cap cuyo functional_area no aparece en ningún target_boxes[*].absorbs
When se corre la migración
Then la migración SE DETIENE y reporta el cap sin mapeo (lista explícita)
  And NO asigna una caja por defecto ni lo deja con config/infra silenciosamente
  And NO continúa hasta que el mapeo se resuelva (manual o agregando absorbs)
```
**graders:**
- `{ type: contract_test, path: "scripts/tests/test_map_zones_migration.py::test_unmapped_cap_halts" }`

### SC-4 · edge · idempotencia + user_visible derivado
```gherkin
Given la migración ya aplicada una vez (caps con map_box + zona)
When se vuelve a correr el script de migración
Then es no-op (cero diffs)
  And si un cap tenía user_visible manual contradiciendo su zona, queda alineado a la zona derivada (Infra→false)
  And re-correr reconcile_capabilities.py sigue verde
```
**graders:**
- `{ type: state_check, target: shell, cmd: "git diff --quiet vitalia/docs/product/capabilities/ && echo clean", expect: "clean" }`
- `{ type: contract_test, path: "scripts/tests/test_map_zones_migration.py::test_rerun_is_noop" }`

### SC-5 · adversarial · box inventado + cross-brand + render no-rompe
```gherkin
Given un cap con map_box: "inventado-x" fuera del registro SYSTEM-MAP
  And caps de comunify/otras brands presentes
When corre el validador + el cockpit renderiza
Then el validador FALLA para "inventado-x" (no se cuela una caja fantasma)
  And la migración NO toca ningún cap de comunify ni de otras brands (scope vitalia)
  And el cockpit MapView NO rompe: un cap sin zona cae en sección "huérfanas" VISIBLE
```
**graders:**
- `{ type: contract_test, path: "scripts/tests/test_map_zones_migration.py::test_invalid_box_rejected" }`
- `{ type: state_check, target: shell, cmd: "git diff --name-only | grep -E '^(comunify|nicolify|lupulo)/' | wc -l", expect: "0" }`
- `{ type: integration, path: "tools/luana-cockpit/lib/__tests__/map-zones.test.ts" }`

### SC-6 · happy · F0 backlog Fase 2 re-mapeado
```gherkin
Given las ~20 stories Fase 2 en state=idea nombradas config-* y por agente
When se aplica el re-mapeo ratificado (00-research § 4, d4 renombrar)
Then config-onboarding-clinica → caja onboarding (zona Plataforma)
  And config-{cuenta,conexiones,avanzado} → caja configuracion
  And valeria-pacientes split: "pacientes del día"→mateo · "historial médico"→configuracion (d2)
  And lisa-compliance: vista cliente→configuracion · enforcement→seguridad (d3)
  And cada story Fase 2 tiene map_zone + map_box válidos en su checkpoint
  And ninguna story idea queda con caja inválida
```
**graders:**
- `{ type: state_check, target: shell, cmd: "grep -L 'map_box:' vitalia/docs/product/stories/vitalia-fase2-*/checkpoint.md | wc -l", expect: "0" }`

### SC-7 · happy · F4 índice de acciones (Plano 2) + 2 lentes cockpit
```gherkin
Given el service layer del DDD (application services) + headers `# cap:` en el código
When se corre el generador del índice de acciones
Then existe un índice estructurado (acción → cap → ruta de código) regenerable + gitignored (R3)
  And el cockpit MapView ofrece 2 lentes sobre los mismos datos: "trabajadores" (por agente) y "proceso" (value-stream)
  And un agente resuelve "¿dónde está la acción X?" leyendo el índice, sin grep
```
**graders:**
- `{ type: state_check, target: shell, cmd: "test -f vitalia/docs/product/capabilities/_actions-index.json && echo ok", expect: "ok" }`
- `{ type: integration, path: "tools/luana-cockpit/lib/__tests__/map-zones.test.ts" }`

## Out of scope (no-objetivos)

- Construir el supervisor LangGraph real / tools / engine (otra epopeya).
- F4 índice de acciones (Plano 2) — puede ser story propia.
- Migrar caps/SYSTEM-MAP de otras brands (comunify) — vitalia-only.
- Tocar `core/luana-core-*` (sería `/pm-luana` lift).

## Decisiones Chris (Q1-Q3 resueltas 2026-05-30)

- **Q1 · ADR:** bump `ADR-vitalia-005` → v2 + revisar previos (ver § ADR review abajo).
- **Q2 · F4:** índice de acciones **EN SCOPE** (esta story).
- **Q3 · F3:** **los 2 lentes** (trabajadores + proceso) en esta story.

## ADR review (pedido Chris Q1) — qué actualizar

| ADR | Estado | Update requerido |
|---|---|---|
| **ADR-vitalia-005** (capability model 4 dims) | v1.0 | → **v2.0**: 5ª dim `zone` (derivada) · enum `agent_owner`/`map_box` nuevo (5 especialistas + 3 Plataforma + 4 Infra) · deprecar `config`/`infra` · Valeria=supervisor (fuera de boxes) · Mateo=Operar (agenda/bookings) · §2.6 MapView por zona + 2 lentes · §2.5 `areas/` (nunca construido — Fase D ⏳) se redefine por zona o se descarta |
| **ADR-vitalia-004** (shell-feature) | v1.1 | → **addendum v1.2**: el Ribbon ya NO es "6 agentes fijos (…Valeria…Configurar)" (línea 75) — es **5 especialistas: Lisa·Mateo·Adrián·Lucas·Camila** + acceso/onboarding/configuracion; **Valeria = sidebar supervisor** (no tab); routing `[agent]` sigue taxonomía SYSTEM-MAP. El patrón de 9 secciones NO cambia |
| **ADR-vitalia-003** (mockup gate) | Accepted | ref menor (línea 22): lista de agentes del shell → 5 especialistas + Valeria sidebar. NO cambia el gate |

## ★ Decisión shell UI — RESUELTO: (B) ratificado Chris (2026-05-30)

Todo entra en esta story — es el cambio **definitivo y último** de agentes. La UI del shell se realinea ACÁ cumpliendo el gate de mockups ADR-vitalia-003 inline (ticket de mockups en el plan `/architect` antes de construir el FE). Mapeo fino en `02-impact.md`.

**Micro-decisiones resueltas (mi criterio — corregí si alguna no va):**
- **Mateo:** tab "Tecnología" → **"Operar/Mi Día"** (agenda + pacientes-del-día). Lo "técnico/IA" que Mateo encarnaba se disuelve en Infra·motor-agentico (no es agente user-facing).
- **Ex-valeria agenda/bookings (3 caps)** → Mateo · **shell-vitalia** → Infra·plataforma-tecnica (es contenedor, no agente).
- **Ribbon "Configurar"** → **"Plataforma"** (1 tab que agrupa acceso/onboarding/configuración) — mantiene 5 especialistas + 1 plataforma, sin inflar el Ribbon.
- **Valeria:** cero caps de valor; supervisora (chat sidebar). Su runtime se documenta en Infra·motor-agentico.

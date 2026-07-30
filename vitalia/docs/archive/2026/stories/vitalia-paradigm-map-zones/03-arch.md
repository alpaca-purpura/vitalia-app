<!-- voseo-allowed: contrato técnico interno de migración, no user-facing -->
---
story_id: vitalia-paradigm-map-zones
brand: vitalia
arch_version: 1
schema_version: v4.1
architect_run_on: 2026-05-30
architecture_pattern: ADR-010-orquestacion-agentica + ADR-vitalia-005 (extend v2) + ADR-vitalia-004 (addendum) + ADR-vitalia-003 (mockup gate · waived)
adr_004_compliance: full   # el shell UI (F6) respeta el patrón de 9 secciones (no crea sub-tab nueva, realinea taxonomía existente)
cap_target: platform.product-map-zonas
cap_change_type: new
autonomous_mode: false
---

# 03-arch — Migración del mapa a 3 zonas (paradigma) · contrato técnico

> Esta es una **service-story / infra-migration**, NO una sub-tab CRUD con entidades/DTOs/endpoints nuevos.
> El "contrato" aquí son: (a) el **schema de datos** (campo `map_box` en caps + bloque `zones` promovido en SYSTEM-MAP),
> (b) los **scripts** (migración de caps idempotente + validador map_box-aware + generador del actions-index),
> (c) la **realineación del shell FE** (catalog → Ribbon → routing → features), (d) los **ADRs/rules/docs**.
> El SSoT verbatim del mapeo cap→caja es **`02-impact.md`** — este arch NO lo re-inventa, lo formaliza en contrato ejecutable.

## § 0 — Context Summary

- **Story:** `vitalia-paradigm-map-zones` · state `refined` → `ready` (este paquete) · release F2 · `mockup_gate_waived: true`.
- **Modules touched:** `platform` (cap nuevo) · datos `capabilities/` (todas las cajas) · `scripts/` (migración + validación + actions-index) · `vitalia/frontend` (shell realign) · `docs/architecture` + `vitalia/.claude/rules` (ADRs + rules).
- **NO toca:** `core/luana-core-*` (cero) · otras brands (cero) · `tools/luana-cockpit/` (F3 = TOOL-SCOPE separado — ver dispatch-plan.md).

### Surface → builder → auditor mapping (PM usa para spawnear agentes)

| Surface | Builder | Auditor |
|---|---|---|
| `scripts/*.py` (migración caps · validate_system_map map_box-aware · actions-index) + `vitalia/docs/product/capabilities/**` (re-tag) + `vitalia/docs/product/stories/vitalia-fase2-*/` (rename) | **`builder-backend`** (Sonnet) | **`auditor-backend`** (Opus) |
| `vitalia/docs/architecture/{SYSTEM-MAP.yaml, ADR-*.md, SHELL-DESIGN-CONTRACT.md}` + `vitalia/.claude/rules/shell-*.md` + `vitalia/CLAUDE.md` + `docs/process/capability-protocol.md §7` | **`builder-backend`** (Sonnet · docs/scripts owner) | **`auditor-backend`** (Opus) |
| `vitalia/frontend/src/**` (agent-catalog.ts · Ribbon.tsx · routing valeria→mateo · features/valeria→mateo · config→plataforma label) | **`builder-frontend`** (Sonnet) | **`auditor-frontend`** (Opus) |
| `vitalia/frontend/e2e/**` (Ribbon/Operar/Valeria specs) | **`builder-frontend`** (Sonnet) | **`auditor-frontend`** (Opus) |

### TOOL-SCOPE (NO son tickets de esta story — dispatch separado · SCOPE_GATE_SKIP fase-solo-bootstrap)

| Frente | Surface | Por qué fuera | Notas |
|---|---|---|---|
| **F3** | `tools/luana-cockpit/{lib,components/map}/` | tool cross-brand, `/pm-vitalia` NO la owna | MapView render por zona + 2 lentes + Valeria sidebar |
| **F4 (consumer cockpit)** | `tools/luana-cockpit/` lectura del `_actions-index.json` | idem | el GENERADOR del índice SÍ es vitalia-scope (scripts/) |
| **capability-protocol §7** (tabla `agent_owner`→`map_box`) | `docs/process/capability-protocol.md` (raíz cross-brand) | doc cross-brand | actualizar tabla v2 fuera de esta story (protocol-scope) |
| **paradigm rule** | `.claude/rules/paradigm-arquitectura.md` (raíz) | rule cross-brand | ya cementada; ref menor opcional |

> **Decisión de scope:** el bloque `zones` ya vive **en `vitalia/docs/architecture/SYSTEM-MAP.yaml`** (brand-scope) — promoverlo a boxes de 1er nivel **es vitalia-scope** y entra en el ready package (F2). La tabla espejo en `capability-protocol.md` (raíz) se actualiza como protocol-scope.

### Skills consultados (decisión tomada de cada uno)

- **`backend-expert`** → la migración de caps es manipulación YAML idempotente + scripts Python; no toca DDD de módulos (`vitalia/backend/src/modules/`). Patrón: script con dry-run + `--apply` + halt-on-unmapped. No hay entidades/migrations Alembic (los caps son docs, no DB).
- **`frontend-expert`** → `agent-catalog.ts` es el SSoT del shell (todo deriva de él: Ribbon, routing dispatcher, subtabs). Cambiar el catalog primero, propagar. `valeria/` agenda (código shipped real) migra a `mateo/` — routing + features + catalog **juntos** (sino 404 silencioso, riesgo §9.1 de 02-impact). Design-system-first: reusar átomos/tokens (`--agent-mateo` ya existe `#FEE209`).
- **`paradigm-arquitectura.md` rule** → árbol de decisión zona/caja aplicado al re-tag: `acceso`/`onboarding` NO van en `configuracion`; enforcement PHI → Infra·seguridad; motor-agéntico = runtime (no caja de feature). Zona se DERIVA del registro, no se escribe por cap.
- **`anti-orphan-integration.md`** → toda cap re-tag tiene hogar (zona→caja del registro SYSTEM-MAP); el validador halta si una cap cae sin caja válida (SC-3). El generador del actions-index conecta cap↔código sin grep (CONN navigable).

### CONTEXT-BRIEF source

- No `CONTEXT-BRIEF.md` presente (story con `02-impact.md` exhaustivo como SSoT). Self-ran greps (Path B) para el NO-NEW-LAYER + cross-brand + core audit. Evidencia en § Existing systems audit.

### capability YAML / docs afectados (post-merge)

- **Nuevo:** `vitalia/docs/product/capabilities/platform/product-map-zonas.yaml` (cap de esta story · `cap_change_type: new` · `agent_owner: infra` → `map_box: plataforma-tecnica` · `user_visible: false`).
- **Re-tag (48 caps):** todos los `agent_owner ∈ {config, infra, valeria}` ganan `map_box` (y pierden `config`/`infra` como agent_owner). Detalle verbatim: `02-impact.md` §1-3.
- **Confirmar zona (22 caps especialistas):** lisa/adrian/lucas/camila — ganan `map_box` = su agente.
- **`modules/{m}.md` (23):** auto-list regenera (no editar a mano · R3).

### Architecture gates que deben seguir verdes

- `cd vitalia/backend && ${WS}/.venv/bin/pytest tests/architecture/ -x -q` (DDD boundaries — esta story no toca `backend/src/`, debe quedar intacto).
- `cd vitalia/frontend && npx tsc --noEmit && npx eslint src/ --cache && npx vitest run` (shell realign).
- `scripts/validate_system_map.py --brand vitalia` (exit 0 · map_box-aware tras F2).
- `scripts/reconcile_capabilities.py --brand vitalia` (exit 0 · cero huérfanos).
- Arch fitness FE `vitalia/frontend/src/__tests__/architecture/` (catalog SSoT tests — actualizar allowlists si shrink).

## § 1 — El cambio de schema de datos (el "contrato" de esta migración)

### 1.1 — Campo `map_box` en cap YAML (NUEVO · derivado de la 5ª dim "zona")

Cada cap declara `map_box` (la caja del mapa). La **zona se deriva** del registro SYSTEM-MAP (`zones[].boxes`), NO se escribe por cap. `user_visible` se alinea a la zona.

```yaml
# ── 5ª dimensión (ADR-vitalia-005 v2) ──
map_box: acceso          # ∈ {lisa,mateo,adrian,lucas,camila} (Agentes)
                         #   ∪ {acceso,onboarding,configuracion} (Plataforma)
                         #   ∪ {seguridad-cumplimiento,observabilidad,plataforma-tecnica,motor-agentico} (Infra)
# map_zone: NO se escribe — se deriva de zones[].boxes en SYSTEM-MAP
user_visible: true       # Agentes/Plataforma → true · Infra → false (alineado a zona)
```

**Convivencia con `agent_owner`/`functional_area` (deprecación gradual):**
- `agent_owner` de valor `config`/`infra` queda **deprecado** (la migración lo reemplaza por `map_box`). Para cajas de **Agentes**, `agent_owner` (lisa/mateo/adrian/lucas/camila) y `map_box` coinciden — `agent_owner` sobrevive como alias del especialista.
- `functional_area` (`<agent>.<area>`) se mantiene para Agentes; para Plataforma/Infra el `functional_area` legacy (`config.auth`, `infra.observability`) se reemplaza por `<map_box>.<area>` (`acceso.middleware`, `observabilidad.health`) según `absorbs`.
- **`valeria` como agent_owner** desaparece de caps de valor: agenda/bookings → `agent_owner: mateo` + `map_box: mateo`; shell → `map_box: plataforma-tecnica`.

### 1.2 — Mapeo cap → caja (SSoT verbatim = 02-impact.md · NO re-inventar)

El script de migración (T-1) **consume el bloque `zones[].target_boxes[].absorbs`** de SYSTEM-MAP como tabla de verdad mecánica:

| Origen (legacy `functional_area` raíz) | → `map_box` | Zona | `user_visible` |
|---|---|---|---|
| `config.auth`, `config.iam` | `acceso` | Plataforma | true |
| `config.onboarding_clinic` (+ valeria-wizard onboarding) | `onboarding` | Plataforma | true |
| `config.cuenta/clinics/conexiones/patients-records/admin/avanzado` | `configuracion` | Plataforma | true |
| `config.compliance` + `infra.scaffolding` (audit/dual-filter/whatsapp-registry/fixtures) | `seguridad-cumplimiento` | Infra | false |
| `infra.observability` | `observabilidad` | Infra | false |
| `infra.platform` + `infra.payment` (+ shell-vitalia + reconcile-sweep + smoke) | `plataforma-tecnica` | Infra | false |
| `infra.copilot` + `infra.agentic-engine` + `infra.sales-agent-engine` | `motor-agentico` | Infra | false |
| `valeria.agenda` / `valeria.bookings` | `mateo` (`mateo.agenda` / `mateo.bookings`) | Agentes | true |
| `valeria.shell` (shell-vitalia) | `plataforma-tecnica` | Infra | false |
| `lisa.*` / `adrian.*` / `lucas.*` / `camila.*` | mismo agente | Agentes | true |

> Casos d3 (compliance) y d2 (pacientes-del-día) ya resueltos en 02-impact §2-3. El script NO inventa default: si una cap no matchea ninguna `absorbs` → **HALT** + lista explícita (SC-3).

### 1.3 — `zones` promovido a 1er nivel en SYSTEM-MAP (F2)

El bloque `zones` (hoy draft con `target_boxes`) se promueve: las 12 cajas (`5 Agentes + 3 Plataforma + 4 Infra`) pasan a ser cajas de **1er nivel** con sus `functional_areas` (heredadas de las `absorbs`). Los pseudo-agentes `config`/`infra` en `agents[]` se marcan `status: deprecated`. Valeria queda en `zones.agentes.boxes` SOLO como nota supervisor (NO como caja de proceso) → se mueve a `motor-agentico.runtime` doc. Mateo entra a `agents[]` como caja Operar.

## § 2 — Scripts (el contrato ejecutable)

### 2.1 — `scripts/map_zones_migration.py` (NUEVO · T-1)

```
Uso:
  python3 scripts/map_zones_migration.py --brand vitalia [--dry-run | --apply] [--strict]

Lee:
  - vitalia/docs/architecture/SYSTEM-MAP.yaml :: zones[].target_boxes[].absorbs   (tabla de verdad)
  - vitalia/docs/product/capabilities/**/*.yaml                                   (caps a re-tag)

Hace (idempotente):
  1. Por cada cap: deriva map_box desde su functional_area/agent_owner legacy vía `absorbs`.
  2. Edita el cap: agrega/actualiza `map_box`, alinea `user_visible` a la zona, re-mapea functional_area si Plataforma/Infra.
  3. Para caps valeria.agenda/bookings → agent_owner: mateo + map_box: mateo.
  4. HALT si una cap no matchea ninguna `absorbs` (SC-3): imprime lista, exit 1, NO escribe default.
  5. --dry-run: imprime diff sin escribir. --apply: aplica Edit. Re-run = no-op (SC-4 idempotencia).

Salida verdes:
  - 0 caps con agent_owner ∈ {config, infra} (SC-1 grader)
  - reconcile_capabilities.py + validate_system_map.py exit 0
```

### 2.2 — `scripts/validate_system_map.py` (MODIFY · T-2)

Hoy valida `functional_area` contra `agents[].functional_areas[]`. **Tras F2 debe ser map_box-aware:**
- Construir `valid_boxes` desde `zones[].boxes` (12 cajas) además de `valid_areas` legacy.
- Check nuevo: `map_box` de cada cap ∈ `valid_boxes` (SC-5: box inventado → FALLA).
- Check nuevo: `user_visible` de cap coherente con la zona derivada de su `map_box` (Infra→false).
- Mantener back-compat: caps aún con `functional_area` legacy de Agentes siguen validando.

### 2.3 — `scripts/reconcile_capabilities.py` (verificar · T-2)

No requiere lógica nueva de map_box (sigue validando ledger + huérfanos), pero **debe seguir exit 0** tras el re-tag (cero caps rotas). Si su validación de `agent_owner` enum rechaza la ausencia de config/infra → ajustar el enum aceptado para incluir el periodo de transición (config/infra deprecados pero presentes como histórico en change_log).

### 2.4 — Actions-index (Plano 2) — **EXTEND, no NEW** (F4 · T-1)

> **NO-NEW-LAYER decisión (ver § Existing systems audit):** YA existe `scripts/generate_code_to_cap_index.py` que produce `_code-index.json` (cap↔archivo bidireccional). El "índice de acciones (Plano 2)" del spec se construye **componiendo** ese índice + el `dev_preview.api_endpoints` de cada cap — NO un grep-layer paralelo.

`scripts/generate_actions_index.py` (NUEVO · thin) compone:
- input A: `_code-index.json` (cap → archivos de código, ya generado).
- input B: cap YAMLs → `dev_preview.api_endpoints` + `dev_preview.route` + `dev_preview.main_component`.
- output: `vitalia/docs/product/capabilities/_actions-index.json` (gitignored R3) con shape `accion → cap → {route, api_endpoints, main_component, e2e_test}`.
- Un agente resuelve "¿dónde está la acción X?" leyendo este JSON, **sin grep** (SC-7, paradigma §7 navegación sin grep).

## § 3 — Shell FE realineado (F6 · T-5)

### 3.1 — `src/lib/agent-catalog.ts` (SSoT — cambiar PRIMERO)

| Símbolo | Hoy | Target |
|---|---|---|
| `AGENT_RIBBON_ORDER` | `[lisa, lucas, adrian, valeria, camila]` | `[lisa, mateo, adrian, lucas, camila]` (Valeria fuera · Mateo entra) |
| `AGENT_CATALOG.mateo` | `tabLabel:"Tecnología"`, `defaultSubtab:"ia"` | `tabLabel:"Operar"` (Mi Día), `defaultSubtab:"agenda"` |
| `AGENT_CATALOG.valeria` | tab `"Operar"` en ribbon | **fuera del ribbon** (sigue en catalog para el sidebar supervisor + `DEFAULT_CHAT_AGENT`) |
| `RIBBON_SUBTABS.mateo` | `[]` | `[{agenda},{pacientes}]` (heredados de valeria) |
| `RIBBON_SUBTABS.valeria` | `[{agenda},{pacientes}]` | `[]` (deja de ser tab) |
| `RibbonTabSlug` / `isValidAgent` | `mateo` excluido, `valeria` incluido | `mateo` incluido, `valeria` excluido del ribbon (sigue válido como chat agent) |
| `SHIPPED_STATIC_SUBTABS` | `valeria.agenda` | `mateo.agenda` |
| `config` slug | tab `"Configurar"` | tab `"Plataforma"` (label) — slug `config` se mantiene o renombra a `plataforma` (decisión builder: preferir mantener `config` slug para minimizar routing churn, solo cambiar `tabLabel`) |

### 3.2 — Routing (`app/[tenantId]/(shell-organism)/`)

- `valeria/agenda/` (ruta estática shipped) → **migrar a `mateo/agenda/`** (git mv del dir + page.tsx).
- `valeria/` dir → eliminar (Valeria ya no es tab; su chat vive en el sidebar, no en `[agent]`).
- El dispatcher `[agent]/[subtab]/page.tsx` + `[agent]/layout.tsx` leen del catalog → propagan automático tras 3.1.
- `config` routing dinámico (`[agent]` con slug especial) — sin cambio de path, solo label.

### 3.3 — Features (`src/features/`)

- `features/valeria/` (agenda real shipped: ~30 componentes) → **`features/mateo/`** (git mv del dir completo + actualizar imports + `// cap:` headers de `valeria.agenda` → `mateo.agenda`).
- `features/config/` placeholders → mantener (label Plataforma se aplica en Ribbon, no rompe feature path).
- `--agent-mateo` (#FEE209) ya existe en globals.css → reusar (design-system-first).

### 3.4 — Ribbon.tsx + SubTabsBar

- Renderean `AGENT_RIBBON_ORDER` + `ConfigTab` → cambio automático tras catalog. `ConfigTab` label "Configurar"→"Plataforma".
- ValeriaSidebar (chat supervisor) — sin cambio funcional (Valeria sigue siendo `DEFAULT_CHAT_AGENT`).

### 3.5 — Mockup gate (ADR-vitalia-003) — **WAIVED**

`checkpoint.md::mockup_gate_waived: true` (Chris 2026-05-30): realineación del Ribbon (mover tabs, sin componente nuevo) → cambio mínimo, sin mockups. La verificación visual se cubre con e2e Ribbon (T-6) + Playwright scoped sobre el Ribbon realineado.

## § 4 — ADRs / rules / docs (F5 · T-3)

| Archivo | Cambio | Owner-builder |
|---|---|---|
| `ADR-vitalia-005-*` | → **v2.0** (5ª dim `map_box` derivada · enum 12 cajas · config/infra deprecados · Valeria=supervisor / Mateo=Operar · §2.6 MapView por zona + 2 lentes · §2.5 areas/ redefinido por zona) | builder-backend |
| `ADR-vitalia-004-*` | **addendum v1.2**: línea 75 N1 Ribbon "6 agentes (…Valeria…Configurar)" → "5 especialistas (Lisa·Mateo·Adrián·Lucas·Camila) + Plataforma; Valeria=sidebar supervisor". Patrón 9 secciones NO cambia | builder-backend |
| `ADR-vitalia-003-*` | ref menor línea 22: lista agentes shell → 5 especialistas + Valeria sidebar. Gate NO cambia | builder-backend |
| `SHELL-DESIGN-CONTRACT.md` | "6 agentes fijos" / "Ribbon 6 tabs" (líneas 110-111,131,468) → 5 especialistas + ConfigTab→Plataforma | builder-backend |
| `vitalia/CLAUDE.md` (overlay) | línea ~81 "6 agentes" → 5 especialistas + Valeria supervisor + Mateo Operar | builder-backend |
| `.claude/skills/vitalia-design-system/SKILL.md` | "6 agentes" / catálogo colores (Valeria/Mateo/Config) → actualizar | builder-backend (vitalia-scope skill) |
| `vitalia/.claude/rules/shell-mockup-per-component.md` | "Ribbon 6 agentes" (58,68) + paleta (130) → 5 + plataforma | builder-backend |
| `vitalia/.claude/rules/shell-feature-architecture-mandatory.md` | línea 39 `config-*` → `plataforma-*` / `configuracion-*` | builder-backend |

> `docs/process/capability-protocol.md §7` (tabla agent_owner→map_box) = **protocol-scope cross-brand** (dispatch separado).

## § 5 — Backlog Fase 2 rename (F0 · T-4)

`git mv` + actualizar `checkpoint.md` (`map_zone`/`map_box`) de cada story (02-impact §8):

| Story actual | → | map_zone · map_box |
|---|---|---|
| `vitalia-fase2-config-cuenta` | `vitalia-fase2-configuracion-cuenta` | plataforma · configuracion |
| `vitalia-fase2-config-conexiones` | `vitalia-fase2-configuracion-conexiones` | plataforma · configuracion |
| `vitalia-fase2-config-avanzado` | `vitalia-fase2-configuracion-avanzado` | plataforma · configuracion |
| `vitalia-fase2-config-onboarding-clinica` | `vitalia-fase2-onboarding-clinica` | plataforma · onboarding |
| `vitalia-fase2-valeria-pacientes` | `vitalia-fase2-mateo-pacientes` | agentes · mateo (pacientes del día, d2) |
| `vitalia-fase2-lisa-compliance` | (queda) | agentes · lisa (vista cliente, d3) |
| resto `lisa-/adrian-/lucas-/camila-*` | sin rename | agentes · <agente> (solo agregar map_box al checkpoint) |

Cada story Fase 2 (todas en `idea`) gana `map_box` válido en su checkpoint (SC-6 grader: `grep -L 'map_box:' ... | wc -l == 0`).

## § 6 — Integration design (CONN · anti-isla)

> Esta story re-organiza el mapa; el "consumo" es que **toda cap re-tag tiene hogar** y el cockpit + el agente las navegan.

### Reachability path (cómo se LLEGA)
```
cap YAML (map_box: acceso)
  → SYSTEM-MAP.yaml zones.plataforma.boxes contiene "acceso"  (hogar válido)
  → validate_system_map.py confirma map_box ∈ valid_boxes      (notarized)
  → cockpit MapView (TOOL-SCOPE) agrupa por zona → caja "Acceso"  (navigable, F3)
  → actions-index _actions-index.json: accion → cap → route/endpoints  (navigable sin grep, F4)
```

### Consumers (quién USA cada salida)
- `map_box` en caps → consumido por `validate_system_map.py` (gate) + cockpit MapView (render, tool-scope) + reconcile (ledger).
- `zones` promovido → consumido por cockpit MapView + el agente que lee el mapa.
- `_actions-index.json` → consumido por cockpit (F3) + cualquier agente que navega "¿dónde está la acción X?".
- shell `agent-catalog.ts` → consumido por Ribbon + routing dispatcher + SubTabsBar (ya cableado).

### Registration points (dónde se CABLEA — deliverables verificables)
- BE/docs: `map_box` escrito en cada cap por T-1; `zones` promovido en SYSTEM-MAP por T-2; validator map_box-aware por T-2.
- FE: `AGENT_RIBBON_ORDER` incluye mateo, excluye valeria (T-5); routing `mateo/agenda` registrado (git mv); `SHIPPED_STATIC_SUBTABS` actualizado.
- Tests: e2e Ribbon (5 tabs + Mateo + sin Valeria-tab) (T-6); test idempotencia migración (T-6).

### Home (cap)
- `cap_target: platform.product-map-zonas` · `cap_change_type: new` · `map_box: plataforma-tecnica` · `user_visible: false`.

## § 7 — Existing systems audit (NO NEW LAYER rule)

### Source of evidence
- [x] Self-run greps (Path B — fallback, no CONTEXT-BRIEF presente).

### Audit cross-module ejecutado
```bash
# 1. ¿Existe ya un generador de índice cap↔código? (evitar grep-layer paralelo para F4)
ls scripts/ | grep -iE 'action|index'
#   → generate_capability_index.py · generate_code_to_cap_index.py · generate_actions_index? NO
grep -rln '_actions-index' scripts/ vitalia/docs/ tools/luana-cockpit/
#   → solo aparece en 01-spec (aún no existe el generador)

# 2. Cross-brand mirror: ¿otra brand tiene zones/map_box? (debería lift a core si sí)
for b in comunify nicolify lupulo; do grep -rln 'map_box\|^zones:' $b/docs/; done
#   → vacío (cero mirror cross-brand)

# 3. Engine: ¿core tiene map_box/zones?
grep -rln 'map_box' core/
#   → vacío (cero en engine)

# 4. ¿Scripts ya conocen map_box? (para saber si MODIFY vs NEW)
grep -c 'map_box\|zones\|target_boxes' scripts/validate_system_map.py scripts/reconcile_capabilities.py
#   → 0 / 0 (ninguno es map_box-aware → MODIFY validate, verify reconcile)
```

### Sistemas existentes encontrados
| Sistema | Path | Estado | Decisión |
|---|---|---|---|
| Code↔cap index | `scripts/generate_code_to_cap_index.py` → `_code-index.json` | active | **EXTEND** — el actions-index (F4) compone sobre este, NO grep-layer nuevo |
| SYSTEM-MAP validator | `scripts/validate_system_map.py` | active (functional_area-aware) | **EXTEND** (MODIFY) — agregar map_box checks |
| Capability reconciler | `scripts/reconcile_capabilities.py` | active | **VERIFY** — debe seguir exit 0; ajustar enum agent_owner si rechaza |
| `zones` draft | `SYSTEM-MAP.yaml :: zones` (con `target_boxes.absorbs`) | partial (draft) | **EXTEND** — promover a boxes 1er nivel |
| Capability index gen | `scripts/generate_capability_index.py` → `areas/` | active | sin cambio (areas/ se redefine por zona en ADR-005 v2, fuera de esta migración mecánica) |

### Decisión por sistema
- **actions-index (F4):** EXTEND `generate_code_to_cap_index.py` componiendo `_code-index.json` + `dev_preview.api_endpoints`. Crear `generate_actions_index.py` thin (compositor), NO un grep-walker paralelo. Justificación: el grep-layer ya existe (cap↔código); duplicarlo = NO-NEW-LAYER violation.
- **validate_system_map (F2):** EXTEND (MODIFY) in-place — agregar `valid_boxes` + map_box checks manteniendo back-compat functional_area.
- **migración caps (F1):** NEW script `map_zones_migration.py` — justificado: no existe migrador de caps por zona; consume el `absorbs` existente (no inventa tabla). Es one-shot idempotente, no layer permanente.
- **Cross-brand / core:** cero mirror, cero engine. La 5ª dim `map_box` es brand-local vitalia (ADR-vitalia-005 v2). Si comunify la adopta → `/pm-luana` lift post-cement (ya previsto en ADR-005 §5).

## § 8 — Cross-cutting concerns

- **Idempotencia (cardinal):** el script de migración es re-runnable (SC-4): segunda corrida = cero diffs. El generador del actions-index es regenerable (gitignored R3).
- **Cero otras brands / cero engine (SC-5):** `git diff --name-only | grep -E '^(comunify|nicolify|lupulo)/' | wc -l == 0`. Cero `core/luana-core-*`.
- **Tenant isolation / PHI:** N/A directo (migración de docs/caps + shell taxonomía). El re-tag de caps de compliance a `seguridad-cumplimiento` PRESERVA su semántica HIPAA-lite (no toca el enforcement, solo la etiqueta de caja).
- **Spanish neutro LatAm:** labels del Ribbon ("Operar", "Plataforma") + docs en español neutro sin voseo (los archivos de migración llevan `<!-- voseo-allowed -->` por citar taxonomía interna).
- **Native-first:** scripts corren con `${WS}/.venv/bin/python`; FE con `npx tsc/eslint/vitest/playwright`. Nunca docker exec.
- **R3 auto-gen:** `_actions-index.json` + `modules/{m}.md` + `BACKLOG.*` son gitignored — regenerar, no editar a mano.
- **Halt-no-silent (SC-3):** migración NUNCA asigna caja por defecto; halta + reporta la cap sin mapeo.

## § 9 — Test surfaces (TDD-mandatory)

- **Migración (BE/scripts · RED primero):** `scripts/tests/test_map_zones_migration.py` con `test_unmapped_cap_halts` (SC-3) · `test_rerun_is_noop` (SC-4) · `test_invalid_box_rejected` (SC-5) · `test_config_infra_valeria_fully_retagged` (SC-1).
- **Validator:** test que `validate_system_map.py` rechaza `map_box` inventado + acepta los 12 válidos.
- **FE (Vitest · RED):** `agent-catalog` arch test — `AGENT_RIBBON_ORDER` incluye `mateo`, excluye `valeria`; `RIBBON_SUBTABS.mateo` tiene agenda+pacientes; `SHIPPED_STATIC_SUBTABS` tiene `mateo.agenda`.
- **E2E (Playwright · RED para ruta nueva):** Ribbon renderiza 5 tabs (Lisa·Mateo·Adrián·Lucas·Camila) + Plataforma; tab "Operar" pertenece a Mateo; NO existe tab Valeria; `mateo/agenda` carga (la agenda migrada). Actualizar specs que buscaban Valeria-tab.
- **Reconcile/validate como graders shell** (ya en 01-spec scenarios).

## § 10 — Open questions for PM

1. **`config` slug → renombrar a `plataforma` o solo cambiar label?** Recomiendo **solo cambiar `tabLabel`** ("Configurar"→"Plataforma") y mantener el slug `config` en routing para minimizar churn (evita migrar `config/` routing + features placeholders). El cap re-tag (config→acceso/onboarding/configuracion) es ortogonal al slug del ribbon. → builder-frontend confirma en T-5.
2. **`areas/` (ADR-005 §2.5, "nunca construido"):** el spec dice "redefinir por zona o descartar". Esta migración NO lo construye (out-of-scope mecánico). ¿Se descarta formalmente en el ADR v2 o se deja `⏳ Fase futura`? → decisión PM al ratificar ADR.
3. **Si al desglosar supera 10 tickets vitalia-scope** → recomiendo split (taxonomía/docs vs shell-UI). Conteo actual: **6 tickets** (T-1..T-6) → cabe en 1 story. Sin split necesario.

# Lifecycle — SSoT del ciclo de vida de producto (Luana platform)

**Cement-date:** 2026-05-28. **Owner:** Chris + `/pm-vitalia`. **Estado:** canónico.

Este doc es la **fuente única de verdad** del modelo de producto y su ciclo de vida. **Supersede** los fragmentos contradictorios de `pm-redesign-2026-05.md`, `release-protocol.md`, `capability-protocol.md` y los skills `/pm-*` donde difieran. Si otro doc contradice a este → este gana, y el otro se corrige.

Nació de la consolidación 2026-05-28 (análisis profundo del proceso SDD: el modelo tenía 9 ejes solapados, atomics fantasma en 1120 archivos, validators verdes-por-vacío, outcome/release coexistiendo). Ver `docs/process/learnings.md` § 2026-05-28.

---

## 1. El modelo: 4 ejes (+ código auto-mapeado)

Antes había 9 ejes solapados (outcome · phase · release · capability · atomic · scenario · tech_module · module · story). Quedan **4**, lineales, cada uno con un dueño claro:

```
Release  (¿cuándo shippeó?)        — contenedor temporal, agrupa stories
  └─ Story  (¿qué trabajo?)         — unidad de trabajo, 10 estados, transitoria
       └─ Capability  (¿qué SABE hacer el producto?) — unidad PERMANENTE, tiene salud
            └─ Scenario  (¿qué hace, concretamente?)  — unidad atómica de comportamiento (Gherkin)
                 ↳ Code files  — auto-mapeados vía header `# cap:` (NO se mantienen a mano)
                 ↳ Tests       — e2e_test por scenario (la prueba)
```

| Eje | Qué es | Vive en | Dueño |
|---|---|---|---|
| **Release** | Agrupación temporal "se shippeó junto" (F0..FN) | `{brand}/docs/product/releases/{id}.yaml` | `/pm-{brand}` |
| **Story** | Unidad de trabajo. Nace `idea`, muere `done`→archive | `{brand}/docs/product/stories/{id}/` | `/pm-{brand}` (estados) |
| **Capability** | Unidad **permanente** de producto. Lo que el producto puede hacer | `{brand}/docs/product/capabilities/{module}/{cap}.yaml` | `/pm-{brand}` (ledger) |
| **Scenario** | Unidad atómica de comportamiento. Gherkin Given/When/Then | autorado en `01-spec.md`, linkeado al cap | `/po-ux`/`/po` autora, `/pm` linkea |

**Agrupación humana:** la capability se agrupa por `agent_owner` (lisa/valeria/adrián/lucas/camila/config/infra) + `functional_area` (`<agent>.<area>`). Eso alimenta el **Mapa Implementado** del cockpit. Se conserva — es el lenguaje humano del producto. La caja vive en una de **3 zonas** del mapa — **Agentes · Plataforma · Infraestructura** — derivadas del registro `{brand}/docs/architecture/SYSTEM-MAP.yaml` (`zones`). Doctrina del modelo (3 planos + zonas + invariantes): `docs/architecture/luana-platform/PARADIGM.md` + rule `paradigm-arquitectura.md`.

---

## 2. Lo que se MATÓ (decisiones 2026-05-28, ratificadas Chris)

| Concepto muerto | Por qué | Reemplazo | Migración |
|---|---|---|---|
| **`atomic`** (+ header `# atomics:`) | Fantasma total: los 1120 archivos tenían `# atomics: TBD`, 71/72 caps con `atomics: []`. Nunca se instanció una vez. Redundante con `scenario` | **`scenario`** es la unidad atómica | Fase 1: borrar header de 1120 archivos + quitar del protocolo |
| **`outcome`** | Coexistía "reemplazado por release" + "épica canónica" según el doc. 6 outcomes vivos + releases con `maps_legacy_*` | **`release`** único contenedor temporal | Fase 1: borrar 6 archivos + quitar `maps_legacy_*` |
| **`phase`** | Legacy pre-release, se solapaba con outcome y release | **`release`** | Fase 1: gone con outcome |
| **`module`** (alias) | Alias deprecado de `tech_module` | **`tech_module`** | Fase 1: drop alias |

**Regla cardinal post-consolidación:** no se agregan ejes nuevos al modelo sin matar uno. Shrink-only.

---

## 3. Ciclo de vida — Story (10 estados macro)

Heredado de paradigm v4. WIP cap **≤1 por `code:{module}` bucket** para developing/developed/reviewing (NO "por worktree" — X6/D-X2; gana la hard rule de `story-closure-gate.md`; exime `AWAIT_CHRIS_VERIFY` + `defer_audit: true`; cualquier doc que diga ≤2/≤3 o "por worktree" está obsoleto). Las 4 fases nombradas {G,R,C,D} viven en `story-closure-gate.md` + el campo `checkpoint.phase`.

| # | Estado | Significado | Owner | WIP cap |
|---|---|---|---|---|
| 1 | `idea` | Spark + research opcional | Chris + `/pm-{brand}` | ∞ |
| 2 | `refining` | Decompose + draft spec/UX | `/pm` + `/po-ux`/`/po`/`/ux-agentico` | ≤ 3 |
| 3 | `refined` | Spec + diseño ratificados | `/pm` cierra | ≤ 5 |
| 4 | `ready` | Paquete completo (03-arch + 04-validators + 05-guidelines + 06-tickets) | `/architect` | ≤ 5 |
| 5 | `developing` | Build autónomo | `/dev-team` | **≤ 1** |
| 6 | `developed` | Validators GREEN | `/dev-team` | **≤ 1** |
| 7 | `reviewing` | Auditor QA | `/auditor` | **≤ 1** |
| 8 | `done` | APPROVED + merge + cap promovida + archive | `/pm-{brand}` | rolling 90d |
| 9 | `parked` | De-prioritized | Chris | ∞ |
| 10 | `dropped` | Won't do (terminal) | Chris | ∞ |

Transiciones de Chris (cockpit): solo `idea↔refining`, `→parked`, `→dropped`. El resto las hace una skill. Ver `cockpit-permissions.md`.

### Tipos de story (`checkpoint.md::type`)

| Tipo | Surface | Refinador | Ceremonia |
|---|---|---|---|
| `ui-story` | UI estándar (CRUD/list/detail/form/dashboard) | `/po-ux` | completa |
| `service-story` | Servicio backend sin UI propia | `/po` | completa |
| `agentic-story` | Flujo conversacional (copilot/sales_agent) | `/po` → `/ux-agentico` | completa |
| `bugfix` | Arreglo de comportamiento roto **o** completion de cableado incompleto, scope quirúrgico (1-N archivos, ≤1-2 días), **sin diseño nuevo** | `/po` (BE/servicio) o `/po-ux` (UI) | **lite** |

**`bugfix` — tipo lightweight (cement 2026-05-30, ADR-011):** recorre los **mismos 10 estados macro** con menos artefactos de *diseño* (nunca menos *verificación*):
- **Gate repro-first (HARD):** hereda `.claude/rules/hotfix-repro-mandatory.md`. `checkpoint.md::repro_verified: true` antes de `developing`. Bug → test RED que reproduce la falla. Completion → "el comportamiento X falta / Y no renderiza" verificado **en vivo** (ejercer la acción real + leer logs, NO un GET 200 — `test-design-doctrine.md` § Verificación REAL).
- **`refining` lite:** `01-spec.md` corto con **scenarios de regresión**, sin `02-design-*` ni mockups salvo UI nueva.
- **`ready` lite:** `/architect` produce ready package reducido (`06-tickets` + `04-validators` con regresión; `03-arch`/`05-guidelines`/`dispatch-plan` opcionales o inline).
- **`cap_change_type`:** `fix` por default (sin scenarios nuevos); `extend` si la fix completa una cap agregando ≥1 scenario.
- **No se reduce:** TDD (RED→GREEN), story-closure-gate, anti-orphan (CONN), gates de calidad (lint/arch-fitness/coverage/jscpd).
- **Reclasificación:** si emerge diseño nuevo (mockups, decisión arquitectónica, ≥1 scenario de feature) → `/pm-{brand}` reclasifica `type` antes de cerrar `ready`.

---

## 4. Ciclo de vida — Capability (salud del producto)

La capability tiene un `status` declarado + un `computed_status` derivado por `scripts/compute_capability_status.py`. El **computed** es la verdad de salud:

```
stub → wip → partial → declared-live → verified-live
                 ↘ drift (deriva detectada) ↘ deprecated → sunset
```

| computed_status | Significado |
|---|---|
| `stub` | Sin scenarios. No describe nada todavía |
| `wip` | Scenarios declarados, sin verificación pasando |
| `partial` | Algunos scenarios verificados |
| `declared-live` | Marcada live, sin evidencia de tests |
| `verified-live` | Live + todos los e2e_test de sus scenarios pasan |
| `drift` | El código/tests/acceso contradicen lo declarado |
| `deprecated`/`sunset` | En retiro |

**Definición de DONE (cement 2026-05-28):** una capability **no puede ser `live`** sin **≥1 scenario + e2e_test pasando**. `live` con scenarios vacíos = inválido (enforce HARD en Fase 5). Esto mata el "verde por vacío".

---

## 5. Ciclo de vida — Release

State machine auto-recomputada desde los estados de las stories miembro:

```
backlog → planning → in_progress → ready_to_merge → shipped
```

`release.yaml.stories[]` es denormalizado (vista); el SSoT por story sigue siendo su `checkpoint.md::release:`. El merge de una story ya squashea por-story; el release agrupa para release-notes + deploy. Ver `release-protocol.md` (corregido: outcome+phase ya no existen).

---

## 6. Trazabilidad — la cadena que se VE en el cockpit

Para cualquier capability, una sola traza conectada:

```
Release (cuándo) → Story-origin (por qué) → Scenarios (qué hace, humano)
   → Code files (dónde · auto vía # cap:) → Tests (prueba) → Status/Health (¿vive?)
```

**Cross-checks que sobreviven** (`validate_code_cap_bidirectional.py`):
- ❌ **cross_check_1** (atomics↔headers) — MUERTO (atomics killed)
- ❌ **cross_check_2** (headers↔atomics) — MUERTO
- ✅ **cross_check_3** (scenario→e2e_test existe) — **HARD** pre-push
- ✅ **cross_check_4** (access roles ↔ `@require_phi_access`) — **HARD para vitalia** (es salud; el control de acceso a PHI no puede ser advisory)

---

## 7. División de labor: Cockpit (bosque) vs Claude Code (ejecución)

| | **Luana Cockpit** (ver el bosque + decidir) | **Claude Code** (ejecutar lo que está hecho) |
|---|---|---|
| Rol | Monitoreo en lenguaje humano, decisiones | Ejecución del pipeline SDD |
| Hace | Ver salud de producto, priorizar, planificar releases, mover `idea↔refining`, autorar intent (notas/refs/scenarios draft en chris-input), disparar "extender cap"/"nueva story" | `/pm-{brand}` → `/po-ux`/`/architect` → `/dev-team` → `/auditor` → merge |
| NO hace | Ejecutar git, avanzar estados de skill, editar código BE/FE | Decisiones de priorización de bosque (eso es de Chris en el cockpit) |
| El puente | `chris-input.md` + `checkpoint.md::state` + APIs `transition`/`extend-cap`/`from-done` que **crean trabajo** | Levanta el trabajo creado, refleja en vivo (SSE) |

**El loop diario (manual operativo):**

```
┌─ COCKPIT (bosque · decidir) ────────────────┐      ┌─ CLAUDE CODE (ejecutar) ───────────────┐
│ cockpit-up  →  chris-corp (multi · :4000)   │      │ /pm-{brand}                            │
│ 1. Roadmap: ¿qué release toca?              │      │ 2. levanta story refining-ratificada   │
│ 2. Salud de Producto: ¿qué caps stub/drift? │ ───► │ 3. encadena /po-ux → /architect →      │
│ 3. Backlog Board: muevo idea→refining       │      │    /dev-team → /auditor (auto-chain)    │
│ 4. dejo notas/scenarios draft en chris-input│      │ 4. /pm-{brand} merge (reviewing→done)  │
│ 5. priorizo / asigno release                │ ◄─── │ 5. cap se actualiza · traza se completa │
└─────────────────────────────────────────────┘ SSE  └────────────────────────────────────────┘
```

_(Cockpit = un solo multi-cockpit en :4000, prendido desde chris-corp (home base). Ver `CLAUDE.md` § Cockpit.)_

1. **Cockpit** (`make -C ~/Proyectos/chris-corp cockpit-up` → multi :4000): ves la Salud de Producto (cuántas caps stub/partial/live/drift), el Roadmap (releases F0..FN), y el Backlog Board (10 estados). Decidís qué sigue. Movés `idea→refining` (única transición que Chris hace en el cockpit), ajustás prioridad/release, dejás notas y scenarios-draft en `chris-input.md`.
2. **Claude Code** (`/pm-{brand}`): levanta la story que marcaste, valida WIP caps (≤1), y encadena `Skill(po-ux)`→`Skill(architect)`→`Skill(dev-team)`→`Skill(auditor)` programáticamente. Ejecuta el build con TDD.
3. **Merge** (`/pm-{brand} merge`): al APPROVED, escribe `07-merge.md`, promueve la capability (status + scenarios desde el spec), archiva la story, squash-merge.
4. **Cockpit refleja en vivo** (SSE): la cap pasa de stub→partial→verified-live, la traza Release→Story→Scenarios→Code→Tests→Status se completa. El bosque se actualizó.

**Regla de oro:** el cockpit nunca ejecuta git ni avanza estados de skill; Claude Code nunca decide priorización de bosque. El puente es `chris-input.md` + `checkpoint.md::state` + las APIs `transition`/`extend-cap`/`from-done` del cockpit que CREAN trabajo para que Claude lo levante.

---

## 8. Roadmap de consolidación (7 fases)

Plan de migración del estado actual al modelo de este doc. Estado en tiempo real abajo.

| Fase | Qué logra | Estado |
|---|---|---|
| **0 — Doctrina** | Este `lifecycle.md` + resolver incoherencias de skills. No destruye nada | ✅ DONE 2026-05-28 (commit c930a333) |
| **1 — Colapsar modelo** | Matar atomics/outcome/phase/module-alias. cross_check_3 HARD | ✅ DONE 2026-05-28 (1a bb988b2a + 1b 7ab119c6) |
| **2 — Backfill trazabilidad** | Fence 8 caps · consolidar shell · backfill +43 scenarios · huérfanos 96→0 · redistribuir releases · borrar dead code | ✅ DONE 2026-05-28 (2a b22ca319 + 2b fa73f363) |
| **3 — Cockpit** | ProductHealthBanner en /map + CapDrawer trace reordenado + README saneado + tooltips sin atomics | ✅ DONE 2026-05-28 (05ad9c69) |
| **4 — Skills** | 22 skills/templates al modelo 4-ejes · menú pm-vitalia sin outcome · Def. de DONE | ✅ DONE 2026-05-28 (dfec5e64) |
| **5 — Enforcement** | cross_check_4 reconoce todos los mecanismos PHI (drift 7→1) · reconcile `live⟹evidencia` WARN · planned caps skip story-resolution | ✅ DONE 2026-05-28 (05ad9c69) |
| **5.1 — cc4 HARD flip** | Resolver el gap RBAC (story `vitalia-compliance-audit-rbac-gap`) → flipear cc4 a HARD vitalia | ⏳ bloqueado por la story de seguridad |
| **6 — Manual diario** | § 7 de este doc es el manual operativo | ✅ DONE (§ 7) |

**Estado post-consolidación (2026-05-28 · Fases 0-6 DONE):** atomics + outcome + phase MUERTOS. Trazabilidad real Release→Story→Capability→Scenario. Validator no miente (cc4 drift 7→1, el único drift era el gap de seguridad RBAC con story dedicada). Cockpit muestra Salud de Producto real. cc3 HARD=0. **Pendiente:** Fase 5.1 (resolver gap seguridad → cc4 HARD) + backfill orgánico de los caps stub cuando sus stories shippeen. _(Snapshot de caps/status en el momento de la consolidación — ver `scripts/compute_capability_status.py` para estado actual.)_

---

## 9. Punch-list de incoherencias (detectadas 2026-05-28)

| # | Incoherencia | Resolución | Estado |
|---|---|---|---|
| 1 | WIP caps `≤2` en pm-vitalia vs `≤1` hard rule | Corregido a ≤1 | ✅ Fase 0 |
| 2 | nicolify "fuente prior-art principal ~80% prod" (es snapshot frozen) | Corregido: vitalia/comunify live, nicolify archivo | ✅ Fase 0 |
| 3 | Conteo cap stale "16 caps" (son 72) | Corregido | ✅ Fase 0 |
| 4 | outcome "reemplazado" vs "canónico" | Release único (decisión #2) | ✅ Fase 1 (6 outcomes borrados + maps_legacy_* quitados) |
| 5 | F2.yaml referencia stories ausentes (valeria-agenda, lisa-marca) | F2.yaml actualizado; ambas stories archivadas como `done` | ✅ Fase 2 |
| 6 | Hooks: docs dicen "Section 14", real es Section 16 | `brand-docs-schema.md` + `docs/rules-detail/brand-docs-schema.md` ya usan Section 16 | ✅ Fase 4 |
| 7 | `/functionality` tab citado pero es Cap Drawer | cockpit README corregido (nota explícita: no existe `/functionality`, es Cap Drawer) | ✅ Fase 3 |
| 8 | README cockpit stale (14 rutas/4 vistas/6 tests) → real 19/6/53 | README saneado (20 API routes · 6 vistas funcionales · stats actuales) | ✅ Fase 3 |
| 9 | `generate_release_notes.py` + `validate_chris_input.py` no existen | **MISSING — no implementado.** Quitar refs a estos scripts hasta crearlos. | ⏳ abierto |
| 10 | ADR path doble en pm-luana (`ADR/` vs `luana-platform/`) | Unificado | ✅ Fase 0 |
| 11 | Validators saltean ~10 caps en silencio | `compute_capability_status.py` loguea WARN por parse error pero sigue iterando; caps con frontmatter inválido se omiten sin contar en total. Fallar ruidoso pendiente | ⏳ abierto |
| 12 | 8 caps sin frontmatter YAML (reconcile saltea → 64/72 cargados) | Todas las caps tienen frontmatter válido (backfill completado) | ✅ Fase 2 |
| 13 | cc4 (PHI access) tiene 6 drifts → no se pudo flipear a HARD aún | Story `vitalia-compliance-audit-rbac-gap` en `idea`; cc4 HARD flip sigue bloqueado | ⏳ Fase 5.1 |

---

## 10. Referencias

- `docs/process/learnings.md` § 2026-05-28 — análisis origen + decisiones
- `docs/process/capability-protocol.md` — schema cap (v4 · atomics eliminados, scenario es la unidad atómica)
- `docs/process/release-protocol.md` — release (v3 · outcome+phase eliminados)
- `docs/process/cockpit-permissions.md` — whitelist Chris vs Claude
- `tools/luana-cockpit/README.md` — la tool
- `.claude/rules/story-closure-gate.md` — WIP caps ≤1 (SSoT)

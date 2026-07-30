<!-- voseo-allowed: internal architecture decision record, not user-facing -->

# ADR-vitalia-004 — Shell-Feature Architecture (transversal Fase 2)

| Campo | Valor |
|---|---|
| **Status** | Accepted (v1.2 — 2026-05-30 addendum taxonomía agentes) |
| **Date** | 2026-05-26 (v1.0) · 2026-05-27 (v1.1 addendum) · **2026-05-30 (v1.2 addendum)** |
| **Authors** | Chris + `/po-ux` (orchestrator Opus 4.7) |
| **Brand** | vitalia |
| **Scope** | Toda story Fase 2 que construya una **sub-tab** dentro del shell-organism agéntico |
| **Supersedes** | — (extiende ADR-vitalia-003 mockup-per-component) |
| **Sources** | `vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/03-arch.md` (architectura cementada por `/architect` Opus 4.7 single-shot 2026-05-27); `SHELL-DESIGN-CONTRACT.md`; rule `.claude/rules/anti-duplication.md`; story `vitalia-paradigm-map-zones` (taxonomía 5 especialistas 2026-05-30) |
| **Changelog** | v1.0 (2026-05-26): cementación inicial · 9 secciones. v1.1 (2026-05-27): cementar N3-static SubSubTabsBar + routing variant `[subtab]/[subsubtab]/page.tsx` + `AGENT_SUBSUBTABS`. **v1.2 (2026-05-30): addendum taxonomía agentes — N1 Ribbon pasa de "6 agentes fijos" a "5 especialistas + tab Plataforma". Valeria sale del Ribbon (es supervisora sidebar). Mateo entra al Ribbon como especialista Operar/Mi Día. Routing `[agent]` sigue usando map_box del SYSTEM-MAP. El patrón de 9 secciones NO cambia.** |

---

## § 1 — Context

Durante la planificación de la Fase 2 emerge un problema repetido: cada story que construye una sub-tab nueva (Lisa→Marca, Valeria→Pacientes, Adrián→Embudo, etc.) llega al `/architect` sin un patrón cementado, y el architect reinventa la estructura BE+FE story por story. Esto produce:

- **Drift arquitectónico** entre sub-tabs (Valeria→Agenda usa Server-First page + Zustand drawer-store, mientras otra story podría usar Client-Only page + Redux por inercia)
- **Trabajo duplicado** del architect re-decidiendo rutas, layout FSD, repository base, audit pattern, etc.
- **Risk de regresión cross-cutting** (HIPAA-lite dual filter, audit log sync, telemetría `growth_studio_event`) si alguna story se salta el patrón
- **Capability inventory inconsistente** (post-merge YAMLs con structure variable según architect del día)

La story `vitalia-fase2-valeria-agenda` (F2-S1, state=ready 2026-05-27) ya tiene el patrón completo cementado en su `03-arch.md`. Este ADR **promueve ese patrón a SSoT transversal** para que las 20+ stories Fase 2 restantes lo repliquen sin re-discovery.

**Decisión Chris (2026-05-26):** "lo que hagamos debe afectar a todas las demás historias de usuario; las demás historias deben saber de esto (la arquitectura)".

---

## § 2 — Decision

Toda story Vitalia Fase 2 que construya una sub-tab dentro del shell-organism **MUST** seguir las 9 secciones de patrón cementadas abajo. El `/architect` cita este ADR verbatim en su `03-arch.md § 0` y solo se permite divergir documentando rationale explícito en `03-arch.md § Architecture Decisions`.

**Aplica a (scope):**

- ✅ Stories Fase 2 sub-tab con UI agentic-organism (`lisa-*`, `mateo-*`, `adrian-*`, `lucas-*`, `camila-*`, `plataforma-*`) — ★★ v1.2: `valeria-*` sub-tabs de valor migradas a `mateo-*`; `config-*` renombradas a `plataforma-*` o `onboarding-*`
- ✅ Stories Fase 1 restantes que construyan componente con data fetching/persistencia (la mayoría ya está `done`)
- ✅ Stories `state ∈ {idea, refining, refined}` actualmente abiertas

**NO aplica:**

- ❌ Service-only stories sin UI (`vitalia-payment-adapter-mvp`, `vitalia-fiscal-emission-pe`) — siguen patrón BE puro
- ❌ Stories agentic-conversacionales puras (Camila→Voz si fuera flow puro) — siguen `/ux-agentico`
- ❌ Bootstrap/infra stories (F1-S0 stack-stability, F1-S1 design-tokens) — históricas, exentas

---

## § 3 — Architecture pattern (9 secciones cementadas)

> **★ Trazabilidad:** cada sub-sección cita el anchor verbatim de `vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/03-arch.md` que la origina.

### § 3.1 — Routing (Next.js 16 App Router con route group)

Ruta canónica per sub-tab:

```
vitalia/frontend/src/app/[tenantId]/(shell-organism)/{agent}/{subtab}/page.tsx
```

- Cada sub-tab tiene su propio **static segment** que **toma precedencia** sobre el dispatcher dinámico `[agent]/[subtab]/page.tsx`
- El dispatcher dinámico solo renderiza placeholders para sub-tabs aún no developed (post F1-S10 empty-states)
- Al mergear una story sub-tab, el placeholder de `SubTabContent.PLACEHOLDER_MAP` se reemplaza por sentinel `"moved to dedicated route"`
- **Server Component** por default (sin `"use client"`). Carga estado inicial vía función `get{Subtab}InitialState({ tenantId, ...searchParams })` server-side con cookies forwarded
- **Search params whitelist** enforced upstream — NUNCA PHI en URL (HIPAA-lite)
- `params` y `searchParams` son `Promise<...>` (Next.js 16 async params API)

**Anchor source:** valeria-agenda 03-arch § 6.0 + § 6.3.

### § 3.1.1 — Niveles de navegación cementados (★ v1.1 — 2026-05-27 · ★★ v1.2 addendum — 2026-05-30)

```
N1 (Ribbon)           → [agent]                                    → 5 especialistas + tab Plataforma
                                                                      (Lisa · Mateo · Adrián · Lucas · Camila + Plataforma)
                                                                      ★★ v1.2: Valeria ya NO aparece en el Ribbon.
                                                                      Valeria = ValeriaSidebar (supervisora, siempre visible).
                                                                      Mateo = especialista Operar/Mi Día (reemplaza a Valeria en Ribbon).
                                                                      ConfigTab label: "Configurar" → "Plataforma".
N2 (SubTabsBar)       → [agent]/[subtab]                           → AGENT_SUBTABS whitelist per agente
N3-static (NEW)       → [agent]/[subtab]/[subsubtab]               → AGENT_SUBSUBTABS opcional (sub-tabs complejas)
N3-dynamic            → [agent]/[subtab]/[...slug]                 → workspace detalle item (catch-all, lower priority)
```

> **★★ Addendum v1.2 (2026-05-30) — Taxonomía agentes actualizada:**
> - Ribbon N1: **5 especialistas (Lisa · Mateo · Adrián · Lucas · Camila) + tab Plataforma** (antes 6 tabs con Valeria + Configurar)
> - Valeria: sale del Ribbon · aparece como sidebar permanente (`ValeriaSidebar`) en el panel izquierdo · es la supervisora orquestadora · su runtime vive en zona infraestructura · motor-agentico
> - Mateo: entra al Ribbon · subtítulo "Operar / Mi Día" · hereda agenda + bookings + pacientes que tenía Valeria · color `--agent-mateo: #FEE209` (ya existía en el design system)
> - Tab Plataforma: reemplaza "Configurar" · abarca zona plataforma (acceso · onboarding · configuracion) · `AGENT_RIBBON_ORDER = [lisa, mateo, adrian, lucas, camila]`
> - El patrón de 9 secciones (routing · FSD-Lite · client root · data layer · forms · BE DDD · migrations · telemetría · tests) NO cambia con v1.2
> - Las stories sub-tab que citen `config-*` en `architecture_pattern` DEBEN ser renombradas a `plataforma-*` (ver story `vitalia-paradigm-map-zones` T-4)

**Reglas de coexistencia:**
- Una sub-tab puede tener **N3-static** (sub-sub-tabs cabecera) **Y** **N3-dynamic** (workspace catch-all) simultáneamente — Next.js prioriza static segment sobre catch-all
- Si `AGENT_SUBSUBTABS[agent][subtab]?.length > 0` → URL `[agent]/[subtab]/` **redirect** a primera entry del array (default convention)
- Si `AGENT_SUBSUBTABS[agent][subtab]` undefined → sub-tab es single panel (no extra navigation)
- N3-dynamic usa Sheet drawer (Shadcn) con URL state opcional vía `[...slug]` — patrón valeria-agenda `AppointmentDrawer`

**Anti-pattern PROHIBIDO:**
- ❌ Shadcn `Tabs` internas en body de sub-tab para agrupar N vistas (esto sería **Nivel 4** anti-pattern — content tab nav fuera de la cabecera shell)
- ❌ Custom tab bar custom dentro de `{Agent}{Subtab}View.tsx` que duplique función de SubSubTabsBar
- ❌ Single scroll con secciones múltiples cuando hay 3+ vistas conceptualmente discretas (usar SubSubTabsBar para discoverability)

**Cuándo usar single scroll vs SubSubTabsBar:**

| Caso | Solución |
|---|---|
| Sub-tab con UN solo panel coherente (ej. `valeria/agenda`) | Single panel — sin N3-static |
| Sub-tab con 2 secciones tightly-coupled (ej. config-simple con form + preview side-by-side) | Single scroll con headers H2 |
| Sub-tab con **3+ vistas conceptualmente discretas** (ej. `lisa/marca` = identidad / voz / presencia) | **SubSubTabsBar (N3-static) MANDATORY** |
| Detalle item dinámico (ej. abrir doctor específico, slot agenda) | Sheet drawer (Shadcn) + URL state opcional via `[...slug]` |

**Anchor source:** SHELL-DESIGN-CONTRACT § 7.4 (Nivel 3 cementación) · lisa-marca refinement 2026-05-27 (origen ratificación Chris).

### § 3.1.2 — `SubSubTabsBar` componente (NEW v1.1)

```
vitalia/frontend/src/components/shared/shell-organism/SubSubTabsBar.tsx
```

**Pattern:** copy verbatim de `SubTabsBar.tsx` (F1-S8) con ajustes mínimos:
- Roving tabindex WAI-ARIA tablist pattern idéntico
- URL-derived state: `extractSubsubtabFromPath(pathname)`
- Render condicional: `if (subsubtabs.length === 0) return null` (mantiene cabecera limpia si sub-tab es single panel)
- Tint color de la sub-sub-tab activa: heredada del agente (`--agent-{name}`) — consistencia visual

**Layout final del shell con N3-static activo:**

```
┌──────────────────────────────────────────────────┐
│ TopBarGlobal                                       │  ← header global
├──────────────────────────────────────────────────┤
│ Ribbon: [Lisa] [Lucas] [Adrián] [Valeria]...      │  ← N1 agentes
├──────────────────────────────────────────────────┤
│ SubTabsBar: [Marca] [Doctores] [Servicios]...     │  ← N2 sub-tabs per agente
├──────────────────────────────────────────────────┤
│ SubSubTabsBar: [Identidad] [Voz y tono] [Presen.] │  ← N3-static (opcional, solo si AGENT_SUBSUBTABS[lisa][marca] !== undefined)
├──────────────────────────────────────────────────┤
│                                                    │
│  {Panel content (single, NO tabs internas)}        │
│                                                    │
└──────────────────────────────────────────────────┘
```

**AppPanelSlot renderiza condicional:**

```tsx
<section role="region" aria-label="Panel aplicación">
  <Ribbon />
  <SubTabsBar />
  <SubSubTabsBar /> {/* renders null si no aplica */}
  <div className="flex-1 min-h-0 overflow-hidden">{children}</div>
</section>
```

### § 3.1.3 — `AGENT_SUBSUBTABS` catalog (NEW v1.1)

```ts
// vitalia/frontend/src/lib/routing/shell-routes.ts  (extiende AGENT_SUBTABS existente)

/**
 * Sub-sub-tabs (N3-static) per (agent, subtab) pair.
 * Opcional — solo declarar cuando la sub-tab agrupa 3+ vistas discretas.
 * Default redirect: primer entry del array.
 */
export const AGENT_SUBSUBTABS: Partial<Record<AgentKey, Partial<Record<string, readonly string[]>>>> = {
  lisa: {
    marca: ['identidad', 'voz-y-tono', 'presencia'],
    // doctores: undefined  → single panel
    // servicios: ['catalogo', 'escalera']  (futuro lisa-servicios)
    // compliance: ['semaforo', 'retencion', 'reportes']  (futuro lisa-compliance)
  },
  // Otros agentes declaran subsubtabs cuando aplica
} as const

/**
 * Default redirect cuando user llega a [agent]/[subtab]/ sin subsubtab.
 * Convention: primera entry del array (KISS — evita catalog duplicado).
 * Sobrescribir SOLO si se requiere default distinto al primero.
 */
// AGENT_DEFAULT_SUBSUBTAB no se exporta — primera entry del array es el default.
```

**Layout file structure post-N3-static (lisa-marca ejemplo):**

```
app/[tenantId]/(shell-organism)/lisa/marca/
├── page.tsx                          # → redirect a /lisa/marca/identidad (primera entry)
├── identidad/page.tsx                # N3-static "identidad"
├── voz-y-tono/page.tsx               # N3-static "voz-y-tono"
└── presencia/page.tsx                # N3-static "presencia"
```

### § 3.2 — FSD-Lite layout per agente

Estructura **obligatoria** per sub-tab dentro de su feature root:

```
vitalia/frontend/src/features/{agent}/
├── index.ts                                # public API — re-export componentes y tipos públicos
├── components/
│   ├── placeholders/                       # placeholders para sub-tabs aún no developed (F1-S10 baseline)
│   └── {subtab}/                           # ★ componentes de ESTA story
│       ├── {Agent}{Subtab}View.tsx         # root client (entry desde page.tsx)
│       ├── {Subtab}Header.tsx
│       ├── {Subtab}Content.tsx
│       ├── ... otros componentes molécula/organismo ...
│       └── __tests__/                      # Vitest unit tests co-located
├── api/
│   ├── {subtab}.ts                         # React Query hooks (useXxxQuery, useXxxMutation)
│   ├── {subtab}-server.ts                  # SSR fetch helpers (getInitialXxxState)
│   └── __tests__/
├── hooks/                                  # hooks UI/derivados (URL params persist, debounce, derived state)
├── store/                                  # zustand stores (UI state SOLAMENTE — NO data fetch state)
└── types/
    ├── {subtab}.types.ts                   # TypeScript types (mirror de DTOs Pydantic backend)
    └── {subtab}-schema.ts                  # Zod schemas (forms + discriminated unions si aplica)
```

**Reglas:**

- ❌ NO `features/{agent}/{subtab}/` (sub-tab fuera de `components/`) — viola FSD-Lite
- ❌ NO componentes shell-organism en `features/` (`TopBarGlobal`, `Ribbon`, `ValeriaSidebar`, etc. van en `components/shared/shell-organism/`)
- ❌ NO Shadcn primitives en `features/` — solo en `components/ui/` (copy-paste local)
- ❌ NO cross-feature imports (`features/lisa` NO importa de `features/valeria`) — si necesitan compartir → escalá a `components/shared/`

**Anchor source:** valeria-agenda 03-arch § 6.2.

### § 3.3 — Client root view (`{Agent}{Subtab}View.tsx`)

- Tiene `"use client"` directive en línea 1
- Recibe `initialData` + `initial{Filters/State}` como props desde el Server Component page
- Hidrata React Query cache con `initialData` (sin re-fetch en mount)
- Compone los sub-componentes (Header, Content, Drawers, Modals) según wireframe
- Mantiene su árbol DOM con `Suspense` boundaries SOLO si hay lazy loading explícito

**Anchor source:** valeria-agenda 03-arch § 6.4.

### § 3.4 — Data layer (React Query + Zustand split)

| Tipo de estado | Storage | Ejemplo |
|---|---|---|
| **Server data** (fetched) | React Query (`useXxxQuery`, `useXxxMutation`) | `useAgendaGrid`, `useAppointmentDetail` |
| **UI state local** (modals, drawers, selected items, filters) | Zustand store (1 store por concern) | `drawer-store.ts`, `filters-store.ts` |
| **URL state** (filtros bookmarkables, vista activa) | `useSearchParams` + `useRouter.replace()` | view, date, preset_filter |
| **Form state** (drafts) | RHF (`useForm`) | `chargeForm`, `createAppointmentForm` |
| **Global app state** | ❌ NO usar — preferir Server Components + props | — |

**Reglas:**

- ❌ NO Redux / Context para data fetch — React Query es SSoT
- ❌ NO Zustand para data fetched — solo UI ephemeral state
- ❌ NO `useState` para datos que persisten cross-mount — usar Zustand o React Query
- ✅ Mutations invalidan keys explícitamente vía `queryClient.invalidateQueries({ queryKey: [...] })`
- ✅ React Query keys siguen convención `[module, subtab, action, ...filtersStable]`

**Anchor source:** valeria-agenda 03-arch § 6.2 (`store/`, `api/`) + skill `tessl__react-patterns`.

### § 3.5 — Forms (RHF + Zod + discriminated unions)

- React Hook Form (`react-hook-form` v7+) como motor de forms
- Zod (v3+) para schema validation — schemas viven en `features/{agent}/types/{subtab}-schema.ts`
- **Discriminated unions** cuando hay sub-formularios condicionales (ej. `chargeSchema` con `payment_method` discriminador, currency-aware)
- `zodResolver` para integrar Zod con RHF
- **Autosave on-change** con debounce 600ms (per `form-runtime-array.md` rule) cuando el contexto lo amerita (Brand Studio sections, configuración, drafts)
- **Submit-driven** cuando la transacción es atómica (charge, emission, status change)
- Toasts vía `sonner` (Shadcn primitive) — never `alert()` o `window.confirm()`
- Errores muestran inline `<FormMessage>` + Alert variant si server error

**Anchor source:** valeria-agenda 03-arch § 7.4 + form-runtime-array.md.

### § 3.6 — Backend DDD Inside-Out + `PhiRepositoryBase`

**Layers (orden de implementación):**

1. `domain/` — entidades + value objects puros (sin framework, sin SQLA). `dataclasses` con `frozen=True` cuando aplique.
2. `infrastructure/` — SQLA 2.0 models + repositories implementando interfaces `application/ports/`. Migrations idempotentes raw SQL.
3. `application/` — services + ports (interfaces abstract). Sagas si hay orquestación multi-step.
4. `api/` — FastAPI routers + Pydantic v2 DTOs. **Thin** — delega a application services.

**Repositories PHI (paciente, appointment, medical_record, etc.) MUST:**

- Heredar de `vitalia/backend/src/modules/vitalia/_shared/repositories/phi_repository.py::PhiRepositoryBase`
- Llamar `self.validate_dual_filter(tenant_id=..., clinic_id=...)` en cada query
- Recibir `tenant_id: UUID, clinic_id: UUID` como kwargs explícitos en cada método (no implícito por session)

**Repositories no-PHI** (config, telemetría, audit) pueden heredar de `Repository` base normal o ninguna.

**Anti-patterns:**

- ❌ `session.query(Model)` (SA 1.x legacy) — usar `select(Model).where(...)` SA 2.0
- ❌ Skip dual filter "porque tenant es single-clinic"
- ❌ Inner class `Config` en DTOs Pydantic (v1 style) — usar `model_config = ConfigDict(...)`
- ❌ Endpoint sin `response_model=` (PII leak risk + arch test bloquea)
- ❌ Hard deletes — soft delete (`deleted_at`) o expungement via cron compliance

**Anchor source:** valeria-agenda 03-arch § 2-§ 5 + § 7 + `backend-ddd.md` rule.

### § 3.7 — Migrations idempotent raw SQL

- Toda migration usa `op.execute("CREATE TABLE IF NOT EXISTS ...")`, `"ALTER TABLE x ADD COLUMN IF NOT EXISTS ..."`, `"CREATE INDEX IF NOT EXISTS ..."`
- **NUNCA** `op.create_table()` / `op.add_column()` / `op.create_index()` (no idempotentes)
- **NUNCA** `sa.Enum(..., create_type=True)` (broken SA 2.0.27) — `op.execute("CREATE TYPE IF NOT EXISTS ...")` raw
- Foreign keys con `ON DELETE` policy explícita (`CASCADE` solo si business logic lo requiere)
- Verify migration idempotency vía `make verify-{brand}-migration-idempotency` (clone DB workflow per `docs/domains/migrations.md`)

**Anchor source:** valeria-agenda 03-arch § 9 + `backend-migrations.md` rule.

### § 3.8 — Telemetría (`growth_studio_event` brand-local)

- Tabla NEW per-brand: `vitalia_growth_studio_event` (NO mezcla con `copilot_trace_event` engine — eso es para LLM runtime traces)
- Schema mínimo: `(id UUID PK, tenant_id, clinic_id NULL, event_name, payload_jsonb, occurred_at, session_id NULL, user_id NULL)`
- Emitter: `vitalia/backend/src/modules/vitalia/_shared/telemetry/growth_studio_emitter.py` (ya shipped F2-S1)
- **Bucketed amounts** — montos monetarios NO se loguean verbatim; se buckeean (`0-100, 100-500, 500-2000, 2000-10000, 10000+`) para evitar PHI re-identification
- Events FE disparados vía hook `useTelemetry({ event, payload })` que POSTea a `/api/v1/telemetry/event`
- Best-effort writes — `try/except + structlog.warning` (no romper response del endpoint primario)

**Eventos canónicos por sub-tab:**

```yaml
{agent}_{subtab}_viewed         # page mount
{agent}_{subtab}_filter_applied # cambio de filtro
{agent}_{subtab}_item_created   # CTA submit success
{agent}_{subtab}_item_saved     # autosave debounce flush
{agent}_{subtab}_error          # error visible al user
```

**Anchor source:** valeria-agenda 03-arch § 10 + `metrics-expert` skill.

### § 3.9 — Tests (Vitest + Playwright + arch + a11y)

**Capas obligatorias per story sub-tab:**

| Capa | Cuántos | Path | Frecuencia |
|---|---|---|---|
| **Vitest unit** co-located | 1+ por componente con lógica no-trivial | `__tests__/` adyacente al componente | every commit |
| **Playwright funcional** | 1+ por scenario `playwright_required: true` | `vitalia/frontend/e2e/shell-organism/{subtab}-*.spec.ts` | every commit |
| **Playwright visual golden** | 3 secciones × 2 themes (light+dark) = 6 PNGs default | `vitalia/frontend/e2e/__screenshots__/{subtab}/{section}-{theme}.png` | every commit (ratchet shrink-only) |
| **axe a11y** | 1 por screen state | embedded en specs Playwright via `@axe-core/playwright` | every commit |
| **BE pytest unit** | 1+ por service/repo | `vitalia/backend/tests/modules/vitalia/{m}/` | every commit |
| **BE pytest dual-tenant** | 1+ por endpoint PHI | idem (cross-tenant + cross-clinic bloqueo) | every commit |
| **Arch fitness** EXTEND | `test_phi_dual_filter.py`, `test_audit_log_sync_write.py`, `test_response_model_required.py` | `vitalia/backend/tests/architecture/` | every commit |
| **MSW network mocks** FE | mock backend per spec en hooks | `vitalia/frontend/src/mocks/handlers/{subtab}.ts` | every commit |

**Visual golden mapping** (mandatory en `01-spec.md § Visual Goldens`):

```yaml
mockup_html: vitalia/docs/product/stories/{story-id}/mockups/{component}.html
golden_snapshot: vitalia/frontend/e2e/__screenshots__/{subtab}/{component}-{theme}.png
react_component: vitalia/frontend/src/features/{agent}/components/{subtab}/{Component}.tsx
design_contract_ref: vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md § {section}
```

**Anchor source:** valeria-agenda 03-arch § 11 + `ADR-vitalia-003-shell-mockup-per-component-protocol.md`.

---

## § 4 — Cross-cutting concerns (auto-aplican)

| Concern | Source rule | Auto-aplica |
|---|---|---|
| HIPAA-lite (dual filter, audit, retention, RBAC) | `vitalia/.claude/rules/hipaa-lite.md` | Cuando story toca paths PHI |
| Mockup-per-component gate | `vitalia/.claude/rules/shell-mockup-per-component.md` + `ADR-vitalia-003` | Cuando story crea componente UI nuevo |
| Sales-agent brand-voice anti-creep | `.claude/rules/sales-agent-brand-voice.md` | Cuando story toca voz/personality |
| Spanish neutro LatAm | `.claude/rules/spanish-text.md` | Toda copy user-facing |
| Tenant isolation raíz | `.claude/rules/tenant-isolation.md` | Toda query |
| Anti-duplication cross-brand | `.claude/rules/anti-duplication.md` | Toda creación de archivo nuevo |
| TDD mandatory | `.claude/rules/tdd-mandatory.md` | Toda implementación |
| FSD-Lite boundaries | `.claude/rules/frontend-fsd.md` | Todo FE |
| Story closure gate | `.claude/rules/story-closure-gate.md` | Todo cycle dev → audit → merge |

---

## § 5 — Capability YAML mandatory post-merge

Cada sub-tab story `done` MUST escribir un capability YAML en:

```
vitalia/docs/product/capabilities/{module}/{capability-slug}.yaml
```

Schema mínimo:

```yaml
---
capability_id: vitalia-{module}-{capability-slug}
module: {module}
slug: {capability-slug}
status: live
date_introduced: YYYY-MM-DD
story_introduced: {story-id}
package_version: x.y.z
package_path: {paths involucrados, comma-separated}
license: proprietary
---

# {Capability title}

## Surface
### Config
### Backend
### Frontend

## Test coverage
- Vitest paths
- Playwright spec paths
- BE pytest paths

## Dependencies
- engine packages consumidos
- otras capabilities brand-local

## Scenarios live
- 1-line resumen por scenario implementado
```

Sin este YAML, brand `status: shipped` queda desincronizada (per `pm-vitalia/SKILL.md § Capability inventory post-merge`).

---

## § 6 — Enforcement

### § 6.1 — Skill `/architect` REFUSE condition

`vitalia/.claude/rules/shell-feature-architecture-mandatory.md` (overlay rule auto-loaded en `vitalia/` workdir) declara:

> Toda story Vitalia `state: refined` que pase a `/architect` MUST tener en su `01-spec.md` frontmatter el campo `architecture_pattern: ADR-vitalia-004`. Sin este campo → `/architect` REFUSE arrancar.

### § 6.2 — Skill `/po-ux` checklist

`/po-ux` (cuando trabajés en story `brand: vitalia`) carga este ADR al Step 1 Bootstrap y verifica al Step 5 gate que el spec lo cite.

### § 6.3 — Auditor frontend + backend cross-check

Auditor verifica que el código entregado siga las 9 secciones. Divergencias sin justificación documentada en `03-arch.md § Architecture Decisions` → REJECT.

### § 6.4 — Architectural fitness tests EXTEND

Tests sumados a `vitalia/backend/tests/architecture/`:

- `test_phi_dual_filter.py` — TODO repo PHI hereda `PhiRepositoryBase`
- `test_audit_log_sync_write.py` — TODO endpoint PHI escribe audit_log row pre-response
- `test_response_model_required.py` — TODO endpoint declara `response_model=`
- `test_growth_studio_event_no_phi.py` — payload de events no contiene PHI

Tests sumados a `vitalia/frontend/src/__tests__/architecture/`:

- `test_no_phi_in_url_params.test.ts` — searchParams whitelist enforced
- `test_react_query_keys_convention.test.ts` — keys siguen `[module, subtab, action, ...filtersStable]`
- `test_features_no_cross_imports.test.ts` — `features/A` no importa de `features/B`

---

## § 7 — Consequences

### Positivas

- **Architect single-shot reduce 40-60%** (deja de re-decidir patrón)
- **Auditor verifica con checklist único** (9 secciones × scoring rapid)
- **Onboarding nuevo dev: 1 ADR + 1 story-ejemplo (valeria-agenda) = arch completa**
- **Cross-cutting gates (HIPAA-lite, mockups, voice) auto-aplican** vía overlay rules registradas
- **Capability inventory consistent** post-merge → portfolio auto-gen confiable

### Negativas / tradeoffs

- **Stories que necesiten divergir** pagan ceremonia (documentar rationale en `03-arch.md § Architecture Decisions`)
- **ADR becomes load-bearing** — cambios al patrón requieren bump version (`ADR-vitalia-004-v2`) + propagation a stories abiertas
- **Cross-brand reuse harder** — si nicolify quiere mismo patrón debe replicar (no hay shared `core/luana-core-shell-feature-pattern` aún). Promotion candidate futuro.

---

## § 8 — Citation requirement (template para `01-spec.md` + `03-arch.md`)

**Frontmatter de `01-spec.md`:**

```yaml
---
story_id: ...
brand: vitalia
type: ui-story
state: refining
architecture_pattern: ADR-vitalia-004      # ★ MANDATORY para sub-tab stories
---
```

**Frontmatter de `03-arch.md`:**

```yaml
---
story_id: ...
brand: vitalia
arch_version: 1
schema_version: v4.1
architecture_pattern: ADR-vitalia-004      # ★ MANDATORY
adr_004_compliance: full | partial-with-rationale
---
```

Si `adr_004_compliance: partial-with-rationale` → sección `§ Architecture Decisions` documenta qué sección del ADR se diverge + por qué + qué tradeoff se acepta.

---

## § 9 — Migration plan (stories abiertas)

Status al 2026-05-26:

| Estado | # stories | Acción |
|---|---|---|
| `idea` | 21 | Frontmatter checkpoint.md sumar `architecture_pattern: ADR-vitalia-004` (script `scripts/propagate-adr-vitalia-004.sh`) |
| `refining` | 2 (`vitalia-fase2-lisa-marca`, `vitalia-fiscal-emission-pe`) | Spec en redacción cita ADR explícito (lisa-marca: este turn; fiscal-emission-pe: cuando reanude, es service-only — exenta) |
| `refined` | 1 (`vitalia-payment-adapter-mvp`) | Service-only — exenta. Si futura iter agrega UI → re-evaluar |
| `ready` | 1 (`vitalia-fase2-valeria-agenda`) | Es la **fuente del patrón** — no cita ADR, ESTA ADR la cita verbatim como source |
| `done` (Fase 1) | varias archived | No requiere backfill (history immutable) |

---

## § 10 — Reference

- **Source story:** `vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/03-arch.md` (`/architect` Opus 4.7 single-shot 2026-05-27)
- **Cementing decision:** conversación Chris + `/po-ux` 2026-05-26 ("la arquitectura debe afectar a todas las historias")
- **Related ADRs:**
  - `ADR-vitalia-001-shared-vs-fork.md` — engine vs brand split
  - `ADR-vitalia-002-vt-deprecation-plan.md` — legacy `.vt-*` migration
  - `ADR-vitalia-003-shell-mockup-per-component-protocol.md` — mockup gate
- **Cross-references:**
  - `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` — visual SSoT
  - `vitalia/docs/specs/templates/01-spec-shell-template.md` — spec template (debe citar este ADR)
  - `.claude/rules/backend-ddd.md`, `frontend-fsd.md`, `backend-migrations.md`, `tdd-mandatory.md`
- **Overlay enforcement rule:** `vitalia/.claude/rules/shell-feature-architecture-mandatory.md`
- **Promotion candidate future:** si comunify/nicolify/lupulo adoptan shell-organism agéntico → lift pattern a `core/luana-core-shell-feature-pattern/` vía `/pm-luana` proposal.

---

## § 11 — Open questions (no bloquean accepted)

1. **Versionado del ADR:** ¿bump `ADR-vitalia-004-v2` o `ADR-vitalia-004` con changelog inline? Propuesta: changelog inline, bump solo si breaking.
2. **Storybook integration:** ¿agregar Storybook 8 al pattern para Visual Goldens? Defer a story dedicada futura `vitalia-fase2-storybook-bootstrap`.
3. **Server Actions vs React Query mutations:** valeria-agenda usa mutations. ¿Cuando Server Actions? Propuesta: form simple sin optimistic UI → Server Action; flujo multi-step con drawer/feedback → mutation. Cementar en ADR v2 cuando emerja segundo caso.

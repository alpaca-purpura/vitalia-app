# 03-arch-{be|fe|agentic}.md — Template

> Owner: `architect-orchestrator` (surface {be|fe|agentic} — instruction doc `.claude/skills/architect/references/{be,fe,agentic}.md`). Documento técnico de UNA capa.
> Lo escribe el orchestrator cargando el instruction doc de la surface. `/architect` los reúne en `06-tickets.yaml`.

---
story_id: STORY_ID
surface: BE                                       # BE | FE | AGENTIC
sub_architect: architect-orchestrator (surface BE · references/be.md)
arch_version: 1
last_modified: 2026-05-04T15:30Z
links:
  spec: "01-spec.md"
  ui_design: "01-spec.md § Wireframes"            # solo si surface=FE · 02-design-ui.md DEAD (paradigma v4) → wireframes viven en 01-spec
  agentic_design: "02-design-agentic.md"          # solo si surface=AGENTIC
  story_yaml: "../../../../../product/stories/{module}/{story-id}.yaml"
  domain_doc: "../../../../../domains/module_{module}.md"
  rules:
    - ".claude/rules/backend-ddd.md"
    - ".claude/rules/tenant-isolation.md"
    - ".claude/rules/backend-migrations.md"
---

## Prior art audit (`anti-duplication-refining.md`)

Scan cross-brand + core ANTES de diseñar (grep `core/` + brands activas):
- ¿Engine cubre el patrón? → consumir vía import `luana_core_*` (NO recrear).
- ¿Otra brand tiene algo parecido? → lift candidate → escalar `/pm-luana`.
- ¿Learning previo aplicable?

Resultado del scan (evidencia grep + decisión `consume | extend | lift | net-new`): `<...>`

## Decisión arquitectónica clave

[1 párrafo: qué se decidió, por qué (con tradeoffs).]

## Surface diff (BE)

### Endpoints nuevos / modificados

| Method | Path | Request DTO | Response DTO | Auth | Notas |
|---|---|---|---|---|---|
| POST | `/api/v1/{module}/{action}` | `RequestDTO` | `ResponseDTO` | clerk-jwt | tenant-scoped |

### DTOs

```python
# backend/src/modules/{m}/api/dtos.py
class RequestDTO(BaseModel):
    field_a: str
    field_b: int
    model_config = ConfigDict(...)

class ResponseDTO(BaseModel):
    id: UUID
    status: Literal["ok", "error"]
    model_config = ConfigDict(...)
```

### Domain entities / VOs

```python
# backend/src/modules/{m}/domain/{entity}.py
@dataclass(frozen=True)
class {Entity}:
    id: UUID
    tenant_id: UUID
    ...
```

### Migrations

```
alembic/versions/XXXX_{description}.py
- op.execute("CREATE TABLE IF NOT EXISTS ...")
- op.execute("ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...")
- op.execute("CREATE INDEX IF NOT EXISTS ...")
```

> **Verificación idempotencia:** correr migration 2x sin error.

### Servicios + Repos

| Componente | Path | Responsabilidad |
|---|---|---|
| `{Name}Service` | `application/services/` | Orquesta use case |
| `{Name}Repository` | `infrastructure/repositories/` | Persistencia |

### Eventos emitidos / consumidos

- Emite: `{Module}{Event}V1` → outbox pattern
- Consume: `{OtherModule}Event` → handler en `application/event_handlers/`

### Tests requeridos

- `tests/modules/{m}/test_{name}_service.py` — domain logic + happy/negative
- `tests/modules/{m}/test_{name}_endpoint.py` — contract test + tenant isolation
- `tests/modules/{m}/test_{name}_migration.py` — migration idempotency
- Coverage minimum: 43% (workspace threshold, no debe bajar)

## Surface diff (FE)

### Routes nuevas / modificadas

| Path | Component | Type |
|---|---|---|
| `/[module]/[section]` | `{Section}Page.tsx` | Server Component |
| `/[module]/[section]/edit` | `{Section}EditClient.tsx` | Client Component |

### Features (FSD-Lite)

```
frontend/src/features/{module}/
├── api/use-{action}.ts              # React Query hook
├── components/{Component}.tsx
├── schemas/{action}-schema.ts        # Zod
├── hooks/use-{custom}.ts
├── types/{module}.types.ts
└── config/{module}.config.ts
```

### Estado / data flow

- React Query keys: `['{module}', '{action}', tenant_id]`
- Mutations: `use{Module}{Action}Mutation` con invalidate keys
- Auth: `useAuth()` Clerk; X-Tenant-ID auto-injected via `fetchClient`

### Tests requeridos

- Vitest unit: `tests/{module}/{component}.test.tsx`
- Vitest integration: `tests/{module}/{flow}.test.tsx`
- Playwright E2E: `e2e/regression/{module}-{story}.spec.ts`
- Coverage minimum: 20% all categories (no bajar)

## Surface diff (Agentic)

### Tool definitions

```python
# backend/src/modules/{module}/tools/{tool_name}.py
@tool
async def {tool_name}(
    tenant_id: UUID,
    {param}: {type},
) -> {ReturnDTO}:
    """{Docstring para LLM — describe función + inputs + outputs claramente.}"""
    ...
```

### Prompt slots affectados

| Slot | TTL | Content | Cache invalidation |
|---|---|---|---|
| 1 (system) | 1h | identity preamble | bump version |
| 2 (tools) | 5min | tool registry | new tool added |
| 3 (task) | not cached | task instructions | per session |
| 5 (brand voice) | 1h | tenant.brand_voice | tenant change |

### State machine LangGraph

```python
graph = StateGraph(AgentState)
graph.add_node("gather_context", gather_context_node)
graph.add_node("reason", reason_node)
graph.add_node("call_tool", call_tool_node)
graph.add_node("respond", respond_node)
graph.add_edge("gather_context", "reason")
graph.add_conditional_edges("reason", route_after_reason, {
    "call_tool": "call_tool",
    "respond": "respond",
})
```

### Agentic eval suite

- Path: `backend/tests/agentic_evals/{module}/{story_id}_eval.py`
- Runner: pytest con fixture `agentic_trial`
- Personas: `docs/specs/personas/{persona}.yaml`
- Rubrics: `docs/specs/rubrics/{rubric}.md`
- Trial policy: `trials_per_scenario=3`, `pass^k_threshold=0.5`
- Cost cap por trial: $0.50

### Observabilidad

- `copilot_trace_event` per turn con `tool_calls`, `tokens`, `latency`
- `copilot_llm_call` per LLM call con `cost_usd`, `model`, `cache_hit`
- PII: `sanitize_payload` ANTES de persistir
- LangSmith / langfuse traces (si configurado)

## Integration design (CONN) — anti-isla (Critical Rule #33 · `anti-orphan-integration.md`)

> Ninguna salida de esta story llega a `done` como isla. Declarar las 4 contenciones CONN con valores CONCRETOS:

- **C — Consumed:** ≥1 consumidor real. Quién consume esta salida: `<...>`
- **O — On the map:** vive en un `capability` YAML con hogar declarado. `cap_target: <...>` · zona derivada (Agentes | Plataforma | Infraestructura): `<...>`
- **N — Navigable/reachable:** camino de acceso explícito (reachability path CONCRETO, no abstracto): `<entrada → … → salida>`
- **N — Notarized/registered:** punto donde el runtime lo descubre: `<include_router | nav tree | tool registry | Extension SDK EP-N | DI provider>`

Sin esta sección con un reachability path concreto, `/architect` NO cierra `state: ready`.

## Cross-cutting concerns

- **Tenant isolation:** confirmar `tenant_id` filter en cada query
- **Idempotency:** key strategy si aplica
- **Rate limiting:** N/min por tenant
- **Caching:** Redis keys + TTL si aplica
- **Backwards compatibility:** ¿existing data migra OK?

## Riesgos y mitigaciones

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Migration lenta en prod | high | Feature flag + chunked migration |
| Tool LLM costo alto | medium | Cap por session + tier pricing |

## ★ Test Construction Plan (v4.1 cement 2026-05-19 — mandatory para stories funcionales)

> El architect dicta CÓMO construir las pruebas (orden, POMs, fixtures, mapping).
> Dev-team CONSTRUYE siguiendo este plan, NO inventa estructura ni orden.

### Playwright required

`playwright_required: true | false`

`true` SIEMPRE para stories ui-story o ui-mixed. `false` solo para service-only stories sin surface FE.

### Creation order (numerado, con dependencias)

| Step | File | Content | Depends on |
|---|---|---|---|
| 1 | `{brand}/frontend/e2e/fixtures/{story-id}.fixture.ts` | Fixtures compartidos — Clerk auth state, tenant setup, DB seed minimal, network mocks | [] |
| 2 | `{brand}/frontend/e2e/regression/{story-id}/poms/{m}-list-page.pom.ts` | POM lista {m} | [1] |
| 3 | `{brand}/frontend/e2e/regression/{story-id}/poms/{m}-detail-page.pom.ts` | POM detail {m} | [1] |
| 4 | `{brand}/frontend/e2e/regression/{story-id}/{m}-happy.spec.ts` | Scenario happy — usa POMs | [2,3] |
| 5 | `{brand}/frontend/e2e/regression/{story-id}/{m}-negative.spec.ts` | Scenario negative | [2,3] |
| 6 | `{brand}/frontend/e2e/regression/{story-id}/{m}-edge.spec.ts` | Sub-categorías: race, concurrent, empty, large, network failure | [2,3] |
| 7 | `{brand}/frontend/e2e/regression/{story-id}/{m}-adversarial.spec.ts` | Scenario adversarial | [2,3] |
| 8 | `{brand}/frontend/e2e/a11y/{story-id}.spec.ts` | Accessibility axe-core scan | [4] |
| 9 | `{brand}/frontend/e2e/i18n/{story-id}.spec.ts` | i18n con 3 fixtures tenants distintos | [4] |

### Scenario → test mapping (verbatim)

| Gherkin scenario (01-spec.md) | Test file | Test function | Assertions clave |
|---|---|---|---|
| Scenario 1 — happy-path | `{story-id}/{m}-happy.spec.ts` | `test('user creates {entity} successfully'` | toast "{entity} guardada", URL contains /detail/, DB row exists |
| Scenario 2 — negative | `{story-id}/{m}-negative.spec.ts` | `test('rejects empty required field'` | form errors "Campo requerido", NO DB row |
| Scenario 3 — edge | `{story-id}/{m}-edge.spec.ts` | `test('handles standard edge case'` | ... |
| Scenario 4 — adversarial | `{story-id}/{m}-adversarial.spec.ts` | `test('rejects cross-tenant access'` | request as B for A → 404, no leak en body |
| Scenario 5 — race_condition | `{story-id}/{m}-edge.spec.ts` | `test('handles concurrent create same slug'` | second request → 409/422, DB 1 row |
| Scenario 6 — concurrent_users | `{story-id}/{m}-edge.spec.ts` | `test('tenant isolation under concurrent load'` | A ve solo A's, B ve solo B's |
| Scenario 7 — network_failure | `{story-id}/{m}-edge.spec.ts` | `test('shows retry on 500'` | error UI visible, retry button, no data loss |
| Scenario 8 — empty_state | `{story-id}/{m}-edge.spec.ts` | `test('renders empty state with CTA'` | illustration + heading + CTA visible |
| Scenario 9 — large_dataset | `{story-id}/{m}-edge.spec.ts` | `test('pagination handles 1000 items'` | scroll smooth, p95 < 200ms |
| Scenario 10 — accessibility | `{story-id}/a11y/{story-id}.spec.ts` | `test('axe-core wcag2aa pass'` | 0 critical/serious violations |
| Scenario 11 — i18n | `{story-id}/i18n/{story-id}.spec.ts` | `test('renders correct currency per tenant'` | AR=$ARS, MX=$MXN, CL=$CLP |

### POMs requeridos (Page Object Models)

```typescript
// {brand}/frontend/e2e/regression/{story-id}/poms/{m}-list-page.pom.ts
export class {M}ListPage {
  constructor(private page: Page) {}
  async goto() { await this.page.goto('/{m}'); }
  async filterBy(criteria: Filters) { ... }
  async clickCreateButton() { ... }
  async getRowCount(): Promise<number> { ... }
  async getRowByName(name: string): Promise<Locator> { ... }
}

// {brand}/frontend/e2e/regression/{story-id}/poms/{m}-detail-page.pom.ts
export class {M}DetailPage {
  constructor(private page: Page) {}
  async goto(id: string) { ... }
  async fillForm(data: FormData) { ... }
  async submit() { ... }
  async getErrorMessage(): Promise<string | null> { ... }
}
```

### Fixtures requeridos

```typescript
// {brand}/frontend/e2e/fixtures/{story-id}.fixture.ts
export const test = base.extend({
  // Clerk auth state per role
  authedAs: async ({ context }, use) => {
    await use(async (role: 'admin' | 'user') => {
      await context.storageState({ path: `playwright/.clerk/${role}.json` });
    });
  },
  // DB seed for the tenant
  dbSeed: async ({ page }, use) => {
    await use(async (m: string, count: number) => {
      await page.request.post(`${API}/test/seed`, { data: { m, count } });
    });
  },
  // Network failure simulation
  networkFailure: async ({ page }, use) => {
    await use(async (endpoint: string) => {
      await page.route(endpoint, route => route.fulfill({ status: 500 }));
    });
  },
});
```

### Acceptance graders (paths verbatim para dev-team)

- `cd {brand}/frontend && E2E_BASE_URL=http://localhost:300X npx playwright test --grep "{story-id}"`
- `cd {brand}/frontend && npx playwright test e2e/a11y/{story-id}.spec.ts`
- `cd {brand}/frontend && npx playwright test e2e/i18n/{story-id}.spec.ts`

## Decisiones registradas

- **2026-05-04** — usar `idempotency-key` header vs natural key. Razón: requests con payload variable.
- ...

## Próximo paso (si soy /architect-X sub-arquitecto)

`done -> 03-arch-{surface}.md` (devuelvo referencia al orchestrator /architect).

## Próximo paso (si soy /architect orchestrator)

Reúno los 03-arch-* paralelos y produzco `06-tickets.yaml` con tickets ordenados, dependencias, owner_eligibility (qwen vs opus), acceptance criteria + gherkin_coverage (post 2026-05-18 mandatory).

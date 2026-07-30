---
story_id: estabilizar-harness-e2e-lisa-marca
brand: vitalia
type: bugfix
arch_version: 1
schema_version: v4.1
architecture_pattern: ADR-vitalia-004
adr_004_compliance: bugfix-lite-na   # NO es sub-tab nueva — bugfix de harness + 2 sub-bugs de auth-header
verification_nature: ambas           # técnica (grep-gates + asserts) + funcional (flujos lisa-marca REAL)
architect_run_on: 2026-06-02
cap_target: lisa-marca
cap_change_type: fix
autonomous_mode: false               # propuesto; Chris ratifica al spawnear /dev-team
---

# Contract · estabilizar-harness-e2e-lisa-marca (bugfix-lite · harness honesto + determinista)

> **Naturaleza:** bugfix-lite del **harness E2E** de lisa-marca + 2 fixes de auth-header acotados.
> NO hay UI nueva. El "producto" bajo prueba ya existe (cap `brand_studio/lisa-marca` shipped). Esta story
> hace que su suite sea **honesta** (backend real, no mock del backend-bajo-prueba) y **determinista**
> (asserts web-first, sin listeners dangling). Diseñado sobre el **root-cause FRESCO** del re-repro
> 2026-06-02 (la race de Clerk auth-readiness está RESUELTA/stale — NO se diseña Clerk-ready gate ni query
> resiliente; esas direcciones quedaron obsoletas).

## 0. Context Summary

- **Story:** `estabilizar-harness-e2e-lisa-marca` (F2 · módulo `brand_studio` · cap `lisa-marca` · agent_owner `lisa`).
- **Architect run on:** 2026-06-02.
- **Tipo:** bugfix-lite (ADR-011). `adr_004_compliance: bugfix-lite-na` — NO es sub-tab nueva, NO exige las 9 secciones de ADR-vitalia-004 (gate `shell-feature-architecture-mandatory.md § NO aplica`: "bugfix del harness").
- **Modules touched:** `brand_studio` (FE tests + 1 FE-prod api-layer + 1 BE GET endpoint + 1 cap YAML). Cero engine. Cero otra brand. Cero PHI runtime (los flujos son brand-config, no clínicos).
- **Surface → builder → auditor mapping** (PM usa para spawnear los agentes):

  | Surface | Path raíz | Builder | Auditor |
  |---|---|---|---|
  | FE-tests (de-mock 11 specs + POMs web-first + fixture forwarding compartida + des-quarantine 5 fixme) | `vitalia/frontend/e2e/regression/{vitalia-fase2-lisa-marca,arreglar-guardado-voz-y-tono}/` | **`builder-frontend`** (Sonnet) | **`auditor-frontend`** (Opus) |
  | FE-prod sub-bug #2 (actor audit real) | `vitalia/frontend/src/features/lisa/api/marca-voice-api.ts` | **`builder-frontend`** (Sonnet) | **`auditor-frontend`** (Opus) |
  | BE sub-bug #1 (X-User-ID opcional en GET prohibited-phrases) | `vitalia/backend/src/modules/vitalia/brand_studio/api/routers/marca_router.py` | **`builder-backend`** (Sonnet) | **`auditor-backend`** (Opus) |
  | Docs cap re-cable | `vitalia/docs/product/capabilities/brand_studio/lisa-marca.yaml` | **`builder-frontend`** (Sonnet) | **`auditor-frontend`** (Opus) |

  > **Por qué Sonnet en todos:** ninguna superficie es agentic production_code (R23 no aplica — no toca `copilot/`/`sales_agent/`). FE-tests + FE-prod + cap docs → Sonnet/builder-frontend; BE endpoint → Sonnet/builder-backend.

- **Skills consultados (decisión tomada de cada uno):**
  - `frontend-expert` (+ `playwright-expert` SSoT E2E) → **forwarding pattern + base.ts + web-first asserts**; el de-mock NO migra el transporte a proxy Next (heredado, out-of-scope); lift del forwarding a fixture compartida (anti-duplicación).
  - `backend-expert` → sub-bug #1: `X-User-ID` opcional en el GET `prohibited-phrases` (read por tenant+país; el `user_id` ya estaba inusado en el body); `response_model=` se mantiene; tenant-isolation intacta.
  - `brand-expert` → contexto cap `lisa-marca` (PersonalityProfile/BrandIdentity engine-consumed); el actor del audit-log del PATCH personality debe ser el usuario real (HIPAA-lite "quién").
- **CONTEXT-BRIEF source:** sin CONTEXT-BRIEF (story chica, brief skipped); **self-ran greps Path B** + re-repro fresco del checkpoint § Re-repro 2026-06-02 (evidencia con paths:líneas verbatim).
- **capability YAML affected (post-merge):** `vitalia/docs/product/capabilities/brand_studio/lisa-marca.yaml` (re-cablear `e2e_test` → specs honestos + `verified_real`; bajar a `partial`/`declared` los scenarios sin spec honesto). `modules/brand_studio.md`: sin cambio narrativo (no hay capability nueva).
- **Architecture gates que deben seguir verdes:** `vitalia/backend/tests/architecture/` (sub-bug #1 toca un router — `test_response_model_required.py` + `test_brand_studio_module_ddd.py` + tenant-isolation); `vitalia/frontend/src/__tests__/architecture/` (sub-bug #2 toca api-layer FE — no debe romper boundaries FSD). Los grep-gates nuevos (SC-2/3/5) son **arch-fitness de harness** (ver § 12).

## Prior art audit (anti-duplication-refining)

- **Engine consumed:** ninguno nuevo. El runtime-error gate `vitalia/frontend/e2e/fixtures/base.ts` ya existe (creado 2026-06-01 por rule #37) → se **adopta**, no se construye.
- **Forwarding a backend real:** el patrón `page.route("**/api/v1/**")` → `page.request.fetch(:8002)` YA existe inline en `arreglar-guardado-voz-y-tono/{voz-arquetipo,voz-bloque}.spec.ts` (story padre). **Decisión NO-NEW-LAYER (ver § Existing systems audit):** **LIFT** ese forwarding a una fixture compartida `e2e/fixtures/real-backend-forward.fixture.ts` consumida por los 11 specs de-mockeados + los specs padre des-quarantined. Copiar el bloque 11+ veces = duplicación prohibida.
- **Cross-brand:** la suite e2e es per-brand. El helper `waitForSelectedArchetype`/asserts web-first es candidato lift cross-brand → **NO lift ahora** (anotar; escalar a `/pm-luana` solo si comunify replica). No hay mirror cross-brand a romper.
- **Learnings aplicados:** `vitalia/docs/learnings/2026-05-31-e2e-mockeado-verde-falso.md` (false-green origen) + `vitalia/docs/learnings/2026-06-01-fe-tenant-from-clerk-org-systemic.md` (`14af22b2` resolvió la race → root-cause viejo stale).

## Existing systems audit (NO NEW LAYER rule)

### Source of evidence
- [x] Self-run greps (Path B — fallback; no hubo CONTEXT-BRIEF para esta story chica)
- [x] Re-repro fresco (checkpoint § Re-repro 2026-06-02) con paths:líneas verbatim

### Audit cross-module ejecutado
```bash
# 1. Forwarding a real BE — ¿ya existe? ¿shared o inline?
grep -rln 'page.route("\*\*/api/v1/\*\*"\|page.request.fetch' vitalia/frontend/e2e/
#   → SOLO en arreglar-guardado-voz-y-tono/{voz-arquetipo,voz-bloque}.spec.ts (inline, NO shared)
# 2. ¿Hay fixture compartida que forwardee a :8002?
grep -rln "page.request.fetch\|VITALIA_BE_URL\|localhost:3002.*8002" vitalia/frontend/e2e/fixtures/
#   → vacío (forwarding NO está lifteado a fixture aún)
# 3. anti-burbuja gate — ¿ya existe?
ls vitalia/frontend/e2e/fixtures/base.ts   # → existe (rule #37 layer 7)
# 4. X-User-ID opcional en marca_router GET — ¿precedente?
grep -n 'Header(alias="X-User-ID", default' vitalia/backend/src/modules/vitalia/brand_studio/api/routers/marca_router.py
#   → ninguno (X-User-ID hoy siempre required en ese GET)
# 5. Resolución Clerk userId → IAM UUID (para sub-bug #2)
grep -rn "_resolve_user_uuid\|clerk_id == \|get_by_clerk_id" vitalia/backend/src/modules/vitalia/iam/ core/luana-core-iam/src/
#   → ClinicResolver._resolve_user_uuid(session, clerk_sub) YA resuelve clerk_id → users.id
```

### Sistemas existentes encontrados
| Sistema | Path | Estado | Decisión |
|---|---|---|---|
| Forwarding a real BE (inline) | `arreglar-guardado-voz-y-tono/voz-{arquetipo,bloque}.spec.ts` | active, inline duplicado | **LIFT** a `e2e/fixtures/real-backend-forward.fixture.ts` (shared) |
| Anti-burbuja gate | `e2e/fixtures/base.ts` | active | **EXTEND/ADOPT** (composición `mergeTests`) |
| Mock del backend-bajo-prueba | `vitalia-fase2-lisa-marca/fixtures/lisa-marca.fixture.ts` (`setupLisaMarcaMocks`) | active, **es el bug** | **REPLACE** por forwarding shared (de-mock) |
| Audit actor resolver (clerk→UUID) | `iam/.../clinic_resolver.py::_resolve_user_uuid` | active | **CONSUME** (no recrear) — informa la decisión de sub-bug #2 |

### Decisión por sistema
- **Forwarding inline → LIFT shared fixture.** Justificación: duplicar el bloque de forwarding en 11 specs + 3 padre = exactamente el anti-pattern. La fixture `real-backend-forward.fixture.ts` encapsula el `page.route("**/api/v1/**")` → `page.request.fetch(BACKEND_API_URL)` una vez; todos los specs la consumen (composición con `base.ts` + auth via `mergeTests`).
- **base.ts → ADOPT** (composición, no recrear).
- **`setupLisaMarcaMocks` → REPLACE.** El mock del backend-bajo-prueba es el false-green; se elimina y los specs corren contra BE real.
- **`_resolve_user_uuid` → CONSUME (no recrear).** Es la prueba de que el actor real existe en el sistema. NO se crea resolver nuevo; ver decisión de sub-bug #2 abajo.

## § Integration design (CONN) — hogar + reachability del harness

> Esta story NO crea funcionalidad user-reachable nueva — el "consumidor" es la **suite de verificación**.
> CONN se interpreta para un bugfix de harness:

- **C — Consumed:** los specs de-mockeados los corre `gate-runner` / `/dev-team` / `/auditor` (suite real); el GET `prohibited-phrases` (sub-bug #1) lo consume `VozTonoView.tsx` (browser real); el actor audit (sub-bug #2) lo consume `vitalia_audit_log`.
- **O — On the map:** el "hogar" es el cap `brand_studio/lisa-marca`. La story re-cablea sus `e2e_test` → specs honestos (SC-8). No hay cap nueva.
- **N — Navigable/reachable:** la reachability es **cap → e2e_test real**. Hoy los `e2e_test` de los scenarios `status:live` apuntan a specs mockeados (isla de verificación falsa). Post-story, cada `e2e_test` apunta a un spec que ejerce la acción real → reachable de verdad.
- **N — Notarized/registered:** los specs ya están registrados en el project `smoke` (`playwright.config.ts` testMatch `/.*\/e2e\/regression\/.*\.spec\.ts/`). La fixture shared se exporta desde `e2e/fixtures/`. El sub-bug #1 (GET endpoint) ya está montado en `marca_router` (`include_router`). El sub-bug #2 (api-layer) ya está cableado en `usePersonalityAutosave`.

**No hay isla:** ningún archivo nuevo queda sin consumidor (la fixture la consumen los specs; los specs los corre el gate; el cap los referencia).

---

# PARTE A — FE-tests (de-mock 11 specs + des-quarantine 5 fixme + fixture forwarding + POMs web-first)

> Owner: `builder-frontend` (Sonnet). Auditor: `auditor-frontend` (Opus). Skills: `playwright-expert` (SSoT) + `frontend-expert`.

## A.1 Fixture compartida de forwarding a backend real (LIFT — NEW shared file)

**Path:** `vitalia/frontend/e2e/fixtures/real-backend-forward.fixture.ts` (NEW — lift del inline de la story padre).

**Responsabilidad:** encapsular (1) auth via Clerk storageState + `setupClerkTestingToken`, (2) forwarding `page.route("**/api/v1/**")` → `page.request.fetch(BACKEND_API_URL)`, (3) composición con el gate anti-burbuja `base.ts`.

**Contrato (qué exporta):**
```ts
// Composición: anti-burbuja (base.ts) + auth (storageState) + forwarding a :8002.
// import { test, expect } from '../../fixtures/real-backend-forward.fixture';
export const test: TestType<RealBackendFixtures, ...>;   // page autenticada + forwardeada + anti-burbuja
export const expect;
export const TENANT_ID: string;       // E2E_TENANT_ID ?? VITALIA_PE_TENANT_ID (tenant real que el user Clerk posee)
export const BACKEND_API_URL: string; // VITALIA_BE_URL ?? NEXT_PUBLIC_API_URL ?? "http://localhost:8002"
```

**Reglas (RN-1, RN-2, RN-6):**
- Tenant = `process.env.E2E_TENANT_ID` (el tenant que el usuario Clerk autenticado posee). NUNCA slug ficticio (`clinica-salud-vitalia-pe-test`).
- El forwarding **NO** inyecta headers de auth canned distintos de los que el browser real manda (excepción RBAC: el forwarding puede normalizar `X-User-Role: owner` para PATCH si el browser real ya lo manda vía api-layer — pero **NO** `X-User-ID` inyectado a mano para enmascarar el 422 de prohibited-phrases; ese contrato se arregla en BE, ver Parte C).
- Composición con `base.ts`: `import { mergeTests } from '@playwright/test'` + `mergeTests(runtimeGate, ...)` para que el gate anti-burbuja (pageerror/console/4xx-5xx/overlay) corra en todos los specs de-mockeados.

**Anti-pattern prohibido en esta fixture:** `route.fulfill()` con data canned sobre `**/api/v1/lisa/marca/{identity,visuals,personality}**` (es el false-green que origina la story).

## A.2 De-mock de los 11 specs `vitalia-fase2-lisa-marca/*.spec.ts`

Para cada spec: (a) reemplazar `import { test, expect } from './fixtures/lisa-marca.fixture'` (mockeada) + `import ... from '@playwright/test'` por `import { test, expect, TENANT_ID } from '../../fixtures/real-backend-forward.fixture'`; (b) eliminar todo `route.fulfill()` inline sobre identity/visuals/personality; (c) los asserts que dependían de seed canned (`LISA_MARCA_FIXTURE.identity.brandName`) → asserts **tolerantes al estado real** (leer lo que el BE devuelve, como hace el template padre línea 177); (d) escrituras (autosave) → ejercer la acción real + assert efecto (badge `saved` + persiste tras reload web-first).

| Spec | Scenario cap | Naturaleza del de-mock | Mock legítimo a preservar |
|---|---|---|---|
| `lisa-marca-identidad-autosave.spec.ts` | admin-configura-identidad | forwarding real + assert badge saved (no canned) | — |
| `lisa-marca-voice-warning.spec.ts` | voz-frase-prohibida-warning-soft | forwarding real + warning soft real | — |
| `lisa-marca-logo-upload-size.spec.ts` | logo-excede-tamano-maximo | validación client-side (no toca BE) + comprimido procede real | — |
| `lisa-marca-cross-tenant.spec.ts` | edicion-cross-tenant-bloqueada | PATCH adulterado → BE 403 real (tenant-isolation) | — |
| `lisa-marca-race-autosave.spec.ts` | autosave-concurrente-dos-tabs | last-write-wins real (DB) | — |
| `lisa-marca-concurrent-owners.spec.ts` | edicion-concurrente-dos-owners | dos contexts reales, audit rows distintos | — |
| `lisa-marca-autosave-timeout.spec.ts` | autosave-timeout-con-reintento | **inyección de timeout/503 = MOCK LEGÍTIMO** (no es happy-path del BE) → `test.use({ failOnRuntimeError: false })` | sí (timeout inyectado) |
| `lisa-marca-empty-state.spec.ts` | tenant-nuevo-empty-state | tenant real sin datos → empty state real (o tolerar estado del tenant E2E) | — |
| `lisa-marca-large-dataset.spec.ts` | render-perf-gran-volumen | render real (perf) | — |
| `lisa-marca-keyboard.spec.ts` | navegacion-teclado | a11y real sobre la página real | — |
| `lisa-marca-i18n.spec.ts` | copy-espanol-neutro | copy real de la página | — |

> **Nota seed-dependency:** los specs que asertaban seed canned (`brandName === "Salud Vitalia"`) NO pueden asertar un valor fijo contra el tenant E2E real. Patrón: **leer el valor actual del BE primero, editar, asertar que el editado persiste** (round-trip) — exactamente como `voz-arquetipo-autosave.spec.ts` hace con el arquetipo (lee inicial → switch al "otro" → assert). El builder NO debe inventar seed; ejerce round-trips contra lo que el tenant real tenga.

## A.3 POMs web-first (el FIX REAL de determinismo — RN-3)

**Path POM principal:** `vitalia/frontend/e2e/regression/vitalia-fase2-lisa-marca/poms/voz-tono-section.pom.ts` (y los POMs `identidad-section.pom.ts`, `presencia-section.pom.ts`, `lisa-marca-page.pom.ts` análogos).

**Cambio cardinal:** reemplazar **once-reads de estado hidratado** por **asserts web-first con polling**. El defecto raíz (re-repro B3): `getSelectedArchetype()` lee `data-selected="true"` UNA vez → null determinista porque el GET no hidrató.

| Método actual (once-read) | Método nuevo (web-first) | Patrón |
|---|---|---|
| `getSelectedArchetype(): Promise<slug \| null>` (lee 1 vez) | **`waitForSelectedArchetype(slug, {timeout})`** | `await expect(card(slug)).toHaveAttribute("data-selected","true",{timeout:15_000})` |
| `getAutosaveBadgeText()` (textContent) | mantener para diagnóstico, PERO los asserts de estado usan `expect(badge).toHaveAttribute("data-state","saved",{timeout})` (ya existe `waitForAutosaveSaved` polling) | web-first matcher |
| cualquier `getAttribute`/`textContent`/`inputValue` sobre estado del GET | `expect(locator).toHave*({timeout})` | auto-retry |

> El POM template de la story padre (`arreglar-guardado-voz-y-tono/poms/voz-tono-section.pom.ts`) ya tiene `waitForAutosaveSaved` con polling (línea 257) — ese es el patrón correcto. El de-mock lo extiende a `getSelectedArchetype` → `waitForSelectedArchetype`.
>
> **Research (accessed 2026-06-02):** Playwright web-first assertions (`expect(locator).toHaveAttribute(...)`) auto-retry hasta el timeout; preferirlas sobre `getAttribute`/`textContent` es la guía canónica anti-flake (ver § 15). Knowledge cutoff Jan 2026; verificado live hoy — API estable de larga data.

## A.4 Sin listeners dangling (RN-4 — el flake real B4)

**Path:** `vitalia/frontend/e2e/regression/arreglar-guardado-voz-y-tono/voz-arquetipo-autosave.spec.ts:251-275` (y cualquier `page.on` análogo en los de-mockeados).

**Defecto:** `authedPage.on("response", () => void pom.getAutosaveStatus().then(...))` sin `page.off` → corre durante teardown → `Target page has been closed`.

**Fix:** eliminar el fire-and-forget. Para asertar "el badge NUNCA llegó a `error`" sin listener dangling, usar una de:
- (a) `await expect(badge).not.toHaveAttribute("data-state","error")` después de `waitForAutosaveSaved()` (el estado final ya no es error si llegó a `saved`), o
- (b) si se necesita observar transiciones: registrar el listener con cleanup explícito (`const handler = ...; page.on("response", handler); ... ; page.off("response", handler)`) **antes** del teardown.

**Prohibido:** `page.on(...)` con callback `void promise` sin `page.off`/cleanup.

## A.5 Des-quarantine los 5 `authTest.fixme` (SC-4 · RN-3)

Los `authTest.fixme(...)` de `arreglar-guardado-voz-y-tono/*.spec.ts` (reload-persist arquetipo + bloque, etc.) se quarantinaron asumiendo la race de Clerk **que ya no existe**. Se des-quarantinan reemplazando sus asserts once-read por web-first:
- `authTest.fixme("persiste en recarga (Sage) ...")` (voz-arquetipo:236) → `authTest(...)` con `await pom.waitForSelectedArchetype("sage")` post-reload (en vez de `getSelectedArchetype()` once-read).
- Análogos en `voz-bloque-autosave.spec.ts` (bloque persiste tras reload) usan `expect(textarea).toHaveValue(..., {timeout:15_000})` (ya pollea — solo des-fixme).

> El builder debe correr `--repeat-each=5 --workers=1` contra backend real para confirmar 5/5 determinista antes de cerrar (re-repro confirmó 5/5 con el fix web-first).

---

# PARTE B — Docs (re-cablear cap `lisa-marca.yaml`)

> Owner: `builder-frontend` (Sonnet) o `haiku`. Auditor: `auditor-frontend` (Opus).

## B.1 Re-cableado de `e2e_test` → specs honestos (RN-7 · SC-8 · AC-4)

Para cada scenario `status: live` del cap `vitalia/docs/product/capabilities/brand_studio/lisa-marca.yaml`:
- Si su `e2e_test` apunta a un spec **de-mockeado en esta story** → mantener el path + poblar `verified_real` (con la evidencia del run real: PATCH/GET 200 + efecto observado).
- Si su `e2e_test` apunta a un spec que **aún mockea el backend-bajo-prueba** y NO se de-mockea acá → bajar `status: live` → `status: partial` (o `declared`) con `verified_real: null` (no puede estar `live` cableado a un mock — RN-7).

| Scenario | e2e_test actual | Acción post-de-mock |
|---|---|---|
| admin-configura-identidad-clinica | `…/lisa-marca-identidad-autosave.spec.ts` (mockeado) | de-mockeado → `verified_real` poblado |
| admin-define-voz-y-tono | `…/arreglar-guardado-voz-y-tono/voz-arquetipo-autosave.spec.ts` (real, ya verified) | mantener `verified_real` existente + des-quarantine reload |
| admin-configura-presencia-web | `null` | sin spec honesto → `status: partial` (declarado, sin e2e real) |
| voz-frase-prohibida-warning-soft | `…/lisa-marca-voice-warning.spec.ts` | de-mockeado → `verified_real` poblado |
| logo-excede-tamano-maximo | `…/lisa-marca-logo-upload-size.spec.ts` | de-mockeado → `verified_real` poblado |
| edicion-cross-tenant-bloqueada | `…/lisa-marca-cross-tenant.spec.ts` | de-mockeado → `verified_real` poblado |
| autosave-concurrente-dos-tabs | `…/lisa-marca-race-autosave.spec.ts` | de-mockeado → `verified_real` poblado |
| edicion-concurrente-dos-owners | `…/lisa-marca-concurrent-owners.spec.ts` | de-mockeado → `verified_real` poblado |
| autosave-timeout-con-reintento | `…/lisa-marca-autosave-timeout.spec.ts` | de-mock (timeout inyectado = mock legítimo) → `verified_real` poblado |
| tenant-nuevo-empty-state | `…/lisa-marca-empty-state.spec.ts` | de-mockeado → `verified_real` poblado |
| render-perf-gran-volumen-marca | `…/lisa-marca-large-dataset.spec.ts` | de-mockeado → `verified_real` poblado |
| navegacion-teclado-marca | `…/lisa-marca-keyboard.spec.ts` | de-mockeado → `verified_real` poblado |
| copy-espanol-neutro-marca | `…/lisa-marca-i18n.spec.ts` | de-mockeado → `verified_real` poblado |

> **`change_log` entry (post-merge):** agregar `{story_id: estabilizar-harness-e2e-lisa-marca, type: fix, summary: "Harness honesto: de-mock 11 specs lisa-marca (backend real, no mock del backend-bajo-prueba) + asserts web-first deterministas + base.ts anti-burbuja; sub-bug #1 (GET prohibited-phrases X-User-ID opcional) + sub-bug #2 (actor audit real); re-cable e2e_test → specs verificados real", merge_sha: <TBD>}`.

---

# PARTE C — BE (sub-bug #1 · X-User-ID opcional en GET prohibited-phrases)

> Owner: `builder-backend` (Sonnet). Auditor: `auditor-backend` (Opus). Skill: `backend-expert`.

## C.1 El bug (re-repro B6 · SC-7 · AC-5)

`GET /api/v1/lisa/marca/prohibited-phrases` exige `user_id: str = Header(alias="X-User-ID")` (marca_router.py:584) pero el `fetchClient` FE **no inyecta** `X-User-ID` en GETs → browser real responde **422**. El e2e lo enmascaraba inyectando el header a mano. `user_id` **nunca se usa** en el body del endpoint (es un read por `tenant_id` + `country`).

## C.2 El fix (mínimo, idempotente, tenant-isolation intacta)

En `marca_router.py::get_prohibited_phrases` (líneas 582-602):

```python
@router.get(
    "/prohibited-phrases",
    response_model=ProhibitedPhrasesListDTO,   # ← se MANTIENE (PII allowlist)
    summary="List seed defaults + tenant overrides (soft warning UI)",
)
async def get_prohibited_phrases(
    tenant_id: str = Header(alias="X-Tenant-ID"),        # ← sigue REQUIRED (tenant-isolation)
    user_id: str | None = Header(alias="X-User-ID", default=None),  # ← OPCIONAL (read, no audita actor)
    country: str | None = Query(default=None, max_length=2, ...),
    session: AsyncSession = Depends(_get_db),
) -> ProhibitedPhrasesListDTO:
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid tenant_id") from exc
    # user_id NO se parsea ni se usa: es un read tenant+país, sin actor para auditar un listado.
    bundle = _build_service(session)
    return await bundle.voice_blocklist.list_for_tenant(tenant_id=tenant_uuid, country=country)
```

**Invariantes preservadas:**
- `X-Tenant-ID` sigue **required** → tenant-isolation intacta (RN-6).
- `response_model=ProhibitedPhrasesListDTO` se mantiene → arch gate `test_response_model_required.py` verde + PII allowlist.
- Es un **GET** (read) → NO escribe audit_log → NO necesita actor (HIPAA-lite audit aplica a writes/reads-de-PHI; esto es brand-config no-PHI).
- Cambio **NO toca** los PATCH/POST/DELETE (esos siguen exigiendo `X-User-ID` para el audit actor).

**Scope discipline:** NO tocar `core/`. NO tocar otros endpoints del router. NO flipear ningún default flag (ver § 9.5).

---

# PARTE D — FE-prod (sub-bug #2 · actor audit real · HIPAA-lite "quién")

> Owner: `builder-frontend` (Sonnet). Auditor: `auditor-frontend` (Opus). Skills: `frontend-expert` + `brand-expert`.

## D.1 El bug (re-repro B5 · SC-6 · AC-3 · RN-5)

`vitalia/frontend/src/features/lisa/api/marca-voice-api.ts:112-113` manda como actor del audit-log:
```ts
const mutationHeaders = { "X-User-ID": opts.tenantId, "X-User-Role": opts.userRole ?? "owner" };
```
→ las filas de `vitalia_audit_log` de los PATCH de marca registran el **tenant UUID** como actor, no el usuario real. Degrada la fidelidad HIPAA-lite del "quién".

## D.2 Restricción dura descubierta (NO ignorar) — el actor del audit debe ser un UUID

El BE escribe el audit con `CAST(:user_id AS uuid)` (`audit_writer.py:105`) y los PATCH parsean `user_uuid = UUID(user_id)` (`marca_router.py:374,241,292`). **El Clerk `useAuth().userId` es `user_2abc...` — NO un UUID.** Plumbear el Clerk userId crudo al `X-User-ID` → **422 / CAST falla**. El actor HIPAA-lite-correcto es el **IAM `users.id` UUID** (resuelto desde `users.clerk_id == clerk_sub`; resolver canónico = `iam/.../clinic_resolver.py::_resolve_user_uuid`, que se CONSUME, no se recrea).

`publicMetadata` del usuario hoy lleva `{role, tenant_id, clinicId}` — **NO** el IAM `users.id`. Entonces el FE no tiene hoy el UUID del actor para plumbear directo.

## D.3 Decisión arquitectónica (Architecture Decision — sub-bug #2)

**Opción elegida: D2-be-resolves-actor — el BE resuelve el actor desde la identidad autenticada (Bearer JWT), NO desde un header FE-supplied.**

Rationale:
- El header `X-User-ID` FE-supplied es **spoofeable** y hoy lleva el dato equivocado (tenant). El actor de un audit HIPAA-lite NUNCA debe venir de un header que el cliente controla — debe derivarse de la identidad autenticada (el `clerk_sub` del Bearer JWT que el FE ya manda).
- El BE ya tiene el resolver canónico `_resolve_user_uuid(clerk_sub) → users.id`. El PATCH personality debe resolver el actor desde el JWT (`clerk_sub`) → `users.id` UUID, en vez de confiar en `X-User-ID`.
- Esto cierra RN-5/AC-3 de verdad (fila audit con `user_id = users.id` real, ≠ tenant_id) sin romper el RBAC (`require_brand_owner_access` lee `X-User-Role`, ortogonal al actor).

**Pero el scope ratificado por Chris ubica sub-bug #2 como ticket FE-prod (`marca-voice-api.ts`).** Tensión real entre "plumbear el userId en el FE" (scope) y "el BE no acepta un userId no-UUID" (restricción). Resolución que respeta ambos **sin salir del módulo `brand_studio` ni tocar core**, manteniendo el ticket primario en FE:

- **T-2 (FE-prod, primario):** en `marca-voice-api.ts::updatePersonality`, **dejar de mandar `X-User-ID: opts.tenantId`** (el dato equivocado). Mandar `X-User-ID: opts.userId` (el Clerk userId real) **si** está disponible — y dejar que el BE lo resuelva. El api-layer deja de mentir (no más tenant-como-actor).
- **T-2b (BE acompañante, mismo ticket o sub-ticket BE en `brand_studio`):** el PATCH `/personality` (y, por consistencia, los PATCH marca que auditan) **resuelven el actor desde el `clerk_sub` del JWT** (vía `_resolve_user_uuid`) en vez de `UUID(X-User-ID)`. Acepta el Clerk userId / lo deriva del Bearer; el `X-User-ID` deja de ser la fuente del actor UUID.

> **Por qué T-2b es necesario:** sin él, T-2 solo (mandar el Clerk userId crudo) rompería el PATCH con 422. El re-repro confirmó que el actor debe ser UUID. El builder DEBE implementar el par (FE deja de mentir + BE resuelve el actor real). **Esto se declara como divergencia menor del scope FE-only ratificado** → surfaceado a PM en § 16 (Chris ratificó "scope completo · sub-bug #2 in-story"; la mecánica exacta FE+BE-resolución es decisión de arquitectura).

**Forbidden:** romper `require_brand_owner_access` (sigue leyendo `X-User-Role`). NO tocar `core/`. NO crear un resolver nuevo (consumir `_resolve_user_uuid`).

## D.4 Verificación (SC-6 · AC-3)

PATCH personality real (cambio arquetipo) ejercido como owner Clerk real → fila `vitalia_audit_log` con `user_id = users.id` del owner (resuelto del clerk_sub), `!= tenant_id`. State_check DB:
```sql
SELECT user_id FROM vitalia_audit_log WHERE resource_type='personality' ORDER BY occurred_at DESC LIMIT 1;
-- expect: = users.id del owner (≠ tenant_id)
```

---

## 9. Migration Notes

**Ninguna migración.** Esta story no crea ni altera tablas. `vitalia_audit_log` ya existe (013_vitalia, partitioned, `user_id UUID NOT NULL`). El sub-bug #1 es un cambio de signature de header (no DDL). El sub-bug #2 cambia el origen del actor (no DDL).

## 9.5 Tests audit (default flip)

`[x] No aplica — 03-arch.md NO flipea defaults side-effect.` Ningún `USE_*_PATTERN_*` / `ENABLE_*` / `LITELLM_PROXY_*` se toca. El sub-bug #1 cambia `X-User-ID` de required→optional en UN GET (no es un feature flag side-effect). El sub-bug #2 cambia el origen del actor (no es flag).

## 10. File Structure

```
vitalia/frontend/e2e/
├── fixtures/
│   ├── base.ts                              [EXISTING — ADOPT vía mergeTests]
│   └── real-backend-forward.fixture.ts      [NEW — lift forwarding + auth + base.ts]
├── regression/vitalia-fase2-lisa-marca/
│   ├── fixtures/lisa-marca.fixture.ts        [MODIFIED — de-mock: setupLisaMarcaMocks REMOVED/replaced]
│   ├── poms/{voz-tono,identidad,presencia}-section.pom.ts + lisa-marca-page.pom.ts  [MODIFIED — web-first asserts]
│   └── *.spec.ts (×11)                        [MODIFIED — import real-backend-forward, de-mock, web-first]
└── regression/arreglar-guardado-voz-y-tono/
    ├── poms/voz-tono-section.pom.ts          [MODIFIED — waitForSelectedArchetype web-first]
    └── {voz-arquetipo,voz-bloque,voz-autosave-error}.spec.ts  [MODIFIED — des-quarantine 5 fixme + no dangling listeners + base.ts opt-out en error-injection]

vitalia/frontend/src/features/lisa/api/marca-voice-api.ts   [MODIFIED — sub-bug #2: X-User-ID = userId real, no tenantId]

vitalia/backend/src/modules/vitalia/brand_studio/api/routers/marca_router.py
   ├── get_prohibited_phrases                  [MODIFIED — sub-bug #1: X-User-ID optional]
   └── patch_personality (+ patch marca que auditan)  [MODIFIED — sub-bug #2b: actor desde clerk_sub via _resolve_user_uuid]

vitalia/docs/product/capabilities/brand_studio/lisa-marca.yaml   [MODIFIED — re-cable e2e_test + verified_real + change_log]
```

## 11. Cross-Cutting Concerns

- **Tenant isolation:** `X-Tenant-ID` sigue required en el GET prohibited-phrases + todos los PATCH. Specs corren con `E2E_TENANT_ID` real (el tenant del owner Clerk). RN-6.
- **PII / HIPAA-lite:** los flujos lisa-marca son **brand-config (no-PHI)** — no hay diagnóstico/treatment. El audit actor real (sub-bug #2) MEJORA la fidelidad HIPAA-lite del "quién". `response_model=` se mantiene en el GET (allowlist). No se loguea PII.
- **Currency / master-data:** N/A (sin campos monetarios ni datetimes nuevos).
- **Spanish neutro:** N/A nuevo (los specs de-mockeados ya asertan copy neutro; harness/tests no se escanean — rule spanish-text § alcance acotado).
- **Native-first:** todos los gates corren native (`npx playwright`/`npx tsc`/`${WS}/.venv/bin/pytest`), NUNCA docker exec. E2E contra `localhost:3002`/`:8002` (stack `make dev-vitalia` UP) o `dev-app.vitalialat.com`.
- **Anti-burbuja (rule #37 layer 7):** todos los specs FE de-mockeados importan `base.ts` (pageerror/console/4xx-5xx/overlay Next). Opt-out solo en error-injection (`test.use({ failOnRuntimeError: false })`).

## 12. Architecture Fitness Impact

- **BE (sub-bug #1):** `vitalia/backend/tests/architecture/` debe seguir verde — `test_response_model_required.py` (se mantiene `response_model=`), `test_brand_studio_module_ddd.py`, tenant-isolation. Allowlists NO crecen.
- **FE (sub-bug #2):** `vitalia/frontend/src/__tests__/architecture/` — no rompe boundaries FSD (api-layer sigue en `features/lisa/api/`); `test-no-clerk-organizations.test.ts` no afectado (usa `useAuth().userId`, no `orgId`).
- **Grep-gates nuevos (harness arch-fitness):** SC-2/SC-3/SC-5 son grep_gates que el `gate-runner` corre como validators ejecutables (ver 04-validators). Son anti-regresión: shrink-only (0 ocurrencias de mock-backend-bajo-prueba / `@playwright/test` directo / `page.on void` fire-and-forget).
- **Gates que correrá `gate-runner`:** `tsc --noEmit` + `eslint --max-warnings 0` (FE) · `ruff check` + `mypy --strict` + `pytest tests/architecture/` (BE) · grep-gates SC-2/3/5 · suite lisa-marca `--repeat-each=3 --workers=1` (SC-1) · des-quarantine `--repeat-each=5` (SC-4) · state_check DB (SC-6) + backend_log (SC-7) · cross_check cap (SC-8).

## 13. capability YAML + modules/{m}.md Updates Required

- `vitalia/docs/product/capabilities/brand_studio/lisa-marca.yaml` — re-cablear `e2e_test` + `verified_real` por scenario (Parte B) + agregar `change_log` entry (post-merge, Fase F.3).
- `vitalia/docs/product/modules/brand_studio.md` — **sin cambio** (no hay capability nueva ni narrativa nueva; es fix del harness de una cap existente).

## 14. Test Surfaces (TDD-mandatory · RED-first)

- **FE-tests:** los specs SON el surface de test. RED-first para el de-mock = el spec de-mockeado falla contra el mock viejo (esperado), pasa contra backend real. Para los grep-gates: el grep falla HOY (hay ocurrencias), pasa post-de-mock.
- **FE-prod (sub-bug #2):** Vitest unit en `usePersonalityAutosave`/`marca-voice-api` que asserta que `X-User-ID` NO es el tenantId (RED contra el código viejo) + e2e SC-6 (state_check audit_log actor real).
- **BE (sub-bug #1):** pytest que GET prohibited-phrases sin `X-User-ID` → 200 (RED contra el required actual → 422) + con `X-Tenant-ID` inválido → 422 (tenant-isolation intacta).
- **Regression guard:** los specs de OTRAS features (valeria/camila/doctores/etc.) NO se tocan ni cambian.

## 15. Research Notes (DATE-AWARE)

- **Playwright web-first assertions / anti-flake** — `https://playwright.dev/docs/test-assertions` + `https://playwright.dev/docs/test-retries` — accessed 2026-06-02.
  - Key takeaway: preferir aserciones auto-retry (`expect(locator).toHaveAttribute/toHaveValue/toBeVisible`) sobre once-reads (`getAttribute`/`textContent`/`inputValue`); usar `expect.poll()` para funciones que devuelven un valor; hard-waits (`waitForTimeout`) son anti-pattern. Es exactamente el fix de determinismo (RN-3 / SC-4).
  - Por qué sobre alternativas: el checkpoint barajó "Clerk-ready gate" / "query resiliente" (direcciones #1/#2) — el re-repro las descartó (la race ya está resuelta). El fix real es el patrón canónico de Playwright (web-first), no infra de auth.
  - Knowledge cutoff disclosure: Opus 4.8 cutoff = Jan 2026; web-first assertions son API estable de larga data, verificado live hoy vía WebSearch para confirmar sigue siendo la guía 2026.
- **Anti-burbuja gate (`base.ts`)** — interno, rule `.claude/rules/definition-of-done-live-verify.md § 3` (Critical Rule #37) — accessed local 2026-06-02. Composición vía `mergeTests` (`@playwright/test`).

## 16. Open Questions for PM

1. **Sub-bug #2 mecánica FE+BE (§ D.3):** Chris ratificó "scope completo · sub-bug #2 in-story". El scope lo etiquetó como ticket FE-prod, pero la restricción dura (audit actor DEBE ser UUID; Clerk userId no es UUID) obliga a un **par FE+BE**: FE deja de mandar el tenant como actor + BE resuelve el actor real desde el `clerk_sub` del JWT (vía `_resolve_user_uuid`, consumido no recreado). **Surfaceo:** esto agrega un toque BE chico al `brand_studio` (no core, no otra brand) — confirmar con PM que es aceptable dentro de "in-story" (es la única forma de cerrar AC-3/RN-5 sin un actor falso). Si PM prefiere FE-only, la alternativa es que IAM escriba `users.id` en `publicMetadata` (cambio de seed/IAM, más invasivo) — NO recomendado.
2. **Seed del tenant E2E:** los specs de-mockeados ejercen round-trips contra el tenant `E2E_TENANT_ID` real. Confirmar que ese tenant (owner Clerk `dr.demo@vitalialat.com`) tiene fila de personality/identity para que los GET no devuelvan empty inesperado en specs que no son empty-state (el builder usa round-trip read→write, tolerante, pero si el tenant está totalmente vacío algunos asserts perf/large-dataset necesitan datos). No-bloqueante (el patrón round-trip lo absorbe), pero anotado.

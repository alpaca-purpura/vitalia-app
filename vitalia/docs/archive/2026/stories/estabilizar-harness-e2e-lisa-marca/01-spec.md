---
story_id: estabilizar-harness-e2e-lisa-marca
brand: vitalia
type: bugfix
state: refined
release: F2
cap_target: lisa-marca
cap_change_type: fix
agent_owner: lisa                 # zona Agentes · caja Lisa (derivada de SYSTEM-MAP)
architecture_pattern: ADR-vitalia-004
adr_004_compliance: bugfix-lite-na
verification_nature: ambas        # técnica (harness/asserts/grep gates) + funcional (los flujos lisa-marca ejercidos REAL)
po_ux_version: 2
ratified_by_chris: true
ratified_by_chris_at: '2026-06-02T16:45:00-05:00'
scope_decisions:                  # ratificadas Chris 2026-06-02
  sub_bug_1_prohibited_phrases: in-story   # SC-7/AC-5 hard
  scope: completo                          # de-mock 11 + des-quarantine 5 + sub-bug #2 + cap re-cable
  a11y_i18n: not_applicable                # meta-harness, cero UI nueva
---

# 01-spec · estabilizar-harness-e2e-lisa-marca (bugfix-lite, harness honesto + determinista)

> **Naturaleza:** bugfix-lite del **harness E2E** de lisa-marca (no hay UI nueva). El "producto" bajo prueba
> ya existe y está specced en el cap `brand_studio/lisa-marca` + stories padre. Esta story hace que su suite
> de tests sea **honesta** (backend real, no mock del backend-bajo-prueba) y **determinista** (asserts
> web-first, sin listeners dangling). Re-repro hecho contra HEAD ANTES de specear — ver § Repro.

## § Context

- **Release:** F2.
- **Módulo:** `brand_studio` (sub-módulo `lisa/marca`). FE: `vitalia/frontend/src/features/lisa/`. Tests:
  `vitalia/frontend/e2e/regression/vitalia-fase2-lisa-marca/` (11 specs + POMs + fixtures).
- **Punto de inserción:** invisible al usuario final — es infraestructura de verificación. El usuario afectado
  es el *equipo* (Chris + Claude): hoy la suite da verde-falso → un bug puede shippear "verificado".
- **Origen:** follow-up de `arreglar-guardado-voz-y-tono` (el bug del guardado shippeó porque la suite
  mockeaba el backend = "verificación teatro"). Learning: `vitalia/docs/learnings/2026-05-31-e2e-mockeado-verde-falso.md`.
- **Out of scope (anti-creep):**
  - NO se rediseña ninguna pantalla de lisa-marca (cero UI nueva).
  - NO se toca la lógica de producto del autosave/voz/identidad salvo los 2 sub-bugs de auth-header acotados.
  - NO se migra la suite a un proxy real de Next (`/api` rewrite) — se mantiene el patrón de *forwarding*
    `page.route` ya shipped por la story padre (decisión heredada; cambiar el transporte es otra story).
  - NO se tocan los specs de OTRAS features (valeria-agenda, camila, etc.).

## § Repro (re-repro 2026-06-02 contra HEAD — bugfix-first, R26)

Corrido contra el stack dev real (BE :8002 + FE :3002 UP, sesión Clerk + storageState). Detalle verbatim +
comandos en `checkpoint.md § Re-repro 2026-06-02`. Resumen del estado real HOY:

- **R0 (root-cause viejo OBSOLETO):** la race de Clerk auth-readiness ("No se pudo cargar") **está resuelta**
  post-`14af22b2` + `retry:5`. La página hidrata confiable (bloque persiste 5/5; arquetipo 5/5 con assert que
  pollea). → NO se diseña ningún "Clerk-ready gate" ni "query resiliente" (direcciones #1/#2 del checkpoint
  quedan obsoletas).
- **B1 — mock del backend-bajo-prueba (false-green):** `fixtures/lisa-marca.fixture.ts:137,252` se
  autodescribe *"API mock base data (NO real BE calls)"* + `page.route("**/api/v1/lisa/marca/{identity,
  visuals,personality}", route.fulfill())`. 10 specs heredan el mock.
- **B2 — anti-burbuja no adoptado:** los 11 specs importan `@playwright/test` directo, NO `e2e/fixtures/base.ts`
  (page-error + hidratación + 4xx/5xx + overlay Next). Cero cobertura de la burbuja roja de Next.
- **B3 — assert NO web-first (flake determinista):** `poms/voz-tono-section.pom.ts:180 getSelectedArchetype()`
  lee `data-selected="true"` **una vez**; `waitForLoaded()` solo espera un card estático, NO la hidratación
  del GET → null determinista (reload-persist arquetipo falla 5/5). Con assert web-first
  (`toHaveAttribute("data-selected","true",{timeout:15s})`) → 5/5 verde. **Este es el fix real de determinismo.**
- **B4 — listener dangling (flake real):** `voz-arquetipo-autosave.spec.ts:251` usa
  `page.on("response", () => void pom.getAutosaveStatus().then(...))` sin `page.off` → corre durante teardown
  → `locator.getAttribute: Target page... has been closed` (1 flaky en repeat-each=3).
- **B5 — sub-bug #2 (HIPAA-lite actor) vivo:** `features/lisa/api/marca-voice-api.ts:113` manda
  `"X-User-ID": opts.tenantId` (org UUID como actor del audit-log, no el Clerk userId real).
- **B6 — sub-bug #1 (prohibited-phrases 422) vivo Y enmascarado:** logs BE muestran 422 (browser real:
  `fetchClient` no manda `X-User-ID` en ese GET) Y 200 (el forwarding fixture lo inyecta manual, spec:137).
  El "real backend" miente sobre el contrato FE.

## § Mapa funcional (lite — bugfix: foco en repro + bifurcaciones + RN; happy path opcional)

**Happy path (narrado):** Claude corre la suite lisa-marca ×3 contra el backend real → cada spec ejerce la
acción real del usuario (escribe identidad/voz, sube logo, edita cross-tenant) → observa el efecto real
(persistencia DB, badge, 422/403 esperado) sin mocks del backend-bajo-prueba → 0 flaky → el cap refleja
`verified_real` honesto.

**Bifurcaciones (árbol — dónde se rompe HOY → qué debe pasar):**

```
¿El spec mockea el backend-bajo-prueba (identity/visuals/personality)?
├─ SÍ (hoy, 10 specs) → false-green                                   [B1] → debe NO mockear  [Bif-1 → SC-2]
└─ NO → ¿el spec importa base.ts (anti-burbuja)?
        ├─ NO (hoy, 11 specs) → burbuja Next invisible                [B2] → debe importar base.ts [Bif-2 → SC-3]
        └─ SÍ → ¿los asserts de estado hidratado son web-first?
                ├─ NO (getSelectedArchetype once-read)                [B3] → web-first/polling     [Bif-3 → SC-4]
                └─ SÍ → ¿hay listeners fire-and-forget sin cleanup?
                        ├─ SÍ (page.on response sin page.off)         [B4] → sin dangling          [Bif-4 → SC-5]
                        └─ NO → spec honesto + determinista ✅
```

**Reglas de negocio (invariantes del harness — `RN`):**

- **RN-1 — Cero mock del backend-bajo-prueba.** Ningún spec de lisa-marca puede usar `route.fulfill()` sobre
  `**/api/v1/lisa/marca/{identity,visuals,personality}**` con data canned. Inyección de *fallos* (503/timeout)
  para probar el estado de error SÍ es mock legítimo (no es el happy-path del backend). (refleja `business_rules` del cap)
- **RN-2 — Anti-burbuja siempre.** Todo spec FE de lisa-marca importa `test`/`expect` de `e2e/fixtures/base.ts`
  (no de `@playwright/test`). Opt-out solo en tests que ejercen un error a propósito (`test.use({ failOnRuntimeError: false })`).
- **RN-3 — Asserts web-first sobre estado hidratado.** Cualquier lectura de estado que dependa del GET
  (`data-selected`, valor de textarea, presencia de card) usa aserción con polling (`expect(...).toHave*({timeout})`),
  NUNCA un read único post-`waitForLoaded`.
- **RN-4 — Sin listeners dangling.** Prohibido `page.on(...)` con callback fire-and-forget (`void promise`) sin
  `page.off`/cleanup antes del fin del test.
- **RN-5 — Actor de audit real (HIPAA-lite).** El header `X-User-ID` de las mutaciones de marca lleva el Clerk
  userId real, no el tenant UUID. (sub-bug #2)
- **RN-6 — Tenant real.** Los specs usan `E2E_TENANT_ID` (el tenant que el usuario Clerk autenticado posee), no
  un slug ficticio.
- **RN-7 — Cap honesto.** Un scenario del cap `lisa-marca` no puede estar `status: live` cableado a un spec que
  mockea el backend-bajo-prueba. `e2e_test` apunta a spec honesto + `verified_real` poblado.

**Criterios de aceptación (`AC` — feature-done):**

- **AC-1 — Suite verde-determinista:** los 11 specs lisa-marca + los 5 reload/error desfixme'ables corren
  **0 flaky en 3 corridas consecutivas** contra backend real (`E2E_BASE_URL=http://localhost:3002 --project=smoke --repeat-each=3`).
- **AC-2 — Honestidad estática:** `grep` no encuentra mock del backend-bajo-prueba (RN-1) ni import directo de
  `@playwright/test` (RN-2) ni `getSelectedArchetype`-once / `page.on` dangling (RN-3/RN-4) en la carpeta.
- **AC-3 — Sub-bug #2 cerrado:** una mutación de marca registra en `vitalia_audit_log` el Clerk userId real
  como actor (verificación REAL: PATCH ejercido → fila con `user_id` = Clerk id, no tenant UUID).
- **AC-4 — Cap re-cableado:** cada scenario `status: live` de `lisa-marca.yaml` apunta a un spec honesto +
  `verified_real`; los que aún no tengan spec honesto bajan a `partial`/`declared` (no `live` falso).
- **AC-5 (in-scope, ratificado Chris 2026-06-02) — Sub-bug #1 cerrado:** GET `/lisa/marca/prohibited-phrases`
  responde 200 desde el browser real (sin que el e2e tenga que inyectar `X-User-ID` a mano).

## § Gherkin scenarios

> Naturaleza mixta. Los SC de harness/contrato (grep + run) son `verification_nature: técnica`; los que ejercen
> el flujo real (SC-6/SC-7) son `funcional`. Cada uno `Covers:` ítems del Mapa funcional.

```yaml
- id: SC-1-suite-determinista
  tipo: happy
  Covers: [AC-1]
  given: "stack dev real UP (BE :8002 + FE :3002) + sesión Clerk + storageState + E2E_TENANT_ID real"
  when:  "se corre la suite lisa-marca de-mockeada + los reload/error desfixme'd, --repeat-each=3 --workers=1"
  then:  "0 flaky · 0 failed · cada spec ejerce acción real + observa efecto real (no GET 200 pelado)"
  playwright_required: true
  graders:
    - { type: e2e, path: "vitalia/frontend/e2e/regression/vitalia-fase2-lisa-marca/", run: "--repeat-each=3" }

- id: SC-2-no-mock-backend-bajo-prueba
  tipo: adversarial          # AI-resistant: impide re-introducir el false-green
  Covers: [Bif-1, RN-1]
  given: "la carpeta e2e/regression/vitalia-fase2-lisa-marca/"
  when:  "se busca route.fulfill() sobre /api/v1/lisa/marca/{identity,visuals,personality}"
  then:  "0 ocurrencias (los fallos inyectados 503/timeout están permitidos y etiquetados aparte)"
  playwright_required: false
  graders:
    - { type: grep_gate, pattern: "route.fulfill.*lisa/marca/(identity|visuals|personality)", expect: 0 }

- id: SC-3-anti-burbuja-adoptado
  tipo: edge
  Covers: [Bif-2, RN-2]
  given: "los 11 specs lisa-marca"
  when:  "se inspecciona el import de test/expect"
  then:  "todos importan de e2e/fixtures/base.ts; ninguna burbuja roja de Next ni error de hidratación al ejercer el flujo"
  playwright_required: true
  graders:
    - { type: grep_gate, pattern: "from \"@playwright/test\"", scope: "*.spec.ts", expect: 0 }
    - { type: e2e, assert: "pageerror[]==0 && nextjs-portal count==0" }

- id: SC-4-reload-persist-web-first
  tipo: edge
  Covers: [Bif-3, RN-3]
  given: "los tests reload-persist (arquetipo Sage + bloque) hoy quarantined"
  when:  "se des-quarantinan con asserts web-first (POM waitForSelectedArchetype / toHaveValue con timeout)"
  then:  "persisten el valor tras reload, 5/5 determinista (no once-read null)"
  playwright_required: true
  graders:
    - { type: e2e, path: "vitalia/frontend/e2e/regression/arreglar-guardado-voz-y-tono/", run: "--repeat-each=5" }

- id: SC-5-sin-listeners-dangling
  tipo: edge
  Covers: [Bif-4, RN-4]
  given: "el test 'badge no llega a error' (voz-arquetipo-autosave:251) + cualquier page.on similar"
  when:  "se elimina el fire-and-forget y se mide el estado del badge de forma awaited/cleanup"
  then:  "0 'Target page... has been closed'; flaky=0 en repeat-each=3"
  playwright_required: true
  graders:
    - { type: grep_gate, pattern: "page.on\\(.*void ", expect: 0 }
    - { type: e2e, run: "--repeat-each=3" }

- id: SC-6-audit-actor-real
  tipo: adversarial          # HIPAA-lite: el "quién" debe ser real
  Covers: [RN-5, AC-3]
  given: "owner autenticado (Clerk userId real) en Lisa › Marca"
  when:  "ejerce un PATCH de personality real (cambio de arquetipo)"
  then:  "la fila de vitalia_audit_log registra user_id = Clerk userId real (NO el tenant UUID)"
  playwright_required: true
  graders:
    - { type: state_check, target: db, query: "SELECT user_id FROM vitalia_audit_log WHERE resource_type='personality' ORDER BY created_at DESC LIMIT 1", expect: "= Clerk userId, != tenant_id" }

- id: SC-7-prohibited-phrases-browser-real     # IN-SCOPE (ratificado Chris 2026-06-02) — AC-5 hard
  tipo: negative
  Covers: [RN-6, AC-5]
  given: "owner autenticado en el browser real (NO e2e con header inyectado)"
  when:  "la pantalla hace GET /lisa/marca/prohibited-phrases"
  then:  "responde 200 (no 422); el e2e ya no necesita inyectar X-User-ID a mano para que pase"
  playwright_required: true
  scope_decision: "in-story (ratificado Chris 2026-06-02) — BE X-User-ID opcional en el GET"
  graders:
    - { type: state_check, target: backend_log, expect: "GET /lisa/marca/prohibited-phrases 200 (browser real)" }

- id: SC-8-cap-honesto
  tipo: edge
  Covers: [RN-7, AC-4]
  given: "capabilities/brand_studio/lisa-marca.yaml"
  when:  "se audita cada scenario status:live"
  then:  "su e2e_test apunta a spec honesto (de-mockeado) + verified_real; ninguno cableado a spec mockeado"
  playwright_required: false
  graders:
    - { type: cross_check, script: "reconcile cap.e2e_test → spec sin route.fulfill backend-bajo-prueba" }
```

> **Sub-categorías mandatory v4.1 — cobertura/justificación (story de harness):** `race_condition`,
> `concurrent_users`, `empty_state`, `large_dataset` ya están cubiertas por specs existentes de la suite
> (`lisa-marca-race-autosave`, `lisa-marca-concurrent-owners`, `lisa-marca-empty-state`,
> `lisa-marca-large-dataset`) — esta story las hace **honestas** (de-mock), no las re-inventa. `network_failure`
> = los specs `voz-autosave-error` (503 inyectado, mock legítimo). `accessibility` / `i18n`: **not_applicable**
> a nivel meta-harness (no hay UI nueva; los specs FE existentes ya asertan copy neutro) — `not_applicable_reason:
> "bugfix de harness, cero superficie UI nueva; a11y/i18n del producto cubiertos por los specs que se de-mockean"`
> — **ratificado por Chris 2026-06-02.**

## § Matriz de cobertura (puente Mapa funcional ↔ verificación REAL)

| Ítem | Tipo | Cubierto por | Verificación REAL (acción + efecto) |
|---|---|---|---|
| Bif-1 · mock backend-bajo-prueba | branch | SC-2 | grep 0 ocurrencias `route.fulfill` sobre identity/visuals/personality |
| Bif-2 · anti-burbuja no adoptado | branch | SC-3 | grep 0 imports `@playwright/test` + ejercer flujo → pageerror[]==0, overlay Next ausente |
| Bif-3 · assert no web-first | branch | SC-4 | reload real → `data-selected=true`/`toHaveValue` con polling, 5/5 |
| Bif-4 · listener dangling | branch | SC-5 | repeat-each=3 → 0 "Target page closed" |
| RN-1 · cero mock backend-bajo-prueba | rule | SC-2 | grep gate |
| RN-2 · anti-burbuja siempre | rule | SC-3 | grep gate + runtime gate |
| RN-3 · web-first hidratado | rule | SC-4 | reload real con polling |
| RN-4 · sin dangling | rule | SC-5 | grep gate + repeat-each |
| RN-5 · actor audit real | rule | SC-6 | PATCH real → fila audit_log con Clerk userId |
| RN-6 · tenant real | rule | SC-1/SC-6 | specs corren con E2E_TENANT_ID real, efecto en DB del tenant |
| RN-7 · cap honesto | rule | SC-8 | cross-check cap.e2e_test → spec honesto |
| AC-1 · suite determinista | accept | SC-1 | suite ×3 → 0 flaky |
| AC-3 · sub-bug #2 cerrado | accept | SC-6 | audit_log actor real |
| AC-4 · cap re-cableado | accept | SC-8 | cap scenarios honestos |
| AC-5 · sub-bug #1 (condicional) | accept | SC-7 | GET 200 desde browser real |

**Huecos detectados (Bif/RN sin SC):** ninguno.
**SC huérfanos (SC sin ítem del mapa):** ninguno.

## § Surfaces tocadas (no hay UI nueva — son archivos de harness + 2 sub-bugs acotados)

| Surface | Path | Cambio |
|---|---|---|
| Fixture mockeada | `vitalia/frontend/e2e/regression/vitalia-fase2-lisa-marca/fixtures/lisa-marca.fixture.ts` | de-mock: forwarding a BE real (patrón story padre) en vez de `route.fulfill` canned |
| 11 specs lisa-marca | `…/vitalia-fase2-lisa-marca/*.spec.ts` | importar `base.ts`; tenant real; asserts web-first; sin dangling |
| POM voz-tono | `…/poms/voz-tono-section.pom.ts` | `getSelectedArchetype` → `waitForSelectedArchetype(slug)` web-first |
| 5 fixme reload/error | `…/arreglar-guardado-voz-y-tono/*.spec.ts` | des-quarantine con asserts web-first |
| Sub-bug #2 (FE) | `vitalia/frontend/src/features/lisa/api/marca-voice-api.ts:113` | `X-User-ID` = Clerk userId real (plumbear), no `tenantId` |
| Sub-bug #1 (BE, condicional) | router GET `prohibited-phrases` | `X-User-ID` opcional en ese GET (read por tenant+país) |
| Cap | `vitalia/docs/product/capabilities/brand_studio/lisa-marca.yaml` | re-cablear `e2e_test` → specs honestos + `verified_real` |

## § Secciones UI estándar — N/A (justificado)

Wireframes / estados visuales / responsive / componentes / microcopy / brand voice / telemetría: **N/A** — esta
story no crea ni modifica ninguna pantalla. Es un bugfix del harness de tests + 2 fixes de auth-header acotados.
`not_applicable_reason: "bugfix-lite de harness E2E + contrato de auth; cero superficie UI nueva"`.

## § Prior art applied

- **Engine consumed:** ninguno nuevo. El runtime-error gate `base.ts` ya existe (creado 2026-06-01 por rule #37)
  — se **adopta**, no se construye.
- **Reused de la story padre (vitalia):** patrón de *forwarding* a backend real
  `arreglar-guardado-voz-y-tono/{voz-arquetipo,voz-bloque,voz-autosave-error}.spec.ts` (`page.route("**/api/v1/**")`
  → `page.request.fetch(:8002)`) + POM `voz-tono-section.pom.ts` + tenant `E2E_TENANT_ID`. Es el template directo
  del de-mock.
- **Learnings aplicados:**
  - `vitalia/docs/learnings/2026-05-31-e2e-mockeado-verde-falso.md` (el false-green que originó esta story).
  - `vitalia/docs/learnings/2026-06-01-fe-tenant-from-clerk-org-systemic.md` (`14af22b2` resolvió la race de auth →
    por eso el root-cause viejo está stale).
- **Lift candidates:** un helper `waitForSelectedArchetype`/asserts web-first es patrón cross-brand candidato a
  `core` e2e helpers — **no lift ahora** (anotar; la suite e2e sigue per-brand). Escalar a `/pm-luana` solo si
  comunify replica el patrón.
- **Net-new justificado:** nada net-new de producto. Los 2 sub-bugs son fixes de contrato existente.

## § Out of scope (recordatorio)

- Migrar el transporte e2e de *forwarding* a proxy Next real → otra story.
- Tocar specs de otras features (valeria/camila/etc.).
- Reabrir el comportamiento de auto-save/voz/identidad (salvo los 2 headers de auth).

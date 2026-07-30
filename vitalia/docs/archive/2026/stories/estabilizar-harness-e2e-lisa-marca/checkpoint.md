---
story_id: estabilizar-harness-e2e-lisa-marca
brand: vitalia
type: bugfix
state: done
phase: MERGED
dev_app_verified: true   # ADR-vitalia-008 — live-verify real (POST/DELETE /logos + visuals + R2) + demo_signoff Chris
release: F2
cap_target: lisa-marca
cap_change_type: fix
architecture_pattern: ADR-vitalia-004
adr_004_compliance: bugfix-lite-na
verification_nature: ambas
autonomous_mode: false
parent_story: arreglar-guardado-voz-y-tono
agent_owner: lisa
module: brand_studio
last_modified: '2026-06-03T19:55:00.000Z'
dod_live_verified: true   # live-verify + demo_signoff Chris APPROVED 2026-06-03 (rule #37 §5)
demo_required: true
demo_signoff: {signed_by: Chris, date: '2026-06-03', result: APPROVED}
spawned_at: '2026-05-30'
spawned_by: chris-followup
ratified_by_chris: true
ratified_by_chris_at: '2026-05-30T23:45:00-05:00'
ready_closed_by: '/architect'
ready_closed_at: '2026-06-02T17:35:00-05:00'
repro_verified: true
parallel_safe: true
next_action: 'AUTO-HANDOFF /auditor vitalia story=estabilizar-harness-e2e-lisa-marca. Todos los tickets pushed (T-1..T-5) + demo_signoff Chris APPROVED 2026-06-03. State developing→developed. Auditor: Phase D gherkin-matrix + revisión técnica (BE marca 14/14 + arch 335 + FE tsc/eslint/vitest 35; bug 3 e2e real POST→GET persist + fetch 200). Si APPROVED → /pm-vitalia merge→done→archive.'
goal: >-
  Estabilizar el harness E2E de lisa-marca (Clerk auth-readiness). El GET
  /personality in-browser flaquea (getToken() transitorio null tras nav directa /
  reload) → la pantalla muestra "No se pudo cargar" sin recuperar → la suite
  lisa-marca es flaky/no-determinista. Además, varios specs viejos de lisa-marca
  siguen mockeando el backend + usando data-testids fantasma (verde falso). Dejar
  la suite lisa-marca verde-determinista contra backend real.
---
# estabilizar-harness-e2e-lisa-marca — checkpoint

## Goal

Dejar la suite E2E de **lisa-marca verde y determinista** contra backend real. Origen: durante
`arreglar-guardado-voz-y-tono` (bugfix del guardado voz-y-tono) se descubrió que el harness E2E de
lisa-marca **nunca estuvo realmente verde** — mockeaba el backend, usaba data-testids fantasma, y apuntaba
a un tenant ficticio. Eso fue **la razón estructural por la que el bug del guardado shipeó** (la
"verificación" era teatro). Parte ya se corrigió para voz-y-tono; esta story cierra lo que falta.

## Tipo: `bugfix` (lite — ADR-011)

Arreglo de comportamiento roto del harness de test (sin diseño nuevo). Hereda gate repro-first
(`repro_verified: true` — el flake está reproducido abajo). NO toca lógica de producto; sí puede tocar
componentes para robustez de la query (retry/auth-ready) y los specs/POMs/fixtures de E2E.

## Root cause primario (reproducido)

El GET `/api/v1/lisa/marca/personality` **in-browser** flaquea en el contexto E2E: tras navegación directa
a `/{tenantId}/lisa/marca/voz-y-tono` (o un `reload`), `useAuth().getToken()` de Clerk devuelve `null`
transitoriamente. El `queryFn` hace `if (!token) throw new Error("Not authenticated")` → la query entra en
error → `isPersonalityError=true` → ArchetypeSelector muestra "No se pudo cargar la configuración de voz"
y NO se recupera. (Se le agregó `retry:5` en `VozTonoView` durante la story padre — mejora pero NO
determinista: si Clerk tarda más que el backoff, agota reintentos.)

**Evidencia (story padre):** correr la suite voz-y-tono con el tenant correcto da **~5-7/9 verde**; los
2-3 que flaquean SIEMPRE son los que recargan/reintentan (bloque-persiste-en-recarga, error-reintento).
Cuando se forzó un `waitFor` HARD del card (sin `.catch`), los fallos subieron a 5/9 → confirma que el GET
in-browser frecuentemente no hidrata a tiempo. **Ningún GET llega al backend** en esos casos (el throw es
client-side) → es 100% race de auth-readiness de Clerk, no del backend.

## Alcance afectado (toda la suite lisa-marca, no solo voz-y-tono)

Specs lisa-marca que heredan el mismo problema (mock + testids fantasma + tenant + auth-race):
`lisa-marca-identidad-autosave.spec.ts`, `lisa-marca-race-autosave.spec.ts`,
`lisa-marca-concurrent-owners.spec.ts`, `lisa-marca-logo-upload-size.spec.ts`,
`lisa-marca-cross-tenant.spec.ts`, `lisa-marca-voice-warning.spec.ts`, `lisa-marca-large-dataset.spec.ts`,
+ fixture `vitalia-fase2-lisa-marca/fixtures/lisa-marca.fixture.ts`.

> `voz-y-tono` (la story padre) ya quedó con tenant correcto + data-testids reales + GET real. Esta story
> extiende ese patrón al resto + ataca la race de auth-readiness de raíz.

## Sub-bug relacionado encontrado (decidir si entra acá)

`GET /api/v1/lisa/marca/prohibited-phrases` requiere header `X-User-ID` (router línea ~576) pero el
`fetchClient` FE **no lo inyecta** → siempre 422 (visto en logs `make dev-vitalia`). No bloquea el archetype
test, pero es un contrato FE↔BE roto del mismo módulo. Opciones: BE hace `X-User-ID` opcional en ese GET
(es un read, no necesita user para listar por tenant+país), ó FE/api-layer lo inyecta. Recomiendo BE-opcional.

## Sub-bug #2 — audit actor identity (HIPAA-lite, WARN del auditor 2026-05-31)

`vitalia/frontend/src/features/lisa/api/marca-voice-api.ts` manda `X-User-ID: tenantId` (el UUID de la
org) como actor del audit-log, en vez del **Clerk userId** real. → las filas de `vitalia_audit_log` de los
PATCH de marca registran el actor equivocado (degrada fidelidad HIPAA-lite del "quién"). Es un mismatch
platform-level Clerk-userId-vs-tenant-UUID (el userId real no está plumbeado al api-layer FE). Non-blocking
para el bugfix del guardado (los headers son lo que hace funcionar el save), pero stake-asimétrico →
arreglar acá: plumbear el Clerk userId real al header `X-User-ID` de los endpoints de marca. Mismo área que
el sub-bug de prohibited-phrases (auth headers FE de los endpoints marca).

## Direcciones de fix candidatas (para /architect)

1. **Gate de Clerk-ready en el harness:** fixture/POM espera a que Clerk esté plenamente autenticado
   (`getToken()` no-null) antes de interactuar/asertar — p.ej. un helper `waitForClerkReady(page)` que
   poll-ea hasta que un GET autenticado responda, o usa el patrón oficial `@clerk/testing` de readiness.
2. **Query resiliente a auth transitoria:** en vez de `throw` en token null, la query espera/reintenta hasta
   token disponible (no deja la pantalla en error permanente). Beneficio: robustez también en producción
   (un blip de token no debe romper la pantalla). Parcialmente hecho (`retry:5`) — formalizar.
3. **De-mock + testids reales** en los specs lisa-marca restantes (mismo patrón ya aplicado a voz-y-tono):
   tenant = `E2E_TENANT_ID` real, backend real, data-testids reales, asserts con polling.
4. **(opcional) prohibited-phrases**: `X-User-ID` opcional en el GET BE.

## Definición de DONE

Suite E2E lisa-marca **determinista verde** (0 flaky en 3 corridas consecutivas) contra backend real, con
`make dev-vitalia` levantado, usando el tenant autenticado real. Wire de los `e2e_test` a los scenarios del
cap `lisa-marca` (mueve la cap de declared-live → verified-live de verdad).

## Estado

`idea` · ratificada por Chris (follow-up de `arreglar-guardado-voz-y-tono`). Lista para `/po`/`/po-ux` lite.

## Rescope 2026-06-02 (revisión de relevancia — Chris: "mantener + rescopear")

Revisión pedida por Chris ("¿sigue siendo relevante? creo que ya lo resolvimos"). Verificado contra
**código de hoy** (no el doc): **NO resuelta**. Lo resuelto fue la story **padre** + la infra que llegó
después, no el DoD propio. Evidencia:

- ❌ `e2e/regression/vitalia-fase2-lisa-marca/fixtures/lisa-marca.fixture.ts:137,252` sigue siendo *"API
  mock base data (NO real BE calls)"* + `page.route("**/api/v1/lisa/marca/{identity,visuals,personality}")`
  con `route.fulfill()`. 10 specs heredan el mock del backend-bajo-prueba (el "verificación = teatro").
- ❌ Specs importan `@playwright/test` directo, no `e2e/fixtures/base.ts` (anti-burbuja, ya existe desde jun-1).
- ❌ Sub-bug #2 vivo: `vitalia/frontend/src/features/lisa/api/marca-voice-api.ts:113` manda
  `"X-User-ID": opts.tenantId` (org UUID como actor del audit-log, no el Clerk userId real).
- ❌ Falso-verde: `capabilities/brand_studio/lisa-marca.yaml` scenarios `status: live` cablean specs
  mockeados (`e2e_test:` líneas 111/160/173/186/199); cap-level `e2e_test: null`. Solo voz-y-tono (l.127)
  apunta a spec real + `verified_real`.
- Git: solo `560a5f54` + `4562140c` tocaron la carpeta e2e — ambos de la story padre. Cero de ESTA.

**Qué cambió desde 2026-05-30 (rescope, la story encogió):**

1. `base.ts` anti-burbuja ya existe → **adoptar**, no construir (rule #37 enforcement layer 7).
2. Rule #37 (dod-live-verify) es ahora estándar cross-brand → de-mock+backend-real = mandato. Esta story =
   aplicar #37 a lisa-marca, no un hallazgo aislado.
3. Fix sistémico tenant-resolution no-clerk-org (`14af22b2`, 35 files) tocó el plumbing de auth → **el
   root-cause primario de la race de Clerk (sección arriba) está parcialmente STALE**. Antes de diseñar,
   **re-reproducir el flake contra HEAD** — la pantalla de error puede comportarse distinto hoy.

**Scope rescopeado (lo que falta de verdad):** (a) re-repro flake post-`14af22b2`; (b) adoptar `base.ts`;
(c) de-mock las 10 specs lisa-marca restantes (tenant real + GET/PATCH real + testids reales); (d) sub-bug
#2 (plumbear Clerk userId real al `X-User-ID`); (e) re-cablear los `e2e_test` de la cap a specs reales +
mover scenarios mockeados de `live`-falso a verificado real. Sub-bug #1 (prohibited-phrases 422): revalidar
si sigue vivo durante el (a).

## Re-repro 2026-06-02 (HEAD, post-`14af22b2`) — phase (a) HECHA · root-cause REVISADO

Corrido contra el stack dev real (BE :8002 + FE :3002 UP, sesión Clerk + storageState, `--project=smoke`).
Probé los specs **real-backend** de la story padre (`arreglar-guardado-voz-y-tono/`, donde vivía la race) +
desfixme'é temporalmente los reload-persist quarantined (revertido después; specs intactos). Hallazgos:

1. **La race original de Clerk auth-readiness (GET /personality → "No se pudo cargar") está RESUELTA/STALE.**
   La página hidrata confiable hoy: el bloque de voz persiste **5/5** tras reload; el arquetipo persiste
   **5/5** (con assert que pollea). Cero ocurrencias de "No se pudo cargar" en ~30 corridas. `14af22b2`
   (tenant-resolution no-clerk-org) + el `retry:5` de `VozTonoView` cerraron esa race. → **La dirección de
   fix candidata #1 (Clerk-ready gate) y #2 (query resiliente) del checkpoint quedan OBSOLETAS** — ya no es
   el problema.

2. **El "flake" de reload-persist era un assert NO web-first del harness (defecto de test, no de producto).**
   `poms/voz-tono-section.pom.ts:180 getSelectedArchetype()` lee `data-selected="true"` **una sola vez**, y
   `waitForLoaded()` (línea 132) solo espera a que un card *estático* sea visible — NO a que el GET hidrate
   la selección. → lee `null` determinista (fallo **5/5**). Reemplazando por assert web-first
   (`expect(card).toHaveAttribute("data-selected","true",{timeout:15_000})`) → **5/5 verde**. El test del
   bloque pasaba porque ya usaba `toHaveValue(..., {timeout:15_000})` (pollea). **Misma clase de bug:
   cualquier assert que lea estado hidratado sin polling.** Este es el fix real de determinismo (no un
   auth-gate).

3. **Flake real residual en `voz-arquetipo-autosave.spec.ts:251`** ("badge no llega a error"): listener
   dangling `authedPage.on("response", () => void pom.getAutosaveStatus().then(...))` sin `page.off` →
   llamada tardía corre durante teardown → `locator.getAttribute: Target page... has been closed`
   (`pom.ts:230`). 1 flaky en `repeat-each=3`. **Defecto de higiene de test** (fire-and-forget sin cleanup).

4. **Sub-bug #1 (prohibited-phrases 422) VIVO — y el e2e lo ENMASCARA.** Logs BE muestran 422 (browser real:
   `fetchClient` NO inyecta `X-User-ID` en ese GET) **y** 200 (el forwarding fixture inyecta `X-User-ID`
   manual — `voz-arquetipo-autosave.spec.ts:137`). → el spec "real backend" miente sobre el contrato FE.
   Fix recomendado: **BE hace `X-User-ID` opcional en ese GET** (read por tenant+país, no necesita actor).

5. **Sub-bug #2 confirmado vivo:** `vitalia/frontend/src/features/lisa/api/marca-voice-api.ts:113`
   `"X-User-ID": opts.tenantId` (org UUID como actor del audit-log en vez del Clerk userId).

**Nota de mecánica para `/architect`:** los specs "real backend" NO son same-origin — usan
`page.route("**/api/v1/**")` que *forwardea* a `http://localhost:8002` (FE :3002 no proxya `/api`). El de-mock
de las 10 specs lisa-marca debe replicar ese forwarding (o introducir un proxy real), NO `route.fulfill()`
con data canned.

**Scope afinado post-re-repro (reemplaza/precisa el del Rescope):**
- (b) adoptar `e2e/fixtures/base.ts` (anti-burbuja) en los specs lisa-marca.
- (c) de-mock las 10 specs lisa-marca: tenant real + GET/PATCH real vía forwarding + testids reales.
- **(c2 NUEVO — el fix real de determinismo)** reemplazar asserts no-web-first por polling en los POMs
  (`getSelectedArchetype` → `waitForSelectedArchetype(slug)`; cualquier read de estado hidratado → web-first).
- **(c3 NUEVO)** quitar listeners dangling fire-and-forget (`page.on("response")` sin `page.off`/cleanup).
- (d) sub-bug #2: plumbear Clerk userId real al `X-User-ID` de los endpoints marca.
- (e) re-cablear los `e2e_test` de la cap a specs reales + mover scenarios de live-falso a verificado real.
- **(f NUEVO)** des-quarantine los 5 `authTest.fixme` de `arreglar-guardado-voz-y-tono/` (pasan una vez que
  los asserts pollean) — su quarantine asumía la race de Clerk que ya no existe.
- sub-bug #1 (prohibited-phrases): BE `X-User-ID` opcional en el GET (decidir si entra en esta story o spin-off).

**Direcciones OBSOLETAS** (no perseguir): #1 Clerk-ready gate, #2 query resiliente a auth-transitoria
(la race ya está resuelta; el `retry:5` queda como red de seguridad, no hay que formalizar nada nuevo).

## Sesión 2026-06-03 (resume) — logo R2 real + cierre-prep + decisiones Chris aplicadas

Chris respondió las 3 decisiones que gateaban el cierre:
1. **Logo R2:** implementar AHORA reusando el módulo engine `assets`. ✅ HECHO.
2. **Clerk flaky:** aceptar retries + harness-story. ✅ HB-28 abierta.
3. **Demo:** preparar demo-script + dar la ruta. ✅ `demo-script.md` creado.

### Logo R2 (T-5 — un-stub, decisión Chris)
El upload de logo era stub (descartaba bytes, `logo:{uuid}` falso). Ahora consume el engine
`core/luana-core-assets` (`AssetsService.upload_asset`, NO se recreó nada — anti-duplication; mismo patrón que
`clinics/assets_proxy_router` D-3). Storage backend = `settings.STORAGE_PROVIDER`.
- **Código** (commit `c67bb62d`): `marca_service.upload_logo` consume AssetsService → persiste `asset.public_url`
  real en `visuals.logo_url`; `delete_logo` elimina el asset del storage. TDD 3 tests RED→GREEN. marca suite
  14/14 · ruff clean · arch fitness 119/119 · cero core/ editado.
- **Infra R2 provisionada** (con `CLOUDFLARE_API_TOKEN`, Chris autorizó): bucket `vitalia-assets-dev` + dominio
  público gestionado `pub-3de7ae1d…r2.dev` + token S3 (access_key_id 32-char + secret sha256). Creds en
  `vitalia/.env.dev` (gitignored) → `STORAGE_PROVIDER=R2` + `R2_*`. ⚠️ el secret de R2 vive SÓLO en
  `vitalia/.env.dev` (Cloudflare lo muestra 1 vez; rotar = recrear token). ⚠️ `STORAGE_PROVIDER=R2` es global
  → los avatares de doctores (lisa-doctores, mismo AssetsService) también van a R2 ahora (end-state correcto).
- **Backend recreado** con `boto3` (estaba ausente en la imagen vieja — causa real del "T-BE-7 deferred") +
  env R2 cargado. `boto3 1.43.6` + `STORAGE_PROVIDER=R2` confirmados en container.

### dod_evidence (live-verify fresco, esta sesión)
```yaml
dod_live_verified: pending_demo_signoff   # técnico hecho; gate final = sign-off Chris
dod_env: "make dev-app-vitalia → stack UP (dev-app 307 + api-health 200); BE recreado STORAGE_PROVIDER=R2"
dod_evidence:
  - action: "nombre/identidad autosave (lisa-marca-identidad-autosave.spec.ts ×1, backend real)"
    observed: "5 passed + 1 flaky-retry (throttle Clerk). BE log: PATCH /identity 200 + GET round-trip 200"
  - action: "colores + tipografía (PATCH /visuals)"
    observed: "GET /visuals 200 live (500-fix aguanta) + BE integration test_marca_visuals_missing_attr 5/5 vs DB real"
  - action: "logo R2 (AssetsService.upload_asset, live creds R2)"
    observed: "R2StorageStrategy activa → upload a bucket vitalia-assets-dev → GET URL pública 200 image/png (renderable)"
verified_at: 2026-06-03
```

### Estado tickets
- T-1 (de-mock+POM) `pushed` e5ad6af6 · T-2 (FE actor) `pushed` 4bf94366 · T-3 (BE headers) `pushed` 5ef8cdd4
- **T-4 (cap re-wire)** HECHO esta sesión: change_log + identidad `verified_real` + presencia-web → `partial` +
  2 flaky con caveat retry. Bidirectional HARD 96/96.
- **T-5 (logo R2)** HECHO: commit `c67bb62d` + R2 provisionado + live-verify.

### PENDIENTE (gateado por Chris)
1. **Chris ejerce `demo-script.md`** contra dev-app + firma `demo_signoff` (rule #37 §5 — NO `done` sin esto).
2. `/auditor` → APPROVED → `/pm-vitalia` merge → archive.

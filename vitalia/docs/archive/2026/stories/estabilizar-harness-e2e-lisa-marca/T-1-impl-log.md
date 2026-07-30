# T-1 impl-log — FE-tests: de-mock + web-first + fixture forwarding shared + des-quarantine

> Owner ejecución: builder-frontend (Sonnet). Orchestrator: /dev-team (Opus).
> Surface: `vitalia/frontend/e2e/**` (SOLO tests; cero prod, cero BE, cero core).
> Depende de: T-3 (`5ef8cdd4`) + T-2 (`4bf94366`) — pushed. El BE real ya tiene header opcional + actor real; el FE-prod ya manda el Clerk userId.

## Decisiones del orchestrator (resuelven flags del CONTEXT-BRIEF §11)

**M1 — grep-gate SC-2 vacuo (FIX en T-1):** el `sc2_no_mock_backend_bajo_prueba` de `04-validators.yaml` matchea `route.fulfill.*lisa/marca/(identity|visuals|personality)` en una sola línea → da **0 hoy** aunque el mock es rampante (es multi-línea: `page.route("...identity")` y `route.fulfill()` líneas después) → pasa vacuo. **El builder ajusta el pattern del validator** a la señal real: `page.route\(.*api/v1/lisa/marca/(identity|visuals|personality|contact|trust-signals)` → 0 tras de-mock. Documentar el cambio del validator en T-1-result.md (es una corrección de correctness del gate, no scope creep).

**M3 — scope de-mock (RN-1):** de-mockear **TODOS los reads del backend-bajo-prueba marca**: `identity`, `visuals`, `personality`, `contact`, `trust-signals`, `voice-preview` (son endpoints reales del marca router). Forwardear al BE real vía la fixture compartida.
- **Mocks que SÍ se conservan (excepción legítima, documentar c/u):** (a) fallas inyectadas para specs de error/timeout (ej. `503` en `voz-autosave-error`, `lisa-marca-autosave-timeout`, `network-failure.ts`) — eso NO es mockear el backend-bajo-prueba, es inyectar una falla para ejercer el error-path; (b) dependencia genuinamente externa/no-determinista CON justificación escrita. Si `voice-preview` resulta LLM-backed no-determinista → stub documentado SOLO en specs que NO aserten voice-preview; si es determinista → de-mock real.
- `large-dataset.fixture.ts`: si provee data canned como respuesta del backend-bajo-prueba → preferir seed real; si es perf-spec con dataset grande imposible de sembrar rápido → excepción documentada. El builder decide por RN-1 + documenta.

## Trabajo (deliverables 06-tickets T-1)

1. NEW `e2e/fixtures/real-backend-forward.fixture.ts` (LIFT del inline ×3 del parent): `mergeTests(base.ts anti-burbuja, auth.fixture Clerk storageState)` + `page.route('**/api/v1/**')` → `page.request.fetch(:8002)` forwarding. Export `test/expect/TENANT_ID/BACKEND_API_URL`. Anti-duplicación: el forwarding vive ACÁ, no inline en 14 specs.
2. MODIFY `vitalia-fase2-lisa-marca/fixtures/lisa-marca.fixture.ts`: REMOVE `setupLisaMarcaMocks` (los `route.fulfill` sobre el backend-bajo-prueba); re-export desde la shared.
3. MODIFY `vitalia-fase2-lisa-marca/poms/*.pom.ts` (4 POMs): once-reads → **web-first** (`getSelectedArchetype()` → `waitForSelectedArchetype(slug,{timeout})`; cualquier estado hidratado → `expect(...).toHave*({timeout})`). **Este es el fix REAL de determinismo (B3).**
4. MODIFY 11 specs `vitalia-fase2-lisa-marca/*.spec.ts`: import de la shared; eliminar `route.fulfill` inline sobre backend-bajo-prueba; round-trips reales; el timeout-spec usa `503` inyectado + `test.use({failOnRuntimeError:false})`.
5. MODIFY `arreglar-guardado-voz-y-tono/poms/voz-tono-section.pom.ts`: +`waitForSelectedArchetype(slug,{timeout})`.
6. MODIFY `arreglar-guardado-voz-y-tono/*.spec.ts`: des-quarantine los **5 `authTest.fixme`** (asserts web-first); eliminar `page.on("response", () => void ...)` fire-and-forget sin `page.off` (B4 / RN-4).
7. FIX `04-validators.yaml` sc2 grep pattern (M1).
8. Todos los specs importan de `base.ts` (vía la shared `mergeTests`), NUNCA `@playwright/test` directo (RN-2 anti-burbuja).

## Verificación (split builder ↔ orchestrator)

- **Builder:** `npx tsc --noEmit` + `npx eslint e2e/` verde + grep-gates SC-2/SC-3/SC-5 (0). Intenta correr la suite live; si el worktree aislado no puede (sin node_modules/browsers propios), lo documenta y deja la verificación live al orchestrator.
- **Orchestrator (yo, post-integración, stack UP en mi worktree):** corro LIVE contra `make dev-vitalia` (BE :8002 + FE :3002):
  - SC-1: `e2e/regression/vitalia-fase2-lisa-marca/ --repeat-each=3 --workers=1` → 0 flaky · 0 failed.
  - SC-4: `e2e/regression/arreglar-guardado-voz-y-tono/ --repeat-each=5` → 5 fixme des-quarantined deterministas.
  - SC-2/3/5 grep-gates + base.ts runtime.
  Esto es la verificación REAL (no 200-teatro) que cierra el determinismo. DoD #37 live-verify se cierra acá + en T-4/demo.

## Iteration log

### iter-1 — builder-frontend (Sonnet) — 2026-06-03

**Resultado:** tests-passing (builder gates verde). Live suite deferida al orchestrator (ver § razón abajo + T-1-result.md).

**Hecho (22 archivos: 20 M + 1 D + 1 new):**
- NEW `e2e/fixtures/real-backend-forward.fixture.ts` — LIFT del forwarding inline. `mergeTests(base.ts, auth+forwarding)`. Headers reales del browser (B6 mask removido).
- D `…/vitalia-fase2-lisa-marca/fixtures/voice-preview-mock.ts` — obsoleto (voice-preview determinístico, de-mockeado).
- M fixtures: `lisa-marca.fixture.ts` (REMOVE setupLisaMarcaMocks + buildMock*), `large-dataset.fixture.ts` (de-mock canned 50-item), `network-failure.ts` (`continue()`→`fallback()` en reads).
- M POMs: lisa-marca `voz-tono-section.pom.ts` + `lisa-marca-page.pom.ts` (+web-first `waitForSelectedArchetype`/`waitForActiveSubsubtab`); parent `voz-tono-section.pom.ts` (+`waitForSelectedArchetype`).
- M 11 specs lisa-marca (de-mock + web-first + import desde shared).
- M 3 specs parent (de-mock + 5 fixme des-quarantined + listeners con `.off`).

**Gates builder (literales):**
- `tsc --noEmit` → 0 errores (worktree source + deps shared symlink temporal, tsc 5.9.3).
- `eslint <22 archivos scope> --max-warnings 0` → 0 errores · 0 warnings.
- SC-2 (M1 new pattern) → PASS (0 mocks). SC-3 → PASS (0 imports directos). SC-5 → PASS (0 dangling). arch_no_new_forwarding_duplication → PASS (0 inline). fixme=0. skip=0. cross-brand(mis archivos)=0.

**M1 deliverable 7:** el `04-validators.yaml` vive committed en `wip/vitalia` (`22f25e4d`), NO en este worktree aislado (branched de `main`). El harness bloquea editar el shared checkout. **PATCH verbatim documentado en T-1-result.md § M1 para que el orchestrator lo aplique al integrar en `wip/vitalia`.** Los grep-gates ya corrieron con el pattern corregido (0 mocks).

**Por qué la live suite NO la corrí (no inventé verde):**
1. Worktree aislado branched de `main` (`09e12ae9`), NO de `wip/vitalia` (`4bf94366`). El prod fix de T-2 (`marca-voice-api.ts` → `X-User-ID: opts.userId`) NO está acá (sigue `opts.tenantId`). Correr SC-6/SC-7 fallaría por falta del actor real.
2. Sin `pnpm install`/browsers propios + sin stack `make dev-vitalia` UP. Corrí tsc/eslint vía symlink temporal a deps del shared checkout (ya removido).

→ Orchestrator corre SC-1 ×3 + SC-4 ×5 + SC-3b/5b/6/7 LIVE en su worktree `wip/vitalia` (T-2/T-3 integrados + stack UP).

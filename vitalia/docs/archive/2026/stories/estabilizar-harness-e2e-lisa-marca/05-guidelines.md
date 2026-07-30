# 05-guidelines · estabilizar-harness-e2e-lisa-marca

> Guías de implementación enforceable para los builders. Naturaleza: bugfix-lite de harness E2E + 2 sub-bugs
> de auth-header. Diseñado sobre el root-cause FRESCO (re-repro 2026-06-02). Las direcciones "Clerk-ready gate"
> y "query resiliente" del checkpoint viejo están OBSOLETAS — NO perseguirlas.

## Must-load skills (por ticket — enforceable)

| Ticket | Surface | must_load_skills |
|---|---|---|
| T-1 | FE-tests (de-mock + web-first + des-quarantine + fixture forwarding) | `playwright-expert` (SSoT E2E) + `frontend-expert` |
| T-2 | FE-prod sub-bug #2 (actor audit real) | `frontend-expert` + `brand-expert` (contexto cap lisa-marca / HIPAA-lite "quién") |
| T-3 | BE sub-bug #1 (X-User-ID opcional) + #2b (actor desde clerk_sub) | `backend-expert` |
| T-4 | Docs cap re-cable | `brand-expert` (contexto cap) — opcional `frontend-expert` |

## Patterns REQUIRED

### P1 — Forwarding a backend real vía fixture compartida (NO inline)
- El forwarding `page.route("**/api/v1/**")` → `page.request.fetch(BACKEND_API_URL)` vive UNA vez en
  `vitalia/frontend/e2e/fixtures/real-backend-forward.fixture.ts` (LIFT del inline de la story padre).
- Todos los specs de-mockeados importan `{ test, expect, TENANT_ID }` de esa fixture. NUNCA copian el bloque.
- `BACKEND_API_URL = process.env.VITALIA_BE_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8002"`.

### P2 — Composición con base.ts (anti-burbuja · rule #37)
- La fixture compone el gate anti-burbuja: `import { mergeTests } from '@playwright/test'` +
  `mergeTests(runtimeGateFromBaseTs, authedForwardingTest)`. Así pageerror/console/hydration/4xx-5xx/overlay
  Next corren en todos los specs de-mockeados.
- Opt-out SOLO en specs que ejercen un error a propósito (timeout/503 inyectado): `test.use({ failOnRuntimeError: false })`.

### P3 — Asserts web-first sobre estado hidratado (el FIX REAL de determinismo)
- Cualquier lectura de estado que dependa del GET (`data-selected`, valor de textarea, presencia de card) usa
  aserción auto-retry: `await expect(locator).toHaveAttribute("data-selected","true",{timeout:15_000})` /
  `expect(textarea).toHaveValue(value,{timeout:15_000})` / `expect(locator).toBeVisible({timeout})`.
- En POMs: `getSelectedArchetype()` (once-read) → `waitForSelectedArchetype(slug, {timeout})` (web-first).
- Para "función que devuelve un valor y se asserta": `expect.poll(() => fn(), {timeout})`.
- Referencia canónica: Playwright web-first assertions (accessed 2026-06-02, `playwright.dev/docs/test-assertions`).

### P4 — Sin listeners dangling (RN-4)
- Para asertar "el badge nunca llegó a error": `await expect(badge).not.toHaveAttribute("data-state","error")`
  después de `waitForAutosaveSaved()`.
- Si se DEBE observar transiciones: registrar handler con cleanup explícito (`page.on(...handler); ...; page.off(...handler)`)
  antes del teardown.

### P5 — Round-trips contra el tenant real (sin seed canned)
- Los specs ejercen `read inicial → editar → assert que el editado persiste` (como `voz-arquetipo-autosave.spec.ts`
  lee el arquetipo inicial → switch al "otro" → assert). NO asertar valores de seed fijos (`brandName === "Salud Vitalia"`)
  que no existen en el tenant E2E real.
- Tenant = `process.env.E2E_TENANT_ID` (el del owner Clerk `dr.demo@vitalialat.com`).

### P6 — Sub-bug #1 (BE): X-User-ID opcional en GET prohibited-phrases
- `user_id: str | None = Header(alias="X-User-ID", default=None)` en `get_prohibited_phrases`.
- `X-Tenant-ID` SIGUE required (tenant-isolation). `response_model=ProhibitedPhrasesListDTO` se MANTIENE.
- `user_id` NO se parsea ni usa (es un read tenant+país). NO tocar otros endpoints.

### P7 — Sub-bug #2 (FE+BE): actor de audit REAL
- **FE (T-2):** `marca-voice-api.ts::updatePersonality` deja de mandar `X-User-ID: opts.tenantId`. Manda
  `X-User-ID: opts.userId` (el Clerk userId real, ya disponible vía `usePersonalityAutosave` → `useAuth().userId`).
- **BE (T-3, #2b):** el PATCH `/personality` (y los PATCH marca que auditan) resuelven el actor desde el `clerk_sub`
  del JWT Bearer vía el resolver canónico `iam/.../clinic_resolver.py::_resolve_user_uuid` (CONSUMIR, no recrear)
  → `users.id` UUID. El `X-User-ID` deja de ser la fuente del actor UUID.
- RBAC (`require_brand_owner_access`) SIGUE leyendo `X-User-Role` — ortogonal al actor. NO romperlo.
- Resultado verificable: fila `vitalia_audit_log` con `user_id = users.id` real (≠ tenant_id).

## Patterns FORBIDDEN

- ❌ `route.fulfill()` con data canned sobre `**/api/v1/lisa/marca/{identity,visuals,personality}**` (false-green — la razón de la story).
- ❌ `import { test, expect } from '@playwright/test'` directo en specs lisa-marca (debe ser vía `real-backend-forward.fixture` → base.ts).
- ❌ `page.on(...)` / `authedPage.on(...)` con callback fire-and-forget (`void promise`) sin `page.off`/cleanup.
- ❌ Once-read de estado hidratado (`getAttribute`/`textContent`/`inputValue` una vez) para asertar — usar web-first.
- ❌ `page.waitForTimeout(...)` como espera de hidratación (hard-wait anti-pattern).
- ❌ Inyectar `X-User-ID` a mano en el forwarding para enmascarar el 422 de prohibited-phrases (el contrato se arregla en BE).
- ❌ Plumbear `X-User-ID: opts.tenantId` (actor falso) o un Clerk userId crudo a un endpoint que hace `UUID(user_id)` sin que el BE lo resuelva.
- ❌ Copiar el bloque de forwarding inline en cada spec (NO-NEW-LAYER: vive en la fixture).
- ❌ Tocar `core/luana-core-*/src/` (engine boundary — sub-bugs viven en `vitalia/backend/src/modules/vitalia/brand_studio` + consumo iam).
- ❌ Tocar otra brand (`nicolify/comunify/lupulo`).
- ❌ Tocar specs de OTRAS features (valeria/camila/doctores) — regression_guard.
- ❌ Migrar el transporte e2e de forwarding a proxy Next real (out-of-scope, otra story).
- ❌ Crear un resolver Clerk→UUID nuevo (consumir `_resolve_user_uuid`).
- ❌ Flipear cualquier default flag.

## Files in scope (whitelist)

**T-1 (FE-tests):**
- `vitalia/frontend/e2e/fixtures/real-backend-forward.fixture.ts` (NEW)
- `vitalia/frontend/e2e/regression/vitalia-fase2-lisa-marca/fixtures/lisa-marca.fixture.ts` (MODIFY — de-mock)
- `vitalia/frontend/e2e/regression/vitalia-fase2-lisa-marca/poms/*.pom.ts` (MODIFY — web-first)
- `vitalia/frontend/e2e/regression/vitalia-fase2-lisa-marca/*.spec.ts` (×11, MODIFY)
- `vitalia/frontend/e2e/regression/arreglar-guardado-voz-y-tono/poms/voz-tono-section.pom.ts` (MODIFY — waitForSelectedArchetype)
- `vitalia/frontend/e2e/regression/arreglar-guardado-voz-y-tono/*.spec.ts` (MODIFY — des-quarantine + sin dangling)

**T-2 (FE-prod):**
- `vitalia/frontend/src/features/lisa/api/marca-voice-api.ts` (MODIFY — X-User-ID = userId real)
- `vitalia/frontend/src/features/lisa/hooks/__tests__/usePersonalityAutosave.test.ts` (coverage_update)
- `vitalia/frontend/src/features/lisa/components/marca/voz-y-tono/__tests__/VozTonoView.test.tsx` (coverage_update si aplica)

**T-3 (BE):**
- `vitalia/backend/src/modules/vitalia/brand_studio/api/routers/marca_router.py` (MODIFY — sub-bug #1 GET + #2b actor resolver)
- `vitalia/backend/tests/modules/vitalia/brand_studio/` (new_coverage — prohibited-phrases optional)

**T-4 (Docs):**
- `vitalia/docs/product/capabilities/brand_studio/lisa-marca.yaml` (MODIFY — re-cable e2e_test + verified_real + change_log)

## Stack / commands (native-first)

```bash
WS=$(git rev-parse --show-toplevel)
# Stack dev
make dev-vitalia          # BE :8002 + FE :3002
# o make dev-app-vitalia → dev-app.vitalialat.com (live-verify owner Clerk dr.demo@vitalialat.com)

# FE gates
cd ${WS}/vitalia/frontend && npx tsc --noEmit
cd ${WS}/vitalia/frontend && npx eslint e2e/ src/features/lisa/api/ --max-warnings 0 --cache
cd ${WS}/vitalia/frontend && npx vitest run src/__tests__/architecture/
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke e2e/regression/vitalia-fase2-lisa-marca/ --repeat-each=3 --workers=1

# BE gates
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/ruff check src/modules/vitalia/brand_studio/ && ${WS}/.venv/bin/mypy --strict src/modules/vitalia/brand_studio/api/routers/marca_router.py
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/architecture/ -x -q
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/modules/vitalia/brand_studio/ -k prohibited_phrases -v
```

## DoD evidence (Critical Rule #37)

Antes de cerrar `developing → developed`, registrar en `checkpoint.md::dod_evidence`:
- SC-6: PATCH personality real (Chrome MCP, owner Clerk) → fila `vitalia_audit_log` con actor UUID real (≠ tenant_id) + leído Network + Console (0 burbuja).
- SC-7: abrir voz-y-tono en browser real → GET prohibited-phrases 200 (Network panel, sin header inyectado) + docker logs sin 422.
- SC-1/SC-4: suite ×3 + fixme ×5 → 0 flaky (output adjunto).
- `demo-script.md` lite (4 secciones): SETUP (make dev-vitalia) / HAPPY (cambiar arquetipo + guardar → persiste) / EDGE (frase prohibida warning) / TEARDOWN.

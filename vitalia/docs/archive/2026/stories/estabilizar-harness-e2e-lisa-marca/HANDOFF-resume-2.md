<!-- voseo-allowed: handoff interno -->
# HANDOFF 2 — continuar review live de `estabilizar-harness-e2e-lisa-marca`

> Continuación de la sesión que hizo el rebuild del layer e2e + el keystone + los fixes de
> visuals/logo. Pegá el bloque "PROMPT PARA PEGAR" en una conversación nueva.

---

## PROMPT PARA PEGAR

```
/dev-team vitalia estabilizar-harness-e2e-lisa-marca — continuar la review LIVE + cierre. Leé primero vitalia/docs/product/stories/estabilizar-harness-e2e-lisa-marca/HANDOFF-resume-2.md (estado completo). El keystone + el de-mock + el rewrite de POMs + los fixes de visuals/colores/tipografía/logo-auth YA están hechos y verificados live (commits 206fb151, e5ad6af6, 58f8a768 en wip/vitalia). Stack dev-app UP: levantá con `make dev-app-vitalia` y verificá contra https://dev-app.vitalialat.com (usuario dr.demo@vitalialat.com, creds en vitalia/.env.dev → DEV_APP_TEST_*). Chris está revisando Identidad live. Estado: nombre+colores+tipografía guardan REAL; logo-upload da 201 pero es STUB (no R2, bytes descartados → no se muestra). Pendiente: (1) que Chris confirme colores/tipografía live tras F5; (2) decisión logo R2 (stub conocido — story aparte o implementar); (3) decisión Clerk-FAPI scaling para el 0-flaky purista (recomiendo aceptar retries + harness-story); (4) demo-script.md formal + sign-off Chris; (5) T-4 re-cablear cap lisa-marca.yaml a specs honestos + verified_real; (6) /auditor → merge. NO marques done sin sign-off de Chris (rule #37). Continuá el live-verify donde Chris lo dejó.
```

---

## ESTADO (cierre sesión, contexto lleno)

- **Branch:** `wip/vitalia` @ `58f8a768` (todo pusheado). Worktree: `~/Proyectos/luana-vitalia`.
- **Story:** `developing`, módulo `brand_studio`. Tipo bugfix-lite.
- **Stack:** UP. **dev-app:** `https://dev-app.vitalialat.com` (307 OK, Clerk real). Levantar: `make dev-app-vitalia` (idempotente, desde ESTE worktree — footgun cross-worktree).
- **Tenant de prueba:** `e69a691d-070e-5caf-a053-6e74642ec100`, owner `dr.demo@vitalialat.com` (creds en `vitalia/.env.dev` → `DEV_APP_TEST_EMAIL`/`DEV_APP_TEST_PASSWORD`).
- **Lock:** `code:brand_studio` adquirido por esta sesión (auto-libera por PID muerto).

### Commits de esta sesión (en wip/vitalia)
- `206fb151` keystone: FE↔BE identity contract (`marca.ts` mapeo+null-safety) + BE visuals 500 (`marca_service` getattr). TDD.
- `e5ad6af6` rewrite completo 4 POMs phantom→ARIA + borrado de ficción + de-fiction 7 specs. Suite 94% ×3.
- `58f8a768` visuals colores/tipografía (PATCH /visuals 422→200 whitelist) + logo auth (403→201 X-User-ID+rol) + dict-reload 500 (`_coerce_visuals`). TDD.
- (+ commits de chris-input.md con bitácora)

> ⚠️ Commits hechos con `STORY_CLOSURE_GATE_SKIP=1` por **pathspec exacto**: una sesión paralela tenía `vitalia-bugfix-shell-nav-scroll-errors` en reviewing (módulo distinto, ADR-009 lo permite). Si el gate sigue bloqueando, mismo patrón: commit por rutas exactas de lisa-marca con el skip documentado.

## YA HECHO + VERIFICADO LIVE (no rehacer)

1. **Keystone autosave identidad** — el de-mock destapó mismatch de contrato FE↔BE (BE da `{name, tagline:null}`, FE consumía forma ficticia de nicolify; `tagline:null` rompía zod → autosave muerto). Fix verificado: `PATCH /identity 200` + persiste. Chris confirmó "A) pasa".
2. **GET /visuals 500** (engine `BrandIdentity` sin `visuals`) → getattr defensivo. Chris confirmó "B) pasa".
3. **Colores + tipografía** — `PATCH /visuals` daba 422 (FE mandaba objeto completo, BE `extra="forbid"` 6 campos). Fix: whitelist 6. Verificado live por mí: `PATCH /visuals 200`. **Falta que Chris confirme tras F5.**
4. **Logo auth** — `POST /logos` daba 403 (sin X-User-ID/rol). Fix: headers de actor + plumbeo userId. Verificado: `201 Created`.
5. **dict-reload 500** (que el fix de colores destapó) — visuals persistido recarga como dict → `_coerce_visuals`. Verificado: round-trip `PATCH 200 → GET 200`.
6. **Suite lisa-marca = 136/144 (94%) verde-determinista ×3** contra backend real. 9/11 specs 100%.

## ⚠️ LOGO = STUB (NO R2) — hallazgo importante

`marca_service.py:upload_logo` (~línea 1000) es **stub deliberado** (03-arch § 1.3, promotion proposal pending):
- Calcula el base64 del archivo y lo **DESCARTA** (línea ~1029, `_ = ...`).
- Persiste `logo_url = "logo:{uuid}"` (referencia falsa, NO URL renderizable).
- → El POST da 201 pero la imagen **no se guarda ni se muestra**. NO es R2/S3.
- Mi fix corrigió solo el **auth** (403→201). El storage real es feature nueva.
- **Decisión pendiente Chris:** dejar stub + NO venderlo como funciona (recomiendo) → story aparte "logo→R2" (bucket+creds+presigned), o implementar ahora (escala scope).

## PENDIENTE (cierre)

1. **Chris confirma colores+tipografía** live tras F5 (logo ya sabemos que es stub).
2. **Decisión logo R2** (stub conocido → backlog/story aparte recomendado).
3. **Decisión Clerk-FAPI scaling** — los 2 residuales del ×3 (`large-dataset:92` + `voice-warning:127`) son autosave-tests que corren tarde + el Clerk dev-FAPI se throttlea bajo 144 page-loads. NO es bug de test. Recomiendo: aceptar retries=1 como verde-de-infra-externa + abrir harness-story para el scaling de Clerk (reuso token/context o tier pago). El otro camino (tocar auth fixture) es riesgo alto.
4. **demo-script.md** formal (template `docs/specs/templates/demo-script-template.md`) + `demo_signoff` de Chris en checkpoint.
5. **T-4** — re-cablear `vitalia/docs/product/capabilities/brand_studio/lisa-marca.yaml`: los `e2e_test` de scenarios `status:live` apuntan a specs ahora honestos + `verified_real`.
6. **`dod_evidence`** en checkpoint.md + `/auditor` → `/pm-vitalia` merge → archive.

## SETUP env para tests (CRÍTICO)
```
# e2e live:
WS=$(git rev-parse --show-toplevel); set -a; source ${WS}/vitalia/.env.dev; set +a
export E2E_BASE_URL=http://localhost:3002
cd ${WS}/vitalia/frontend
npx playwright test --project=smoke e2e/regression/vitalia-fase2-lisa-marca/ --workers=1 --retries=1

# BE pytest native (DB real) — sin el export POSTGRES_DSN los integration skipean (falso verde):
WS=$(git rev-parse --show-toplevel); cd ${WS}/vitalia/backend
set -a; source ${WS}/vitalia/.env.dev; set +a
export POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=5435
export POSTGRES_DSN="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:5435/${POSTGRES_DB}"
${WS}/.venv/bin/pytest tests/modules/vitalia/brand_studio/test_marca_visuals_missing_attr.py -p no:randomly
```

## TRAMPAS / NOTAS
- ⚠️ **NO delegar la iteración e2e a builders aislados** — branchean de base divergente (sin de-mock) + no corren live. (Origen: un builder-frontend esta sesión corrió en `.claude/worktrees/agent-*` = base vieja con fixture mockeada; sus POM-edits se adoptaron por copia de archivo, pero sus specs NO — eran pre-de-mock.)
- Clerk dev-FAPI rate-limit: la suite ×3 hammers Clerk → los autosave-tests tardíos fallan. retries=1 cubre la mayoría; el "0 flaky" purista necesita scaling de Clerk.
- Footgun cross-worktree (rule #37): `make dev-app-vitalia` desde ESTE worktree antes de verificar.
- Blueprint del rewrite de POMs: `T-1b-pom-selector-map.md` (mapeo phantom→real + features NOT_RENDERED).

# Runbook — Verificación live contra dev-app.vitalialat.com

> Operativo. Cómo levantar dev-app y ejercer una acción real para verificar. **Doctrina/proceso:** `.claude/rules/definition-of-done-live-verify.md`. **Gate:** `vitalia/docs/architecture/ADR-vitalia-008-dev-app-live-verification-gate.md`.

## TL;DR (un comando)

```bash
make dev-app-vitalia      # stack + tunnel + verifica + imprime URL/creds
```

Si imprime `✅ dev-app LISTO` → ve a verificar. URL: `https://dev-app.vitalialat.com`.

## Qué es

`dev-app.vitalialat.com` = el stack dev real (FE Next.js :3002 + BE FastAPI :8002) expuesto por un **Cloudflare Tunnel locally-managed**, con **Clerk real** y usuario de prueba. Sirve para ejercer flujos autenticados de verdad — lo que `localhost` no permite bien porque el redirect de Clerk necesita un origin público.

- Ingress: `/api/*` → backend `:8002`; resto → frontend `:3002` (mismo subdominio).
- Tunnel ID: `737ae13f-7482-4a57-b5cc-6ae26bea9e69` (cuenta CF vitalia).
- Config: `vitalia/deploy/cloudflared/dev-config.yml` (versionado) + `.credentials/dev-tunnel.json` (gitignored).

## Credenciales de prueba

En `vitalia/.env.dev` (gitignored):

| Var | Para qué |
|---|---|
| `DEV_APP_TEST_EMAIL` = `dr.demo@vitalialat.com` | login (owner tenant Sanaré) |
| `DEV_APP_TEST_PASSWORD` | login UI/automation |
| `CLERK_TESTING_TOKEN_VITALIA` | bypass bot-detection en Playwright/automation |

`public_metadata` del usuario: `role=owner`, `clinicId`, `tenant_id` (tenant Sanaré).

## Verificar — opción A: Chrome DevTools MCP (live, recomendado para "ver que funciona")

Skill: `chrome-devtools-verify`. Pasos típicos:

1. Navegar a `https://dev-app.vitalialat.com`.
2. Login con `DEV_APP_TEST_EMAIL` / `DEV_APP_TEST_PASSWORD`.
3. Ir a la pantalla bajo prueba y **ejercer la acción real** (ej. cambiar un campo → Guardar = PATCH/PUT).
4. Observar el efecto: respuesta network (status real, no solo 200 de un GET), console sin errores, y/o confirmar la fila en DB:
   ```bash
   docker exec luana-dev-vitalia_backend_dev-1 \
     psql "$DATABASE_URL" -c "SELECT id, updated_at FROM personality_profiles ORDER BY updated_at DESC LIMIT 3;"
   ```
5. Anotar 1-3 líneas honestas en `dev_app_verified.evidence` del `checkpoint.md`.

## Verificar — opción B: Playwright autenticado (golden / regression)

Skill: `playwright-expert` + `clerk-testing`. Para el artefacto persistido:

```bash
cd vitalia/frontend
E2E_BASE_URL=https://dev-app.vitalialat.com npx playwright test --project=smoke
```

Usa `setupClerkTestingToken(page)` + storageState. Es lo que queda en la suite para que no se rompa en silencio mañana.

## Diagnóstico (si algo no responde — NO abandonar)

| Síntoma | Acción |
|---|---|
| dev-app timeout / 502 | `docker logs luana-dev-vitalia_cloudflared_dev-1 --tail 30` · re-`make dev-app-vitalia` |
| sign-in loop / bot detected | confirmar `allowed_origins` (Clerk) incluye dev-app · usar testing token |
| sirve código de otro worktree | **footgun:** re-`make dev-app-vitalia` desde tu worktree (ver abajo) |
| falta `.credentials/dev-tunnel.json` | copiar de otro worktree o `bash vitalia/deploy/cloudflared/setup-tunnel.sh` |
| recrear creds desde cero | CF API token en `.env.dev` (`CLOUDFLARE_API_TOKEN`) + tunnel ID — vía CF API/`cloudflared` |

### ⚠️ Footgun cross-worktree

El compose usa project compartido `luana-dev`. Los bind-mounts (incluido el del tunnel) apuntan al worktree desde donde se corrió `up` por última vez. Si construís en `luana-vitalia` pero el stack se levantó desde `luana-platform`, **dev-app sirve el código de `luana-platform`.** Solución: corré `make dev-app-vitalia` desde tu worktree antes de verificar — el script avisa si detecta mismatch.

## Seguridad

- `vitalia/.env.dev` y `.credentials/` son **gitignored** — nunca se commitean.
- El `CLOUDFLARE_API_TOKEN` guardado fue pegado en chat el 2026-05-31 → **rotar** desde el dashboard CF cuando se pueda.

## Referencias

- `.claude/rules/definition-of-done-live-verify.md` — proceso + obligación por skill
- `vitalia/docs/architecture/ADR-vitalia-008-dev-app-live-verification-gate.md` — gate de merge
- `scripts/dev-app-up.sh` — el wrapper que corre `make dev-app-vitalia`
- `vitalia/deploy/cloudflared/{dev-config.yml,setup-tunnel.sh}` — config del tunnel

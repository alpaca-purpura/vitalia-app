# 01-spec.md — vitalia-dev-stack-functional

---
story_id: vitalia-dev-stack-functional
type: service-story
module: vitalia-dev-infra
capability: dev-environment
po_version: 1
last_modified: 2026-05-17T01:50:00Z
ratified_by_chris: false
links:
  story_yaml: null
  prev_commit: "e7dc4a0 feat(dev-tunnels)"
---

## Resumen ejecutivo

Resolver bugs de bootstrap del Dockerfile + compose vitalia para que `make dev-vitalia-tunnel` levante el stack completo (postgres + backend + frontend + cloudflared) y `https://dev-app.vitalialat.com/` responda 200 OK con la app vitalia renderizada y auth Clerk operativa. **Solo dev local.** No toca código de negocio vitalia ni features funcionales.

## Acceptance Criteria (Gherkin AI-resistant)

### Scenario 1 — `happy-stack-up` (`type: happy`)

**Given:**
- Repo en `main` con commit `e7dc4a0` o superior aplicado
- `vitalia/.env.dev` poblado con valores reales (Clerk test keys, OpenAI key opcional, `NEXT_PUBLIC_APP_URL=https://dev-app.vitalialat.com` y bloque tunnel descomentado)
- Cloudflared credentials.json existe en `vitalia/deploy/cloudflared/.credentials/dev-tunnel.json` con `chmod 644`
- No hay containers conflictivos (`docker ps` no muestra otro postgres ocupando 127.0.0.1:5435)

**When:**
- Usuario ejecuta `make dev-vitalia-tunnel`
- Espera 90 segundos para hot-reload init

**Then:**
- `docker ps --filter "name=luana-dev-vitalia"` muestra 3 containers `Up` (backend, frontend, cloudflared) + `luana-dev-luana_postgres_dev-1` Healthy
- `docker logs luana-dev-vitalia_frontend_dev-1` muestra `Next dev ready on http://0.0.0.0:3002` SIN `next: not found`
- `docker logs luana-dev-vitalia_backend_dev-1` muestra `Uvicorn running on http://0.0.0.0:8002` SIN errores de `.venv`
- `docker logs luana-dev-vitalia_cloudflared_dev-1` muestra 4 `Registered tunnel connection` sin retry loops
- `curl -sS -o /dev/null -w "%{http_code}" https://dev-app.vitalialat.com/` retorna `200`
- `curl -sS https://dev-app.vitalialat.com/api/v1/health` retorna JSON con backend status

**Graders:**
- Bash assertions sobre `docker ps`, `docker logs`, `curl` (4 commands, todos must_pass)
- No nuevos warnings BE/FE en logs (ratchet check)

---

### Scenario 2 — `happy-auth-flow` (`type: happy`)

**Given:**
- Stack levantada (Scenario 1 verde)
- Clerk dashboard tenant vitalia configurado con `https://dev-app.vitalialat.com` como Authorized Origin
- Clerk Publishable Key (`pk_test_*`) en `vitalia/.env.dev` válida

**When:**
- Browser abre `https://dev-app.vitalialat.com/`

**Then:**
- Página renderiza sin error de Clerk "Bot traffic detected" o "Frontend API URL is required"
- Hay botón Sign In de Clerk visible
- Click Sign In abre modal Clerk
- Sign up con email test (`test+vitalia@example.com`) flow completa hasta dashboard
- Cookie `__session` set con `Secure=true` (porque CF termina HTTPS aunque origen sea HTTP)

**Graders:**
- Playwright E2E spec `vitalia/frontend/e2e/specs/tunnel-auth.spec.ts` (nuevo) cubre browser flow

---

### Scenario 3 — `backend-db-migration` (`type: edge`)

**Given:**
- Postgres `luana_postgres_dev` levantado por primera vez (volume `luana_postgres_dev_data` vacío)

**When:**
- `make dev-vitalia-tunnel` levanta backend

**Then:**
- DB `vitalia_dev` existe (`SELECT datname FROM pg_database WHERE datname='vitalia_dev'` retorna row)
- `alembic upgrade head` corrió cleanly (tabla `alembic_version` con la última revision)
- Backend NO crashea por DB missing o migration pending

**Graders:**
- Bash: `docker exec luana-dev-luana_postgres_dev-1 psql -U postgres -c "\l" | grep vitalia_dev`
- Bash: `docker exec luana-dev-vitalia_backend_dev-1 sh -c "cd /workspace/vitalia/backend && uv run alembic current"`

---

### Scenario 4 — `idempotent-restart` (`type: negative-edge`)

**Given:**
- Stack ya levantada y funcionando (Scenario 1 verde)

**When:**
- `make dev-down-vitalia` luego `make dev-vitalia-tunnel` (recreate cycle)

**Then:**
- Stack vuelve a `Up` sin requerir `pnpm install` manual ni `docker volume rm`
- node_modules y .venv sobreviven el restart (no se vacían)
- Cloudflared reconnect a CF edge sin error
- `https://dev-app.vitalialat.com/` sigue respondiendo 200

---

### Scenario 5 — `tunnel-down-graceful` (`type: negative`)

**Given:**
- Stack levantada normalmente

**When:**
- `docker stop luana-dev-vitalia_cloudflared_dev-1` (solo cloudflared down, app sigue corriendo)

**Then:**
- `https://dev-app.vitalialat.com/` retorna `530` (Cloudflare error "no connector")
- `curl http://127.0.0.1:3002/` (acceso directo localhost) sigue retornando 200 (FE accesible localmente)
- Backend + DB no se ven afectados (independientes del tunnel)

---

## Open questions (necesitan respuesta de Chris antes /architect)

> Estas preguntas determinan el approach del fix. La respuesta de Chris a cada una redirige el architect a un patrón distinto.

### Q1: Estrategia node_modules FE

**Tres caminos:**

- **A) Eliminar named volume `vitalia_frontend_node_modules` del compose.** El bind mount `./vitalia/frontend:/app` provee node_modules desde host. Pro: simple, no shadow. Contra: requiere `pnpm install` host-side primero (cross-OS issue para macOS devs, pero hoy somos Linux only).
- **B) Cambiar Dockerfile multi-stage:** stage `deps` instala en `/deps/node_modules` y stage `dev` copia + symlinks. Volume named persiste entre rebuilds. Pro: contained. Contra: complejidad Dockerfile.
- **C) Entrypoint que ejecuta `pnpm install --frozen-lockfile` si node_modules está vacío.** Pro: self-healing first run. Contra: 60s+ extra primer arranque.

### Q2: Estrategia `.venv` BE

**Dos caminos:**

- **A) Eliminar named volume `vitalia_backend_venv`** del compose. `uv sync` se ejecuta sobre la bind mount cada arranque. Pro: simple. Contra: 30s+ extra primer arranque por rebuild venv si invalidado.
- **B) Entrypoint `uv sync --frozen` antes del uvicorn.** Detecta venv corrupta + recrea. Pro: self-healing.

### Q3: DB init para `vitalia_dev`

**Tres caminos:**

- **A) `init.sql` en root compose** que crea `vitalia_dev`, `nicolify_dev`, `comunify_dev` databases al inicializar postgres por primera vez.
- **B) Entrypoint backend ejecuta `CREATE DATABASE IF NOT EXISTS` antes de alembic.**
- **C) Manual paso documentado**: usuario corre `docker exec luana_postgres_dev psql -U postgres -c "CREATE DATABASE vitalia_dev;"` post first up.

### Q4: Alembic auto-upgrade

**Dos caminos:**

- **A) Entrypoint backend ejecuta `alembic upgrade head` antes de uvicorn.** Pro: zero-config para dev. Contra: bloquea startup si migration falla.
- **B) Step manual documentado** después del primer arranque.

### Q5: Permisos credentials.json

Actualmente `chmod 644` (world-readable en disk local). Aceptable dev. **¿Codificar el chmod en algún setup script?** o queda como TODO mental?

---

## Approach recomendado (sujeto a ratificación)

| Q | Recomendación | Justificación |
|---|---|---|
| Q1 | **A — eliminar named volume** | Linux-only dev, host pnpm install ya funciona, evita complejidad |
| Q2 | **A — eliminar named volume** | Mismo razonamiento |
| Q3 | **A — init.sql en root compose** | Una sola fuente de verdad, no requiere conocimiento per-brand |
| Q4 | **A — entrypoint auto-upgrade** | DX cero-fricción, dev-only (no aplica a prod) |
| Q5 | **Script `scripts/cloudflared-fix-perms.sh`** que chmod 644 los 3 credentials.json | Idempotente, documentado en runbook |

## Dependencias entre fixes

```
Q1 (FE) ─────┐
Q2 (BE) ─────┼─→ stack levanta
              │
Q3 (DB) ─────┤
Q4 (alembic) ┘
```

Q1 y Q2 son independientes. Q3 debe completarse antes que Q4 (no se puede upgrade en DB que no existe).

## Out of scope (recordatorio)

- Nicolify + Comunify mismas bootstrap issues (si existen): SCOPE solo vitalia. Si Chris quiere extender a las 3 brands, ese es un story aparte (`luana-dev-bootstrap-all-brands`).
- HIPAA hardening, multi-site UI, voice cloning, K8s prod deploy.
- Performance tuning del dev stack (hot-reload speed, etc.).
- E2E test infrastructure mejoras (más allá del 1 spec nuevo de auth happy path).

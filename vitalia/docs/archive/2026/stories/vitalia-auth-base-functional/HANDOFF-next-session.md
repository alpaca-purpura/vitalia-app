# HANDOFF — vitalia-auth-base-functional → next session

> Created: 2026-05-19T05:47Z
> Session state: **CLOSED** (Chris requested clean-context handoff)
> Story state: **done** (per checkpoint.md), pero con followups críticos descubiertos durante admin Streamlit smoke

## Estado actual (resumen 1-línea)

Story `vitalia-auth-base-functional` mergeada a main (commit `9e7351f`), LIVE confirmado en `dev-app.vitalialat.com` para flujo FE (auth + dashboard + middleware). Admin Streamlit corriendo en docker container + accesible vía host port-forward `http://127.0.0.1:8501` PERO admin login falla con errores DB (migrations no aplicadas).

## Procesos vivos al cierre

| Proceso | Cómo verificar | Cómo matar |
|---|---|---|
| Streamlit dentro container `luana-dev-vitalia_backend_dev-1` puerto 0.0.0.0:8501 | `docker exec luana-dev-vitalia_backend_dev-1 cat /tmp/streamlit.log \| tail -5` | `docker exec luana-dev-vitalia_backend_dev-1 pkill -f streamlit` |
| Host TCP forwarder PID `1162119` (Python script `/tmp/forward_8501.py`) listening 127.0.0.1:8501 → container 172.19.0.5:8501 | `ps -p 1162119` + `curl -sS -I http://127.0.0.1:8501/_stcore/health` | `kill 1162119` |
| Docker stack vitalia (BE 8002, FE 3002, postgres 5435, cloudflared tunnel) | `docker ps --filter "name=luana-dev-vitalia"` | `make dev-down-vitalia` (o `docker compose -f vitalia/docker-compose.dev.yml down`) |

## Bugs descubiertos en admin Streamlit smoke (followup ticket)

### Bug #1 — `$` literal en `.env.dev` rompe bash `source` ✅ FIXED en sesión

**Síntoma:** `bcrypt_error: Invalid salt` — el hash bcrypt cargaba como `b2.i` (4 chars) en lugar de los 60 chars reales.

**Causa:** El valor `VITALIA_ADMIN_PASSWORD_HASH=$2b$12$VLIx...` tenía `$` literales que bash interpretaba como expansion de variables al hacer `set -a; . .env.dev; set +a` (`$2b` → ``, `$12` → ``, etc).

**Fix aplicado:** Quoted con single-quotes en `.env.dev`:
```bash
VITALIA_ADMIN_PASSWORD_HASH='$2b$12$VLIx7S6S6Nb14KKfd4WIxe1va9OjpG09vcjwOec5BV0fkkFxlDb.i'
```

**Cementar en followup:** documentar en `.env.dev.template` que valores con caracteres especiales ($, !, espacios, etc.) requieren single-quote.

### Bug #2 — `Settings` requiere 14 env vars que el shell no tiene ✅ MITIGATED

**Síntoma:** `14 validation errors for Settings` cuando admin importa `SessionLocal` desde `luana_core_platform.core.database`.

**Causa:** El `Settings` class en `luana_core_platform.core.config` requiere `LOG_LEVEL`, `DOMAIN_NAME`, `TRAEFIK_NETWORK`, `API_SECRET_KEY`, `WHATSAPP_*`, `QDRANT_URL`, `POSTGRES_*`, `API_URL` — el host shell no tiene esos (solo el docker container BE los tiene).

**Mitigation aplicada:** Streamlit corriendo INSIDE docker container `luana-dev-vitalia_backend_dev-1` via `docker exec -d` + env vars inyectadas en el comando.

**Cementar en followup:**
- Refactorizar `vitalia/backend/src/modules/vitalia/admin/_shared/db.py` para usar config minimal (solo DATABASE_URL) sin importar el heavy Settings
- O agregar `vitalia-admin` service al `vitalia/docker-compose.dev.yml` para que se levante con `make dev-vitalia`

### Bug #3 — Puerto 8501 no expuesto por docker-compose ✅ WORKAROUND ACTIVO

**Síntoma:** No reachable desde browser host en `http://127.0.0.1:8501` aunque Streamlit corra inside container.

**Causa:** `vitalia/docker-compose.dev.yml` solo mapea `8002` (BE) y `3002` (FE), no `8501`.

**Workaround activo:** Python TCP forwarder PID 1162119 hace `127.0.0.1:8501 → 172.19.0.5:8501` (docker bridge IP del container).

**Cementar en followup:**
- Agregar service `vitalia-admin` con `ports: ["8501:8501"]` al `docker-compose.dev.yml`
- O subpath routing via cloudflared para producción

### Bug #4 — Tabla `vitalia_clinics` no existe en postgres ❌ BLOQUEA admin login flow

**Síntoma:** Después de login (que ya funciona con el hash fixed), admin tenta listar clinics → `(psycopg2.errors.UndefinedTable) relation "vitalia_clinics" does not exist`.

**Causa probable:** Las migrations alembic para `vitalia_clinics` no se aplicaron en la DB `vitalia_dev` que el container ve.

**Investigación pendiente:**
```bash
# Check current alembic state
docker exec luana-dev-vitalia_backend_dev-1 bash -c "cd /workspace/vitalia/backend && uv run alembic current"

# Check migrations list
docker exec luana-dev-vitalia_backend_dev-1 bash -c "cd /workspace/vitalia/backend && uv run alembic history | head -20"

# Check actual DB schema
docker exec luana-dev-luana_postgres_dev-1 psql -U postgres -d vitalia_dev -c "\dt"

# Look for vitalia_clinics migration file
find /home/chalreme/Proyectos/luana-platform/vitalia/backend -name "*.py" | xargs grep -l "vitalia_clinics" | head -5
```

**Fix esperado:**
- Si migration existe pero no aplicada: `docker exec luana-dev-vitalia_backend_dev-1 bash -c "cd /workspace/vitalia/backend && uv run alembic upgrade head"`
- Si migration NO existe: T-4 builder olvidó crear la migration → generar nueva alembic revision

### Bug #5 — Redis container DNS fail (graceful degrade) ⚠ NO CRITICAL

**Síntoma:** `redis_unavailable error='Error -3 connecting to luana_redis_dev:6379. Temporary failure in name resolution.'`

**Causa:** No hay container `luana_redis_dev` en el docker network actual (al menos no visible en `docker ps`).

**Impact:** App degraded sin Redis (cache/queue features no funcionan, pero core operations sí).

**Decisión pendiente:** ¿Vitalia necesita Redis para auth/admin flow? Probablemente no — es para cache features futuras. Confirmar.

## Cómo retomar próxima sesión

### Opción A — Continuar story closure (recomendado)

```bash
# 1. Open new session with:
/pm-vitalia
"retomar bugs descubiertos en admin Streamlit smoke — leer HANDOFF-next-session.md"

# 2. Resume from:
- Bug #4 investigación + fix (migration vitalia_clinics)
- Bug #2 + #3 refactor (admin docker-compose service)
- Bug #1 documentation en .env.dev.template
```

### Opción B — Abrir story de followups formalmente

```bash
/pm-vitalia
"nueva story: vitalia-auth-base-functional-followups (5 BE WARNs auditor + 4 bugs admin Streamlit + Playwright selectors)"
```

## Estado git al cierre

- Branch actual: `wip/vitalia`
- HEAD: `95f3c7c docs(vitalia/stories): close vitalia-auth-base-functional + post-hoc fix onboarding-wizard state`
- Synced con `origin/wip/vitalia` (push completo)
- Main HEAD: `9e7351f` (PR #1 squash-merge)
- Untracked: Clerk CLI skills auto-installed (no scope story, ignorables)

## Credenciales para retomar

```
Admin Streamlit URL:        http://127.0.0.1:8501  (vía forwarder PID 1162119)
Admin password:             7BFinws7Irux4wUGAzQ4
Admin password hash (env):  $2b$12$VLIx7S6S6Nb14KKfd4WIxe1va9OjpG09vcjwOec5BV0fkkFxlDb.i

Vitalia LIVE:               https://dev-app.vitalialat.com/
                            /sign-in funciona, dashboard requiere user signed-in via Clerk

Clerk Vitalia app:          app_3DonQYFeFiJAPBKgtJs4q1sxyA0
Clerk instance:             ins_3DonQYwEGZmOp7RCtptjnroBJgJ (development)
Clerk domain:               moral-gator-27.clerk.accounts.dev (auto-generated keyless, claimed)

Webhook secret en Svix:     whsec_7Kna56vuCnW1KbsVFGA1TkQgnHJMAUsZ
Webhook endpoint:           https://dev-app.vitalialat.com/api/v1/vitalia/webhooks/clerk (filter: user.created)

Testing token (Clerk):      Regenerar al inicio próxima sesión via:
                            npx clerk api --secret-key $CLERK_SECRET_KEY /v1/testing_tokens -X POST --yes
                            (válido ~60min, no persistir)
```

## Artifacts de la story (immutables)

- `vitalia/docs/product/stories/vitalia-auth-base-functional/01-spec.md`
- `vitalia/docs/product/stories/vitalia-auth-base-functional/03-arch-brief.md`
- `vitalia/docs/product/stories/vitalia-auth-base-functional/04-validators.yaml`
- `vitalia/docs/product/stories/vitalia-auth-base-functional/05-guidelines.md`
- `vitalia/docs/product/stories/vitalia-auth-base-functional/06-tickets.yaml`
- `vitalia/docs/product/stories/vitalia-auth-base-functional/CHECKPOINTS.md`
- `vitalia/docs/product/stories/vitalia-auth-base-functional/07-merge.md` (5 secciones + LIVE verification)
- `vitalia/docs/product/stories/vitalia-auth-base-functional/06-audit/{gherkin-matrix,T-4-review,T-5-review}.md`
- `vitalia/docs/product/stories/vitalia-auth-base-functional/T-{1,2,3,4,5,6.a,6.b,self-fix-1}-result.md`
- 7 capabilities en `vitalia/docs/product/capabilities/{auth,dashboard,admin,observability,ops,tests}/*.yaml`

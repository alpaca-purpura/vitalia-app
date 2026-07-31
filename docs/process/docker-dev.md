# Runbook — Docker dev local (vitalia)

> Origen: S-DOCKER-DEV-MULTIBRAND 2026-05-15 (renombrado `docker-dev.md` 2026-07-31 al quedar vitalia-app standalone single-brand).
> ADR de referencia: docs/architecture/luana-platform/ADR-003-docker-dev-multibrand.md

## Quick start

```bash
# Levantar una brand para desarrollo
cp vitalia/.env.dev.template vitalia/.env.dev  # primera vez — rellena con valores reales
make dev-vitalia

# Verificar que esta corriendo
curl http://127.0.0.1:8002/health   # vitalia backend
# → {"status": "ok"}

# Ver logs en tiempo real
docker logs -f luana-dev-vitalia_backend_dev-1

# Detener
make dev-down-vitalia
```

## Que hace cada Makefile target

| Target | Que hace |
|---|---|
| `make dev-vitalia` | Levanta postgres + backend vitalia + frontend vitalia |
| `make dev-vitalia-tunnel` | Idem + cloudflared tunnel (profile=tunnel) |
| `make dev-down-vitalia` | Para los containers de vitalia (postgres sigue corriendo) |
| `make dev-clean-vitalia` | Para containers + elimina volumes (borra .venv y node_modules del container) |
| `make install-hooks` | Instala git hooks (symlink pre-commit) |

## Port allocation (cementada)

| Brand | Backend | Frontend | DB | Redis DB |
|---|---|---|---|---|
| vitalia | 8002 | 3002 | vitalia_dev | 1 |

Postgres: `127.0.0.1:5435`. Qdrant: `6333/6334`. Redis: `6379`.

> Los puertos 8001/8003/8004 · 3001/3003/3004 pertenecían a las otras marcas del monorepo luana-platform (nicolify/comunify/lupulo) — no existen en este repo. Herencia archivada en `docs/archive/2026/multibrand-legacy/`.

## Como funciona el hot-reload

El backend usa un bind mount del monorepo completo + un volume nombrado que protege el `.venv` del container:

```yaml
volumes:
  - .:/workspace:rw              # bind mount — cambios en host se reflejan al instante
  - vitalia_backend_venv:/workspace/vitalia/backend/.venv  # protege .venv del container
```

Cuando modificas cualquier archivo de `vitalia/backend/src/` o `core/`, uvicorn detecta el cambio y reinicia automaticamente (<2s). No necesitas `docker compose build`.

**Para que funcione:**
- El compose file debe ejecutarse desde la raiz del monorepo (lo que `make dev-vitalia` garantiza)
- El `target: dev` del Dockerfile hace `COPY pyproject.toml uv.lock` para pre-instalar deps pero el source viene via bind mount, no via COPY

## Como hacer hot-reload funcionar con core/

Los cambios en `core/luana-core-*/` se propagan automaticamente gracias a `--reload-dir /workspace/core` en el command de uvicorn:

```yaml
command: >
  uv run uvicorn src.main:app
  --host 0.0.0.0
  --port 8002
  --reload
  --reload-dir /workspace/vitalia/backend/src
  --reload-dir /workspace/core  # ← esto hace que cambios en core/ disparen reload
```

## Troubleshooting top 5 errores

### 1. `make dev-vitalia` falla con "No such file or directory: vitalia/.env.dev"

```bash
cp vitalia/.env.dev.template vitalia/.env.dev
# Edita vitalia/.env.dev y rellena los valores reales
```

### 2. Postgres healthcheck falla, backend no arranca

```bash
# Ver estado de postgres
docker ps --filter name=luana_postgres_dev
docker logs luana-dev-luana_postgres_dev-1 --tail 20

# Si el data volume esta corrupto:
make dev-clean-vitalia  # elimina volumes
make dev-vitalia        # recrea
```

### 3. Build falla con "COPY failed: file not found in build context"

El build context DEBE ser la raiz del monorepo. Asegurate de ejecutar desde la raiz del worktree (`git rev-parse --show-toplevel`), no desde `vitalia/`.

```bash
# CORRECTO — desde la raiz
cd $(git rev-parse --show-toplevel)
make dev-vitalia

# INCORRECTO — desde la brand folder
cd vitalia && docker compose up -d  # pierde acceso a core/
```

### 4. Hot-reload no funciona

Verificar que el compose file tiene el bind mount correcto:

```bash
WS=$(git rev-parse --show-toplevel)
docker inspect luana-dev-vitalia_backend_dev-1 | grep -A5 "Mounts"
# Debe mostrar: "Source": "${WS}"
```

Si `.venv` del host esta sobreescribiendo el del container, limpiar:

```bash
make dev-clean-vitalia  # elimina el volume vitalia_backend_venv
make dev-vitalia        # reinstala desde cero
```

### 5. "Address already in use" al levantar una brand

Otro proceso usa el puerto. Verificar:

```bash
ss -tlnp | grep -E "8002|3002"
# O:
lsof -i :8002
```

Detener el proceso o cambiar el puerto en el compose file (y actualizar `vitalia/config/brand.yaml`).

## Notas sobre build context

El argumento `context: .` en los compose files de brand asume que `docker compose` se ejecuta desde la raiz del monorepo. Los targets `make dev-{brand}` garantizan esto porque Make ejecuta desde el directorio donde se invoca.

Si ejecutas `docker compose` manualmente:

```bash
# CORRECTO — build context = raiz
docker compose -f docker-compose.dev.yml -f vitalia/docker-compose.dev.yml up -d

# INCORRECTO — build context = vitalia/ (no accede a core/)
cd vitalia && docker compose -f docker-compose.dev.yml up -d
```

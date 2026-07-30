# Runbook — Docker dev local multimarca brand-autocontenida

> S-DOCKER-DEV-MULTIBRAND — 2026-05-15. Owner: /pm-luana.
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
| `make dev-{brand}` | Levanta postgres (shared) + backend brand + frontend brand |
| `make dev-{brand}-tunnel` | Idem + cloudflared tunnel (profile=tunnel) |
| `make dev-all` | Levanta las 4 brands simultaneamente |
| `make dev-all-vector` | Levanta las 4 brands + qdrant (copilot/sales_agent) |
| `make dev-all-cache` | Levanta las 4 brands + redis |
| `make dev-down-{brand}` | Para los containers de la brand (postgres sigue corriendo) |
| `make dev-down-all` | Para todos los containers de brand (postgres sigue corriendo) |
| `make dev-clean-{brand}` | Para containers + elimina volumes (borra .venv y node_modules del container) |
| `make dev-clean-all` | Limpieza total — usado para reset completo |
| `make infra-matrix` | Regenera docs/portfolio/INFRA-MATRIX.md desde brand.yaml |
| `make install-hooks` | Instala git hooks (symlink pre-commit) |

## Port allocation (cementada)

| Brand | Backend | Frontend | DB | Redis DB |
|---|---|---|---|---|
| nicolify | 8001 | 3001 | nicolify_dev | 0 |
| vitalia | 8002 | 3002 | vitalia_dev | 1 |
| comunify | 8003 | 3003 | comunify_dev | 2 |
| lupulo | 8004 | 3004 | lupulo_dev | 3 |
| (futuros) | 8005-8010 | 3005-3010 | {brand}_dev | 4-9 |

Postgres compartido: `127.0.0.1:5435`. Qdrant: `6333/6334`. Redis: `6379`.

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

## Como agregar una nueva brand al sistema

1. Crear la carpeta brand: `mkdir -p {brand}/backend/src {brand}/frontend/src {brand}/config`

2. Crear `{brand}/config/brand.yaml` con la seccion `infra:` completa (ver schema en 05-guidelines.md § Pattern 10)

3. Crear `{brand}/backend/Dockerfile` y `{brand}/frontend/Dockerfile` (copiar patron de vitalia, ajustar puertos)

4. Crear `{brand}/docker-compose.dev.yml` (copiar patron de vitalia, ajustar puertos y names)

5. Crear `{brand}/.env.dev.template` y `{brand}/.env.prod.template`

6. Agregar al Makefile: `dev-{brand}`, `dev-{brand}-tunnel`, `dev-down-{brand}`, `dev-clean-{brand}`

7. Agregar al `Makefile::BRANDS` := variable

8. Agregar al `scripts/generate_infra_matrix.py::BRANDS` lista

9. Agregar al `scripts/postgres-init/01-create-databases.sh::DATABASES` array

10. Correr `make infra-matrix` para actualizar el indice

11. Agregar `{brand}/.env.dev` y `{brand}/.env.prod` al `.gitignore`

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
ss -tlnp | grep -E "8001|8002|8003|8004|3001|3002|3003|3004"
# O:
lsof -i :8002
```

Detener el proceso o cambiar el puerto en el compose file (y actualizar brand.yaml + make infra-matrix).

## Notas sobre build context

El argumento `context: .` en los compose files de brand asume que `docker compose` se ejecuta desde la raiz del monorepo. Los targets `make dev-{brand}` garantizan esto porque Make ejecuta desde el directorio donde se invoca.

Si ejecutas `docker compose` manualmente:

```bash
# CORRECTO — build context = raiz
docker compose -f docker-compose.dev.yml -f vitalia/docker-compose.dev.yml up -d

# INCORRECTO — build context = vitalia/ (no accede a core/)
cd vitalia && docker compose -f docker-compose.dev.yml up -d
```

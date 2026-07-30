---
date: 2026-05-20
slug: docker-frontend-ram-turbopack-issue
brand: vitalia
promotable: no
severity: medium
affects: E2E pipeline, native build, Playwright smoke tests
---

# Aprendizaje — Vitalia frontend Docker RAM + Turbopack lazy-compile issue

## Contexto

Durante la sesión T-mk-fe-7 (wave 6 marketing — E2E smoke + a11y + perf + bundle), se detectaron 2 problemas de infraestructura que bloquearon la ejecución local de los validators.

## Problema 1 — Turbopack dev server drops connections bajo carga Playwright

**Síntoma:** `ERR_EMPTY_RESPONSE` / `ERR_SOCKET_NOT_CONNECTED` cuando Playwright Chromium navega a `/marketing` (primer acceso = lazy compile).

**Root cause:** El servidor dev de Turbopack (en Docker) está bajo RAM pressure. Cuando 3 browsers Playwright paralelos hacen requests a una ruta nueva (lazy compile trigger), el servidor cierra las conexiones durante la compilación inicial del route. Después de compilado (curl funciona), el servidor sirve correctamente vía curl pero sigue siendo inestable para browsers.

**Evidencia:**
```bash
curl http://localhost:3002/marketing → HTTP 307 (redirect a sign-in, OK)
npx playwright test /marketing → ERR_EMPTY_RESPONSE (connection dropped)
```

**Fix recomendado:**
1. Aumentar `--max-old-space-size` del proceso Next.js en Docker (actualmente sin límite explícito).
2. En `vitalia/docker-compose.dev.yml`, en el servicio `frontend`, agregar:
   ```yaml
   environment:
     NODE_OPTIONS: "--max-old-space-size=4096"
   mem_limit: 4g
   memswap_limit: 4g
   ```
3. Alternativa: pre-warm routes críticas en el startup script del container: `wget -q http://localhost:3002/marketing -O /dev/null` antes de que Playwright empiece.

**Workaround actual:** todos los validators E2E deferidos a CI (donde el server está pre-built con `next build`, sin lazy compilation).

## Problema 2 — `.next/` directory owned by root (Docker) bloquea native build

**Síntoma:** `EACCES: permission denied, open '.../vitalia/frontend/.next/trace'` cuando se intenta correr `next build` nativamente.

**Root cause:** El servidor Docker (corriendo como `root` dentro del container) crea `.next/` con ownership `root:root`. Cuando el usuario `chalreme` intenta correr `next build` nativo, no tiene permisos de escritura.

**Evidencia:**
```bash
ls -la vitalia/frontend/.next/
# drwxr-xr-x 3 root root ... .
```

**Fix recomendado:**
1. En `vitalia/docker-compose.dev.yml`, servicio `frontend`, agregar `user: "1000:1000"` (UID del usuario host `chalreme`):
   ```yaml
   services:
     frontend:
       user: "1000:1000"
   ```
2. O bien, en el Dockerfile base del frontend, agregar `RUN mkdir -p /app/.next && chown -R node:node /app/.next` y correr como usuario `node`.
3. O pre-crear `.next/` con ownership correcto antes de `make dev-vitalia`: `mkdir -p vitalia/frontend/.next && chown -R chalreme:chalreme vitalia/frontend/.next/`.

**Workaround actual:** `visual_bowtie_bundle_size` deferido a CI donde el build corre como usuario CI sin conflicto de ownership.

## Impacto en T-mk-fe-7

Los 4 validators de T-mk-fe-7 quedaron DEFERRED a CI:
- `e2e_smoke_marketing` → Turbopack connection drops
- `visual_a11y_axe` → mismo
- `visual_perf_budget_lighthouse` → mismo + requiere LHCI
- `visual_bowtie_bundle_size` → `.next/` EACCES

Los artifacts están completos y listos para CI. El issue NO bloquea el merge de la story si CI pasa.

## Para /pm-vitalia

Accionar en próxima sesión de infraestructura:

- [ ] Aumentar RAM Docker servicio frontend vitalia (mem_limit: 4g + NODE_OPTIONS: `--max-old-space-size=4096`)
- [ ] Agregar `user: "1000:1000"` en servicio frontend docker-compose.dev.yml para evitar `.next/` owned by root
- [ ] Considerar script de pre-warm de rutas críticas en docker healthcheck (`/marketing`, `/inbox`, `/fidelizacion`)
- [ ] Verificar que `make dev-vitalia` funciona después de los cambios (el stack ya está corriendo — cambiar en frío)

Referencia: `vitalia/docs/product/stories/vitalia-slice-1-marketing/T-mk-fe-7-result.md` § "Infrastructure issue flagged"

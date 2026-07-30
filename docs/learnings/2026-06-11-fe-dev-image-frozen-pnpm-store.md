---
title: "FE dev image: store pnpm congelado rompe ante deps nuevas de core/@luana"
date: 2026-06-11
type: technical
brands_affected: [vitalia, nicolify, comunify, lupulo]
origen: "incidente 2026-06-11 — stack vitalia caído post-lift @luana/ui-kit 0.4.0"
ratified_by: chris
promotable: yes
tags: [docker, pnpm, dev-infra, module-not-found, anonymous-volumes, workspace]
---

# FE dev image: store pnpm congelado rompe ante deps nuevas de core/@luana

## Contexto

Tras el lift de shell chrome a `@luana/ui-kit 0.4.0` (que introdujo `@luana/format` con dep `tailwind-merge@^2`), el stack dev de vitalia murió completo: **500 en TODAS las rutas** (`Module not found: tailwind-merge`). Síntomas en cascada que enmascararon el root cause: "se cayó el sistema", "crear lead se cuelga", y Playwright/Clerk timeout (el SDK Clerk nunca hidrataba porque la página era un build-error overlay). Se gastó tiempo persiguiendo "auth Clerk roto" cuando el auth estaba perfecto.

**Segunda vez del patrón**: 2026-05-29 (`@luana/hooks@0.2.0` bump → 500 en :3002) se "arregló" montando `core/` como bind — pero eso solo refresca el SOURCE, no el store de dependencias.

## Aprendizaje

El contenedor FE dev tiene **tres capas de node_modules con frescura distinta**:

1. **Bind mounts** (`vitalia/frontend`, `core`) → frescos (host)
2. **Anonymous volumes** (`/app/*/node_modules`) → congelados al CREATE del container
3. **Store raíz `/app/node_modules/.pnpm`** (target de TODOS los symlinks pnpm) → congelado al BUILD de la imagen

Los symlinks pnpm del host (`../../../../node_modules/.pnpm/...`) resuelven dentro del container contra el store de la IMAGEN. Una dep nueva agregada post-build → symlink roto → `Module not found`, sin importar cuántas veces reinicies.

**Root cause de fondo:** el Dockerfile solo copiaba manifests root + `{brand}/frontend/package.json` y corría `pnpm install --filter "@luana/{brand}-web"` (sin `...`) → las deps de los workspace packages `@luana/*` JAMÁS entraban al store de la imagen. Funcionaba por coincidencia (deps compartidas con la web app).

## Aplicación práctica

- **Fix estructural** (aplicado a vitalia, portar a toda brand con FE Docker): el Dockerfile dev/builder debe `COPY core/@luana ./core/@luana` ANTES del install y filtrar con `"@luana/{brand}-web..."` (los `...` incluyen workspace deps). Commit `8ce72b0e`.
- **Tras cambiar deps de cualquier `core/@luana/*`**: rebuild imagen FE + `up -d -V --force-recreate` (el `-V` renueva anonymous volumes desde la imagen nueva).
- **Diagnóstico exprés**: 500 global + `Module not found` de un paquete que SÍ está en el host → `docker exec {fe} ls .../node_modules/{pkg}/package.json` (symlink roto = este patrón).
- **Síntoma trampa**: Playwright/Clerk "timeout esperando window.Clerk" puede ser la app 500eando, no auth. Verificar `curl /sign-in` ANTES de debuggear auth.
- `.dockerignore` root (node_modules/.next/.git/.venv) evita copiar symlinks rotos del host a la imagen.

## Referencias

- Commit fix: `8ce72b0e` (Dockerfile vitalia + .dockerignore + compose KEK)
- Caso anterior del patrón: comentario en `vitalia/docker-compose.dev.yml` (2026-05-29, @luana/hooks)
- [[verification-real-not-200]] — el síntoma visible (Clerk timeout) no era el root cause

# Dev bundler por tamaño de marca (no "turbopack para todas")

**Fecha:** 2026-06-17. **Tipo:** tooling/dev-infra. **Origen:** investigación de RAM (vitalia FE consumía ~4.5GB en dev). **Supersede parcialmente:** HB-78 (que migró las 3 marcas a turbopack asumiendo "turbopack ahorra RAM" — verdad solo a escala chica).

## Hallazgo

La elección de bundler de **desarrollo** (turbopack vs webpack) debe ser **por marca, según el tamaño del codebase** — no uniforme. Es solo herramienta de dev; **no afecta el build ni la perf de producción**.

- **turbopack** arma un grafo de **todo el proyecto** en memoria en la primera compilación y lo retiene (front-loaded). Genial en proyectos chicos / máquinas con RAM de sobra; **escala mal** con el tamaño del codebase y en RAM limitada.
- **webpack** compila **incremental por ruta** (lazy, acotado por `onDemandEntries`). Footprint base mayor en chico, pero mucho menor en grande.

El cruce es por tamaño: chico → turbopack gana; grande → webpack gana.

## Mediciones (laptop 14GB, Next 16.2.6 · bundler confirmado por cmdline del proceso)

| Marca | LOC FE | bundler | RAM (warm) |
|---|---|---|---|
| vitalia (grande) | 127K | **turbopack** | **4.1–4.8 GB** |
| vitalia (grande) | 127K | **webpack** | **~1.8 GB** ← decisión |
| nicolify (chica) | 15K | webpack | ~1.95 GB |
| comunify (chica) | 8K | turbopack | ~2.15 GB |

- True idle (server Ready, 0 requests): ~150 MB → el costo es de **compilación**, no de arranque.
- `anon` real (cgroup `memory.stat`), no page cache reclamable → memoria genuina.
- **A escala chica (8–15K LOC) ambos bundlers rondan ~2GB** — ese es el piso por dev-server (React/Next/Clerk/@luana/ui-kit). El delta turbopack-vs-webpack a esa escala es ruido. **turbopack solo explota a escala grande** (vitalia, grafo de proyecto front-loaded). El número "turbopack 1.5 < webpack 2.37 en chicas" del HB-78 NO se re-verificó limpio esta sesión; vale como referencia, no como medición de esta corrida.
- **Gotcha de bind-mount:** el bundler EN EFECTO = el `package.json` del **worktree desde el que se lanza** `make dev-*` (compose bind-montea ese árbol). `vitalia=webpack` vive en `wip/vitalia` → se obtiene lanzando vitalia desde `~/Proyectos/luana-vitalia` (su worktree canónico). Lanzar desde `~/luana-platform` (main) daría turbopack hasta el squash-merge a main. nicolify ya tiene `--webpack` en main. Banners de `docker logs` NO sirven para verificar (buffer stale cross-restart) — usar el cmdline del proceso.

### Qué NO era la causa (descartado con datos, para no caer en sobre-ingeniería)

Una página **mínima** (`/sign-in`) ya pesaba ~4GB en vitalia con turbopack → el costo es del bundler a escala de proyecto, **no** del contenido de la ruta. Probado y descartado como driver:
- Barrels de feature / dispatcher (`SubTabContent`) — solo compilan al entrar a su ruta.
- `optimizePackageImports` — **empeoró** (5.3GB, +18s): analizar el barrel transpilado de `@luana/ui-kit` agrega overhead.
- Tailwind v4 — desactivado, siguió en 3.9GB (solo ~0.26GB era Tailwind).
- Grafo JS del root layout — liviano, no toca `@/features`.

→ Refactorizar barrels / lazy-load **no baja la RAM de dev** (sí ayuda la perf de **prod**, track separado).

## Política

- **vitalia → webpack** (`next dev --webpack` en `package.json`). nicolify/comunify → turbopack (default).
- **Regla:** cuando una marca supere ~2.5–3 GB de FE-dev en turbopack, pasarla a webpack.
- HMR medido en esta laptop: webpack 0.1–0.3s incremental; turbopack 2–6s **errático** (a 4.8GB empuja el sistema a swap → el thrashing mata su ventaja teórica). En máquina holgada turbopack es más rápido; en 14GB con 3 stacks, no.

## Verificación (DoD)

webpack en vitalia: BUILD limpio (5 rutas shell compilan, 0 errores) + RENDER limpio del shell autenticado (Playwright smoke: marca light/dark + inbox light/dark, fixture anti-burbuja verde). Flakes ocasionales = `ERR_EMPTY_RESPONSE`/`ERR_SOCKET_NOT_CONNECTED` en chunks bajo contención de cold-compile (artefacto de dev-server, no bug).

## Techo real

14GB es el límite para 3 marcas que crecen. Para las 10 del roadmap, 32GB destraba turbopack-para-todas con velocidad. El bundler-por-tamaño administra el síntoma; la RAM física cura la causa.

## Palanca complementaria

`make dev-active BRAND=X` — corre en dev solo la marca activa (su FE), detiene los FE de las otras (libera ~2.5GB c/u), deja sus backends vivos. Para sesiones de una sola marca: ~2.7GB total.

---
date: 2026-06-15
slug: uikit-tailwind-source-and-dev-cache
type: tooling
promotable: yes
applies_to: [vitalia, nicolify, comunify, lupulo]   # toda marca que consuma @luana/ui-kit
tags: [tailwind-v4, next-dev, turbopack, "@luana/ui-kit", caching, live-verify]
---

# Verificar cambios de `core/@luana/*` en el FE dev: `@source`, dev-cache y hard-reload

**Origen:** sesión 2026-06-15. Un "bugfix UI mínimo" (toolbar sticky) llevó a editar
`core/@luana/ui-kit` y los `.next` clears para verificarlo destaparon DOS gotchas de tooling
que costaron varias rondas de debug + una regresión visible (avatares gigantes / shell roto).

## Gotcha 1 — Tailwind v4 `@source` off-by-one → clases exclusivas del kit NO se generan

Cada brand FE escanea el kit con un `@source` en `globals.css` para que Tailwind v4 JIT vea
las clases usadas DENTRO de `@luana/ui-kit` (está en `node_modules`, que v4 ignora por default).
El path es **relativo al archivo CSS**. vitalia lo tenía mal por un nivel:

```css
/* vitalia/frontend/src/app/globals.css  (dir = vitalia/frontend/src/app/) */
@source "../../../core/@luana/ui-kit/src/organism/shell";   /* ✗ → vitalia/core/… NO existe (core está en el ROOT) */
@source "../../../../core/@luana/ui-kit/src";                /* ✓ 4 niveles: app→src→frontend→vitalia→root */
```

**Síntoma traicionero:** el shell se ve MAYORMENTE bien (las clases comunes — `h-14`, `flex`,
`size-8/9/10` — también se usan en el src de la brand, así que se generan igual). Solo las
clases **exclusivas del kit** desaparecen. Caso real: `size-7` (solo en `RibbonTab.tsx`) no se
generó → el `<Avatar>` sin tamaño → el `<img>` `h-full w-full aspect-square` ballooneó a su
natural 500px → avatares gigantes + scroll horizontal + "shell roto".

**Por qué pasaba desapercibido:** con el dev server caliente, Tailwind tenía las clases de un
build/HMR previo. El bug solo aparece en un **build LIMPIO** (`.next` borrado, fresh clone, CI,
prod). → un `@source` mal NUNCA fallará en el dev caliente de quien lo escribió.

**Regla:** al consumir `@luana/ui-kit` (o cualquier paquete de `core/@luana/*`) en una brand,
el `@source` debe resolver al path REAL (contá los niveles desde el CSS hasta el root) y conviene
apuntar a `…/src` (no solo a un subdir) para no perder clases de átomos. Verificá en build limpio:
una clase exclusiva del kit (ej. `size-7`) debe estar en el CSS generado.

## Gotcha 2 — Next dev sirve chunks bajo filename ESTABLE → los caches sirven stale

Editar un archivo de `@luana/ui-kit` y borrar `.next` + reiniciar el FE **sí** recompila
(Turbopack lee el bind-mount). Pero el chunk (CSS/JS) se sirve bajo un **filename estable**
(ej. `globals_0m9gcrk.css`) que NO cambia aunque cambie el contenido → el **cache HTTP del
browser** (y cualquier edge) sigue sirviendo la versión vieja bajo ese mismo nombre. Un reload
normal reusa el cache. Pasó 2 veces esta sesión (CSS del shell + el JS de AppPanelSlot).

**Para live-verificar un cambio de `core/@luana/*`:**
1. en el container: `rm -rf {brand}/frontend/.next` + `docker restart …_frontend_dev-1`.
2. en el browser: **hard-reload (`ignoreCache`)** o un **contexto/incognito FRESCO** (sin cache).
   Un reload normal NO basta. Cloudflare tunnel NO cacheaba (un contexto fresco trae lo nuevo);
   el stale era cache del browser keyed por URL.
3. confirmá leyendo el CSS/DOM real (ej. `getComputedStyle` de una clase del kit), no "se ve igual".

**Caveat extra:** Turbopack no watchea archivos symlinked fuera del root del app → un cambio en
`core/@luana/*` puede no HMR-ear; el `.next` clear + restart es lo confiable. (Algunas marcas —
comunify — ni siquiera bind-montan `core` / no consumen el kit → ahí no aplica.)

## How to apply

- Tocás `core/@luana/*` y verificás en el FE de una brand → `.next` clear + restart + **hard-reload**
  (o contexto fresco). Nunca confíes en el dev caliente ni en un reload normal.
- Agregás/movés un `@source` a un paquete del kit → contá los niveles al root + apuntá a `…/src` +
  probá una clase kit-exclusiva en build limpio.
- Refuerza [[verification-real-not-200]]: "se ve igual" tras un reload normal = no verificaste.

## Refs
- Fix: `vitalia/frontend/src/app/globals.css` (commit 6597b3b1) · `core/@luana/ui-kit/src/organism/shell/AppPanelSlot.tsx` (88c56dc9).
- Relacionado: `docs/learnings/2026-06-11-fe-dev-image-frozen-pnpm-store.md` (frozen pnpm store, otra cara del mismo "core/@luana FE changes no reflejan").

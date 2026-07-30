---
title: node_modules stale tras migración node-linker in-place → dual-instance de Playwright ("did not expect test()")
date: 2026-06-23
type: tooling
scope: cross-brand
promotable: candidate
applied: applied
origin: pasada /dev-team HB-98 2026-06-23 — runner E2E vitalia roto; diagnóstico previo (loader-bug Playwright 1.60) refutado
---

# `node_modules` stale tras cambiar `node-linker` → dual-instance de Playwright

## Síntoma

`cd vitalia/frontend && npx playwright test --project=setup --list` →
`Playwright Test did not expect test()` (o `test.describe.configure()`) `to be called here`
→ `No tests found`. **Ningún** spec colecta. nicolify/comunify colectan OK; solo vitalia roto.

## Causa raíz (lo que NO era, primero)

El error de Playwright lista 3 causas; la real es la 3ª — **"dos copias de
`@playwright/test`"** — pero con un giro: **misma versión, dos físicos distintos**.

- El runner se lanza vía el shim `node_modules/.bin/playwright` que ejecuta
  `.pnpm/@playwright+test@1.60.0/.../cli.js` → bindea `playwright/lib/common` de un físico.
- Los specs hacen `import { test } from "@playwright/test"` → resuelven a OTRO
  físico de `playwright` (la copia hoisted en `node_modules/playwright`, un
  hardlink con **path distinto** — Node deduplica por realpath-string, no por inode).
- Cada físico tiene su propia variable módulo-level `currentlyLoadingFileSuite`.
  El runner setea el flag en su copia; el `test` del spec lee la otra → unset →
  "did not expect test()".

**Por qué solo vitalia:** el `.npmrc` pasó a `node-linker=hoisted` (HB-78,
2026-06-17) con una migración **in-place** (sin `rm -rf node_modules`).
`vitalia/frontend/node_modules` quedó con el layout viejo (físico de `playwright`
divergente); nicolify/comunify sí se clean-reinstalaron en algún punto → layout sano.

## Refutaciones empíricas (descartá estos antes de perder horas)

| Hipótesis previa | Prueba que la mata |
|---|---|
| Bug del loader de Playwright 1.60 | Trivial spec (`test("x",()=>{})`) en `/tmp` con el MISMO binario → **pasa**. Dentro del paquete FE → falla. No es el binario. |
| `setup.describe.configure({mode:"serial"})` top-level ilegal en 1.60 | Con loader sano colecta perfecto. Es **legal**; era síntoma del dual-instance. **No tocar clerk.setup.ts.** |
| Afecta las 4/3 marcas | nicolify+comunify colectan OK desde el vamos. Solo vitalia. |
| tsconfig / jiti / cache | Borrar tsconfig no cambia nada; no hay hook global de `.ts`; no había cache. |
| `@playwright/test` como devDep directa "fuerza la misma instancia" | Con `node-linker=hoisted` NO crea symlink local; agregar el dep SIN reinstalar limpio **no arregla**. El symlink local de nicolify era leftover stale pre-hoisted. |

## Fix

**Operativo (lo que arregla):** clean reinstall canónico — el procedimiento que el
propio `.npmrc` exige tras cambiar `node-linker`:

```bash
find . -name node_modules -type d -prune -exec rm -rf {} +
pnpm install
```

Normaliza el layout: runner y specs bindean el mismo único físico de `playwright`.
**No deja artefacto en git** (node_modules gitignored, lockfile intacto) → un clone
fresco + `pnpm install` ya colecta bien.

**Hardening (defensa, no load-bearing):** declarar `@playwright/test` como devDep
DIRECTA en `vitalia/frontend/package.json` (cierra el **phantom-dep**: 215 specs lo
importan sin declararlo; nicolify/comunify ya lo declaran).

## Regla durable

- **Cambiar `node-linker` (o cualquier reescritura del layout de pnpm) = clean
  reinstall de TODOS los `node_modules`, no solo el root.** Una migración in-place
  deja paquetes con layout viejo que fallan silencioso (acá: el runner E2E entero).
- Ante "did not expect test()" en pnpm: NO asumir version mismatch del `package.json`.
  Comparar el **realpath físico** de `playwright/lib/common` que ve el runner vs el
  que ve el spec. Si difieren con misma versión → `node_modules` stale → clean reinstall.
- Un diagnóstico de harness-backlog es hipótesis, no verdad: **reproducí y refutá**
  cada hipótesis antes de actuar (acá 3 de 3 hipótesis previas eran falsas).

## Seguimiento — bump a 1.61.1 (2026-06-23)

Tras resolver HB-98 (en 1.60.0), se bumpeó Playwright **1.60.0 → 1.61.1** en las 3
marcas (copia hoisted única, no se puede por-marca). Motivo principal: el changelog
de **1.61.1 lista "ESM loader resolution issues with pnpm workspaces"** + **"Sync
loader error on Node 22.15"** — endurece justo el loader pnpm-workspace de esta clase
de bug → reduce recurrencia. 1 minor, cero breaking, peers OK (`@axe-core/playwright`
`>=1.0.0`, `@clerk/testing` `^1`), Node 20 OK. `pnpm dedupe` necesario para purgar el
físico 1.60.0 residual (un consumer lo retenía → si no, dual-version reintroducida).
Browsers nuevos (Chromium 149/FF 151/WebKit 26.5) descargados; el warning `libavif16` del
`playwright install` es **no-fatal** (Chromium 149 lanza OK). Verificado: 3 marcas
colectan, chromium launch OK, tsc 0.

## Referencias

- `docs/process/harness-backlog.md` § HB-98 (applied)
- `.npmrc` — comentario HB-78: "Cambiar node-linker requiere reinstall (rm -rf node_modules + pnpm install)"
- Files: `vitalia/frontend/package.json` + `pnpm-lock.yaml` (clerk.setup.ts INTACTO)

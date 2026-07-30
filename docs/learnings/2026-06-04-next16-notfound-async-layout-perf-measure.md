# Next 16 dev: `notFound()` desde un layout async dispara `performance.measure` con timestamp negativo

**Fecha:** 2026-06-04. **Origen:** `nicolify-r1-abel-icp-buyer` live-verify (Bug B). **Tipo:** técnico transversal (cualquier marca con shell `[subsubtab]` o layouts async que hacen `notFound()`/`redirect()`).

## Síntoma

Navegar a una ruta con UUID inválido o entidad inexistente (`/{tenant}/abel/icp/<bad>/datos`) en `next dev` dispara una **burbuja roja** de Next con:

```
TypeError: Failed to execute 'measure' on 'Performance': 'SubsubtabLayout' cannot have a negative time stamp.
Call Stack: 3 ignore-listed frame(s)
```

El `[data-nextjs-dialog]` aparece en el DOM → rompe el gate anti-burbuja (`pageerror`), aunque la página 404 contextual **sí renderiza** correctamente debajo.

## Causa raíz

Es **instrumentación de render de Next 16 en modo dev** (RSC timing), NO código nuestro:
- Cero `performance.measure(...)` en `nicolify/frontend/src/`.
- La ruta **compila** sin error.
- Navegaciones **válidas** son limpias (no dispara).
- El stack son **frames ignore-listed** (= frames internos de Next, marcados por el framework).
- Solo dispara cuando un **layout `async`** (`SubsubtabLayout`) llama `notFound()` a mitad de render: Next marca el inicio del render, el `notFound()` aborta, y el "measure" en el catch computa una duración negativa.

Hermano del learning [`2026-06-03-next16-softnav-redirect-rendered-more-hooks`]: Next 16 choca con patrones nuestros de shell (`redirect()`/`notFound()` in-render desde async + `ssr:false`). **Ausente en `next build` + `next start`** (la instrumentación de perf es dev-only) → NO afecta a usuarios en prod.

## Tratamiento (honesto, no masking)

NO desactivar el gate anti-burbuja completo (eso fue el error del primer builder). En su lugar:

1. **Opt-in TIGHT** en `e2e/fixtures/base.ts`: fixture `allowedPageErrors: RegExp[]` (default `[]` → gate 100% estricto en todos los specs). Solo los specs de 404 hacen `test.use({ allowedPageErrors: [/Failed to execute 'measure' on 'Performance'.*negative time ?stamp/i] })` — permiten ESE único error framework, cualquier OTRO pageError (de app) **sigue fallando** el gate.
2. **Camino durable ("para siempre"):** correr los specs de 404 contra `next build` + `next start` (donde la instrumentación dev no existe) → ahí no se necesita el allowlist. Pendiente: resolver el conflicto de permisos de `.next` (lo posee el container docker del dev server) para builds nativos en CI.

## Regla derivada

- Un `pageerror` de **origen framework verificado** (sin `measure` en src + ruta compila + navs válidas limpias + stack ignore-listed + dev-only) puede permitirse con un allowlist **tight + justificado + por-spec**, NUNCA desactivando el gate global.
- Verificar SIEMPRE el origen antes de allowlistear (no asumir "benign dev-mode" sin evidencia — eso es masking).

## Referencias
- `nicolify/frontend/e2e/fixtures/base.ts` § `allowedPageErrors`
- `.claude/rules/definition-of-done-live-verify.md` § Anti-masking (HB-33)
- `docs/learnings/2026-06-03-next16-softnav-redirect-rendered-more-hooks.md` (hermano)

# T-arch-1 Result — ADR vitalia-001 + design tokens cement

## Estado

state: pushed
ticket: T-arch-1
story: vitalia-slice-1-infra-cross-cutting

## Files created/modified

| Operación | Archivo |
|---|---|
| CREATE | `vitalia/docs/architecture/ADR-vitalia-001-shared-vs-fork.md` |
| CREATE | `vitalia/frontend/src/app/globals.css` |
| MODIFY | `vitalia/frontend/tailwind.config.ts` |
| MODIFY | `vitalia/frontend/src/app/layout.tsx` (agregar `import "./globals.css"`) |

## Validators — último run (GREEN)

### fe_typecheck_tsc
```
$ cd /home/chalreme/Proyectos/luana-platform/vitalia/frontend && npx tsc --noEmit
(no output — 0 errors)
```
Estado: PASS

### fe_lint_eslint
```
$ cd /home/chalreme/Proyectos/luana-platform/vitalia/frontend && npx eslint src/ --cache --cache-location .eslintcache --max-warnings 0
(no output — 0 errors, 0 warnings)
```
Estado: PASS

### fe_arch_fitness
```
$ cd /home/chalreme/Proyectos/luana-platform/vitalia/frontend && npx vitest run src/__tests__/architecture/ --reporter=default

 RUN  v2.1.9 /home/chalreme/Proyectos/luana-platform/vitalia/frontend

 ✓ src/__tests__/architecture/test-vitalia-ui-strings-no-voseo.test.ts (18 tests) 17ms

 Test Files  1 passed (1)
      Tests  18 passed (18)
   Start at  19:31:42
   Duration  327ms
```
Estado: PASS

## Decisiones técnicas tomadas

### globals.css — formato HSL channels
Tokens en formato `H S% L%` (no `hsl(H, S%, L%)`) per Tailwind v4 + Shadcn pattern.
Esto permite `hsl(var(--vitalia-cian))` en tailwind.config.ts y también
`rgb(var(--vitalia-cian) / 0.12)` para opacidad con `vitalia-cian/12` en clases Tailwind.

### Gradients en globals.css con HEX literales
Los gradients CSS (`linear-gradient(...)`) usan HEX literales como stops ya que CSS vars
`hsl()` no pueden componerse dentro de `linear-gradient` sin interpolación modern-color-mix.
Los HEX en globals.css son excepción aceptada (arch test `test_no_hardcoded_colors.test.ts`
excluye `globals.css` explícitamente per spec `03-arch-fe.md § 8.1`).

### tailwind.config.ts — REEMPLAZA seed values
El config original tenía 6 tokens SEED (`vitalia-primary`, `vitalia-accent`, `vitalia-critical`,
`vitalia-warning`, `vitalia-stable`) que fueron reemplazados por los 18 tokens oficiales del
brandbook. El token `vitalia-warning` fue mapeado al token semantic correcto
(se mantiene el nombre pero cambia la referencia CSS var a `--vitalia-warning` definida en
design-system.md § 1).

### layout.tsx — import globals.css
Agregado `import "./globals.css"` al inicio del archivo. No afecta el árbol de componentes
(Server Component puro). El `<body>` usa `bg-white font-sans` como clases Tailwind —
estas se deberán migrar a `bg-vitalia-bg font-body` en T-infra-1 (shell layout).

## Commit SHA pushed

`d6f01b6` — branch `wip/vitalia-slice-1-shipping`

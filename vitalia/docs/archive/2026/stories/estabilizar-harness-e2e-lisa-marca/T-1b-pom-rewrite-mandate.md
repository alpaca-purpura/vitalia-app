# T-1b — Reescritura POMs lisa-marca (phantom testids → locators reales)

> Continuación de T-1. Owner ejecución: builder-frontend. Orchestrator: /dev-team.
> Surface: SOLO `vitalia/frontend/e2e/regression/{vitalia-fase2-lisa-marca,arreglar-guardado-voz-y-tono}/`.
> Cero prod (src/), cero BE, cero core.

## Hallazgo (auditoría live del orchestrator)

Corriendo la suite de-mockeada LIVE contra el backend real, se descubrió que **~63 de 73 testids
referenciados por los POMs lisa-marca son FANTASMA** (no existen en `src/`). La página marca SÍ
funciona; el FE usa **ARIA semántico real** (roles/labels), NO data-testids. La suite NUNCA corrió
verde contra el DOM real — los POMs se escribieron contra un contrato de testids que nunca se
implementó. Inventario completo: `T-1b-phantom-testid-audit.txt`.

## Mandato

Para CADA locator en los 4 POMs lisa-marca (`poms/lisa-marca-page.pom.ts`, `identidad-section.pom.ts`,
`voz-tono-section.pom.ts`, `presencia` si existe) + el parent `arreglar-guardado-voz-y-tono/poms/voz-tono-section.pom.ts`:

1. LEÉ el componente FE correspondiente (`src/features/lisa/components/marca/{identidad,voz-y-tono,presencia}/*.tsx`)
   para encontrar el locator REAL.
2. Reescribí el locator priorizando (playwright-expert): **getByRole > getByLabel > getByText > getByTestId**.
   El FE expone roles/labels reales (ej. `textbox` con name "Nombre de la clínica", `heading "Identidad de la clínica"`,
   `tab "Identidad" [selected]`). Usá esos. Solo usá getByTestId para los testids que SÍ existen.
3. Testids REALES ya confirmados (NO son fantasma — usalos): `identidad-view`, `voz-tono-section-root`,
   `presencia-view`, `sub-sub-tabs-bar`, `sub-sub-tab-{id}` (con `aria-current="page"` en el activo),
   `autosave-badge` (verificá su `data-state`). Todo lo demás del inventario: verificá contra el FE.

## Tests dependientes de data pre-existente (deterministas sin seed)

El tenant de test (`e69a691d-...`) tiene identity VACÍO (`name:""`). Los tests que asertan "datos cargan
al montar" con `not.toHaveValue("")` fallan (no hay seed). Convertilos a **write-then-assert round-trip**:
escribir un valor → esperar PATCH 200 (real) → reload → asertar que persiste (web-first). Eso es
determinista + prueba el round-trip real + no depende de seed. Los tests de autosave ya escriben; ajustá los
de "load" para que creen su propia data primero.

## Verificación (split)

- VOS (builder): `npx tsc --noEmit` + `npx eslint e2e/ --max-warnings 0` (scoped a tus archivos) verde. NO podés
  correr la suite live (worktree aislado). Documentá en T-1b-result.md qué locator real mapeaste a cada phantom.
- ORCHESTRATOR (yo): corro la suite LIVE ×3 + parent ×5 contra el stack, itero lo que quede.

## Forbidden
- src/ (prod), BE, core, otras brands, otras features e2e (valeria/camila/staff). SOLO los POMs+specs lisa-marca + parent.

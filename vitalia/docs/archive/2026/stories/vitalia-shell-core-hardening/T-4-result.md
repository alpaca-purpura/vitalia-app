# T-4-result — Soft-nav (Decisión A): edge-redirect proxy + revertir band-aid hard-nav frozen-kpi-badge → next/link

**State:** pushed · **Builder:** builder-frontend (sonnet) · **Commit:** `523fe7c8` · **Branch:** `wip/vitalia`

## Qué se construyó

- **`vitalia/frontend/src/features/adrian/components/embudo/EmbudoMetrics.tsx`** — revertido el band-aid B1. El chip `frozen-kpi-badge` vuelve de hard-nav (`<a href>`) a **`next/link`** (soft-nav). Comentario `B1 fix v2` documenta la causa raíz + por qué el revert es seguro ahora. (AC-13)
- **`vitalia/frontend/src/proxy.ts`** — **verificada** la cobertura del 307 `bareTenantLandingRedirect`. Sin cambio funcional: el matcher ya cubre el único redirect IN-RENDER intra-route-group del shell (landing bare-tenant `/{uuid}` → `/{uuid}/mateo/agenda`). Agregada nota de auditoría T-4 explicando que `board→/adrian/recuperar` NO requiere extender el matcher.
- **`vitalia/frontend/src/features/adrian/components/embudo/__tests__/EmbudoMetrics.test.tsx`** (nuevo) — render + AC-13 source assertion. TDD RED→GREEN. 6 tests.

## Por qué el revert es seguro (root cause)

Per `03-arch.md § Architecture Decisions A` (§84-93) + learning `2026-06-03-next16-softnav`:

- El "Rendered more hooks" lo disparaba el **redirect IN-RENDER intra-route-group** de `(shell-organism)/page.tsx` hacia el layout `dynamic({ssr:false})` — NO cualquier soft-nav.
- Ese redirect se movió al **edge** (proxy.ts 307) → el browser pide el destino con fetch fresco → el Router monta limpio.
- `grep redirect( en (shell-organism)/**` = **0 fuera del landing** → no hay otro redirect in-render.
- `/adrian/recuperar` es una **ruta estática real** (`(shell-organism)/adrian/recuperar/page.tsx`, sin redirect in-render). El soft-nav del chip (`next/link`) por tanto **no dispara el hang** → el band-aid `<a>` ya no es necesario.
- `ssr:false` del shell **se conserva** (mandatorio por `react-resizable-panels v4.11.1` bare-name `localStorage` default param que crashea el SSR pass). NO se tocó.

## Cobertura del proxy 307 (deliverable a)

| Caso | Es redirect in-render? | Cubierto por 307? | Acción T-4 |
|---|---|---|---|
| `/{uuid}` (bare-tenant landing) | sí — `(shell-organism)/page.tsx` | ✅ sí (`bareTenantLandingRedirect`) | verificado, sin cambio |
| `board → /adrian/recuperar` (chip) | no — ruta estática real | n/a (no hay redirect) | revert `<a>`→`next/link` |

Conclusión: el matcher UUID-only ya es suficiente; **no se extendió** (extenderlo a `/adrian/recuperar` sería incorrecto — esa ruta no es un redirect).

## Chequeo fix upstream Next (deliverable c — mandatory pause-point)

- **Versión instalada:** `next 16.2.6` (`package.json` declara `^16.2.3`; `node_modules/next/package.json` resuelto a **16.2.6**).
- **WebSearch + WebFetch DESHABILITADOS** en este contexto de subagente (`No such tool available: WebSearch/WebFetch ... not enabled`) → **no fue posible verificar release notes upstream por red**.
- **Decisión:** default = **Decisión A (opción 2)**, edge-redirect + revert. **Next NO se bumpeó** — un bump requeriría (1) gate de regresión completo y (2) **escalate Chris** per ticket rationale ("no bumpear Next sin gate completo → bump = escalate Chris"), independientemente del resultado de la búsqueda. El pause-point se respeta: no se introdujo riesgo.
- **Follow-up sugerido (no bloqueante):** verificar manualmente en `https://nextjs.org` / GitHub releases si una versión 16.x posterior consumible sin breaking fixea "Rendered more hooks" en el client Router; si existe, preferirla a más edge-redirects (con gate de regresión + ratificación Chris).

## Gates

| Gate | Resultado |
|---|---|
| `npx tsc --noEmit` (archivos tocados) | ✅ 0 errors |
| `npx eslint` (EmbudoMetrics.tsx · .test.tsx · proxy.ts) | ✅ clean (exit 0) |
| `npx vitest run EmbudoMetrics.test.tsx + shell-routes.test.ts` | ✅ 14/14 (RED→GREEN) |
| `npx vitest run src/features/adrian/components/embudo` (colateral) | ✅ 37/37 (7 files) |

## Skills consulted (Step 0 GATE enforcement)

| Skill / Rule | Por qué | Decisión tomada |
|---|---|---|
| `frontend-expert` | must_load_skills · patrón FE/soft-nav/Next App Router | Confirmado Server Component default conservado; `next/link` para nav interna soft (no `<a>`); revert respeta FSD-Lite (named export, no default). |
| `playwright-expert` (e2e-testing rule) | must_load_skills · e2e SC-21 | e2e SC-21 ×15 = **T-7** (e2e_functional), fuera de scope T-4. NO se reescribió el e2e. `recuperar-live.spec.ts` queda con comentario stale ("hard-nav <a>") → flaggeado abajo para T-7/auditor. |
| `tdd-mandatory` | must_load_skills · RED→GREEN | Test RED primero (2 fails AC-13: `import Link` + `<a` literal) → revert → GREEN. Regex de source acotada a tag JSX (`/<a[\s>]/`) para no matchear prose. |
| `frontend-visual-fidelity` (canon) | inyectada al leer `frontend/src` | Sin surface visual nueva — solo mecanismo de nav. Chip conserva tokens/clases existentes. |
| `frontend-fsd` · `frontend-quality` | inyectadas al leer `frontend/src` | Boundary OK (feature:own); 0 default export; eslint clean. |

## Notas / handoff

- **e2e stale (T-7):** `vitalia/frontend/e2e/regression/vitalia-fase2-adrian-embudo/recuperar-live.spec.ts` R-1 tiene comentarios que dicen "el chip es `<a>` (hard-nav)" y el título `(hard-nav)`. Tras el revert eso es **factualmente incorrecto** (ahora es `next/link` soft-nav). El spec sigue funcionando (clickea `[data-testid=frozen-kpi-badge]` + assert sin burbuja), pero **T-7 debe actualizar el SC-21 ×15** a soft-nav real (el ticket T-4 scopea e2e a T-7, no lo toqué para no invadir esa surface).
- **DoD live-verify (#37):** NO ejercido en dev-app — requiere stack dev levantado (`make dev-app-vitalia` + tunnel + Clerk). Per instrucción, NO se levantó el stack desde el builder. El live-verify (write real + leer logs) + SC-21 ×15 quedan para T-7 / auditor / Chris-verify (G).
- **Commit por pathspec:** solo 3 archivos (proxy.ts · EmbudoMetrics.tsx · EmbudoMetrics.test.tsx). Sin contaminación cross-sesión (T-3 background agent toca shell-organism, surfaces disjuntas).

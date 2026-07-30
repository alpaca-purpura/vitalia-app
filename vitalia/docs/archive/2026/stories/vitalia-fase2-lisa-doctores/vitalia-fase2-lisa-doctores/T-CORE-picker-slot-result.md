# T-CORE-picker-slot — Result

- **Ticket:** T-CORE-picker-slot (06-tickets.yaml delta_v3 · group D3A-switcher · surface core-ui-kit)
- **Builder:** builder-frontend (Fable 5 — mandato Chris `model_mandate_2026_06_12`)
- **State:** build phase done (tests-passing) — awaiting orchestrator → gate-runner → auditor-frontend
- **Date:** 2026-06-12

## Lift gate (requires_pm_luana_lift)

Promotion proposal **EXISTE y está ACCEPTED** — el deliverable "redactar proposal" queda satisfecho por:
`docs/promotion-protocol/proposals/2026-06-12-ui-kit-entity-subnavbar-picker-slot.md`
(`status: accepted` · accepted_by: Chris, ratificación verbal 2026-06-11 · risk: low, aditivo/opt-in/back-compat). NO se redactó una segunda proposal (instrucción explícita del caller). Naming del contrato: la proposal delegaba el naming final al builder ("naming final lo fija el builder"); el ticket + `03-arch-delta.md §2.1` lo fijan como `entityIdentitySlot?: React.ReactNode` — ese es el implementado.

## Diff resumen (4 archivos, SOLO dentro del scope permitido)

| Archivo | Cambio |
|---|---|
| `core/@luana/ui-kit/src/EntitySubNavBar.tsx` | + prop opcional `entityIdentitySlot?: ReactNode` (JSDoc canon §6.3). Render: workspace mode (`entity !== null`) + slot presente → wrapper `data-testid="entity-identity-slot"` (clases Tailwind estáticas, JIT-safe) renderiza el nodo EN LUGAR del bloque estático avatar+nombre; slot ausente → bloque estático **verbatim** (solo se agregó el guard `!entityIdentitySlot`); master mode (`entity=null`) → slot NUNCA renderiza. El slot NO es tab (tablist/roving tabindex intactos — a11y del combobox la posee EntityPicker, consumido as-is, no tocado). |
| `core/@luana/ui-kit/src/EntityWorkspaceLayout.tsx` | + prop `entityIdentitySlot?: ReactNode` forwarded **verbatim** a `<EntitySubNavBar entityIdentitySlot={...}/>` (espejo exacto del forwarding de `onAddAffordance`). |
| `core/@luana/ui-kit/src/__tests__/EntitySubNavBar.test.tsx` | + describe `entityIdentitySlot (canon §6.3)` — 4 tests: back-compat ausente→estático sin wrapper · presente→nodo custom renderiza + bloque estático ausente (`aria-label="Editando: …"` null) · tablist no afectada (4 tabs) · master→slot no renderiza. **Cero líneas existentes modificadas** (diff aditivo puro, verificado `git diff | grep "^-"` = vacío). |
| `core/@luana/ui-kit/src/__tests__/EntityWorkspaceLayout.test.tsx` | + describe `entityIdentitySlot forwarding` — 3 tests: forward verbatim (detail) · back-compat ausente→estático · master→no renderiza. Diff aditivo puro. |

API existente: cero breaking (prop opcional, named exports intactos, `index.ts` sin cambios — la prop vive en la interface ya exportada).

## TDD

RED primero: los 7 tests nuevos se escribieron ANTES de la implementación. Run RED: `2 failed | 37 passed` (las assertions load-bearing "slot renderiza" fallaron contra el componente sin la prop). Luego implementación → GREEN.

## Gates (G5)

| Gate | Resultado |
|---|---|
| ui-kit unit suite completa (`npx vitest run`) | ✅ **266/266 PASS** (20 files) — baseline 259 + 7 nuevos. Back-compat ratchet: TODOS los tests existentes sin modificar pasan (diff test files 100% aditivo). |
| ui-kit `tsc --noEmit` | ⚠️ pre-existente ROJO a baseline (142 líneas de error: typings jest-dom no registrados package-wide + `Intl.supportedValuesOf` en `timezone-select.tsx` — archivos fuera de mi scope permitido). **Ratchet: 142 baseline → 142 con mi diff (cero crecimiento)**, verificado con stash A/B. **0 errores en los 2 archivos de producción tocados.** Los tests nuevos usan matchers nativos (`toBeTruthy`/`toBeNull`) para no sumar al baseline. Fix del typing gap = fuera de scope (requiere tocar `vitest.setup.ts`/`tsconfig.json`, no permitidos) → candidato CIL L3. |
| ui-kit eslint | **N/A — pre-existente**: no existe config ESLint que cubra `core/@luana/*` (sin config package-level ni root; `vitalia/frontend/eslint.config.mjs` ignora fuera de base path — verificado: "File ignored because outside of base path"). Gates reales del package: vitest + tsc. |
| Downstream `vitalia/frontend && npx tsc --noEmit` | ✅ **EXIT 0** (consumers compilan: adrian/NewLeadPage, ICPs, staff). |
| Downstream `nicolify/frontend && npx tsc --noEmit` (extra, consumer citado en la proposal) | ✅ **EXIT 0**. |

## Live verification

N/A para este ticket: cambio CORE aditivo opt-in, sin wiring de marca — no hay superficie user-visible que ejercer hasta que `T-FE-switcher-wire` (depends_on este ticket) cablee el EntityPicker en `StaffWorkspaceShell`. El exit_criterion de ESE ticket carga el live-verify dev-app + `dod_evidence` (06-tickets.yaml L350). El exit_criterion de este ticket = suite core GREEN + back-compat ratchet + proposal (cumplidos arriba). Matches checklist runtime-quality § "Cuándo skip": sin UI changes user-visible.

## Skills Consulted

| Skill | Por qué | Decisión tomada |
|---|---|---|
| `frontend-expert` (+ `references/runtime-quality-checklist.md` leído completo pre-commit) | always-on FE | Sin `useEffect` nuevo, sin hooks state-derived, sin routing — checklist limpio. Mock `next/navigation` ya incluye todas las exports usadas (useRouter/usePathname/useParams). Live-verify gate: skip justificado (sin UI change user-visible; wiring = T-FE-switcher-wire). |
| `vitalia-design-system` / design-system-canon §6.3 + §2.4 (must_load_artifacts) | contrato del slot | Identidad = selector ("cambiar sin volver"); slot reemplaza bloque estático, no agrega tab; EntityPicker consumido as-is (forbidden_to_touch), posee su propia a11y combobox/listbox. |
| React patterns baseline | always-on | Slot guard triple (`!isMasterMode && entity && entityIdentitySlot`); estáticas Tailwind JIT-safe; keys/memoization sin cambios; tablist ARIA intacta (test dedicado). |
| Shadcn/Tailwind conventions | always-on | Cero primitiva nueva, cero inline style, clases estáticas en wrapper (`flex items-center min-w-0 flex-shrink-0 mx-3`). |
| `anti-duplication` (must_load_rules) | pre-write gate | No se creó archivo nuevo; EXTEND aditivo del componente engine existente vía lift gate accepted — exactamente el carril correcto (no mirror en vitalia). |
| `chrome-devtools-verify` | declarada | NO invocada — justificación en § Live verification (sin superficie live hasta T-FE-switcher-wire). |
| brand/offer/preset/copilot/sales-agent/metrics experts | cargadas por el caller | No aplicables — ticket no toca esos dominios. |

## Mockup scope notes

El mockup `mockups/doctores.html` muestra el EntityPicker dentro de `doctoresN3Bar` — eso es scope de T-FE-switcher-wire, NO de este ticket. Este ticket entrega SOLO el slot genérico brand-agnostic (scope discipline D3).

## Commit

- `feat(ui-kit): EntitySubNavBar + EntityWorkspaceLayout — entityIdentitySlot opcional (canon §6.3, back-compat)` — pathspec scoped a los 4 archivos. SHA en footer del reply del builder. ⛔ NO push (orchestrator pushea serial — hub compartido).

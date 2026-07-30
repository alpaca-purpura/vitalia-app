# T-R3 result — ResumenView fidelity (collapsibles + hydrate + autosave + modality conditionals + KnowledgePanel)

**Story:** vitalia-fase2-lisa-servicios · **Ticket:** T-R3 (reconcile-delta · gated on T-R0 + T-R1, both met)
**Date:** 2026-06-16 · **Brand:** vitalia

> Builder (builder-frontend) implemented the edits, then hit an API 500 before running the final gates / writing this result. Orchestrator (sole driver) ran the gates, found + fixed one test regression (shell test mock), confirmed GREEN, and authored this result.

## Summary

Brings the ResumenView workspace from ~40% to mockup fidelity (`mockups/servicio-workspace.html`):
1. **6 collapsibles** — the 6 flat `<Group>` replaced by `<CollapsibleSection>` (`@luana/ui-kit`, from T-R0): Identidad `defaultOpen`, the other 5 closed, `summary` = field-count, `accentVar="--agent-lisa"`, click toggle.
2. **Hydrate all rich fields** — every rich field now binds `value={servicio.X}` + `onChange→schedule({X})` (use-autosave 600ms, single `FloatingAutosaveIndicator`). Previously dead placeholders.
3. **VariantsRepeater** — `value={servicio.variants}` + autosave + currency from `servicio.currency` (not hardcoded).
4. **Modality conditionals** — sesiones→`session_interval` / recurrente→`recurrence_interval` reveal+bind+autosave.
5. **KnowledgeSourcesPanel** — mounted in `ServicioWorkspaceShell` (persistent cross-leaf, native `<details>` collapsible per mockup `kpanel`).
6. **FE types** — `servicios.types.ts` extended with the rich fields (snake_case mirror of the T-R1 `ServiceDetailDTO`) + widened patch payload type.

## Files modified

| File | Change |
|---|---|
| `vitalia/frontend/src/features/lisa/components/servicios/leaves/ResumenView.tsx` | 6 CollapsibleSection + hydrate all rich fields + onChange→autosave + variants + modality conditionals |
| `vitalia/frontend/src/features/lisa/components/servicios/leaves/__tests__/ResumenView.test.tsx` | RED-first vitest — hydration + autosave + conditionals + collapsibles |
| `vitalia/frontend/src/features/lisa/components/servicios/workspace/ServicioWorkspaceShell.tsx` | mount KnowledgeSourcesPanel (persistent `<details>` below {children}) |
| `vitalia/frontend/src/features/lisa/types/servicios.types.ts` | rich fields on ServiceDetail + widened patch type |
| `vitalia/frontend/src/features/lisa/components/servicios/__tests__/ServicioWorkspaceShell.test.tsx` | **orchestrator fix:** mock `KnowledgeSourcesPanel` to a thin passthrough (the shell now mounts it → its `useProcessDocument` crashed all 11 shell tests; same isolation pattern as the ServiceStatusBar mock) |

## Orchestrator gate-completion (builder died at API 500 pre-gates)

- **Regression found:** mounting `KnowledgeSourcesPanel` in the shell broke all 11 `ServicioWorkspaceShell.test.tsx` tests — the shell test's `vi.mock("../../../api/servicios")` did not stub `useProcessDocument` (new dependency), so the hook was `undefined` → render crash. NOT a real-app bug (the hook exists + works live). Fixed test-side by mocking the panel to a passthrough.

## Gate output (orchestrator-run · native)

```
tsc --noEmit:     0 errors (clean)
eslint servicios: 0 errors, 0 warnings (clean)
vitest lisa:      668 passed / 0 failed (70 test files)
```

## Constraints verified

- [x] Consumes `@luana/ui-kit` CollapsibleSection (did NOT edit ui-kit)
- [x] `components/ui/accordion.tsx` dup NOT deleted (2 live mateo importers · deferred cleanup story)
- [x] Other leaves / EscaleraView / CatalogoView / other features untouched
- [x] ONE FloatingAutosaveIndicator (canon §2.6) · Select canónico · tokens not arbitrary
- [x] useTenantId never orgId · Spanish-neutro
- [x] layout.tsx untouched (G2 SSR-safe)

## Next (CLOSE gate)

Re-live-verify (DoD #37 · Chrome DevTools MCP): exercise a rich-field autosave write live + read BE logs + confirm DB + visual match vs mockup (collapsibles + hydrated fields + StatusBar + KnowledgePanel) + 8 visual goldens. Then /auditor → chris_verify.signoff (G).

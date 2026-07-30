# T-R2 result — Mount ServiceStatusBar inside ServicioWorkspaceShell + delete orphan ServicioWorkspaceView

**Story:** vitalia-fase2-lisa-servicios  
**Ticket:** T-R2 (reconcile-delta · independent of T-R0/T-R1)  
**Date:** 2026-06-16  
**Brand:** vitalia  

## Summary

F1 (StatusBar never rendered in the real app) fixed by:

1. Moving `ServiceStatusBar` render into `ServicioWorkspaceShell` (which already owns `servicio` from `useServicioDetail` + `offerId`) — sticky above `{children}`.
2. Deleting `ServicioWorkspaceView` (confirmed orphan: only in barrel, never consumed by `layout.tsx`).
3. Wiring `useActivateServicio` directly in the shell so the Activo toggle fires `POST /api/v1/offer/servicios/{offerId}/activate`.

`layout.tsx` untouched — G2 SSR-safe constraint preserved.

## Files modified

| Action | Path |
|---|---|
| MODIFIED | `vitalia/frontend/src/features/lisa/components/servicios/workspace/ServicioWorkspaceShell.tsx` |
| DELETED | `vitalia/frontend/src/features/lisa/components/servicios/ServicioWorkspaceView.tsx` |
| MODIFIED | `vitalia/frontend/src/features/lisa/index.ts` (removed `ServicioWorkspaceView` export line 132) |
| MODIFIED | `vitalia/frontend/src/features/lisa/components/servicios/__tests__/ServicioWorkspaceShell.test.tsx` (4 new T-R2 test cases) |

## Changes detail

### ServicioWorkspaceShell.tsx (diff summary)

```
+ import { useActivateServicio } from "../../../api/servicios";
+ import { ServiceStatusBar } from "../ServiceStatusBar";

  // Inside component body:
+ const { mutate: toggleActive, isPending: isToggling } = useActivateServicio();
+ const handleToggleActive = (isActive: boolean) => { toggleActive({ offerId, isActive }); };

  // Inside EntityWorkspaceLayout, above {children}:
+ {servicio && (
+   <ServiceStatusBar servicio={servicio} onToggleActive={handleToggleActive} isToggling={isToggling} />
+ )}
```

### index.ts barrel

Removed: `export { ServicioWorkspaceView } from "./components/servicios/ServicioWorkspaceView";`

## Gate output

```
tsc --noEmit:     0 errors (clean)
ESLint servicios: 0 errors, 0 warnings (clean)
vitest run lisa:  656 passed / 0 failed (70 test files)
  — including 4 new T-R2 cases:
    ✓ T-R2: renders ServiceStatusBar above {children} when servicio is loaded
    ✓ T-R2: does NOT render ServiceStatusBar when servicio is not yet loaded
    ✓ T-R2: toggle button calls useActivateServicio mutate with {offerId, isActive}
    ✓ T-R2: toggle button reflects isPending=true as isToggling
```

## Skills consulted

| Skill | Decision |
|---|---|
| `frontend-expert` (React patterns baseline) | Mount StatusBar conditionally on `servicio` (not isLoading), memoization not needed (re-render only on servicio change) |
| `frontend-fsd` (FSD-Lite boundaries) | Import `ServiceStatusBar` from sibling path `../ServiceStatusBar` — same feature, no cross-feature violation |
| `tenant-isolation` | `useActivateServicio` receives `offerId` (not tenantId); `fetchClient` auto-injects `X-Tenant-ID`; `useTenantId` NEVER `orgId` (not used in this component) |
| `tdd-mandatory` | RED-first: wrote 3 failing T-R2 tests → confirmed RED → implemented GREEN → 11/11 pass |

## Architectural constraint respected

`layout.tsx` was NOT modified. It remains a pure Server Component importing `ServicioWorkspaceShell` directly (G2 store-free SSR-safe layout).

## Changes UNCOMMITTED (as requested)

`git status` will show:
- modified: `vitalia/frontend/src/features/lisa/components/servicios/workspace/ServicioWorkspaceShell.tsx`
- deleted: `vitalia/frontend/src/features/lisa/components/servicios/ServicioWorkspaceView.tsx`
- modified: `vitalia/frontend/src/features/lisa/index.ts`
- modified: `vitalia/frontend/src/features/lisa/components/servicios/__tests__/ServicioWorkspaceShell.test.tsx`

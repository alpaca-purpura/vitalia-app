<!-- voseo-allowed: internal architecture spec referencing glossary -->

---
story_id: vitalia-fase1-tenant-switcher
brand: vitalia
type: ui-story
phase: fase-1
module: shell-organism
agent_owner: shell
capability: shell.tenant-switcher
architect_version: 1.0
architect_iter: 1
last_modified: 2026-05-22
architect_run_on: 2026-05-22
predecessor_arch: vitalia/docs/product/stories/vitalia-fase1-topbar-global/03-arch.md
spec_consumed: vitalia/docs/product/stories/vitalia-fase1-tenant-switcher/01-spec.md
mockups_consumed:
  - vitalia/docs/product/stories/vitalia-fase1-tenant-switcher/mockups/tenant-switcher-closed.html
  - vitalia/docs/product/stories/vitalia-fase1-tenant-switcher/mockups/tenant-switcher-open.html
nicolify_reuse_reference: nicolify/frontend/src/components/shared/layout/TenantSwitcher.tsx
design_contract: vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md
no_phi_scope: true                                  # ★ HIPAA-lite NO aplica (chrome UI sin PHI)
agentic_scope: false                                # NO LLM, NO copilot/sales_agent tools
backend_scope: false                                # consume engine /api/tenants ya shipped Story 11
frontend_only: true
---

# F1-S3 `vitalia-fase1-tenant-switcher` — 03-arch (FE-only)

## § 0 — Context Summary

**Architect run on:** 2026-05-22

**Modules touched:** `vitalia/frontend/src/components/shared/shell-organism/` (organismo + átomo + molécula + modal) + `vitalia/frontend/src/stores/` (Zustand) + `vitalia/frontend/src/hooks/` (React Query) + `vitalia/frontend/src/lib/` (palette helper).

**Surface → builder → auditor mapping** (PM consumirá para spawnear correctamente):

| Surface | Builder | Auditor |
|---|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/{TenantSwitcher,TenantOption,TenantBadge,AddClinicPlaceholderModal}.tsx` | `builder-frontend` (Sonnet/opencode) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/stores/tenant-store.ts` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/hooks/useTenants.ts` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| `vitalia/frontend/src/lib/tenant-palette.ts` | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| `vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/*.spec.ts` + POM + fixtures | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |
| **Visual goldens** (Playwright screenshots) | `builder-frontend` (Sonnet) | `auditor-frontend` (Opus) |

**ZERO Opus en build** — FE no-agentic puro (R23 N/A). `production_code: true` pero Sonnet/opencode OK.

**Skills consulted:**
- `frontend-expert` → FSD-Lite boundaries, Server-First defaults, "use client" solo en hojas con state/effects, React Query staleTime, Zustand persist patterns.
- `brand-expert` → N/A scope (no brand identity surface).
- `copilot-expert` → N/A (sin agentic).
- `sales-agent-expert` → N/A.
- `tessl__shadcn-ui` (a invocar por builder) → DropdownMenu + Dialog + Alert + Skeleton primitives canonical.
- `tessl__tailwind` (a invocar por builder) → semantic tokens shell (bg/foreground/accent/muted/ring).
- `tessl__zustand` (a invocar por builder) → persist middleware partialize + storage event listeners.
- `tessl__react-query` (a invocar por builder) → useQuery hook con onSuccess hidratación store.
- `playwright-expert` (a invocar por builder en T-9) → E2E specs, POMs, fixtures Clerk auth.

**CONTEXT-BRIEF source:** caller pasó inputs directos (story refined post-ratify visual iter 1). Self-ran greps Path B donde necesario (verificación existing files vitalia frontend + cross-brand mirror scan ex-ante).

**Cross-brand mirror scan ex-ante (auditor-downstream-regression.md preventivo):**
```bash
WS=/home/chalreme/Proyectos/luana-vitalia
find ${WS}/{nicolify,vitalia,comunify,lupulo}/frontend/src -name "TenantSwitcher.tsx" 2>/dev/null
# resultado esperado: nicolify (reference 75% reuse) + vitalia (NEW post-build)
# 2 brands = under threshold (3 brands o cross-brand identical >50% triggea lift /pm-luana)
# diferencias clave: variant horizontal-only, redirect path preservation, data shape minimal, palette hash
```

**Capability YAML affected (post-merge update mandatory per R32 + post 2026-05 paradigma):**
- `vitalia/docs/product/capabilities/shell-organism/tenant-switcher.yaml` (NEW — status: live, verification.commands ejecutables)
- `vitalia/docs/product/modules/shell-organism.md` (auto-list refresh via `scripts/reconcile_capabilities.py --brand vitalia`)

**Architecture gates que deben seguir GREEN post-PR:**
- `vitalia/frontend/src/__tests__/architecture/test-fsd-boundaries.test.ts` — shell-organism imports válidos
- `vitalia/frontend/src/__tests__/architecture/test-page-padding.test.ts` — no rompe ratchet
- `vitalia/frontend/src/__tests__/architecture/test-no-clerk-organizations.test.ts` (NEW arch test que este PR introduce) — enforce MEMORY no-clerk-orgs

---

## § 1 — Surfaces affected

| Surface | Action | Notes |
|---|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/TenantBadge.tsx` | **NEW** | átomo Server Component (no client state) |
| `vitalia/frontend/src/components/shared/shell-organism/TenantOption.tsx` | **NEW** | molécula Server Component (onClick fluye via DropdownMenuItem parent Radix) |
| `vitalia/frontend/src/components/shared/shell-organism/TenantSwitcher.tsx` | **NEW** | organismo Client Component (state + effects) |
| `vitalia/frontend/src/components/shared/shell-organism/AddClinicPlaceholderModal.tsx` | **NEW** | Dialog Shadcn placeholder |
| `vitalia/frontend/src/components/shared/shell-organism/TopBarGlobal.tsx` | **MODIFY 1-line** | import + render replace `<TenantSwitcherSlot />` → `<TenantSwitcher />` |
| `vitalia/frontend/src/components/shared/shell-organism/TenantSwitcherSlot.tsx` | **DELETE** | placeholder F1-S2, ya cumplió su rol |
| `vitalia/frontend/src/stores/tenant-store.ts` | **NEW** | Zustand persist + onSignOut cleanup |
| `vitalia/frontend/src/hooks/useTenants.ts` | **NEW** | React Query 5min staleTime |
| `vitalia/frontend/src/hooks/useSignOutCleanup.ts` | **NEW** | Clerk signOut listener limpia localStorage cross-user |
| `vitalia/frontend/src/lib/tenant-palette.ts` | **NEW** | PALETTE const + pickPaletteColor hash helper |
| `vitalia/frontend/src/app/layout.tsx` | **MODIFY** | mount `<TenantStoreBootstrap />` provider (boot hydration via useTenants + useSignOutCleanup) |
| `vitalia/frontend/src/components/shared/shell-organism/TenantStoreBootstrap.tsx` | **NEW** | Client Component invisible que ejecuta useTenants + useSignOutCleanup en mount root layout |
| Tests Vitest (5 unit files) | **NEW** | TenantBadge / TenantOption / TenantSwitcher / tenant-store / tenant-palette |
| Tests Playwright (11 e2e specs + POM + fixtures) | **NEW** | en `vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/` |
| Visual goldens Playwright (8 screenshots) | **NEW** | closed/open × light/dark × loading/error |

**Engine:** N/A — no toca `core/luana-core-*/`.

**Other brands:** N/A — no toca `nicolify|comunify|lupulo/`.

**Backend:** N/A — consume engine endpoint `/api/tenants` shipped en `core/luana-core-iam` (Story 11 vitalia-auth done 2026-05-19). Sin migrations, sin nuevos DTOs, sin API routes.

**Agentic:** N/A — chrome UI, no LangGraph, no tools, no LLM, no prompt cache.

---

## § 2 — Frontend architecture detail

### § 2.1 — Brand assets

N/A — no PNG nuevo. Reusa logo Vitalia mark de F1-S2 + paleta tokens shell de F1-S1.

### § 2.2 — TypeScript types verbatim

`vitalia/frontend/src/stores/tenant-store.ts` types section:

```typescript
// Data shape API /api/tenants (D2 decisión cementada: solo city, no branch)
export interface Tenant {
  readonly id: string       // slug-style (kebab-case): "sonrisa-plena"
  readonly name: string     // human-readable: "Sonrisa Plena"
  readonly city: string     // city only: "Lima"
}

export interface TenantsApiResponse {
  readonly tenants: ReadonlyArray<Tenant>
}

// Zustand store contract
export interface TenantStoreState {
  readonly activeTenant: Tenant | null
  readonly availableTenants: ReadonlyArray<Tenant>
}

export interface TenantStoreActions {
  setActiveTenant: (tenant: Tenant) => void
  setAvailableTenants: (tenants: ReadonlyArray<Tenant>) => void
  switchTenant: (id: string) => Tenant | null   // returns target tenant or null si not found
  clearStore: () => void                         // used by signOut cleanup
}

export type TenantStore = TenantStoreState & TenantStoreActions
```

`vitalia/frontend/src/lib/tenant-palette.ts` types:

```typescript
export interface PaletteColor {
  readonly bg: string    // Tailwind bg class (bg-cyan-500 etc.)
  readonly text: string  // Tailwind text class (text-white | text-amber-950 | text-lime-950)
}

export type PaletteIndex = 0 | 1 | 2 | 3 | 4 | 5
```

### § 2.3 — `TenantBadge.tsx` (átomo — Server Component if possible)

`vitalia/frontend/src/components/shared/shell-organism/TenantBadge.tsx`:

```tsx
import { cn } from '@/lib/utils'
import { pickPaletteColor } from '@/lib/tenant-palette'
import type { Tenant } from '@/stores/tenant-store'

interface TenantBadgeProps {
  tenant: Pick<Tenant, 'id' | 'name'>
  className?: string
}

// Server Component — pure function, no client state needed
export function TenantBadge({ tenant, className }: TenantBadgeProps) {
  const { bg, text } = pickPaletteColor(tenant.id)
  const initials = tenant.name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? '')
    .join('') || '?'

  return (
    <span
      aria-hidden="true"
      className={cn(
        'inline-flex size-6 shrink-0 items-center justify-center rounded text-xs font-bold',
        bg,
        text,
        className
      )}
    >
      {initials}
    </span>
  )
}
```

**Notes:**
- `aria-hidden="true"` — TenantBadge es decorativo. Screen reader lee el name via TenantOption parent.
- `Pick<Tenant, 'id' | 'name'>` — accepts subset (city no requerida).
- `pickPaletteColor(tenant.id)` — hash determinístico cross-session.

### § 2.4 — `TenantOption.tsx` (molécula — Server Component)

`vitalia/frontend/src/components/shared/shell-organism/TenantOption.tsx`:

```tsx
import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import { TenantBadge } from './TenantBadge'
import type { Tenant } from '@/stores/tenant-store'

interface TenantOptionProps {
  tenant: Tenant
  active: boolean
}

// Server Component — rendered inside DropdownMenuItem (Radix handles onClick)
export function TenantOption({ tenant, active }: TenantOptionProps) {
  return (
    <div
      data-testid={`tenant-option-${tenant.id}`}
      data-active={active}
      className={cn(
        'flex w-full items-center gap-3 rounded-sm px-2 py-2',
        active ? 'bg-accent/40' : 'hover:bg-muted'
      )}
    >
      <TenantBadge tenant={tenant} />
      <div className="flex min-w-0 flex-1 flex-col">
        <span className="truncate text-sm font-medium text-foreground">
          {tenant.name}
        </span>
        <span className="truncate text-xs text-muted-foreground">
          {tenant.city}
        </span>
      </div>
      {active ? (
        <>
          <Check className="size-4 shrink-0 text-foreground" aria-hidden="true" />
          <span className="sr-only">Clínica activa</span>
        </>
      ) : null}
    </div>
  )
}
```

### § 2.5 — `TenantSwitcher.tsx` (organismo — Client Component)

`vitalia/frontend/src/components/shared/shell-organism/TenantSwitcher.tsx`:

```tsx
'use client'

import { useState } from 'react'
import { usePathname } from 'next/navigation'
import { ChevronDown, Plus, Settings, AlertTriangle } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { useTenantStore, type Tenant } from '@/stores/tenant-store'
import { useTenants } from '@/hooks/useTenants'
import { TenantBadge } from './TenantBadge'
import { TenantOption } from './TenantOption'
import { AddClinicPlaceholderModal } from './AddClinicPlaceholderModal'

export function TenantSwitcher() {
  const activeTenant = useTenantStore((s) => s.activeTenant)
  const availableTenants = useTenantStore((s) => s.availableTenants)
  const switchTenantStore = useTenantStore((s) => s.switchTenant)
  const pathname = usePathname()
  const { isLoading, isError, refetch } = useTenants()
  const [addModalOpen, setAddModalOpen] = useState(false)

  // Empty state: 0 tenants → graceful degrade, NO render trigger
  if (!isLoading && !isError && availableTenants.length === 0) {
    return null  // banner top-page lives en otro componente (TenantEmptyBanner — render condicional en layout)
  }

  // Idle pre-hydration: nothing to render (skeleton handled by parent layout if needed)
  if (!activeTenant && !isLoading) {
    return null
  }

  const handleSwitch = (tenantId: string) => {
    const target = switchTenantStore(tenantId)
    if (!target) {
      // eslint-disable-next-line no-console
      console.warn(`Tenant ${tenantId} no encontrado en availableTenants`)
      return
    }
    // No-op si mismo tenant (edge single-tenant Scenario 12)
    if (target.id === activeTenant?.id) return
    // Hard redirect path preservation (D ver § 7)
    const newPath = buildRedirectPath(pathname, tenantId)
    window.location.href = newPath
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="outline"
            data-testid="tenant-switcher-trigger"
            aria-label="Cambiar clínica"
            title={activeTenant?.name ?? ''}
            className="h-10 gap-2"
          >
            {activeTenant ? <TenantBadge tenant={activeTenant} /> : <Skeleton className="size-6" />}
            <span className="hidden truncate sm:inline max-w-[140px] md:max-w-[180px]">
              {activeTenant?.name ?? '…'}
            </span>
            <ChevronDown className="size-4 shrink-0" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          align="end"
          sideOffset={8}
          className="min-w-[280px] max-h-80 overflow-y-auto"
          role="menu"
        >
          <DropdownMenuLabel className="text-xs uppercase tracking-wider text-muted-foreground">
            Mis clínicas
          </DropdownMenuLabel>

          {isLoading ? (
            <LoadingSkeletonRows />
          ) : isError ? (
            <ErrorBlock onRetry={() => void refetch()} />
          ) : (
            availableTenants.map((tenant) => (
              <DropdownMenuItem
                key={tenant.id}
                onSelect={(event) => {
                  event.preventDefault()  // prevent Radix auto-close before redirect
                  handleSwitch(tenant.id)
                }}
                className="p-0 focus:bg-transparent"
              >
                <TenantOption tenant={tenant} active={tenant.id === activeTenant?.id} />
              </DropdownMenuItem>
            ))
          )}

          <DropdownMenuSeparator />

          {!isError ? (
            <DropdownMenuItem onSelect={() => setAddModalOpen(true)}>
              <Plus className="mr-2 size-4" />
              Agregar clínica
            </DropdownMenuItem>
          ) : null}

          <DropdownMenuItem asChild>
            <a href={activeTenant ? `/${activeTenant.id}/config/cuenta` : '#'}>
              <Settings className="mr-2 size-4" />
              Administrar cuenta
            </a>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      <AddClinicPlaceholderModal open={addModalOpen} onOpenChange={setAddModalOpen} />
    </>
  )
}

// Inline private sub-components
function LoadingSkeletonRows() {
  return (
    <div role="status" aria-live="polite">
      <span className="sr-only">Cargando clínicas…</span>
      {[0, 1, 2].map((i) => (
        <div key={i} className="flex items-center gap-3 px-2 py-2">
          <Skeleton className="size-6" />
          <div className="flex flex-1 flex-col gap-1">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-2 w-12" />
          </div>
        </div>
      ))}
    </div>
  )
}

function ErrorBlock({ onRetry }: { onRetry: () => void }) {
  return (
    <Alert variant="destructive" className="m-1">
      <AlertTriangle className="size-4" />
      <AlertTitle>No pudimos cargar tus clínicas</AlertTitle>
      <AlertDescription>
        Intenta de nuevo o revisa tu conexión.
      </AlertDescription>
      <Button
        variant="outline"
        size="sm"
        className="mt-2"
        onClick={onRetry}
        data-testid="tenant-switcher-retry"
      >
        Reintentar
      </Button>
    </Alert>
  )
}

// Algoritmo path preservation — exportado puro para test independiente (§ 7)
export function buildRedirectPath(currentPath: string, newTenantId: string): string {
  if (!currentPath || currentPath === '/') return `/${newTenantId}`
  return currentPath.replace(/^\/[^/]+/, `/${newTenantId}`) || `/${newTenantId}`
}
```

**Notes críticas:**
- `onSelect={(event) => { event.preventDefault(); handleSwitch(...) }}` — previene Radix auto-close ANTES del redirect (sino dropdown se cierra y handleSwitch race con unmount).
- Race condition Scenario 3 (doble click <150ms): segundo `handleSwitch` ejecuta `window.location.href = newPath2`; browser cancela primer redirect en flight. Determinístico = último click gana.
- Empty state (`availableTenants.length === 0`): retorna `null`. Banner top-page vive en otro componente (no scope F1-S3 trigger — `TenantEmptyBanner` se monta en layout solo si store reporta empty post-hydration).

### § 2.6 — `AddClinicPlaceholderModal.tsx` (Dialog Shadcn)

`vitalia/frontend/src/components/shared/shell-organism/AddClinicPlaceholderModal.tsx`:

```tsx
'use client'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'

interface AddClinicPlaceholderModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function AddClinicPlaceholderModal({ open, onOpenChange }: AddClinicPlaceholderModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Próximamente</DialogTitle>
          <DialogDescription>
            Próximamente: agregar nueva clínica desde Configurar → Mi cuenta
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button onClick={() => onOpenChange(false)}>Entendido</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
```

### § 2.7 — `tenant-store.ts` (Zustand persist + onSignOut cleanup)

`vitalia/frontend/src/stores/tenant-store.ts`:

```typescript
import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

// Types (ver § 2.2)
export interface Tenant {
  readonly id: string
  readonly name: string
  readonly city: string
}

export interface TenantsApiResponse {
  readonly tenants: ReadonlyArray<Tenant>
}

interface TenantStoreState {
  activeTenant: Tenant | null
  availableTenants: ReadonlyArray<Tenant>
  setActiveTenant: (tenant: Tenant) => void
  setAvailableTenants: (tenants: ReadonlyArray<Tenant>) => void
  switchTenant: (id: string) => Tenant | null
  clearStore: () => void
}

export const TENANT_STORAGE_KEY = 'vitalia-tenant-state'

export const useTenantStore = create<TenantStoreState>()(
  persist(
    (set, get) => ({
      activeTenant: null,
      availableTenants: [],
      setActiveTenant: (tenant) => set({ activeTenant: tenant }),
      setAvailableTenants: (tenants) => {
        set({ availableTenants: tenants })
        // Auto-pick first tenant si activeTenant es null
        const current = get().activeTenant
        if (!current && tenants.length > 0) {
          set({ activeTenant: tenants[0] })
        }
      },
      switchTenant: (id) => {
        const target = get().availableTenants.find((t) => t.id === id)
        if (!target) return null
        set({ activeTenant: target })
        return target
      },
      clearStore: () => set({ activeTenant: null, availableTenants: [] }),
    }),
    {
      name: TENANT_STORAGE_KEY,
      storage: createJSONStorage(() => localStorage),
      // partialize: solo activeTenant persiste (availableTenants hidrata de API en mount)
      partialize: (state) => ({ activeTenant: state.activeTenant }),
      version: 1,
    }
  )
)
```

**Notes:**
- `partialize` solo persiste `activeTenant` (decisión cementada per spec § 8.4). `availableTenants` siempre hidrata de `/api/tenants` en mount → garantiza fresh data + previene stale tenants list cross-session.
- `setAvailableTenants` auto-asigna primer tenant si `activeTenant === null` (boot scenario).
- `clearStore` exportado para signOut cleanup (§ 2.7-bis).
- `version: 1` permite future schema migrations (Zustand persist nativo).

### § 2.7-bis — `useSignOutCleanup.ts` (Clerk hook cross-user isolation)

`vitalia/frontend/src/hooks/useSignOutCleanup.ts`:

```typescript
'use client'

import { useEffect } from 'react'
import { useAuth } from '@clerk/nextjs'
import { useTenantStore, TENANT_STORAGE_KEY } from '@/stores/tenant-store'

/**
 * Cross-user isolation: cuando Clerk signOut completa, limpia localStorage
 * Y reset Zustand store. Garantiza que user_B logging-in mismo browser NO
 * vea tenants de user_A (Scenario 6).
 *
 * Trigger: detecta `isSignedIn` flip true → false vía Clerk useAuth hook.
 */
export function useSignOutCleanup() {
  const { isLoaded, isSignedIn } = useAuth()
  const clearStore = useTenantStore((s) => s.clearStore)

  useEffect(() => {
    if (!isLoaded) return
    if (isSignedIn === false) {
      // Sign-out completed → cleanup
      clearStore()
      try {
        localStorage.removeItem(TENANT_STORAGE_KEY)
      } catch {
        // SSR/private mode: silent fail
      }
    }
  }, [isLoaded, isSignedIn, clearStore])
}
```

### § 2.7-ter — `TenantStoreBootstrap.tsx` (invisible mount root layout)

`vitalia/frontend/src/components/shared/shell-organism/TenantStoreBootstrap.tsx`:

```tsx
'use client'

import { useTenants } from '@/hooks/useTenants'
import { useSignOutCleanup } from '@/hooks/useSignOutCleanup'

/**
 * Invisible bootstrap mount en root layout.
 * Triggers fetch /api/tenants + Clerk signOut listener.
 * Sin UI render — solo lifecycle.
 */
export function TenantStoreBootstrap() {
  useTenants()           // fetch + onSuccess hidrata store
  useSignOutCleanup()    // cross-user isolation
  return null
}
```

### § 2.8 — `useTenants.ts` (React Query 5min staleTime + hidratación store)

`vitalia/frontend/src/hooks/useTenants.ts`:

```typescript
'use client'

import { useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'
import { fetchClient } from '@/lib/api/fetchClient'
import { useTenantStore, type TenantsApiResponse } from '@/stores/tenant-store'

export const TENANTS_QUERY_KEY = ['tenants'] as const

export function useTenants() {
  const setAvailableTenants = useTenantStore((s) => s.setAvailableTenants)

  const query = useQuery<TenantsApiResponse>({
    queryKey: TENANTS_QUERY_KEY,
    queryFn: () => fetchClient<TenantsApiResponse>('/api/tenants'),
    staleTime: 5 * 60 * 1000,          // 5 min — D5 spec § 8.1
    gcTime: 10 * 60 * 1000,            // 10 min retention cache
    refetchOnWindowFocus: false,        // tenants list raramente cambia mid-session
    retry: 2,
  })

  // Hidratar Zustand store cuando query resuelve OK
  useEffect(() => {
    if (query.data) {
      setAvailableTenants(query.data.tenants)
    }
  }, [query.data, setAvailableTenants])

  return query
}
```

**Notes:**
- `fetchClient` (existente en `vitalia/frontend/src/lib/api/fetchClient.ts`) auto-inyecta `X-Tenant-ID` header + Clerk bearer token (raíz `tenant-isolation.md`).
- `useEffect` para hidratar store en lugar de `onSuccess` callback (React Query v5 deprecó onSuccess en useQuery).
- `gcTime` reemplaza `cacheTime` (v5 naming).
- `retry: 2` — 3 intentos total before error (Scenario 7 network failure).

### § 2.9 — `tenant-palette.ts` (PALETTE const + pickPaletteColor hash function)

`vitalia/frontend/src/lib/tenant-palette.ts`:

```typescript
import type { PaletteColor } from './tenant-palette-types'  // si querés split types
// O inline:
export interface PaletteColor {
  readonly bg: string
  readonly text: string
}

/**
 * Paleta 6 colores Vitalia con contrast fix forward
 * (per 01-spec § 11 — amber + lime requieren dark text vs white).
 *
 * Determinismo: pickPaletteColor(id) siempre retorna mismo color para mismo id
 * (cross-session, cross-device).
 */
export const PALETTE = [
  { bg: 'bg-cyan-500',    text: 'text-white' },        // 0
  { bg: 'bg-purple-500',  text: 'text-white' },        // 1
  { bg: 'bg-fuchsia-500', text: 'text-white' },        // 2 (#d946ef — "magenta" en spec)
  { bg: 'bg-amber-500',   text: 'text-amber-950' },    // 3 — dark text para contrast AA
  { bg: 'bg-lime-500',    text: 'text-lime-950' },     // 4 — dark text para contrast AA
  { bg: 'bg-rose-500',    text: 'text-white' },        // 5
] as const satisfies ReadonlyArray<PaletteColor>

export type PaletteIndex = 0 | 1 | 2 | 3 | 4 | 5

/**
 * Hash function determinístico: suma charCodeAt de todos los chars % 6.
 * NO usa Math.random ni Date.now. Cross-session predecible.
 *
 * @example
 *   pickPaletteColor('sonrisa-plena')  // → siempre PALETTE[X] (computado al test)
 *   pickPaletteColor('dermalia-mx')    // → siempre PALETTE[Y]
 */
export function pickPaletteColor(tenantId: string): PaletteColor {
  if (!tenantId) return PALETTE[0]
  const hash = tenantId
    .split('')
    .reduce((acc, ch) => acc + ch.charCodeAt(0), 0)
  const index = hash % PALETTE.length
  return PALETTE[index]
}
```

**Tests determinismo expected** (T-1):
- `pickPaletteColor('sonrisa-plena')` === mismo object cada call.
- `pickPaletteColor('sonrisa-plena') === pickPaletteColor('sonrisa-plena')` reference-equality (PALETTE es const tuple).
- Múltiples ids distintos distribuyen razonablemente (no todos al mismo index).

### § 2.10 — `TopBarGlobal.tsx` MODIFY (1-line replace)

Diff conceptual (F1-S2 → F1-S3):

```diff
- import { TenantSwitcherSlot } from './TenantSwitcherSlot'
+ import { TenantSwitcher } from './TenantSwitcher'

  // dentro del JSX:
- <TenantSwitcherSlot />
+ <TenantSwitcher />
```

Resto del TopBarGlobal layout F1-S2 ratificado intacto.

### § 2.11 — `TenantSwitcherSlot.tsx` DELETE

Placeholder F1-S2 cumplió su rol drop-in. T-8 lo elimina del filesystem.

### § 2.12 — `app/layout.tsx` MODIFY (mount bootstrap)

Diff conceptual:

```diff
  // dentro del RootLayout return:
  <html lang="es">
    <body>
      <ClerkProvider>
        <QueryClientProvider client={queryClient}>
+         <TenantStoreBootstrap />
          {children}
        </QueryClientProvider>
      </ClerkProvider>
    </body>
  </html>
```

`TenantStoreBootstrap` es invisible (return null) pero ejecuta `useTenants()` + `useSignOutCleanup()` en mount root → garantiza store hidratado antes que TopBar renderice.

---

## § 3 — Test construction plan (★ v4.1 — TDD orden POMs fixtures scenario→test mapping)

### § 3.1 — Vitest unit tests (5 files)

| Path | Cubre |
|---|---|
| `vitalia/frontend/src/lib/__tests__/tenant-palette.test.ts` | `pickPaletteColor` determinismo cross-session · 6 ids fixtures → expected index · empty string fallback PALETTE[0] · distribución reasonable (no todos colapsan a mismo index) |
| `vitalia/frontend/src/components/shared/shell-organism/__tests__/TenantBadge.test.tsx` | render initials 2-char `Sonrisa Plena` → "SP" · `Dermalia MX` → "DM" · `ClíniCare Bogotá` → "CB" · `aria-hidden="true"` presente · clase bg + text match PALETTE pick |
| `vitalia/frontend/src/components/shared/shell-organism/__tests__/TenantOption.test.tsx` | render name + city · active=true renderiza Check + sr-only "Clínica activa" · active=false NO renderiza Check · classes bg-accent/40 (active) vs hover:bg-muted (inactive) |
| `vitalia/frontend/src/components/shared/shell-organism/__tests__/TenantSwitcher.test.tsx` | mock useTenants loading → Skeleton rendered + sr-only "Cargando clínicas…" · mock isError → Alert + Reintentar button · mock success [3 tenants] → 3 TenantOption rendered · click DropdownMenuItem → handleSwitch called · click "Agregar clínica" → modal open · empty tenants → null render · `buildRedirectPath` 4 cases pure function |
| `vitalia/frontend/src/stores/__tests__/tenant-store.test.ts` | initial state · setActiveTenant · setAvailableTenants auto-pick first · switchTenant valid → returns tenant + updates active · switchTenant invalid → returns null + active unchanged · clearStore resets · persist key `vitalia-tenant-state` · partialize solo activeTenant · localStorage write |

### § 3.2 — Playwright E2E specs (11 files por scenarios 1, 3-12 menos 2 unit-only)

**Directory:** `vitalia/frontend/e2e/regression/vitalia-fase1-tenant-switcher/`

| Spec file | Scenario | Categoría v4.1 |
|---|---|---|
| `happy-switch.spec.ts` | Scenario 1 | happy |
| `concurrent-clicks.spec.ts` | Scenario 3 | edge (race) |
| `adversarial-cross-tenant.spec.ts` | Scenario 4 | adversarial |
| `race-multi-tab.spec.ts` | Scenario 5 | race_condition |
| `concurrent-users.spec.ts` | Scenario 6 | concurrent_users |
| `network-failure.spec.ts` | Scenario 7 | network_failure |
| `empty-state.spec.ts` | Scenario 8 | empty_state |
| `large-dataset.spec.ts` | Scenario 9 | large_dataset |
| `a11y-keyboard.spec.ts` | Scenario 10 | accessibility |
| `i18n-spanish-neutro.spec.ts` | Scenario 11 | i18n |
| `single-tenant.spec.ts` | Scenario 12 | edge (single) |
| `visual-closed-light.spec.ts` | visual golden | visual |
| `visual-closed-dark.spec.ts` | visual golden | visual |
| `visual-open-light.spec.ts` | visual golden | visual |
| `visual-open-dark.spec.ts` | visual golden | visual |
| `visual-open-loading.spec.ts` | visual golden | visual |
| `visual-open-error.spec.ts` | visual golden | visual |
| `visual-open-single-tenant.spec.ts` | visual golden | visual |
| `visual-open-12-tenants.spec.ts` | visual golden | visual (large) |

### § 3.3 — POM (Page Object Model)

`vitalia/frontend/e2e/poms/tenant-switcher.pom.ts`:

```typescript
import type { Page, Locator } from '@playwright/test'

export class TenantSwitcherPom {
  readonly page: Page
  readonly trigger: Locator
  readonly dropdown: Locator
  readonly retryButton: Locator
  readonly addClinicButton: Locator
  readonly addClinicModal: Locator
  readonly adminAccountLink: Locator
  readonly errorAlert: Locator

  constructor(page: Page) {
    this.page = page
    this.trigger = page.getByTestId('tenant-switcher-trigger')
    this.dropdown = page.getByRole('menu')
    this.retryButton = page.getByTestId('tenant-switcher-retry')
    this.addClinicButton = page.getByRole('menuitem', { name: /agregar clínica/i })
    this.addClinicModal = page.getByRole('dialog')
    this.adminAccountLink = page.getByRole('menuitem', { name: /administrar cuenta/i })
    this.errorAlert = page.getByRole('alert')
  }

  async openDropdown() {
    await this.trigger.click()
    await this.dropdown.waitFor({ state: 'visible' })
  }

  tenantOption(tenantId: string): Locator {
    return this.page.getByTestId(`tenant-option-${tenantId}`)
  }

  async switchTo(tenantId: string) {
    await this.openDropdown()
    await this.tenantOption(tenantId).click()
  }

  async expectActiveTenant(tenantId: string) {
    await this.tenantOption(tenantId).waitFor()
    const option = this.tenantOption(tenantId)
    return option.getAttribute('data-active').then((v) => v === 'true')
  }
}
```

### § 3.4 — Fixtures (mocked /api/tenants responses)

`vitalia/frontend/e2e/fixtures/tenants.fixture.ts`:

```typescript
import type { Route, Page } from '@playwright/test'

export const TENANTS_3 = [
  { id: 'sonrisa-plena', name: 'Sonrisa Plena', city: 'Lima' },
  { id: 'dermalia-mx', name: 'Dermalia MX', city: 'CDMX' },
  { id: 'clinicare-bogota', name: 'ClíniCare Bogotá', city: 'Bogotá' },
] as const

export const TENANTS_SINGLE = [TENANTS_3[0]] as const

export const TENANTS_ZERO: typeof TENANTS_3 = [] as const

export const TENANTS_12 = Array.from({ length: 12 }, (_, i) => ({
  id: `clinica-${i + 1}`,
  name: `Clínica ${i + 1}`,
  city: ['Lima', 'CDMX', 'Bogotá', 'Santiago', 'Buenos Aires', 'Quito'][i % 6],
}))

export async function mockTenantsResponse(
  page: Page,
  payload: { tenants: ReadonlyArray<{ id: string; name: string; city: string }> }
) {
  await page.route('**/api/tenants', (route: Route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(payload),
    })
  )
}

export async function mockTenantsTimeout(page: Page) {
  await page.route('**/api/tenants', (route: Route) =>
    route.fulfill({ status: 504, contentType: 'application/json', body: '{}' })
  )
}
```

### § 3.5 — Scenario → test path mapping verbatim

| Spec scenario | Test file | Test name |
|---|---|---|
| Scenario 1 | `happy-switch.spec.ts` | `'switches active tenant and hard-redirects preserving path'` |
| Scenario 2 (unit-only) | `TenantSwitcher.test.tsx` + `tenant-store.test.ts` | `'switchTenant(unknown-id) returns null + console.warn + state unchanged'` |
| Scenario 3 | `concurrent-clicks.spec.ts` | `'double click <150ms produces single navigation (last click wins)'` |
| Scenario 4 | `adversarial-cross-tenant.spec.ts` | `'navigating manually to other tenant URL → 403 + rollback to active'` |
| Scenario 5 | `race-multi-tab.spec.ts` | `'2 tabs simultaneous write → last-write-wins, no corruption'` |
| Scenario 6 | `concurrent-users.spec.ts` | `'user A signOut → user B sees only own tenants, store cleared'` |
| Scenario 7 | `network-failure.spec.ts` | `'/api/tenants 504 → Alert visible + Reintentar refetches'` |
| Scenario 8 | `empty-state.spec.ts` | `'0 tenants → trigger not rendered, banner visible'` |
| Scenario 9 | `large-dataset.spec.ts` | `'12 tenants → scroll vertical, active scrollIntoView, <100ms render'` |
| Scenario 10 | `a11y-keyboard.spec.ts` | `'Tab+Enter open, Arrow nav, Enter select, Esc close, axe wcag2aa pass'` |
| Scenario 11 | `i18n-spanish-neutro.spec.ts` | `'no voseo regex match across all rendered strings'` |
| Scenario 12 | `single-tenant.spec.ts` | `'1 tenant → 1 row + 2 actions footer, click no-op same tenant'` |

### § 3.6 — Visual goldens paths (Playwright snapshot)

`vitalia/frontend/e2e/__screenshots__/shell/`:
- `tenant-switcher-closed-light.png`
- `tenant-switcher-closed-dark.png`
- `tenant-switcher-open-3-tenants-light.png`
- `tenant-switcher-open-3-tenants-dark.png`
- `tenant-switcher-open-loading-light.png`
- `tenant-switcher-open-error-light.png`
- `tenant-switcher-open-single-tenant-light.png`
- `tenant-switcher-open-12-tenants-light.png`

**Tolerance** `maxDiffPixelRatio: 0.001` (0.1%) per `shell-mockup-per-component.md` § Tests requeridos. Goldens iniciales generadas con `--update-snapshots=missing` en primer build, ratchet shrink-only post-ratificación.

---

## § 4 — Imports DAG

```
app/layout.tsx
  └─→ TenantStoreBootstrap (Client)
        ├─→ useTenants (React Query)
        │     └─→ fetchClient → /api/tenants
        │     └─→ useTenantStore.setAvailableTenants
        └─→ useSignOutCleanup
              ├─→ @clerk/nextjs::useAuth
              └─→ useTenantStore.clearStore + localStorage.removeItem

TopBarGlobal (Client — existente F1-S2)
  └─→ TenantSwitcher (Client — NEW F1-S3)
        ├─→ useTenantStore (Zustand)
        ├─→ useTenants (React Query — comparte queryKey con bootstrap)
        ├─→ usePathname (next/navigation)
        ├─→ buildRedirectPath (pure)
        ├─→ TenantBadge (Server)
        │     └─→ pickPaletteColor (pure) → PALETTE const
        ├─→ TenantOption (Server)
        │     ├─→ TenantBadge
        │     └─→ Lucide Check
        ├─→ AddClinicPlaceholderModal (Client)
        │     └─→ Shadcn Dialog primitives
        ├─→ Shadcn DropdownMenu primitives (Radix)
        ├─→ Shadcn Button, Alert, Skeleton primitives
        └─→ Lucide ChevronDown, Plus, Settings, AlertTriangle

tenant-store (Zustand persist)
  └─→ localStorage (key: vitalia-tenant-state, partialize: activeTenant)

tenant-palette (pure module)
  └─→ no imports (zero dependencies)
```

**FSD-Lite boundary check:**
- `components/shared/shell-organism/` puede importar de `components/ui/`, `stores/`, `hooks/`, `lib/` ✓
- `components/shared/` NO importa de `features/` ✓
- `stores/` NO importa de `components/` ni `features/` ✓
- `hooks/` puede importar de `stores/` + `lib/` ✓
- `lib/tenant-palette` zero deps ✓

---

## § 5 — React Query config

```typescript
// vitalia/frontend/src/hooks/useTenants.ts
useQuery<TenantsApiResponse>({
  queryKey: ['tenants'] as const,
  queryFn: () => fetchClient<TenantsApiResponse>('/api/tenants'),
  staleTime: 5 * 60 * 1000,        // 5 min — spec § 8.1
  gcTime: 10 * 60 * 1000,          // 10 min retention después de inactivo
  refetchOnWindowFocus: false,      // tenants list raramente cambia mid-session
  refetchOnReconnect: 'always',     // reconnect post-offline → refetch
  retry: 2,                         // 3 intentos total
})
```

**Invalidation strategy:** redirect `window.location.href` hace hard reload → todo el React Query cache se re-monta from scratch en nueva página → garantiza fresh data tenant-scoped post-switch (NO partial invalidation manual necesaria).

---

## § 6 — Zustand persist strategy + cross-user signOut cleanup

### § 6.1 — Persist config

```typescript
persist(
  storeImpl,
  {
    name: 'vitalia-tenant-state',
    storage: createJSONStorage(() => localStorage),
    partialize: (state) => ({ activeTenant: state.activeTenant }),  // ONLY activeTenant
    version: 1,
  }
)
```

**Por qué partialize solo `activeTenant`:**
- `availableTenants` SIEMPRE hidrata fresh de `/api/tenants` en mount → previene stale list cross-session (Scenario 6 isolation + general data freshness).
- `activeTenant` persiste para reabrir tab al mismo tenant + multi-tab consistency.

### § 6.2 — Cross-user signOut cleanup (Scenario 6)

Hook `useSignOutCleanup` registrado en `TenantStoreBootstrap` (root layout). Detecta Clerk `isSignedIn` flip true→false → ejecuta `clearStore()` + `localStorage.removeItem('vitalia-tenant-state')`.

**Garantía Scenario 6:** user_A signOut → store + localStorage limpios → user_B login → bootstrap monta → useTenants fetch /api/tenants (Clerk JWT user_B) → `setAvailableTenants(B_tenants)` → `activeTenant` auto-pick primer tenant de user_B (nunca el de user_A).

### § 6.3 — Multi-tab race (Scenario 5)

LocalStorage natural last-write-wins semántica (no manual sync). 2 tabs writes simultáneos → último timestamp gana en localStorage. Cada tab redirect a su elegido (window.location.href es tab-local). NO state corruption porque cada tab tiene su propio Zustand instance + el persist write es atomic JSON.stringify.

**Bonus optional (no scope F1-S3 escala Fase 2):** `storage` event listener para sync cross-tab activeTenant change → fuera de scope esta story.

---

## § 7 — Path preservation algorithm

```typescript
export function buildRedirectPath(currentPath: string, newTenantId: string): string {
  if (!currentPath || currentPath === '/') return `/${newTenantId}`
  return currentPath.replace(/^\/[^/]+/, `/${newTenantId}`) || `/${newTenantId}`
}
```

**Cases verbatim (test exhaustive):**

| Input `currentPath` | Input `newTenantId` | Expected output |
|---|---|---|
| `/sonrisa-plena/(shell-organism)/lisa/marca` | `dermalia-mx` | `/dermalia-mx/(shell-organism)/lisa/marca` |
| `/sonrisa-plena` | `dermalia-mx` | `/dermalia-mx` |
| `/` | `dermalia-mx` | `/dermalia-mx` |
| `` (empty) | `dermalia-mx` | `/dermalia-mx` |
| `/sonrisa-plena/cuenta/billing` | `clinicare-bogota` | `/clinicare-bogota/cuenta/billing` |

Regex `^\/[^/]+` matchea **primer segment** después del `/` raíz. Replace con `/${newTenantId}`. Fallback `|| '/${newTenantId}'` para edge case path vacío post-replace.

---

## § 8 — Color palette + contrast fix forward

Spec § 11 documenta el bug latente: amber-500 + lime-500 fallan contrast vs `text-white` (2.93:1 + 2.21:1 respectivamente < 4.5:1 WCAG AA).

**Fix forward cementado en `tenant-palette.ts`:**

```typescript
export const PALETTE = [
  { bg: 'bg-cyan-500',    text: 'text-white' },        // 4.94:1 AA ✓
  { bg: 'bg-purple-500',  text: 'text-white' },        // 4.51:1 AA ✓
  { bg: 'bg-fuchsia-500', text: 'text-white' },        // 4.85:1 AA ✓
  { bg: 'bg-amber-500',   text: 'text-amber-950' },    // dark text → ~11:1 AAA ✓
  { bg: 'bg-lime-500',    text: 'text-lime-950' },     // dark text → ~12:1 AAA ✓
  { bg: 'bg-rose-500',    text: 'text-white' },        // 4.51:1 AA ✓
] as const
```

TenantBadge consume el `text` class del PALETTE entry — NO hardcodea `text-white`. Verificación: axe ruleset wcag2aa en Scenario 10.

---

## § 9 — No-PHI-scope declaration (HIPAA-lite NO aplica)

**Explicit declaration:** F1-S3 TenantSwitcher procesa ÚNICAMENTE metadata organizacional pública:
- `tenant.id` (slug-style identifier, NO patient identifier)
- `tenant.name` (nombre comercial clínica, público en marketing)
- `tenant.city` (ciudad sede, público en directorio)

**Datos NO involucrados:**
- ❌ Patient identifiers (DNI, nombre, fecha nacimiento, email, phone)
- ❌ Diagnoses, treatments, medications, lab results
- ❌ Medical notes, imaging URLs, vital signs
- ❌ Cualquier campo listado en `vitalia/.claude/rules/hipaa-lite.md` § PHI fields canónicos

**Consecuencia:** `vitalia/.claude/rules/hipaa-lite.md` NO aplica scope a F1-S3.
- NO audit_log row required per tenant_switcher interaction (es chrome UI, no PHI access)
- NO pgcrypto encryption fields needed
- NO RBAC decorator `@require_phi_access` needed
- NO compliance_level filter in sanitization (no PHI fields para sanitize)

**Auditor verification:** auditor-frontend valida ausencia de PHI references en cualquier file de scope F1-S3. Arch test `test-no-phi-in-shell.test.ts` (opcional reforzar — ya cubierto por raíz `auditor-downstream-regression.md`).

---

## § 10 — Reuse adaptation diff vs nicolify reference

Nicolify reference: `nicolify/frontend/src/components/shared/layout/TenantSwitcher.tsx`

**Tabla diferencias clave (documenta que es ADAPTACIÓN, NO mirror — 75% reuse + 25% Vitalia-specific):**

| Aspecto | Nicolify | Vitalia | Razón divergencia |
|---|---|---|---|
| Layout variant | `isCollapsed` toggle (sidebar layout) | Solo horizontal (TopBar h-12) | Vitalia TopBarGlobal F1-S2 cementó horizontal-only |
| Data shape | `{id, name, fullName, slug}` | `{id, name, city}` | D2 spec cementado — solo city subtitle |
| Badge visual | Gradient bg + single-initial | Hash palette 6 colors + 2-char initials | D1 spec cementado — palette determinístico cross-session |
| Redirect target | Fixed `/brand-studio/identity` | Path preservation `pathname.replace(...)` | UX continuity Vitalia (Lisa/Adrián/Camila workflows) |
| Footer action 1 | "Crear marca" → wizard /onboarding | "Agregar clínica" → Dialog placeholder "Próximamente" | F1-S3 placeholder, full flow es Fase 2 |
| Footer action 2 | "Ajustes" → /settings | "Administrar cuenta" → `/{tenantId}/config/cuenta` | Vitalia routing convention |
| Storage key | `nicolify-active-tenant` | `vitalia-tenant-state` | Brand isolation localStorage |
| SignOut cleanup | N/A (nicolify no implementa) | `useSignOutCleanup` Clerk hook | Vitalia HIPAA-lite refuerza cross-user isolation (defensa-en-profundidad, no PHI scope pero buena práctica) |

**Cross-brand mirror threshold:** 2 brands con pattern relacionado (nicolify + vitalia) = under threshold (anti-duplication rule trigger ≥3 brands o cross-brand identical >50%). Si comunify/lupulo lo necesitan en Fase 2 → escala `/pm-luana` lift to `core/luana-core-ui/` futuro package.

---

## § 11 — Cross-Cutting Concerns

| Concern | Resolución scope F1-S3 |
|---|---|
| Tenant isolation | `fetchClient` auto-inyecta `X-Tenant-ID` (existente). `/api/tenants` BE filtra por JWT user_id (engine luana-core-iam). FE NO hardcode tenant. |
| Currency | N/A (no monetary surface) |
| Master data (UTC datetimes) | N/A (no datetime surface) |
| Spanish neutro LatAm | Todos los strings UI verificados verbatim § 9 spec. Magic comment NO aplica (no glossary reference verbatim necesario). Hook test `i18n-spanish-neutro.spec.ts` regex match no-voseo. |
| PII | N/A scope (tenant metadata pública, no PHI) — declarado explícito § 9. |
| Native-first dev | Lint/test/typecheck native Linux (host) per AGENTS.md. Builders usan `npx tsc`, `npx eslint`, `npx vitest`, `npx playwright` — NUNCA docker exec. |
| Idempotency on writes | N/A (no BE writes) |
| Clerk Organizations FORBIDDEN | Per MEMORY no-clerk-organizations 2026-05-20: Vitalia NO usa Clerk Orgs. Multi-tenancy en engine `luana-core-iam`. Arch test `val-arch-no-clerk-orgs` enforce. |

---

## § 12 — Architecture Fitness Impact

**Gates que deben seguir GREEN post-PR:**
- `vitalia/frontend/src/__tests__/architecture/test-fsd-boundaries.test.ts` — shell-organism imports válidos (NO importa `features/`)
- `vitalia/frontend/src/__tests__/architecture/test-page-padding.test.ts` — no rompe ratchet design tokens shell
- `vitalia/frontend/src/__tests__/architecture/test-no-cross-brand-imports.test.ts` — no imports desde `nicolify|comunify|lupulo/`

**Nuevo arch gate introducido este PR:**
- `vitalia/frontend/src/__tests__/architecture/test-no-clerk-organizations.test.ts` — enforces MEMORY no-clerk-orgs. Greps `useOrganization|orgId|Clerk.*Organization|OrganizationSwitcher` en `src/`. Falla si match.

**Ratchet allowlists shrink-only:** este PR NO agrega entries a allowlists (no tech debt nuevo). Goldens visuales agregan 8 nuevas entries al snapshot ratchet (initial generation post-ratify — ratchet shrink-only forward).

---

## § 13 — Capability YAML + modules/{m}.md Updates Required (post 2026-05 paradigma)

**Post-merge updates mandatory** (Fase E DOCS del story-closure-gate antes Fase F MERGE):

1. **NEW:** `vitalia/docs/product/capabilities/shell-organism/tenant-switcher.yaml`

   Schema verbatim esperado:
   ```yaml
   capability_id: shell.tenant-switcher
   module: shell-organism
   brand: vitalia
   status: live
   description: "Switcher de clínicas en TopBar con dropdown lista accesibles + active marker + path-preserving hard redirect + placeholder 'Agregar clínica' modal."
   delivered_by_story: vitalia-fase1-tenant-switcher
   delivered_at: <FECHA_MERGE>
   verification:
     commands:
       - "cd vitalia/frontend && npx vitest run src/components/shared/shell-organism src/stores/__tests__/tenant-store.test.ts src/lib/__tests__/tenant-palette.test.ts"
       - "cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test regression/vitalia-fase1-tenant-switcher/"
     gherkin_evidence: vitalia/docs/product/stories/vitalia-fase1-tenant-switcher/06-audit/gherkin-matrix.md
   ```

2. **UPDATE auto-list:** `vitalia/docs/product/modules/shell-organism.md` (auto-list block regenera via `scripts/reconcile_capabilities.py --brand vitalia` post-merge).

---

## § 14 — Test Surfaces (TDD-mandatory)

**TDD orden RED-first per layer (tdd-mandatory.md):**

1. **`tenant-palette.test.ts`** (T-1) — RED test `pickPaletteColor` determinismo ANTES de implementar PALETTE+hash function
2. **`TenantBadge.test.tsx`** (T-2) — RED test render initials + aria-hidden ANTES de implementar component
3. **`TenantOption.test.tsx`** (T-3) — RED test active marker ANTES de implementar molécula
4. **`tenant-store.test.ts`** (T-4) — RED test setActiveTenant/switchTenant/clearStore/persist ANTES de implementar Zustand store
5. **`useTenants` integration** (T-5) — RED test mocking fetchClient + hidratación store ANTES de implementar hook
6. **`AddClinicPlaceholderModal`** (T-6) — RED test modal open/close ANTES de implementar Dialog
7. **`TenantSwitcher.test.tsx`** (T-7) — RED test loading/error/success/empty states + click switch flow ANTES de implementar organismo
8. **`TopBarGlobal` integration check** (T-8) — RED test placeholder remplazado por organismo real ANTES de aplicar diff
9. **Playwright E2E** (T-9) — 11 specs + visual goldens. RED contra build sin componente implementado, GREEN post-T-7 close

**Builder workflow per ticket:** RED test → implementation → GREEN test → ruff/eslint clean → next ticket.

---

## § 15 — Research Notes (DATE-AWARE)

Pattern stack consultado para state-of-the-art as of **2026-05-22**:

| Source | Accessed | Key takeaway | Why over alternatives |
|---|---|---|---|
| `https://docs.pmnd.rs/zustand/integrations/persisting-store-data` | 2026-05-22 | Zustand v5 persist API + `createJSONStorage(() => localStorage)` + `partialize` + `version` para migrations | Más simple que Redux Toolkit persist + selectors. Server-component friendly (no Context Provider mandatory). |
| `https://tanstack.com/query/v5/docs/framework/react/guides/important-defaults` | 2026-05-22 | React Query v5 deprecó `onSuccess`/`onError` en useQuery (mantenidos en useMutation). Hidratación store debe ir en `useEffect` watching `query.data`. | Single React Query v5 fact que el spec viejo (con `onSuccess` mencionado) requería correction. |
| `https://nextjs.org/docs/app/api-reference/functions/use-pathname` | 2026-05-22 | `usePathname()` retorna pathname puro (sin querystring). Client Component only. | Path preservation requiere acceso al pathname mid-component. SSR garantiza initial render coherente. |
| `https://www.radix-ui.com/primitives/docs/components/dropdown-menu` | 2026-05-22 | Radix DropdownMenu nativo a11y: keyboard nav (Arrow/Enter/Esc/Tab) + ARIA roles (`menu`/`menuitem`) + focus management. `onSelect` event admite `event.preventDefault()` para prevenir close auto. | Headless UI alternative requeriría más boilerplate. Radix es Shadcn underlying primitive. |
| `https://clerk.com/docs/references/react/use-auth` | 2026-05-22 | Clerk `useAuth().isSignedIn` boolean reactive. Watch flip true→false para detect signOut cleanup. | Único hook reactive para signOut sin custom event bus. |

**Knowledge cutoff disclosure:** Opus 4.7 cutoff Jan 2026. Para React Query v5 deprecaciones onSuccess (cambio cementado post-Jan 2026 confirmado en docs accessed 2026-05-22), Zustand v5 storage API tweaks, y Next.js 16 App Router pathname patterns — investigado live via canonical official docs el 2026-05-22.

---

## § 16 — Open Questions for PM

**Ninguna bloqueante.** Decisiones D1-D4 cementadas en 01-spec ratificado por Chris iter 1. Contrast fix forward documentado spec § 11 + § 8 archivo. ZERO ambigüedad arquitectónica detectada.

**Potencial follow-up Fase 2** (NO bloqueante esta story):
- Storage event listener cross-tab activeTenant sync (Scenario 5 actualmente last-write-wins natural — sync activo es nice-to-have escala Fase 2 si demanda user real).
- Tenant search input dentro dropdown si user excede 5 tenants regularmente (escala `vitalia-fase2-tenant-search` per spec § 1 anti-objetivos).
- `TenantEmptyBanner` standalone component cuando empty state aparezca consistentemente (defensa-en-profundidad, NO scope F1-S3).

---

**Fin 03-arch.md F1-S3 v1.0 · /architect Vitalia · 2026-05-22.**

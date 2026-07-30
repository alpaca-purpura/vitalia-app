// cap: shell-organism.shell-vitalia
// story-origin: vitalia-fase1-s3-TBD
/**
 * types.ts — TypeScript types for tenant-switcher shell-organism components.
 * Kept after T-V2: TenantBadge, TenantOption, TenantSwitcher, TenantStoreBootstrap,
 * AddClinicPlaceholderModal, and hooks (useTenants, tenant-store) all use these types.
 *
 * Mirrors 03-arch.md § 2.2 TypeScript interfaces (camelCase, ISO 8601 datetimes as string).
 * All fields readonly per immutable domain pattern.
 *
 * Named exports (no default export) per FSD-Lite enforce.
 * HIPAA-lite: no-phi-scope — tenant/clinic names are business entities, NOT PHI.
 *
 * downstream-regression-na: brand-local shell-organism types; no cross-brand consumers
 */

/** A clinic/tenant entity accessible to the authenticated user */
export interface Tenant {
  readonly id: string;
  readonly name: string;
  /** Subtítulo opcional en el dropdown — el endpoint real /me/tenants NO lo devuelve. */
  readonly city?: string;
  /** Slug del tenant (BE TenantSchema). */
  readonly slug?: string;
  /** Rol del usuario en ese tenant (BE TenantSchema). */
  readonly role?: string;
}

/**
 * API response del BE `GET /api/v1/iam/users/me/tenants` → `list[TenantSchema]`
 * (array plano, NO `{ tenants: [...] }`). El path viejo `/api/tenants` 404eaba en
 * el stack real (bug#2 live): el selector quedaba sin datos → oculto.
 */
export type TenantsApiResponse = ReadonlyArray<Tenant>;

/** Zustand store state */
export interface TenantStoreState {
  readonly activeTenant: Tenant | null;
  readonly availableTenants: ReadonlyArray<Tenant>;
}

/** Zustand store actions */
export interface TenantStoreActions {
  setActiveTenant: (tenant: Tenant) => void;
  setAvailableTenants: (tenants: ReadonlyArray<Tenant>) => void;
  /** Returns the new active tenant or null if id not found */
  switchTenant: (id: string) => Tenant | null;
  clearStore: () => void;
}

/** Full store shape */
export type TenantStore = TenantStoreState & TenantStoreActions;

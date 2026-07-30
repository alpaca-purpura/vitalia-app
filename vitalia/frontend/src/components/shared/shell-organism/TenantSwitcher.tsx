// cap: shell-organism.shell-vitalia
// story-origin: vitalia-fase1-s3-TBD
"use client";

/**
 * TenantSwitcher — tenant/clinic switcher dropdown organism.
 * F1-S3 vitalia-fase1-tenant-switcher — T-7
 *
 * Client Component ("use client") — uses Radix DropdownMenu for native a11y.
 *
 * States:
 * - Loading: 3 Skeleton rows + sr-only "Cargando clínicas…"
 * - Error: Alert destructive + Reintentar button (calls refetch)
 * - Empty (0 tenants): returns null — no trigger rendered (graceful degrade)
 * - Success: list of TenantOption rows + footer actions
 *
 * Path preservation redirect (03-arch § 7, § 8.5):
 * - On tenant switch: replaces /{oldTenantId} prefix with /{newTenantId}
 * - Uses window.location.href for hard reload (clears React Query cache + Zustand state)
 * - No-op if user clicks the already-active tenant
 *
 * Accessible:
 * - aria-label="Cambiar clínica" on trigger
 * - title={activeTenant.name} on trigger (tooltip)
 * - Radix DropdownMenu handles Arrow/Enter/Esc keyboard nav natively
 *
 * Microcopy verbatim (01-spec.md § 9, Spanish neutro — no voseo):
 * - Header: "MIS CLÍNICAS"
 * - Footer: "Agregar clínica", "Administrar cuenta"
 * - Loading: "Cargando clínicas…"
 * - Error title: "No pudimos cargar tus clínicas"
 * - Error desc: "Intenta de nuevo o revisa tu conexión."
 * - Error CTA: "Reintentar"
 * - Empty: sr-only "Aún no tienes clínicas asignadas. Contacta a soporte."
 *
 * No Clerk Organizations used — per MEMORY.md::no-clerk-organizations 2026-05-20.
 *
 * 03-arch.md § 2.5 + § 7 — implementation verbatim.
 * Named export (no default export) per FSD-Lite enforce.
 * HIPAA-lite: no-phi-scope — tenant name/city are business entities, not PHI.
 *
 * downstream-regression-na: brand-local shell-organism component; no cross-brand consumers
 */

import { usePathname } from "next/navigation";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle, ChevronDown } from "lucide-react";
import { useTenants } from "@/hooks/useTenants";
import { useTenantStore } from "@/stores/tenant-store";
import { TenantBadge } from "./TenantBadge";
import { TenantOption } from "./TenantOption";
import { AddClinicPlaceholderModal } from "./AddClinicPlaceholderModal";

/**
 * Builds the redirect path for a tenant switch.
 * Replaces the first path segment (/{tenantId}) with the new tenant's id.
 *
 * Examples:
 * - '/sonrisa-plena/(shell-organism)/lisa/marca' + 'dermalia-mx'
 *   → '/dermalia-mx/(shell-organism)/lisa/marca'
 * - '/' + 'dermalia-mx' → '/dermalia-mx'
 *
 * @param currentPath - Current pathname from usePathname()
 * @param newTenantId - The target tenant id to navigate to
 */
export function buildRedirectPath(
  currentPath: string,
  newTenantId: string,
): string {
  if (!currentPath || currentPath === "/") return `/${newTenantId}`;
  return (
    currentPath.replace(/^\/[^/]+/, `/${newTenantId}`) || `/${newTenantId}`
  );
}

/**
 * TenantSwitcher — main tenant switcher dropdown.
 * Renders null when no tenants are available (empty state graceful degrade).
 * Client Component.
 */
export function TenantSwitcher() {
  const pathname = usePathname();
  const { isLoading, isError, refetch } = useTenants();

  const activeTenant = useTenantStore((s) => s.activeTenant);
  const availableTenants = useTenantStore((s) => s.availableTenants);
  const switchTenant = useTenantStore((s) => s.switchTenant);

  // ── Empty state: no tenants at all — no trigger (graceful degrade) ─────
  if (!isLoading && !isError && availableTenants.length === 0) {
    return null;
  }

  // ── Determine what to show in trigger ─────────────────────────────────
  // Bug #2 fix (vitalia-bugfix-shell-nav-scroll-errors T-4): el trigger debe
  // verse SIEMPRE que haya ≥1 tenant disponible (RN-2), aunque activeTenant aún
  // no esté resuelto (ventana pre-rehydration / pre-auto-pick). Antes esta guarda
  // retornaba null en esa ventana → con 1 tenant el selector quedaba invisible.
  // Solo ocultamos cuando NO hay activeTenant, NO estamos cargando, Y tampoco hay
  // tenants disponibles (defensa redundante con la guarda :99 — mantiene la
  // semántica de "≥1 tenant ⇒ trigger visible"). El trigger ya muestra un Skeleton
  // interno mientras activeTenant es null.
  if (!activeTenant && !isLoading && availableTenants.length === 0) {
    return null;
  }

  // ── Handle tenant switch ───────────────────────────────────────────────
  function handleTenantSelect(tenantId: string) {
    if (activeTenant?.id === tenantId) {
      // Already active — no-op (Scenario 12)
      return;
    }
    const result = switchTenant(tenantId);
    if (result) {
      const redirectPath = buildRedirectPath(pathname, result.id);
      window.location.href = redirectPath;
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          data-testid="tenant-switcher-trigger"
          aria-label="Cambiar clínica"
          title={activeTenant?.name ?? ""}
          className="flex h-8 items-center gap-1.5 px-2 text-sm font-medium"
        >
          {activeTenant ? (
            <>
              <TenantBadge tenant={activeTenant} />
              <span className="hidden max-w-[120px] truncate sm:inline-block">
                {activeTenant.name}
              </span>
            </>
          ) : (
            <Skeleton className="h-6 w-20" />
          )}
          <ChevronDown
            className="size-3.5 shrink-0 opacity-60"
            aria-hidden="true"
          />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align="start"
        className="w-64"
        data-testid="tenant-switcher-dropdown"
      >
        {/* ── Header ─────────────────────────────────────────────── */}
        <DropdownMenuLabel className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          MIS CLÍNICAS
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        {/* ── Loading state ──────────────────────────────────────── */}
        {isLoading && (
          <div className="space-y-1 px-2 py-1">
            <span className="sr-only">Cargando clínicas…</span>
            <Skeleton className="h-10 w-full rounded-sm" />
            <Skeleton className="h-10 w-full rounded-sm" />
            <Skeleton className="h-10 w-full rounded-sm" />
          </div>
        )}

        {/* ── Error state ────────────────────────────────────────── */}
        {isError && !isLoading && (
          <div className="p-2">
            <Alert variant="destructive" className="py-2">
              <AlertCircle className="size-4" />
              <AlertTitle className="text-sm">
                No pudimos cargar tus clínicas
              </AlertTitle>
              <AlertDescription className="text-xs">
                Intenta de nuevo o revisa tu conexión.
              </AlertDescription>
            </Alert>
            <Button
              variant="outline"
              size="sm"
              className="mt-2 w-full"
              onClick={() => void refetch()}
            >
              Reintentar
            </Button>
          </div>
        )}

        {/* ── Success state — tenant list ────────────────────────── */}
        {!isLoading && !isError && availableTenants.length > 0 && (
          <div className="max-h-64 overflow-y-auto">
            {availableTenants.map((tenant) => (
              <div
                key={tenant.id}
                role="menuitem"
                tabIndex={0}
                className="cursor-pointer outline-none"
                onClick={() => handleTenantSelect(tenant.id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    handleTenantSelect(tenant.id);
                  }
                }}
              >
                <TenantOption
                  tenant={tenant}
                  active={activeTenant?.id === tenant.id}
                />
              </div>
            ))}
          </div>
        )}

        {/* ── Footer actions ──────────────────────────────────────── */}
        {!isLoading && (
          <>
            <DropdownMenuSeparator />
            <div className="flex flex-col gap-0.5 p-1">
              {/* Agregar clínica — opens placeholder modal */}
              <AddClinicPlaceholderModal>
                <button
                  type="button"
                  className="flex w-full items-center rounded-sm px-2 py-1.5 text-sm text-foreground hover:bg-muted focus:outline-none"
                >
                  Agregar clínica
                </button>
              </AddClinicPlaceholderModal>

              {/* Administrar cuenta — navigates to config */}
              {activeTenant && (
                <a
                  href={`/${activeTenant.id}/config/cuenta`}
                  className="flex w-full items-center rounded-sm px-2 py-1.5 text-sm text-foreground hover:bg-muted"
                >
                  Administrar cuenta
                </a>
              )}
            </div>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

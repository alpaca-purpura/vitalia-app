// cap: configuracion.cuenta
// story-origin: vitalia-fase2-config-cuenta
"use client";
/**
 * PreferencesView.tsx — Client root for preferencias sub-sub-tab.
 *
 * Renders: currency selector + timezone selector (both from @luana/ui-kit) +
 * read-only language field + FloatingAutosaveIndicator.
 *
 * NO native <select> elements (arch test enforces CurrencySelector + TimezoneSelect).
 * NEVER hardcode 'USD' (master-data.md rule).
 *
 * T-1 vitalia-fase2-config-cuenta
 * spec_anchor: 03-arch.md § 5 + § Cross-Cutting Concerns (currency/timezone)
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

import { useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { CurrencySelector, TimezoneSelect, FloatingAutosaveIndicator, PageContentStack } from "@luana/ui-kit";
import { cuentaKeys } from "../../api/get-account";
import { patchAccount } from "../../api/patch-account";
import { useAccountForm } from "../../hooks/use-account-form";
import { useAccountQuery } from "../../hooks/use-account-query";
import { useTenants } from "@/hooks/useTenants";
import { SectionCard } from "./SectionCard";
import type { ClinicAccountDTO, ClinicAccountPatchDTO } from "../../types/cuenta.types";

export interface PreferencesViewProps {
  tenantId: string;
  initialData: ClinicAccountDTO | null | undefined;
  className?: string;
}

/**
 * PreferencesView — currency + timezone + language preferences.
 */
export function PreferencesView({
  tenantId,
  initialData,
  className,
}: PreferencesViewProps) {
  const { getToken, userId } = useAuth();
  // Rol PER-TENANT desde /me/tenants (user_tenants.role — fuente correcta).
  // NO useCurrentUser(): el /me del engine devuelve users.role LEGACY global
  // (drift detectado 2026-06-11: dr.demo global=doctor vs per-tenant=owner).
  const { data: tenantMemberships } = useTenants();
  const userRole = tenantMemberships?.find((t) => t.id === tenantId)?.role ?? null;
  const queryClient = useQueryClient();

  // Client GET account — fuente canónica (pages SSR pasan initialData=null).
  const accountQuery = useAccountQuery(tenantId);
  const account = accountQuery.data ?? initialData;

  const patchMutation = useMutation({
    mutationFn: async (payload: ClinicAccountPatchDTO) => {
      const token = await getToken();
      if (!token || !userId) throw new Error("No autenticado");
      return patchAccount({ token, tenantId, userId, userRole, payload });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: cuentaKeys.account(tenantId) });
    },
  });

  const { scheduleAutosave, autosaveStatus } = useAccountForm({
    initialData: account,
    saveFn: async (payload) => patchMutation.mutateAsync(payload),
    tenantId,
  });

  const handleCurrencyChange = useCallback(
    (currency: string) => {
      scheduleAutosave({ currency });
    },
    [scheduleAutosave],
  );

  const handleTimezoneChange = useCallback(
    (timezone: string) => {
      scheduleAutosave({ timezone });
    },
    [scheduleAutosave],
  );

  return (
    <PageContentStack
      className={cn("p-6", className)}
      data-testid="preferences-view"
    >
      {/* Section header (mockup: section-title + subtitle) */}
      <div>
        <h1 className="text-base font-semibold text-foreground">Preferencias regionales</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Cómo se muestran fechas, horas y montos en toda la plataforma.
        </p>
      </div>

      {/* 🌎 Formato regional — zona + moneda + idioma RO (mockup card) */}
      <SectionCard title="🌎 Formato regional" titleId="card-regional-heading">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {/* Timezone selector */}
          <div className="space-y-1.5" data-testid="timezone-select">
            <Label htmlFor="timezone-select-trigger">Zona horaria</Label>
            <TimezoneSelect
              value={account?.timezone ?? "America/Argentina/Buenos_Aires"}
              onValueChange={handleTimezoneChange}
              placeholder="Selecciona zona horaria..."
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              Se usa para mostrar fechas y horarios en tu franja horaria.
            </p>
          </div>

          {/* Currency selector */}
          <div className="space-y-1.5" data-testid="currency-selector">
            <Label htmlFor="currency-selector-trigger">Moneda</Label>
            <CurrencySelector
              value={account?.currency ?? ""}
              onValueChange={handleCurrencyChange}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              Moneda en la que se mostrarán los precios y presupuestos.
            </p>
          </div>
        </div>

        {/* Language — read-only */}
        <div className="space-y-1.5">
          <Label className="text-xs text-muted-foreground">Idioma</Label>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">{account?.language ?? "es-419"}</span>
            <Badge variant="outline" className="text-xs text-muted-foreground">
              definido en el alta
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground">
            El idioma de la interfaz se define al crear la cuenta.
          </p>
        </div>
      </SectionCard>

      {/* Autosave indicator */}
      <FloatingAutosaveIndicator status={autosaveStatus} />
    </PageContentStack>
  );
}

PreferencesView.displayName = "PreferencesView";

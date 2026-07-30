// cap: configuracion.cuenta
// story-origin: vitalia-fase2-config-cuenta
"use client";
/**
 * AccountDataView.tsx — Client root for datos sub-sub-tab.
 *
 * ADR-vitalia-004 § 3 — client root pattern.
 * Composes: editable fields (name/legalName/fiscalId/address/phone/email) +
 * SpecialtiesField multi-select + read-only badges (country/language/clinicType) +
 * FloatingAutosaveIndicator.
 *
 * Autosave: onChange → useAccountForm.scheduleAutosave (600ms debounce + coalesce).
 * NO "Guardar" button (form-runtime-array.md non-negotiable).
 *
 * Error boundary: wrapped by Suspense in page.tsx.
 * Loading/error/empty states: handled inline.
 *
 * tenant_id: from props (page.tsx SSR param) — NEVER from useAuth().orgId.
 *
 * T-1 vitalia-fase2-config-cuenta
 * spec_anchor: 03-arch.md § 5 + 03-arch.md § 10
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

import { useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { PageContentStack } from "@luana/ui-kit";
import { FloatingAutosaveIndicator } from "@/components/shared/FloatingAutosaveIndicator";
import { cuentaKeys, getSpecialtyCatalog } from "../../api/get-account";
import { patchAccount } from "../../api/patch-account";
import { accountDataSchema, type AccountDataFormValues, fiscalIdValidatorForCountry } from "../../types/cuenta-schema";
import { useAccountForm } from "../../hooks/use-account-form";
import { useAccountQuery } from "../../hooks/use-account-query";
import { useTenants } from "@/hooks/useTenants";
import { SectionCard } from "./SectionCard";
import { SpecialtiesField } from "./SpecialtiesField";
import type { ClinicAccountDTO, ClinicAccountPatchDTO } from "../../types/cuenta.types";
import { z } from "zod";

export interface AccountDataViewProps {
  /** Tenant ID from SSR page.tsx param (NEVER from useAuth().orgId). */
  tenantId: string;
  /** Initial account data — SSR hydration from page.tsx or null. */
  initialData: ClinicAccountDTO | null | undefined;
  className?: string;
}

// ── Loading skeleton ──────────────────────────────────────────────────────────

function DataSkeleton() {
  return (
    <div
      aria-label="Cargando datos de la cuenta"
      aria-busy="true"
      className="flex flex-col gap-4"
    >
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex flex-col gap-1">
          <Skeleton className="h-3 w-[25%] rounded" />
          <Skeleton className="h-9 w-full rounded-md" />
        </div>
      ))}
    </div>
  );
}

// ── Error banner ──────────────────────────────────────────────────────────────

function ErrorBanner({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive"
    >
      <p className="font-medium">No se pudo guardar. Inténtalo de nuevo.</p>
      <p className="mt-1 text-xs text-muted-foreground">{message}</p>
    </div>
  );
}

// ── Read-only badge (country/language/clinicType) ─────────────────────────────

function ReadOnlyBadge({ label, value }: { label: string; value: string }) {
  return (
    <div className="space-y-1">
      <Label className="text-xs text-muted-foreground">{label}</Label>
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium">{value}</span>
        <Badge variant="outline" className="text-xs text-muted-foreground">
          definido en el alta
        </Badge>
      </div>
    </div>
  );
}

// ── AccountDataView ───────────────────────────────────────────────────────────

/**
 * AccountDataView — interactive client root for datos sub-sub-tab.
 */
export function AccountDataView({
  tenantId,
  initialData,
  className,
}: AccountDataViewProps) {
  const { getToken, isLoaded, isSignedIn, userId } = useAuth();
  // Rol PER-TENANT desde /me/tenants (user_tenants.role — fuente correcta).
  // NO useCurrentUser(): el /me del engine devuelve users.role LEGACY global
  // (drift detectado 2026-06-11: dr.demo global=doctor vs per-tenant=owner).
  const { data: tenantMemberships } = useTenants();
  const userRole = tenantMemberships?.find((t) => t.id === tenantId)?.role ?? null;
  const queryClient = useQueryClient();

  const enabled = isLoaded && !!isSignedIn && !!userId;

  // Client GET account — fuente canónica de datos (los pages SSR pasan
  // initialData=null; sin este fetch el form nacía vacío — fix live-verify).
  const accountQuery = useAccountQuery(tenantId);
  const account = accountQuery.data ?? initialData;

  // Build dynamic schema with fiscal-id validator based on country
  const country = account?.country ?? "AR";
  const dynamicSchema = accountDataSchema.extend({
    fiscalId: fiscalIdValidatorForCountry(country)
      .optional()
      .nullable()
      .or(z.literal("").transform(() => null)),
  });

  // RHF setup — `values` re-sincroniza cuando llega el fetch async;
  // keepDirtyValues evita pisar lo que el usuario está tipeando mid-edit.
  const {
    register,
    formState: { errors },
    watch,
    setValue,
  } = useForm<AccountDataFormValues>({
    resolver: zodResolver(dynamicSchema),
    values: {
      name: account?.name ?? "",
      legalName: account?.legalName ?? "",
      fiscalId: account?.fiscalId ?? "",
      address: account?.address ?? "",
      phone: account?.phone ?? "",
      email: account?.email ?? "",
      primarySpecialties: account?.primarySpecialties ?? [],
    },
    resetOptions: { keepDirtyValues: true },
  });

  // PATCH mutation
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

  // Autosave hook
  const { scheduleAutosave, autosaveStatus } = useAccountForm({
    initialData: account,
    saveFn: async (payload) => patchMutation.mutateAsync(payload),
    tenantId,
  });

  // Specialty catalog query
  const {
    data: catalogData,
    isLoading: catalogLoading,
  } = useQuery({
    queryKey: cuentaKeys.specialtyCatalog(tenantId),
    queryFn: async () => {
      const token = await getToken();
      if (!token || !userId) throw new Error("No autenticado");
      return getSpecialtyCatalog({ token, tenantId, userId });
    },
    enabled,
  });

  // Field change handler — schedules autosave
  const handleFieldChange = useCallback(
    (field: keyof ClinicAccountPatchDTO, value: string | string[] | null) => {
      scheduleAutosave({ [field]: value ?? undefined } as ClinicAccountPatchDTO);
    },
    [scheduleAutosave],
  );

  const specialties = watch("primarySpecialties") ?? [];

  if (!account && (accountQuery.isLoading || !isLoaded)) {
    return (
      <PageContentStack className={cn("p-6", className)}>
        <DataSkeleton />
      </PageContentStack>
    );
  }

  return (
    <PageContentStack
      className={cn("p-6", className)}
      data-testid="account-data-view"
    >
      {/* Section header (mockup: section-title + subtitle) */}
      <div>
        <h1 className="text-base font-semibold text-foreground">Datos de la clínica</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          La información legal y de contacto de tu clínica. Se guarda sola.
        </p>
      </div>

      {/* 🏥 Identidad — nombre + razón social + tipo (RO) + especialidades (editables D3-revoked) */}
      <SectionCard title="🏥 Identidad" titleId="card-identidad-heading">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {/* Name */}
          <div className="space-y-1.5">
            <Label htmlFor="account-name">Nombre comercial</Label>
            <Input
              id="account-name"
              {...register("name")}
              aria-invalid={!!errors.name}
              aria-describedby={errors.name ? "name-error" : undefined}
              onChange={(e) => {
                void register("name").onChange(e);
                handleFieldChange("name", e.target.value);
              }}
            />
            {errors.name && (
              <p id="name-error" className="text-xs text-destructive" role="alert">
                {errors.name.message}
              </p>
            )}
          </div>

          {/* Legal name */}
          <div className="space-y-1.5">
            <Label htmlFor="account-legal-name">Razón social (opcional)</Label>
            <Input
              id="account-legal-name"
              placeholder="Nombre legal o razón social"
              {...register("legalName")}
              onChange={(e) => {
                void register("legalName").onChange(e);
                handleFieldChange("legalName", e.target.value || null);
              }}
            />
          </div>
        </div>

        <ReadOnlyBadge label="Tipo de clínica" value={account?.clinicType ?? "—"} />

        {/* Specialties multi-select (editables — D3-revoked) */}
        <div className="space-y-1.5">
          <Label id="specialties-heading">Especialidades principales</Label>
          {catalogLoading ? (
            <Skeleton className="h-9 w-[280px] rounded-md" />
          ) : (
            <SpecialtiesField
              value={specialties}
              catalog={catalogData?.specialties ?? []}
              onChange={(next) => {
                setValue("primarySpecialties", next);
                scheduleAutosave({ primarySpecialties: next });
              }}
            />
          )}
          <p className="text-xs text-muted-foreground">
            El tipo de clínica se definió al crear la cuenta (cambiarlo afecta agentes, catálogo y
            compliance — escribe a soporte). Las especialidades sí puedes ajustarlas aquí.
          </p>
        </div>
      </SectionCard>

      {/* 🧾 Identificación fiscal — país (RO) + ID fiscal */}
      <SectionCard title="🧾 Identificación fiscal" titleId="card-fiscal-heading">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <ReadOnlyBadge label="País" value={account?.country ?? "—"} />

          <div className="space-y-1.5">
            <Label htmlFor="account-fiscal-id">
              {account?.fiscalIdLabel ?? "ID fiscal"} (opcional)
            </Label>
            <Input
              id="account-fiscal-id"
              placeholder={`Ingresa tu ${account?.fiscalIdLabel ?? "ID fiscal"}`}
              {...register("fiscalId")}
              aria-invalid={!!errors.fiscalId}
              aria-describedby={errors.fiscalId ? "fiscal-id-error" : undefined}
              onChange={(e) => {
                void register("fiscalId").onChange(e);
                handleFieldChange("fiscalId", e.target.value || null);
              }}
            />
            {errors.fiscalId && (
              <p id="fiscal-id-error" className="text-xs text-destructive" role="alert">
                {errors.fiscalId.message}
              </p>
            )}
          </div>
        </div>
        <p className="text-xs text-muted-foreground">
          El identificador fiscal cambia de formato según el país (CUIT AR · RUC PE · RFC MX ·
          NIT CL/CO · RUT UY). Se valida al guardar.
        </p>
      </SectionCard>

      {/* 📍 Dirección y contacto */}
      <SectionCard title="📍 Dirección y contacto" titleId="card-contacto-heading">
        <div className="space-y-1.5">
          <Label htmlFor="account-address">Dirección (opcional)</Label>
          <Input
            id="account-address"
            placeholder="Dirección física de la clínica"
            {...register("address")}
            onChange={(e) => {
              void register("address").onChange(e);
              handleFieldChange("address", e.target.value || null);
            }}
          />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="account-phone">Teléfono (opcional)</Label>
            <Input
              id="account-phone"
              type="tel"
              placeholder="+54 11 1234-5678"
              {...register("phone")}
              onChange={(e) => {
                void register("phone").onChange(e);
                handleFieldChange("phone", e.target.value || null);
              }}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="account-email">Correo electrónico (opcional)</Label>
            <Input
              id="account-email"
              type="email"
              placeholder="contacto@clinica.com"
              {...register("email")}
              aria-invalid={!!errors.email}
              aria-describedby={errors.email ? "email-error" : undefined}
              onChange={(e) => {
                void register("email").onChange(e);
                handleFieldChange("email", e.target.value || null);
              }}
            />
            {errors.email && (
              <p id="email-error" className="text-xs text-destructive" role="alert">
                {errors.email.message}
              </p>
            )}
          </div>
        </div>
      </SectionCard>

      {/* Mutation error banner */}
      {patchMutation.isError && (
        <ErrorBanner
          message={(patchMutation.error as Error)?.message ?? "Error al guardar"}
        />
      )}

      {/* Autosave indicator — ONE per page (canon §2.6) */}
      <FloatingAutosaveIndicator status={autosaveStatus} />
    </PageContentStack>
  );
}

AccountDataView.displayName = "AccountDataView";

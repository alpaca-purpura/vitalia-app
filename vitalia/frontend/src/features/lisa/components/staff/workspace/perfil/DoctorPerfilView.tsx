// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
"use client";
/**
 * DoctorPerfilView.tsx — Doctor profile form with autosave.
 *
 * Business rules:
 *   - autosave-no-save-button HARD: every field autosaves on-change, 600ms debounce
 *   - NO "Guardar" button (forbidden)
 *   - Shows hint: "Los cambios se guardan automáticamente"
 *   - Avatar upload via proxy (useAvatarUpload)
 *
 * Layout sections:
 *   1. Avatar + identity (name/credential/specialty)
 *   2. Contact (email/phone)
 *   3. Professional (years experience, languages, visibility toggle)
 *   4. Cross-link card → Página pública (D3-D)
 *
 * Note: BioRepoInputs was moved to DoctorPaginaView (hoja Página) per spec § D3-D.
 *
 * Per ADR-vitalia-004 § 3-5: Client Component, React Query, RHF + Zod, autosave.
 *
 * T-FE-2 vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § Wireframes (Hoja Perfil) + 03-arch-fe.md § Forms
 * downstream-regression-na: brand-local vitalia feature component
 */

import { useEffect } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { staffKeys, useDoctor, usePatchDoctor } from "../../../../api/staff";
import { useAutosave } from "@/hooks/use-autosave";
import { AvatarUploader } from "../AvatarUploader";
import { Skeleton } from "@/components/ui/skeleton";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { FloatingAutosaveIndicator } from "@/components/shared/FloatingAutosaveIndicator";
import { cn } from "@/lib/utils";
import { doctorPerfilSchema, type DoctorPerfilFormValues } from "../../../../types/staff-schema";
import type { DoctorDetail } from "../../../../types/staff.types";

// ── Switch import (Shadcn) — check if it exists ───────────────────────────────
// Note: Shadcn Switch not installed. Using checkbox as fallback.


interface DoctorPerfilViewProps {
  doctorId: string;
}

/**
 * DoctorPerfilView — autosave profile form for a doctor.
 *
 * Autosave flow: field onChange → schedule(payload) → 600ms → usePatchDoctor mutate
 */
export function DoctorPerfilView({ doctorId }: DoctorPerfilViewProps) {
  const queryClient = useQueryClient();
  const pathname = usePathname();

  // ── Data ────────────────────────────────────────────────────────────────────
  const { data: doctor, isLoading, isError } = useDoctor(doctorId);
  const patchMutation = usePatchDoctor(doctorId);

  // ── Form ─────────────────────────────────────────────────────────────────────
  const form = useForm<DoctorPerfilFormValues>({
    resolver: zodResolver(doctorPerfilSchema),
    defaultValues: {
      specialty: "",
      phone: "",
      yearsExperience: "",
      languages: "",
      visibleEnLanding: false,
    },
  });

  // Hydrate form when doctor data loads
  useEffect(() => {
    if (doctor) {
      form.reset({
        specialty: doctor.specialty ?? "",
        phone: doctor.phone ?? "",
        yearsExperience: doctor.yearsExperience != null ? String(doctor.yearsExperience) : "",
        languages: doctor.languages.join(", "),
        visibleEnLanding: doctor.visibleEnLanding,
      });
    }
  }, [doctor, form]);

  // ── Autosave ──────────────────────────────────────────────────────────────────
  const { schedule: scheduleAutosave, status: autosaveStatus } = useAutosave({
    saveFn: async (payload: Partial<DoctorDetail>) => {
      await patchMutation.mutateAsync(payload);
    },
    debounceMs: 600,
  });

  const handleFieldChange = (field: keyof DoctorPerfilFormValues, value: unknown) => {
    // Map form field to API payload field
    const patchPayload: Record<string, unknown> = {};
    if (field === "specialty") patchPayload.specialty = value;
    if (field === "phone") patchPayload.phone = value;
    if (field === "yearsExperience") {
      const num = value ? parseInt(String(value), 10) : null;
      patchPayload.yearsExperience = isNaN(num as number) ? null : num;
    }
    if (field === "languages") {
      patchPayload.languages = String(value)
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
    }
    if (field === "visibleEnLanding") patchPayload.visibleEnLanding = value;

    scheduleAutosave(patchPayload as Partial<DoctorDetail>);
  };

  // ── Loading state ─────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="space-y-4" aria-busy="true" aria-label="Cargando perfil">
        <Skeleton className="h-20 w-20 rounded-full" />
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-4 w-64" />
      </div>
    );
  }

  if (isError || !doctor) {
    return (
      <div
        role="alert"
        className="rounded-lg border border-destructive/50 bg-destructive/5 p-4 text-sm text-destructive"
      >
        No se pudo cargar el perfil. Vuelve a intentarlo.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 p-6" data-testid="doctor-perfil-view">
      {/* Cards grid — 2-col responsive (homologado con marca/identidad);
          colapsa a 1 col en espacio reducido. Secciones densas span full-width. */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {/* Avatar + identity (read-only fields from create) */}
      <section
        aria-labelledby="identity-heading"
        className="rounded-xl border border-border bg-card p-4 sm:p-5"
      >
        <h2
          id="identity-heading"
          className="mb-3 flex items-center gap-2 text-sm font-semibold"
        >
          <span aria-hidden="true" className="h-4 w-1 rounded-full bg-agent-lisa" />
          Identidad
        </h2>
        <div className="flex items-start gap-4">
          <AvatarUploader
            doctorId={doctorId}
            currentAvatarUrl={doctor.avatarUrl ?? null}
            onSuccess={(_avatarUrl) => {
              void queryClient.invalidateQueries({
                queryKey: staffKeys.detail(doctorId),
              });
            }}
          />
          <div className="flex-1 space-y-1">
            <p className="font-medium">
              {doctor.firstName} {doctor.lastName}
            </p>
            <p className="text-sm text-muted-foreground">
              {doctor.credentialCountry} — {doctor.credential}
            </p>
            <p className="text-xs text-muted-foreground">
              DNI: {doctor.dni ? "***" + doctor.dni.slice(-3) : "***"}
            </p>
          </div>
        </div>
      </section>

      {/* Contact */}
      <section
        aria-labelledby="contact-heading"
        className="rounded-xl border border-border bg-card p-4 sm:p-5"
      >
        <h2
          id="contact-heading"
          className="mb-3 flex items-center gap-2 text-sm font-semibold"
        >
          <span aria-hidden="true" className="h-4 w-1 rounded-full bg-agent-lisa" />
          Contacto
        </h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div className="space-y-1">
            <Label htmlFor="email">Correo electrónico</Label>
            <Input
              id="email"
              type="email"
              value={doctor.email}
              disabled
              aria-label="Correo electrónico (no editable)"
              className="opacity-70"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="phone">Teléfono</Label>
            <Controller
              control={form.control}
              name="phone"
              render={({ field, fieldState }) => (
                <>
                  <Input
                    id="phone"
                    type="tel"
                    placeholder="+51 999 000 000"
                    aria-invalid={!!fieldState.error}
                    {...field}
                    onChange={(e) => {
                      field.onChange(e);
                      handleFieldChange("phone", e.target.value);
                    }}
                  />
                  {fieldState.error && (
                    <p className="text-xs text-destructive" role="alert">
                      {fieldState.error.message}
                    </p>
                  )}
                </>
              )}
            />
          </div>
        </div>
      </section>

      {/* Professional */}
      <section
        aria-labelledby="professional-heading"
        className="rounded-xl border border-border bg-card p-4 sm:p-5 sm:col-span-2"
      >
        <h2
          id="professional-heading"
          className="mb-3 flex items-center gap-2 text-sm font-semibold"
        >
          <span aria-hidden="true" className="h-4 w-1 rounded-full bg-agent-lisa" />
          Datos profesionales
        </h2>
        <div className="space-y-3">
          <div className="space-y-1">
            <Label htmlFor="specialty">Especialidad</Label>
            <Controller
              control={form.control}
              name="specialty"
              render={({ field, fieldState }) => (
                <>
                  <Input
                    id="specialty"
                    placeholder="Ej. Odontología cosmética"
                    aria-invalid={!!fieldState.error}
                    {...field}
                    onChange={(e) => {
                      field.onChange(e);
                      handleFieldChange("specialty", e.target.value);
                    }}
                  />
                  {fieldState.error && (
                    <p className="text-xs text-destructive" role="alert">
                      {fieldState.error.message}
                    </p>
                  )}
                </>
              )}
            />
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="space-y-1">
              <Label htmlFor="yearsExperience">Años de experiencia</Label>
              <Controller
                control={form.control}
                name="yearsExperience"
                render={({ field }) => (
                  <Input
                    id="yearsExperience"
                    type="number"
                    min={0}
                    max={60}
                    placeholder="0"
                    {...field}
                    onChange={(e) => {
                      field.onChange(e);
                      handleFieldChange("yearsExperience", e.target.value);
                    }}
                  />
                )}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="languages">Idiomas (separados por coma)</Label>
              <Controller
                control={form.control}
                name="languages"
                render={({ field }) => (
                  <Input
                    id="languages"
                    placeholder="Español, Inglés"
                    {...field}
                    onChange={(e) => {
                      field.onChange(e);
                      handleFieldChange("languages", e.target.value);
                    }}
                  />
                )}
              />
            </div>
          </div>

          {/* Visibility toggle */}
          <div className="flex items-center justify-between rounded-lg border border-border/60 p-3">
            <div>
              <p className="text-sm font-medium">Visible en landing</p>
              <p className="text-xs text-muted-foreground">
                Muestra este integrante en la página pública de la clínica
              </p>
            </div>
            <Controller
              control={form.control}
              name="visibleEnLanding"
              render={({ field }) => (
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    className="sr-only"
                    checked={field.value}
                    onChange={(e) => {
                      field.onChange(e);
                      handleFieldChange("visibleEnLanding", e.target.checked);
                    }}
                    aria-label="Visible en landing"
                  />
                  <div
                    className={cn(
                      "w-10 h-6 rounded-full transition-colors",
                      field.value ? "bg-agent-lisa" : "bg-muted",
                    )}
                  >
                    <div
                      className={cn(
                        "w-4 h-4 rounded-full bg-background shadow-sm mt-1 transition-transform",
                        field.value ? "translate-x-5" : "translate-x-1",
                      )}
                    />
                  </div>
                </label>
              )}
            />
          </div>
        </div>
      </section>

      </div>

      {/* Cross-link to Página tab (D3-D) — BioRepoInputs lives in DoctorPaginaView */}
      <div className="sm:col-span-2">
        <Link
          href={pathname ? pathname.replace("/perfil", "/pagina") : "#"}
          className="group flex items-center justify-between rounded-xl border border-border bg-card/60 p-4 hover:bg-card transition-colors"
          aria-label="Ir a la hoja Página pública del doctor"
        >
          <div className="flex items-center gap-3">
            <span className="text-base" aria-hidden="true">🌐</span>
            <div>
              <p className="text-sm font-medium">Página pública del doctor</p>
              <p className="text-xs text-muted-foreground">
                Configura y publica el perfil que verán los pacientes
              </p>
            </div>
          </div>
          <span
            className="text-muted-foreground group-hover:text-foreground transition-colors text-sm"
            aria-hidden="true"
          >
            →
          </span>
        </Link>
      </div>

      <FloatingAutosaveIndicator status={autosaveStatus} />
    </div>
  );
}

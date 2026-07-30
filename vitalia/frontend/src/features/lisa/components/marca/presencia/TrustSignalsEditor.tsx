// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
"use client";

/**
 * TrustSignalsEditor.tsx — OQ-D hybrid trust catalog for Presencia sub-sub-tab.
 *
 * Architecture:
 *   - Certifications section: active chips (existing trust signals) + expandable
 *     <details> catalog grid for PE seed entries + free-text "Otra"
 *   - useQuery for catalog: GET /lisa/marca/trust-catalog/PE
 *   - useMutation: POST /lisa/marca/trust-signals (add) + DELETE /lisa/marca/trust-signals/{id}
 *   - Años de experiencia (number input)
 *   - Pacientes atendidos (text input)
 *   - Premios y reconocimientos (textarea)
 *
 * All trust catalog mutations are independent of the contact autosave debounce.
 * The años/pacientes/premios fields use the trust signals PUT endpoint.
 *
 * Spanish neutro LatAm — no voseo.
 *
 * T-7 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-7 A1 + mockups/presencia-section.html § trust-signals
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { marcaKeys } from "../../../api/marca";
import {
  getTrustCatalog,
  getTrustSignals,
  createTrustSignal,
  deleteTrustSignal,
} from "../../../api/marca-presence-api";
import type { TrustSignalItem } from "../../../api/marca-presence-api";

// ── Types ──────────────────────────────────────────────────────────────────────

export interface TrustSignalsEditorProps {
  tenantId: string;
  clinicId?: string | null;
  /** Default country for catalog (PE for Peru seed). */
  countryCode?: string;
  /** Current años experiencia from server. */
  yearsExperience?: number | null;
  /** Current pacientes count from server. */
  patientsCount?: string | null;
  /** Current awards text from server. */
  awards?: string | null;
  /** Called when años/pacientes/premios change (debounce in parent). */
  onScheduleAutosave: (values: Record<string, unknown>) => void;
  className?: string;
}

// ── Certification chip ─────────────────────────────────────────────────────────

interface CertChipProps {
  signal: TrustSignalItem;
  onRemove: (id: string) => void;
  isRemoving: boolean;
}

function CertChip({ signal, onRemove, isRemoving }: CertChipProps) {
  return (
    <Badge
      variant="secondary"
      className={cn(
        "flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium",
        "border border-border/60 bg-muted/60",
        isRemoving && "opacity-50",
      )}
    >
      <span>{signal.label}</span>
      <button
        type="button"
        aria-label={`Quitar certificación ${signal.label}`}
        disabled={isRemoving}
        onClick={() => onRemove(signal.id)}
        className="ml-1 flex h-3.5 w-3.5 items-center justify-center rounded-full text-muted-foreground hover:text-destructive focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
      >
        <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-3 w-3">
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </Badge>
  );
}

// ── TrustSignalsEditor ─────────────────────────────────────────────────────────

/**
 * TrustSignalsEditor — OQ-D hybrid: catalog checkboxes + free-text + numeric fields.
 * Section A (certifications), Section B (experiencia + pacientes), Section C (premios).
 */
export function TrustSignalsEditor({
  tenantId,
  clinicId,
  countryCode = "PE",
  yearsExperience,
  patientsCount,
  awards,
  onScheduleAutosave,
  className,
}: TrustSignalsEditorProps) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const queryClient = useQueryClient();

  // Local state for free-text "Otra" input
  const [otraLabel, setOtraLabel] = useState("");
  const [removingId, setRemovingId] = useState<string | null>(null);

  // Local controlled state for años/pacientes/premios
  const [localYears, setLocalYears] = useState<string>(
    yearsExperience != null ? String(yearsExperience) : "",
  );
  const [localPatients, setLocalPatients] = useState<string>(patientsCount ?? "");
  const [localAwards, setLocalAwards] = useState<string>(awards ?? "");

  // ── Queries ────────────────────────────────────────────────────────────────

  /** GET active trust signals for this tenant */
  const {
    data: signalsData,
    isLoading: isSignalsLoading,
    isError: isSignalsError,
  } = useQuery({
    queryKey: marcaKeys.trustSignals(tenantId),
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return getTrustSignals({ token, tenantId, clinicId });
    },
    enabled: isLoaded && !!isSignedIn,
  });

  /** GET PE certification catalog (OQ-D seed) */
  const {
    data: catalogData,
    isLoading: isCatalogLoading,
  } = useQuery({
    queryKey: marcaKeys.trustCatalog(tenantId, countryCode),
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return getTrustCatalog({ token, tenantId, clinicId }, countryCode);
    },
    enabled: isLoaded && !!isSignedIn,
    staleTime: 10 * 60_000, // catalog rarely changes
  });

  const activeSignals = signalsData?.items ?? [];
  const activeCodes = new Set(
    activeSignals
      .map((s) => s.catalogCode)
      .filter((c): c is string => c !== null),
  );
  const catalogItems = catalogData?.items ?? [];

  // ── Mutations ──────────────────────────────────────────────────────────────

  const addMutation = useMutation({
    mutationFn: async (payload: { label: string; catalogCode?: string | null }) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return createTrustSignal({ token, tenantId, clinicId }, payload);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: marcaKeys.trustSignals(tenantId) });
    },
  });

  const removeMutation = useMutation({
    mutationFn: async (signalId: string) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return deleteTrustSignal({ token, tenantId, clinicId }, signalId);
    },
    onSuccess: () => {
      setRemovingId(null);
      void queryClient.invalidateQueries({ queryKey: marcaKeys.trustSignals(tenantId) });
    },
    onError: () => {
      setRemovingId(null);
    },
  });

  // ── Handlers ───────────────────────────────────────────────────────────────

  const handleToggleCatalogItem = (code: string, label: string) => {
    if (activeCodes.has(code)) {
      // Remove: find the signal item with this code
      const target = activeSignals.find((s) => s.catalogCode === code);
      if (target) {
        setRemovingId(target.id);
        removeMutation.mutate(target.id);
      }
    } else {
      // Add from catalog
      addMutation.mutate({ label, catalogCode: code });
    }
  };

  const handleAddOtra = () => {
    const trimmed = otraLabel.trim();
    if (!trimmed) return;
    addMutation.mutate({ label: trimmed, catalogCode: null });
    setOtraLabel("");
  };

  const handleRemoveSignal = (id: string) => {
    setRemovingId(id);
    removeMutation.mutate(id);
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className={cn("rounded-lg border border-border bg-card p-4 shadow-sm", className)}>
      <div className="flex flex-col gap-5">
        {/* Card header */}
        <h3 className="text-sm font-semibold text-foreground">
          Señales de autoridad
        </h3>

        {/* ── Section A: Certificaciones ───────────────────────────────── */}
        <section aria-labelledby="trust-certs-heading">
          <h4
            id="trust-certs-heading"
            className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground"
          >
            Certificaciones y acreditaciones
          </h4>

          {/* Active chips */}
          {isSignalsLoading ? (
            <div className="flex flex-wrap gap-2" aria-busy="true">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-7 w-24 rounded-full" />
              ))}
            </div>
          ) : isSignalsError ? (
            <p className="text-xs text-destructive" role="alert">
              No se pudieron cargar las certificaciones activas.
            </p>
          ) : activeSignals.length > 0 ? (
            <div className="flex flex-wrap gap-2" role="list" aria-label="Certificaciones activas">
              {activeSignals.map((signal) => (
                <div key={signal.id} role="listitem">
                  <CertChip
                    signal={signal}
                    onRemove={handleRemoveSignal}
                    isRemoving={removingId === signal.id}
                  />
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">
              Aún no se han agregado certificaciones. Selecciona del catálogo o agrega una propia.
            </p>
          )}

          {/* Expandable OQ-D catalog */}
          <details className="mt-3 rounded-md border border-border/50 bg-muted/30">
            <summary className="flex cursor-pointer items-center gap-2 px-3 py-2 text-xs font-medium text-foreground select-none hover:bg-muted/50">
              <svg
                aria-hidden="true"
                className="h-3.5 w-3.5 text-muted-foreground transition-transform [[open]_&]:rotate-90"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
              Catálogo de certificaciones ({countryCode})
              {isCatalogLoading && (
                <span className="ml-1 text-muted-foreground">(cargando...)</span>
              )}
            </summary>

            <div className="border-t border-border/50 px-3 pb-3 pt-2">
              {isCatalogLoading ? (
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-3" aria-busy="true">
                  {Array.from({ length: 6 }).map((_, i) => (
                    <Skeleton key={i} className="h-8 rounded-md" />
                  ))}
                </div>
              ) : catalogItems.length === 0 ? (
                <p className="text-xs text-muted-foreground">
                  No hay catálogo disponible para este país.
                </p>
              ) : (
                <div
                  role="group"
                  aria-label={`Catálogo de certificaciones ${countryCode}`}
                  className="grid grid-cols-2 gap-2 sm:grid-cols-3"
                >
                  {catalogItems.map((item) => {
                    const isActive = activeCodes.has(item.code);
                    const isLoading = addMutation.isPending || removeMutation.isPending;
                    return (
                      <label
                        key={item.code}
                        className={cn(
                          "flex cursor-pointer items-center gap-2 rounded-md border p-2 text-xs transition-colors",
                          isActive
                            ? "border-primary/60 bg-primary/10 text-foreground"
                            : "border-border/50 bg-background hover:bg-muted/50 text-muted-foreground",
                        )}
                      >
                        <input
                          type="checkbox"
                          className="h-3.5 w-3.5 shrink-0 accent-primary"
                          checked={isActive}
                          disabled={isLoading}
                          onChange={() => handleToggleCatalogItem(item.code, item.label)}
                          aria-label={`${isActive ? "Quitar" : "Agregar"} ${item.label}`}
                        />
                        <span>{item.label}</span>
                        {item.hint && (
                          <span
                            title={item.hint}
                            className="ml-auto shrink-0 text-muted-foreground/60"
                          >
                            ℹ
                          </span>
                        )}
                      </label>
                    );
                  })}
                </div>
              )}

              {/* Free-text "Otra" */}
              <div className="mt-3 flex gap-2">
                <Input
                  type="text"
                  value={otraLabel}
                  onChange={(e) => setOtraLabel(e.target.value)}
                  placeholder="Otra certificación..."
                  aria-label="Agregar otra certificación (texto libre)"
                  className="h-8 text-xs"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleAddOtra();
                    }
                  }}
                />
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={handleAddOtra}
                  disabled={!otraLabel.trim() || addMutation.isPending}
                  aria-label="Agregar certificación personalizada"
                  className="h-8 shrink-0 text-xs"
                >
                  Agregar
                </Button>
              </div>
            </div>
          </details>
        </section>

        {/* ── Section B: Experiencia + Pacientes (2-col grid) ──────────── */}
        <section aria-labelledby="trust-exp-heading">
          <h4
            id="trust-exp-heading"
            className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground"
          >
            Experiencia y alcance
          </h4>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {/* Años de experiencia */}
            <div className="flex flex-col gap-1">
              <label
                htmlFor="trust-years-experience"
                className="text-xs font-medium text-foreground"
              >
                Años de experiencia
              </label>
              <Input
                id="trust-years-experience"
                type="number"
                min={0}
                max={200}
                value={localYears}
                placeholder="Ej: 15"
                aria-label="Años de experiencia"
                onChange={(e) => {
                  setLocalYears(e.target.value);
                  const num = e.target.value ? parseInt(e.target.value, 10) : undefined;
                  onScheduleAutosave({ yearsExperience: num });
                }}
              />
              <p className="text-xs text-muted-foreground">Años que lleva operando la clínica</p>
            </div>

            {/* Pacientes atendidos */}
            <div className="flex flex-col gap-1">
              <label
                htmlFor="trust-patients-count"
                className="text-xs font-medium text-foreground"
              >
                Pacientes atendidos
              </label>
              <Input
                id="trust-patients-count"
                type="text"
                value={localPatients}
                placeholder="Ej: +5000"
                aria-label="Pacientes atendidos"
                onChange={(e) => {
                  setLocalPatients(e.target.value);
                  onScheduleAutosave({ patientsCount: e.target.value || undefined });
                }}
              />
              <p className="text-xs text-muted-foreground">
                Puedes usar texto aproximado (ej: +5000)
              </p>
            </div>
          </div>
        </section>

        {/* ── Section C: Premios ────────────────────────────────────────── */}
        <section aria-labelledby="trust-awards-heading">
          <h4
            id="trust-awards-heading"
            className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground"
          >
            Premios y reconocimientos
          </h4>
          <div className="flex flex-col gap-1">
            <label htmlFor="trust-awards" className="sr-only">
              Premios y reconocimientos
            </label>
            <Textarea
              id="trust-awards"
              value={localAwards}
              placeholder="Ej: Premio Excelencia Médica 2023, Acreditación JCI..."
              aria-label="Premios y reconocimientos"
              rows={3}
              onChange={(e) => {
                setLocalAwards(e.target.value);
                onScheduleAutosave({ awards: e.target.value || undefined });
              }}
            />
            <p className="text-xs text-muted-foreground">
              Uno por línea o separados por coma.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}

TrustSignalsEditor.displayName = "TrustSignalsEditor";

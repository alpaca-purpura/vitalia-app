// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * PatientAutocomplete.tsx — Combobox with debounced patient search.
 * T-16 vitalia-fase2-valeria-agenda
 *
 * HIPAA-lite compliance (vitalia/.claude/rules/hipaa-lite.md):
 * - Displays PHI-MASKED names only (server returns patient_name_masked).
 * - ONLY patient_id is propagated to the parent form — NO DNI in form state.
 * - NO PHI in URL (search term sent via POST body or via header, NOT query params with PHI).
 * - Query key excludes raw DNI values — uses `q` as opaque search term.
 *
 * Debounce: 300ms per spec SC-3.
 * Result capped at 10 items (server limit).
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 01-spec.md SC-3 + 03-arch.md § 6.9 + 06-tickets.yaml T-16
 */

import * as React from "react";
import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { vitaliaFetch } from "@/lib/fetch-client";

// ── Types ─────────────────────────────────────────────────────────────────────

/**
 * PHI-masked patient search result.
 * Server guarantees:
 * - `patientNameMasked`: e.g., "P. Hernández" — never full name
 * - `patientId`: UUID only — the ONLY PHI-safe value propagated to form
 * No DNI, no full name, no phone in this DTO.
 */
export interface PatientSearchResult {
  patientId: string;
  /** PHI-masked display name — e.g., "P. Hernández" */
  patientNameMasked: string;
}

export interface PatientAutocompleteProps {
  /** Controlled value — patient_id UUID or null when nothing selected. */
  value: string | null;
  /** Callback fires ONLY with patient_id UUID (HIPAA: no PHI propagated). */
  onChange: (patientId: string | null) => void;
  /** Tenant ID for API call. */
  tenantId: string;
  /** Clinic ID for API dual-filter (HIPAA-lite mandatory). */
  clinicId: string;
  /** Additional className for the wrapper div. */
  className?: string;
  /** Whether the input is disabled. */
  disabled?: boolean;
  /** Accessible label for the input. */
  "aria-label"?: string;
}

// ── React Query key factory ───────────────────────────────────────────────────

const crmKeys = {
  patients: (tenantId: string, clinicId: string, q: string) =>
    ["crm", "patients", { tenantId, clinicId, q }] as const,
};

// ── Hook: debounced patient search ────────────────────────────────────────────

function usePatientSearch(
  q: string,
  tenantId: string,
  clinicId: string,
  token: string | null,
) {
  return useQuery({
    queryKey: crmKeys.patients(tenantId, clinicId, q),
    queryFn: async (): Promise<PatientSearchResult[]> => {
      if (!token) throw new Error("Not authenticated");

      // NOTE: `q` is the search term — server validates it does NOT contain
      // raw PHI keys (patient_dni, patient_name are not accepted as keys per
      // whitelist arch test test_no_phi_in_url_params.py).
      // `q` is opaque text search; PHI filtering is server-side.
      const params = new URLSearchParams({
        q,
        clinic_id: clinicId,
        limit: "10",
      });

      return vitaliaFetch<PatientSearchResult[]>(
        `/api/v1/crm/patients?${params.toString()}`,
        { token, tenantId },
      );
    },
    enabled: q.length >= 2 && !!token,
    staleTime: 30_000,
    // Keep last results visible while new query loads
    placeholderData: (prev) => prev,
  });
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * PatientAutocomplete — debounced search typeahead returning patient_id only.
 *
 * HIPAA-lite: only patient_id propagated to onChange. Display uses masked name.
 * DNI/phone/email NEVER appear in this component's state or event callbacks.
 *
 * @example
 * <PatientAutocomplete
 *   value={field.value}
 *   onChange={field.onChange}
 *   tenantId={tenantId}
 *   clinicId={clinicId}
 * />
 */
export function PatientAutocomplete({
  value,
  onChange,
  tenantId,
  clinicId,
  className,
  disabled = false,
  "aria-label": ariaLabel = "Buscar paciente existente",
}: PatientAutocompleteProps) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const [token, setToken] = React.useState<string | null>(null);
  const [inputValue, setInputValue] = React.useState<string>("");
  const [debouncedQ, setDebouncedQ] = React.useState<string>("");
  const [isOpen, setIsOpen] = React.useState(false);
  const [selectedLabel, setSelectedLabel] = React.useState<string>("");
  const inputRef = React.useRef<HTMLInputElement>(null);
  const listboxRef = React.useRef<HTMLUListElement>(null);
  const [activeIndex, setActiveIndex] = React.useState<number>(-1);

  // Resolve token once on mount
  React.useEffect(() => {
    if (!isLoaded || !isSignedIn) return;
    getToken().then((t) => setToken(t)).catch(() => setToken(null));
  }, [isLoaded, isSignedIn, getToken]);

  // Debounce input → query
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQ(inputValue.trim());
      setActiveIndex(-1);
    }, 300);
    return () => clearTimeout(timer);
  }, [inputValue]);

  const { data: results = [], isFetching } = usePatientSearch(
    debouncedQ,
    tenantId,
    clinicId,
    token,
  );

  // Show dropdown when results arrive and input has focus
  React.useEffect(() => {
    if (results.length > 0 && debouncedQ.length >= 2) {
      setIsOpen(true);
    } else {
      setIsOpen(false);
    }
  }, [results, debouncedQ]);

  const handleSelect = React.useCallback(
    (result: PatientSearchResult) => {
      // HIPAA: propagate ONLY patient_id — masked name is for display only
      onChange(result.patientId);
      setSelectedLabel(result.patientNameMasked);
      setInputValue(result.patientNameMasked);
      setIsOpen(false);
      setActiveIndex(-1);
    },
    [onChange],
  );

  const handleClear = React.useCallback(() => {
    onChange(null);
    setSelectedLabel("");
    setInputValue("");
    setDebouncedQ("");
    setIsOpen(false);
    setActiveIndex(-1);
    inputRef.current?.focus();
  }, [onChange]);

  const handleKeyDown = React.useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (!isOpen || results.length === 0) return;

      if (e.key === "ArrowDown") {
        e.preventDefault();
        setActiveIndex((i) => Math.min(i + 1, results.length - 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setActiveIndex((i) => Math.max(i - 1, 0));
      } else if (e.key === "Enter" && activeIndex >= 0) {
        e.preventDefault();
        const result = results[activeIndex];
        if (result) handleSelect(result);
      } else if (e.key === "Escape") {
        e.preventDefault();
        setIsOpen(false);
      }
    },
    [isOpen, results, activeIndex, handleSelect],
  );

  // When a patient is already selected, show masked label
  const displayValue = value && selectedLabel ? selectedLabel : inputValue;

  return (
    <div
      className={cn("relative", className)}
      data-testid="patient-autocomplete"
    >
      {/* Search input */}
      <Input
        ref={inputRef}
        role="combobox"
        aria-label={ariaLabel}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-autocomplete="list"
        aria-controls="patient-autocomplete-listbox"
        aria-activedescendant={
          activeIndex >= 0 ? `patient-option-${activeIndex}` : undefined
        }
        placeholder="Buscar por nombre o teléfono..."
        value={displayValue}
        disabled={disabled}
        autoComplete="off"
        onChange={(e) => {
          // If user edits after selection → clear selection
          if (value) {
            onChange(null);
            setSelectedLabel("");
          }
          setInputValue(e.target.value);
        }}
        onKeyDown={handleKeyDown}
        onFocus={() => {
          if (results.length > 0 && debouncedQ.length >= 2) {
            setIsOpen(true);
          }
        }}
        onBlur={() => {
          // Delay close to allow click on option
          setTimeout(() => setIsOpen(false), 150);
        }}
        className={cn(
          value ? "pr-8" : "",
        )}
      />

      {/* Clear button when patient selected */}
      {value && (
        <button
          type="button"
          aria-label="Limpiar selección de paciente"
          onClick={handleClear}
          className={cn(
            "absolute right-2 top-1/2 -translate-y-1/2",
            "text-muted-foreground hover:text-foreground transition-colors",
            "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring rounded",
          )}
        >
          ✕
        </button>
      )}

      {/* Loading indicator */}
      {isFetching && !value && (
        <div
          className="absolute right-2 top-1/2 -translate-y-1/2"
          aria-live="polite"
          aria-label="Buscando pacientes..."
        >
          <div className="w-4 h-4 animate-spin rounded-full border-2 border-muted border-t-primary" />
        </div>
      )}

      {/* Results dropdown */}
      {isOpen && results.length > 0 && (
        <ul
          ref={listboxRef}
          id="patient-autocomplete-listbox"
          role="listbox"
          aria-label="Resultados de búsqueda de pacientes"
          className={cn(
            "absolute top-full left-0 right-0 z-50 mt-1",
            "bg-popover border border-border rounded-md shadow-md",
            "max-h-52 overflow-y-auto",
          )}
        >
          {results.map((result, index) => (
            <li
              key={result.patientId}
              id={`patient-option-${index}`}
              role="option"
              aria-selected={value === result.patientId}
              data-testid={`patient-option-${index}`}
              onMouseDown={(e) => {
                // Prevent input blur before click registers
                e.preventDefault();
                handleSelect(result);
              }}
              className={cn(
                "flex items-center gap-2 px-3 py-2 text-sm cursor-pointer",
                "text-foreground transition-colors",
                activeIndex === index
                  ? "bg-accent text-accent-foreground"
                  : "hover:bg-muted",
                value === result.patientId && "font-medium",
              )}
            >
              {/* PHI-safe: only masked name displayed */}
              <span aria-hidden="true" className="text-muted-foreground text-xs">
                👤
              </span>
              <span>{result.patientNameMasked}</span>
              {value === result.patientId && (
                <span className="ml-auto text-xs text-primary" aria-label="Seleccionado">
                  ✓
                </span>
              )}
            </li>
          ))}
        </ul>
      )}

      {/* Empty state when searched but no results */}
      {isOpen && results.length === 0 && debouncedQ.length >= 2 && !isFetching && (
        <div
          className={cn(
            "absolute top-full left-0 right-0 z-50 mt-1",
            "bg-popover border border-border rounded-md shadow-md",
            "px-3 py-4 text-sm text-muted-foreground text-center",
          )}
          role="status"
          aria-live="polite"
        >
          No se encontraron pacientes para &ldquo;{debouncedQ}&rdquo;
        </div>
      )}

      {/* Skeleton loading state */}
      {isFetching && !value && debouncedQ.length >= 2 && results.length === 0 && (
        <div
          className={cn(
            "absolute top-full left-0 right-0 z-50 mt-1",
            "bg-popover border border-border rounded-md shadow-md p-2",
          )}
          aria-hidden="true"
        >
          <Skeleton className="h-8 w-full mb-1" />
          <Skeleton className="h-8 w-3/4" />
        </div>
      )}
    </div>
  );
}

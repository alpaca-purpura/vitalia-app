// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
"use client";

/**
 * TreatmentLanguageCard.tsx — Tratamiento e idioma selects.
 *
 * Two selects:
 *   1. Tratamiento: tuteo ("tú") | ustedeo ("usted")
 *   2. Idioma: Español neutro | Portugués BR
 *
 * Autosaves on change (calls onChange immediately — debounce handled by parent).
 * Spanish neutro LatAm UI strings. Accessibility: Labels with htmlFor.
 *
 * T-6 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-6 deliverables + 03-arch.md § 5 TreatmentLanguageCard
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

import { cn } from "@/lib/utils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";

export type TreatmentMode = "tuteo" | "ustedeo";
export type LanguageOption = "es_neutro" | "pt_br";

export interface TreatmentLanguageValues {
  treatment: TreatmentMode;
  language: LanguageOption;
}

export interface TreatmentLanguageCardProps {
  values: TreatmentLanguageValues;
  onChange: (values: TreatmentLanguageValues) => void;
  className?: string;
}

export function TreatmentLanguageCard({
  values,
  onChange,
  className,
}: TreatmentLanguageCardProps) {
  function handleTreatmentChange(treatment: string) {
    onChange({ ...values, treatment: treatment as TreatmentMode });
  }

  function handleLanguageChange(language: string) {
    onChange({ ...values, language: language as LanguageOption });
  }

  return (
    <section className={cn("flex flex-col gap-3", className)}>
      <p className="text-sm font-semibold text-foreground">Tratamiento e idioma</p>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {/* Tratamiento */}
        <div className="flex flex-col gap-1.5">
          <Label
            htmlFor="treatment-select"
            className="text-xs font-semibold uppercase tracking-wide text-muted-foreground"
          >
            Tratamiento
          </Label>
          <Select
            value={values.treatment}
            onValueChange={handleTreatmentChange}
          >
            <SelectTrigger id="treatment-select" className="text-sm">
              <SelectValue placeholder="Selecciona tratamiento" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="tuteo">Tuteo (tú)</SelectItem>
              <SelectItem value="ustedeo">Ustedeo (usted)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Idioma */}
        <div className="flex flex-col gap-1.5">
          <Label
            htmlFor="language-select"
            className="text-xs font-semibold uppercase tracking-wide text-muted-foreground"
          >
            Idioma
          </Label>
          <Select
            value={values.language}
            onValueChange={handleLanguageChange}
          >
            <SelectTrigger id="language-select" className="text-sm">
              <SelectValue placeholder="Selecciona idioma" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="es_neutro">Español neutro</SelectItem>
              <SelectItem value="pt_br">Portugués BR</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
    </section>
  );
}

TreatmentLanguageCard.displayName = "TreatmentLanguageCard";

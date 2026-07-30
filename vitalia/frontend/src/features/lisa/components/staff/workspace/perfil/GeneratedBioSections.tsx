// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
"use client";
/**
 * GeneratedBioSections.tsx — Generated bio display + contenteditable edit + autosave.
 *
 * Business rules:
 *   - bio-generated-from-inputs-no-invent: bio must be generated from BioRepoInputs
 *     material only; no LLM invention. Guardrail enforced by BE service (D-4).
 *   - "✨ Generar bio" CTA triggers POST {id}/generate-bio
 *   - 3 contenteditable sections: Resumen · Formación · Enfoque
 *   - All 3 sections autosave on-change (600ms debounce)
 *
 * Microcopy per spec:
 *   - Bio CTA: "✨ Generar bio"
 *   - Bio hint: "La bio se genera a partir del material que agregaste arriba"
 *
 * T-FE-2 vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § Componentes (GeneratedBioSections) + § Microcopy
 * downstream-regression-na: brand-local vitalia feature component
 */

import { useState, useCallback } from "react";
import { useGenerateBio, usePatchDoctor } from "../../../../api/staff";
import { useAutosave } from "@/hooks/use-autosave";
import { cn } from "@/lib/utils";
import type { DoctorDetail, BioPublic } from "../../../../types/staff.types";

interface GeneratedBioSectionsProps {
  doctorId: string;
  initialDoctor: DoctorDetail;
}

type BioSection = "resumen" | "formacion" | "enfoque";

const SECTION_LABELS: Record<BioSection, string> = {
  resumen: "Resumen",
  formacion: "Formación",
  enfoque: "Enfoque",
};

export function GeneratedBioSections({
  doctorId,
  initialDoctor,
}: GeneratedBioSectionsProps) {
  const [bioPublic, setBioPublic] = useState<BioPublic>(
    initialDoctor.bioPublic ?? {},
  );

  const generateMutation = useGenerateBio(doctorId);
  const patchMutation = usePatchDoctor(doctorId);

  // Autosave bio sections on-change
  const { schedule: scheduleBioSave, status: bioSaveStatus } = useAutosave({
    saveFn: async (updated: BioPublic) => {
      await patchMutation.mutateAsync({ bioPublic: updated });
    },
    debounceMs: 600,
  });

  const handleGenerate = useCallback(async () => {
    try {
      const result = await generateMutation.mutateAsync();
      const generated: BioPublic = {
        resumen: result.resumen,
        formacion: result.formacion,
        enfoque: result.enfoque,
      };
      setBioPublic(generated);
      scheduleBioSave(generated);
    } catch {
      // Error is handled via generateMutation.isError state
    }
  }, [generateMutation, scheduleBioSave]);

  const handleSectionChange = useCallback(
    (section: BioSection, value: string) => {
      const updated = { ...bioPublic, [section]: value };
      setBioPublic(updated);
      scheduleBioSave(updated);
    },
    [bioPublic, scheduleBioSave],
  );

  const hasContent = Object.values(bioPublic).some((v) => v && v.trim());

  return (
    <section aria-labelledby="bio-generated-heading" className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 id="bio-generated-heading" className="text-sm font-semibold">
            Bio pública
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            La bio se genera a partir del material que agregaste arriba
          </p>
        </div>

        {/* Autosave status */}
        {bioSaveStatus !== "idle" && (
          <span className="text-xs text-muted-foreground" aria-live="polite">
            {bioSaveStatus === "saving" && "Guardando..."}
            {bioSaveStatus === "saved" && "✓ Guardado"}
            {bioSaveStatus === "error" && "⚠️ Error al guardar"}
          </span>
        )}
      </div>

      {/* Generate button */}
      <button
        type="button"
        onClick={handleGenerate}
        disabled={generateMutation.isPending}
        className={cn(
          "inline-flex items-center gap-2 px-4 py-2 text-sm rounded-md",
          "bg-[var(--agent-lisa)] text-white font-medium",
          "hover:opacity-90 active:opacity-80 transition-opacity",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
          "disabled:opacity-50 disabled:cursor-not-allowed",
        )}
        aria-label="Generar bio"
        aria-busy={generateMutation.isPending}
      >
        {generateMutation.isPending ? (
          <>
            <span aria-hidden="true">⏳</span>
            Generando...
          </>
        ) : (
          <>
            <span aria-hidden="true">✨</span>
            Generar bio
          </>
        )}
      </button>

      {/* Error state */}
      {generateMutation.isError && (
        <p className="text-sm text-destructive" role="alert">
          No se pudo generar la bio. Vuelve a intentarlo.
        </p>
      )}

      {/* Bio sections — contenteditable */}
      {(hasContent || generateMutation.isSuccess) && (
        <div className="space-y-3">
          {(["resumen", "formacion", "enfoque"] as BioSection[]).map(
            (section) => (
              <div key={section} className="space-y-1">
                <label
                  htmlFor={`bio-${section}`}
                  className="text-xs font-medium text-muted-foreground uppercase tracking-wide"
                >
                  {SECTION_LABELS[section]}
                </label>
                <div
                  id={`bio-${section}`}
                  role="textbox"
                  aria-multiline="true"
                  aria-label={SECTION_LABELS[section]}
                  contentEditable
                  suppressContentEditableWarning
                  onInput={(e) => {
                    const content =
                      (e.target as HTMLDivElement).textContent ?? "";
                    handleSectionChange(section, content);
                  }}
                  className={cn(
                    "min-h-[80px] rounded-md border border-input bg-background px-3 py-2 text-sm",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
                    "empty:before:content-[attr(data-placeholder)] empty:before:text-muted-foreground",
                  )}
                  data-placeholder={`Contenido de ${SECTION_LABELS[section].toLowerCase()}...`}
                  dangerouslySetInnerHTML={{
                    __html: bioPublic[section] ?? "",
                  }}
                />
              </div>
            ),
          )}
        </div>
      )}

      {/* Empty state */}
      {!hasContent && !generateMutation.isSuccess && !generateMutation.isPending && (
        <div className="rounded-lg border border-dashed border-border/60 p-4 text-center text-xs text-muted-foreground">
          Agrega material de referencia arriba y haz clic en "✨ Generar bio" para crear la bio del integrante.
        </div>
      )}
    </section>
  );
}

// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
"use client";
/**
 * DoctorPaginaView.tsx — Root Client Component for "Página" workspace leaf.
 *
 * Orchestrates:
 *   - PublicLinkBar (pill Publicada/Borrador + URL + Copiar + Ver + toggle)
 *   - BioRepoInputs (Material del doctor — notas + archivos + enlaces; privado, nunca se publica tal cual)
 *   - State-driven generation banner (never→CTA | quiet→date+⋮ | material_new→⚡banner)
 *   - StructuredProfileEditor (RHF+Zod, autosave 600ms)
 *   - PhonePreview (Doctoralia phone frame preview)
 *
 * Layout order (per spec § D3-D + mockup doctores.html hoja Página):
 *   1. PublicLinkBar
 *   2. BioRepoInputs ("Material del doctor")   ← D3-B material lives here, not in Perfil
 *   3. Generation banner (state-driven)
 *   4. 2-col: StructuredProfileEditor + PhonePreview
 *
 * Per ADR-vitalia-004 § 3-5: Client Component, React Query, RHF + Zod, autosave.
 * canon §2.6: ONE FloatingAutosaveIndicator per page.
 *
 * T-FE-pagina-publica vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § D3-D
 */

import { useState, useCallback } from "react";
import { useDoctor, useGenerateProfile } from "../../../../api/staff";
import { StructuredProfileEditor } from "./StructuredProfileEditor";
import { PhonePreview } from "./PhonePreview";
import { PublicLinkBar } from "./PublicLinkBar";
import { BioRepoInputs } from "../perfil/BioRepoInputs";
import { FloatingAutosaveIndicator } from "@/components/shared/FloatingAutosaveIndicator";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { AutosaveStatus } from "@/hooks/use-autosave";

interface DoctorPaginaViewProps {
  doctorId: string;
}

/** Derives generation UI state from profileState fields */
type GenerationState = "never" | "quiet" | "material_new";

function deriveGenerationState(
  generatedAt: string | null | undefined,
  materialNew: boolean | undefined,
): GenerationState {
  if (!generatedAt) return "never";
  if (materialNew) return "material_new";
  return "quiet";
}

/**
 * combineAutosaveStatuses — page-level priority combiner for multiple autosave sources.
 * Priority: saving > error > saved > idle (canon §2.6 — ONE FloatingAutosaveIndicator)
 */
function combineAutosaveStatuses(...statuses: AutosaveStatus[]): AutosaveStatus {
  if (statuses.includes("saving")) return "saving";
  if (statuses.includes("error")) return "error";
  if (statuses.includes("saved")) return "saved";
  return "idle";
}

/** Formats ISO 8601 to "DD/MM/YYYY HH:mm" for display */
function formatGeneratedAt(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/**
 * DoctorPaginaView — manages public page editor + generation state UI.
 */
export function DoctorPaginaView({ doctorId }: DoctorPaginaViewProps) {
  const { data: doctor, isLoading, isError } = useDoctor(doctorId);
  const generateProfile = useGenerateProfile(doctorId);
  const [showConfirmOverwrite, setShowConfirmOverwrite] = useState(false);

  // W4: combined autosave status from BioRepoInputs + StructuredProfileEditor
  // ONE FloatingAutosaveIndicator per page (canon §2.6)
  const [bioAutosaveStatus, setBioAutosaveStatus] = useState<AutosaveStatus>("idle");
  const [profileAutosaveStatus, setProfileAutosaveStatus] = useState<AutosaveStatus>("idle");
  const combinedAutosaveStatus = combineAutosaveStatuses(bioAutosaveStatus, profileAutosaveStatus);

  const handleBioAutosaveStatus = useCallback(
    (status: AutosaveStatus) => setBioAutosaveStatus(status),
    [],
  );
  const handleProfileAutosaveStatus = useCallback(
    (status: AutosaveStatus) => setProfileAutosaveStatus(status),
    [],
  );

  // ── Loading state ─────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="space-y-4" aria-busy="true" aria-label="Cargando página pública">
        <Skeleton className="h-12 w-full rounded-lg" />
        <Skeleton className="h-64 w-full rounded-lg" />
        <Skeleton className="h-32 w-full rounded-lg" />
      </div>
    );
  }

  if (isError || !doctor) {
    return (
      <div
        role="alert"
        className="rounded-lg border border-destructive/50 bg-destructive/5 p-4 text-sm text-destructive"
      >
        No se pudo cargar la información. Vuelve a intentarlo.
      </div>
    );
  }

  const genState = deriveGenerationState(
    doctor.profileState?.generatedAt,
    doctor.profileState?.materialNew,
  );

  const hasPublicProfile =
    doctor.publicProfile != null &&
    (doctor.publicProfile.sobreMi ||
      doctor.publicProfile.formacion.length > 0 ||
      doctor.publicProfile.experiencia.length > 0 ||
      doctor.publicProfile.tratamientos.length > 0);

  function handleGenerate(overwrite = false) {
    // If there's already a profile and user hasn't confirmed overwrite — show modal
    if (hasPublicProfile && !overwrite) {
      setShowConfirmOverwrite(true);
      return;
    }
    setShowConfirmOverwrite(false);
    void generateProfile.mutate();
  }

  return (
    <section className="flex flex-col gap-5" aria-label="Página pública del doctor" data-testid="doctor-pagina-view">
      {/* ── Public link bar (pill + toggle + URL) ────────────────────────── */}
      <PublicLinkBar doctorId={doctorId} doctor={doctor} />

      {/* ── Material del doctor (D3-B) ────────────────────────────────────── */}
      {/* Privado — nunca se publica tal cual. Alimenta la generación de perfil. */}
      <section aria-labelledby="material-heading" data-testid="bio-material-section">
        <h2
          id="material-heading"
          className="mb-3 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground"
        >
          <span aria-hidden="true" className="h-3 w-0.5 rounded-full bg-agent-lisa" />
          Material del doctor
          <span className="ml-1 font-normal normal-case tracking-normal text-muted-foreground/70">
            — privado, nunca se publica tal cual
          </span>
        </h2>
        <BioRepoInputs
          doctorId={doctorId}
          initialDoctor={doctor}
          onAutosaveStatusChange={handleBioAutosaveStatus}
        />
      </section>

      {/* ── Generation state banner ───────────────────────────────────────── */}
      {genState === "never" && (
        <article className="flex flex-col gap-3 rounded-xl border border-border bg-card p-5" aria-label="Generar perfil por primera vez">
          <div className="flex items-center gap-2">
            <span className="text-lg" aria-hidden="true">✨</span>
            <div>
              <p className="font-medium text-sm">Genera el perfil público del doctor</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                Usa los materiales cargados (documentos, notas, enlaces) para crear
                automáticamente la presentación profesional.
              </p>
            </div>
          </div>
          <Button
            size="sm"
            onClick={() => handleGenerate()}
            disabled={generateProfile.isPending}
            className="self-start bg-agent-lisa hover:bg-agent-lisa/90 text-white"
            aria-label="Generar perfil público con IA"
          >
            {generateProfile.isPending ? "Generando..." : "✨ Generar perfil"}
          </Button>
          {generateProfile.isError && (
            <p className="text-xs text-destructive" role="alert">
              Error al generar el perfil. Vuelve a intentarlo.
            </p>
          )}
        </article>
      )}

      {genState === "quiet" && (
        <div className="flex items-center justify-between rounded-xl border border-border bg-card/50 p-3 px-4">
          <p className="text-xs text-muted-foreground">
            Última generación: {formatGeneratedAt(doctor.profileState?.generatedAt)}
          </p>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleGenerate()}
            disabled={generateProfile.isPending}
            className="h-7 text-xs"
            aria-label="Regenerar perfil público"
          >
            {generateProfile.isPending ? "Generando..." : "⋮ Regenerar"}
          </Button>
        </div>
      )}

      {genState === "material_new" && (
        <div
          className={cn(
            "flex items-start gap-3 rounded-xl border p-4",
            "border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/30",
          )}
          role="status"
          aria-label="Nuevo material disponible"
        >
          <span className="text-base shrink-0 mt-0.5" aria-hidden="true">⚡</span>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-amber-900 dark:text-amber-200">
              Hay{" "}
              {(doctor.profileState?.materialNewCount ?? 0) > 1
                ? `${doctor.profileState?.materialNewCount ?? ""} archivos nuevos`
                : "material nuevo"}{" "}
              desde la última generación
            </p>
            <p className="text-xs text-amber-700 dark:text-amber-400 mt-0.5">
              Actualiza el perfil para reflejar los últimos materiales cargados.
            </p>
          </div>
          <Button
            size="sm"
            onClick={() => handleGenerate()}
            disabled={generateProfile.isPending}
            className="shrink-0 bg-amber-600 hover:bg-amber-700 text-white"
            aria-label="Actualizar perfil público con nuevo material"
          >
            {generateProfile.isPending ? "Actualizando..." : "✨ Actualizar perfil"}
          </Button>
        </div>
      )}

      {/* ── Overwrite confirm modal ───────────────────────────────────────── */}
      {showConfirmOverwrite && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="overwrite-dialog-title"
          className="rounded-xl border border-border bg-card p-5 shadow-lg space-y-3"
        >
          <p id="overwrite-dialog-title" className="font-medium text-sm">
            ¿Reemplazar el perfil actual?
          </p>
          <p className="text-xs text-muted-foreground">
            Los cambios manuales que hayas hecho serán reemplazados por la nueva
            generación con IA. Esta acción no se puede deshacer.
          </p>
          <div className="flex gap-2">
            <Button
              size="sm"
              onClick={() => handleGenerate(true)}
              disabled={generateProfile.isPending}
              className="bg-agent-lisa hover:bg-agent-lisa/90 text-white"
            >
              {generateProfile.isPending ? "Generando..." : "Sí, reemplazar"}
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowConfirmOverwrite(false)}
            >
              Cancelar
            </Button>
          </div>
        </div>
      )}

      {/* ── 2-column layout: editor + preview ────────────────────────────── */}
      <section className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_320px]" aria-label="Editor y vista previa">
        {/* Structured profile editor — emits status to combined FloatingAutosaveIndicator (W4) */}
        <StructuredProfileEditor
          doctorId={doctorId}
          doctor={doctor}
          onAutosaveStatusChange={handleProfileAutosaveStatus}
        />

        {/* Phone preview (Doctoralia frame) */}
        <aside aria-label="Vista previa en móvil">
          <PhonePreview doctor={doctor} />
        </aside>
      </section>

      {/* ── canon §2.6 singleton FloatingAutosaveIndicator — W4: combines BioRepoInputs
           + StructuredProfileEditor statuses in ONE indicator per page leaf ────── */}
      <FloatingAutosaveIndicator status={combinedAutosaveStatus} />
    </section>
  );
}

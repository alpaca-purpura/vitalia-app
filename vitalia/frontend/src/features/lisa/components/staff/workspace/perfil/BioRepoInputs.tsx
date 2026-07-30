// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
"use client";
/**
 * BioRepoInputs.tsx — Bio repository inputs (notes + file attachments + link chips).
 *
 * Business rules:
 *   - Bio = raw material repository: notes + files + links → feeds "✨ Generar bio".
 *   - All text/link changes autosave on-change (600ms debounce).
 *   - File upload: 2-step proxy → register (useBioFileUpload, kind=bio_doc).
 *   - File rows: icon by content-type + name + size + date + download + delete with confirm.
 *   - Inline emoji autosave badges KILLED — page-level FloatingAutosaveIndicator covers (canon §2.6).
 *   - Card with agent-lisa border accent + section header.
 *   - Links: Zod URL validation + chip display.
 *
 * T-FE-bio-docs vitalia-fase2-lisa-doctores (D3-B delta v3)
 * spec_anchor: 01-spec.md § D3-B + § D3-B.1
 * downstream-regression-na: brand-local vitalia feature component
 */

import { useState, useCallback, useId, useEffect } from "react";
import { z } from "zod";
import { useAutosave } from "@/hooks/use-autosave";
import { usePatchDoctor } from "../../../../api/staff";
import {
  useBioFileUpload,
  useBioFiles,
  useDeleteBioFile,
  useBioFileDownload,
} from "../../../../api/staff";
import { Dropzone } from "@/components/ui/dropzone";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { DoctorDetail, BioFile } from "../../../../types/staff.types";

// ── Validation ────────────────────────────────────────────────────────────────

const linkSchema = z.string().url();

// ── Helpers ───────────────────────────────────────────────────────────────────

const ALLOWED_TYPES = [
  "application/pdf",
  "image/jpeg",
  "image/png",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];
const MAX_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatUploadedAt(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("es-419", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return iso.slice(0, 10);
  }
}

function fileIcon(contentType: string): string {
  if (contentType === "application/pdf") return "📄";
  if (contentType.startsWith("image/")) return "🖼️";
  if (contentType.includes("word")) return "📝";
  return "📎";
}

// ── Sub-components ────────────────────────────────────────────────────────────

interface BioFileRowProps {
  file: BioFile;
  doctorId: string;
  onDeleteSuccess?: () => void;
}

function BioFileRow({ file, doctorId }: BioFileRowProps) {
  const [confirming, setConfirming] = useState(false);
  const downloadMutation = useBioFileDownload(doctorId);
  const deleteMutation = useDeleteBioFile(doctorId);

  const handleDownload = useCallback(() => {
    downloadMutation.mutate({ fileId: file.id, filename: file.filename });
  }, [downloadMutation, file.id, file.filename]);

  const handleDeleteRequest = useCallback(() => {
    setConfirming(true);
  }, []);

  const handleDeleteConfirm = useCallback(() => {
    deleteMutation.mutate(file.id, {
      onSettled: () => setConfirming(false),
    });
  }, [deleteMutation, file.id]);

  const handleDeleteCancel = useCallback(() => {
    setConfirming(false);
  }, []);

  return (
    <li
      className={cn(
        "flex items-center gap-2 rounded-md border border-border/60 bg-muted/30 px-3 py-2 text-sm",
        deleteMutation.isPending && "opacity-60",
      )}
      aria-label={`Archivo: ${file.filename}`}
    >
      {/* Icon */}
      <span className="shrink-0 text-base" aria-hidden>
        {fileIcon(file.contentType)}
      </span>

      {/* Name + meta */}
      <div className="min-w-0 flex-1">
        <p
          className="truncate font-medium leading-tight"
          title={file.filename}
        >
          {file.filename}
        </p>
        <p className="text-xs text-muted-foreground">
          {formatBytes(file.sizeBytes)} · {formatUploadedAt(file.uploadedAt)}
        </p>
      </div>

      {/* Error state */}
      {deleteMutation.isError && !confirming && (
        <span className="text-xs text-destructive" aria-live="polite">
          Error al eliminar
        </span>
      )}
      {downloadMutation.isError && (
        <span className="text-xs text-destructive" aria-live="polite">
          Error al descargar
        </span>
      )}

      {/* Confirm delete inline */}
      {confirming ? (
        <div className="flex items-center gap-1">
          <span className="text-xs text-muted-foreground">¿Eliminar?</span>
          <Button
            type="button"
            variant="destructive"
            size="sm"
            onClick={handleDeleteConfirm}
            disabled={deleteMutation.isPending}
            aria-label="Confirmar eliminación"
          >
            Sí
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleDeleteCancel}
            aria-label="Cancelar eliminación"
          >
            No
          </Button>
        </div>
      ) : (
        <>
          {/* Download */}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={handleDownload}
            disabled={downloadMutation.isPending}
            aria-label={`Descargar ${file.filename}`}
            title="Descargar"
          >
            {downloadMutation.isPending ? (
              <span className="text-xs">…</span>
            ) : (
              <span aria-hidden className="text-base">⬇</span>
            )}
          </Button>

          {/* Delete */}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={handleDeleteRequest}
            disabled={deleteMutation.isPending}
            aria-label={`Eliminar ${file.filename}`}
            title="Eliminar"
            className="text-muted-foreground hover:text-destructive"
          >
            <span aria-hidden className="text-base">✕</span>
          </Button>
        </>
      )}
    </li>
  );
}

interface UploadingRowProps {
  filename: string;
  error?: string;
  onRetry?: () => void;
  onRemove?: () => void;
}

function UploadingRow({ filename, error, onRetry, onRemove }: UploadingRowProps) {
  return (
    <li
      className="flex items-center gap-2 rounded-md border border-border/60 bg-muted/20 px-3 py-2 text-sm"
      aria-label={error ? `Error subiendo ${filename}` : `Subiendo ${filename}`}
    >
      <span className="shrink-0 text-base" aria-hidden>
        {error ? "⚠️" : "📤"}
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate font-medium leading-tight text-muted-foreground" title={filename}>
          {filename}
        </p>
        {error ? (
          <p className="text-xs text-destructive" aria-live="polite">
            {error === "STORAGE_UNAVAILABLE"
              ? "Almacenamiento no disponible"
              : "Error al subir"}
          </p>
        ) : (
          <p className="text-xs text-muted-foreground" aria-live="polite">
            Subiendo…
          </p>
        )}
      </div>
      {error && onRetry && (
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={onRetry}
          aria-label={`Reintentar subida de ${filename}`}
        >
          Reintentar
        </Button>
      )}
      {onRemove && (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={onRemove}
          aria-label={`Quitar ${filename} de la cola`}
          className="text-muted-foreground"
        >
          <span aria-hidden>✕</span>
        </Button>
      )}
    </li>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

interface PendingUpload {
  key: string; // stable key for list rendering
  file: File;
  error?: string;
}

interface BioRepoInputsProps {
  doctorId: string;
  initialDoctor: DoctorDetail;
  /** W4: callback to lift autosave status to page-level FloatingAutosaveIndicator (canon §2.6) */
  onAutosaveStatusChange?: (status: import("@/hooks/use-autosave").AutosaveStatus) => void;
}

export function BioRepoInputs({ doctorId, initialDoctor, onAutosaveStatusChange }: BioRepoInputsProps) {
  const uid = useId();
  const [notes, setNotes] = useState(initialDoctor.bioInputsNotes ?? "");
  const [links, setLinks] = useState<string[]>(initialDoctor.bioLinks ?? []);
  const [linkInput, setLinkInput] = useState("");
  const [linkError, setLinkError] = useState<string | null>(null);
  const [pendingUploads, setPendingUploads] = useState<PendingUpload[]>([]);

  const patchMutation = usePatchDoctor(doctorId);
  const bioFilesQuery = useBioFiles(doctorId);
  const uploadMutation = useBioFileUpload(doctorId);

  // ── Autosave (notes + links) — W4: emit status via onAutosaveStatusChange for page-level
  // FloatingAutosaveIndicator singleton (canon §2.6). Both schedules emit to same callback;
  // the page-level component handles priority (saving > saved > error > idle).
  const { schedule: scheduleNotesSave, status: notesStatus } = useAutosave({
    saveFn: async (value: string) => {
      await patchMutation.mutateAsync({ bioInputsNotes: value });
    },
    debounceMs: 600,
  });

  const { schedule: scheduleLinksSave, status: linksStatus } = useAutosave({
    saveFn: async (value: string[]) => {
      await patchMutation.mutateAsync({ bioLinks: value });
    },
    debounceMs: 600,
  });

  // ── Emit combined autosave status to page-level FloatingAutosaveIndicator (W4)
  // Priority: saving > error > saved > idle
  useEffect(() => {
    if (!onAutosaveStatusChange) return;
    const statuses = [notesStatus, linksStatus];
    if (statuses.includes("saving")) { onAutosaveStatusChange("saving"); return; }
    if (statuses.includes("error")) { onAutosaveStatusChange("error"); return; }
    if (statuses.includes("saved")) { onAutosaveStatusChange("saved"); return; }
    onAutosaveStatusChange("idle");
  }, [notesStatus, linksStatus, onAutosaveStatusChange]);

  // ── Notes handler
  const handleNotesChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setNotes(e.target.value);
      scheduleNotesSave(e.target.value);
    },
    [scheduleNotesSave],
  );

  // ── Link handlers (Zod URL validation)
  const handleAddLink = useCallback(() => {
    const raw = linkInput.trim();
    if (!raw) return;
    const result = linkSchema.safeParse(raw);
    if (!result.success) {
      setLinkError("Ingresa una URL válida (https://...)");
      return;
    }
    setLinkError(null);
    const updated = [...links, raw];
    setLinks(updated);
    setLinkInput("");
    scheduleLinksSave(updated);
  }, [linkInput, links, scheduleLinksSave]);

  const handleRemoveLink = useCallback(
    (idx: number) => {
      const updated = links.filter((_, i) => i !== idx);
      setLinks(updated);
      scheduleLinksSave(updated);
    },
    [links, scheduleLinksSave],
  );

  const handleLinkInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setLinkInput(e.target.value);
      if (linkError) setLinkError(null);
    },
    [linkError],
  );

  const handleLinkKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        e.preventDefault();
        handleAddLink();
      }
    },
    [handleAddLink],
  );

  // ── File upload handler
  const handleFilesChange = useCallback(
    (files: File[]) => {
      for (const file of files) {
        // Validate type + size inline
        if (!ALLOWED_TYPES.includes(file.type)) {
          const pendingKey = `${file.name}-${Date.now()}`;
          setPendingUploads((prev) => [
            ...prev,
            { key: pendingKey, file, error: "Tipo de archivo no permitido" },
          ]);
          continue;
        }
        if (file.size > MAX_SIZE_BYTES) {
          const pendingKey = `${file.name}-${Date.now()}`;
          setPendingUploads((prev) => [
            ...prev,
            { key: pendingKey, file, error: "El archivo supera 10 MB" },
          ]);
          continue;
        }

        const pendingKey = `${file.name}-${Date.now()}`;
        // Add as uploading
        setPendingUploads((prev) => [...prev, { key: pendingKey, file }]);

        uploadMutation.mutate(file, {
          onSuccess: () => {
            setPendingUploads((prev) =>
              prev.filter((p) => p.key !== pendingKey),
            );
          },
          onError: (err: unknown) => {
            const errorCode =
              err instanceof Error && err.message === "STORAGE_UNAVAILABLE"
                ? "STORAGE_UNAVAILABLE"
                : "UPLOAD_ERROR";
            setPendingUploads((prev) =>
              prev.map((p) =>
                p.key === pendingKey ? { ...p, error: errorCode } : p,
              ),
            );
          },
        });
      }
    },
    [uploadMutation],
  );

  const handleRetryUpload = useCallback(
    (pendingKey: string, file: File) => {
      // Reset error state
      setPendingUploads((prev) =>
        prev.map((p) => (p.key === pendingKey ? { ...p, error: undefined } : p)),
      );
      uploadMutation.mutate(file, {
        onSuccess: () => {
          setPendingUploads((prev) =>
            prev.filter((p) => p.key !== pendingKey),
          );
        },
        onError: (err: unknown) => {
          const errorCode =
            err instanceof Error && err.message === "STORAGE_UNAVAILABLE"
              ? "STORAGE_UNAVAILABLE"
              : "UPLOAD_ERROR";
          setPendingUploads((prev) =>
            prev.map((p) =>
              p.key === pendingKey ? { ...p, error: errorCode } : p,
            ),
          );
        },
      });
    },
    [uploadMutation],
  );

  const handleRemovePending = useCallback((pendingKey: string) => {
    setPendingUploads((prev) => prev.filter((p) => p.key !== pendingKey));
  }, []);

  // ── Render ────────────────────────────────────────────────────────────────

  const bioFiles: BioFile[] = bioFilesQuery.data ?? [];

  return (
    <section
      aria-labelledby={`${uid}-bio-repo-heading`}
      className={cn(
        "space-y-5 rounded-lg border-l-2 border-agent-lisa bg-card p-4",
      )}
    >
      {/* Header */}
      <div>
        <h2
          id={`${uid}-bio-repo-heading`}
          className="text-sm font-semibold"
        >
          Material para bio
        </h2>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Agrega notas, archivos y enlaces que describan la trayectoria del integrante.
          Con esta información se generará su bio.
        </p>
      </div>

      {/* Notes — Textarea atom (canon §D1: no raw <textarea>) */}
      <div className="space-y-1">
        <Label htmlFor={`${uid}-bio-notes`}>Notas</Label>
        <Textarea
          id={`${uid}-bio-notes`}
          value={notes}
          onChange={handleNotesChange}
          rows={4}
          placeholder="Agrega información sobre formación, experiencia, logros, áreas de interés..."
          aria-label="Notas para la bio"
          className="resize-none"
        />
      </div>

      {/* File attachments */}
      <div className="space-y-2">
        <Label>Archivos adjuntos</Label>

        {/* Dropzone */}
        <Dropzone
          accept=".pdf,.jpg,.jpeg,.png,.docx"
          maxSizeBytes={MAX_SIZE_BYTES}
          multiple
          description="Arrastra o haz clic · PDF, JPG, PNG, DOCX · hasta 10 MB"
          onFilesChange={handleFilesChange}
        />

        {/* Loading skeleton */}
        {bioFilesQuery.isLoading && (
          <ul className="space-y-1.5" aria-label="Cargando archivos" aria-busy>
            {[1, 2].map((n) => (
              <li key={n}>
                <Skeleton className="h-11 w-full rounded-md" />
              </li>
            ))}
          </ul>
        )}

        {/* Error loading list */}
        {bioFilesQuery.isError && (
          <p className="text-xs text-destructive" role="alert">
            No se pudieron cargar los archivos adjuntos.
          </p>
        )}

        {/* Pending uploads (in-progress or errored) */}
        {pendingUploads.length > 0 && (
          <ul className="space-y-1.5" aria-label="Archivos en proceso">
            {pendingUploads.map((p) => (
              <UploadingRow
                key={p.key}
                filename={p.file.name}
                error={p.error}
                onRetry={
                  p.error
                    ? () => handleRetryUpload(p.key, p.file)
                    : undefined
                }
                onRemove={
                  p.error ? () => handleRemovePending(p.key) : undefined
                }
              />
            ))}
          </ul>
        )}

        {/* Persisted file rows */}
        {!bioFilesQuery.isLoading && bioFiles.length > 0 && (
          <ul className="space-y-1.5" aria-label="Archivos adjuntos">
            {bioFiles.map((f) => (
              <BioFileRow
                key={f.id}
                file={f}
                doctorId={doctorId}
              />
            ))}
          </ul>
        )}

        {/* Empty state */}
        {!bioFilesQuery.isLoading &&
          !bioFilesQuery.isError &&
          bioFiles.length === 0 &&
          pendingUploads.length === 0 && (
            <p className="py-2 text-center text-xs text-muted-foreground">
              Sin archivos adjuntos. Sube documentos para enriquecer la bio.
            </p>
          )}
      </div>

      {/* Link chips (Zod URL validation) */}
      <div className="space-y-2">
        <Label htmlFor={`${uid}-bio-link-input`}>Referencias y enlaces</Label>
        <div className="flex gap-2">
          <Input
            id={`${uid}-bio-link-input`}
            type="url"
            value={linkInput}
            onChange={handleLinkInputChange}
            placeholder="https://..."
            onKeyDown={handleLinkKeyDown}
            aria-label="URL de referencia"
            aria-invalid={!!linkError}
            aria-describedby={linkError ? `${uid}-link-error` : undefined}
          />
          {/* Button atom (canon §D1: no raw <button>) */}
          <Button
            type="button"
            variant="outline"
            onClick={handleAddLink}
            disabled={!linkInput.trim()}
            aria-label="Agregar enlace"
          >
            Agregar
          </Button>
        </div>
        {linkError && (
          <p
            id={`${uid}-link-error`}
            className="text-xs text-destructive"
            role="alert"
          >
            {linkError}
          </p>
        )}
        {links.length > 0 && (
          <ul
            className="flex flex-wrap gap-1.5"
            aria-label="Enlaces agregados"
          >
            {links.map((link, idx) => (
              // stable key: combine url + index (urls may repeat in edge cases, idx disambiguates)
              <li
                key={`link-${idx}-${link}`}
                className="inline-flex items-center gap-1 rounded-full bg-muted px-2.5 py-0.5 text-xs"
              >
                <a
                  href={link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="max-w-[200px] truncate hover:underline"
                >
                  {link}
                </a>
                <button
                  type="button"
                  onClick={() => handleRemoveLink(idx)}
                  className="text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring rounded-full"
                  aria-label={`Eliminar enlace ${link}`}
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

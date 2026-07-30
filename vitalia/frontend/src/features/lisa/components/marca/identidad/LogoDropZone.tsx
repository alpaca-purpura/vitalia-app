// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
"use client";

/**
 * LogoDropZone.tsx — Drag-and-drop logo upload component.
 *
 * Client-side validation:
 *   - Max 5 MB (lisa_marca_logo_oversized telemetry on reject)
 *   - Formats: image/png, image/jpeg, image/webp, image/svg+xml
 * On valid file: calls onUpload(file) for parent to handle S3 upload.
 * Shows live preview of current logo or newly selected file.
 *
 * Accessible:
 *   - Visible drag-and-drop zone with keyboard activation (Space/Enter on button)
 *   - aria-live="polite" error announcements
 *
 * Spanish neutro LatAm — no voseo.
 *
 * T-5 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-5 A2
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */


import { useCallback, useRef, useState } from "react";
import Image from "next/image";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const MAX_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB
const ALLOWED_TYPES = new Set([
  "image/png",
  "image/jpeg",
  "image/webp",
  "image/svg+xml",
]);

export interface LogoDropZoneProps {
  /** Current logo URL (S3 presigned or CDN). */
  logoUrl?: string | null;
  /** Called when a valid file is selected. Parent handles the actual upload. */
  onUpload: (file: File) => void;
  /** Called when client-side validation fails. Receives error message. */
  onValidationError?: (message: string) => void;
  isUploading?: boolean;
  /** Called when the user removes the persisted logo. */
  onDelete?: () => void;
  isDeleting?: boolean;
  className?: string;
}

/**
 * LogoDropZone — drag-and-drop + click-to-upload logo area with live preview.
 */
export function LogoDropZone({
  logoUrl,
  onUpload,
  onValidationError,
  isUploading = false,
  onDelete,
  isDeleting = false,
  className,
}: LogoDropZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  const validateAndUpload = useCallback(
    (file: File) => {
      // Reset previous error
      setValidationError(null);

      // Size check
      if (file.size > MAX_SIZE_BYTES) {
        const msg = "El archivo supera el límite de 5 MB. Selecciona una imagen más pequeña.";
        setValidationError(msg);
        onValidationError?.(msg);
        return;
      }

      // Format check
      if (!ALLOWED_TYPES.has(file.type)) {
        const msg =
          "Formato no permitido. Usa PNG, JPEG, WebP o SVG.";
        setValidationError(msg);
        onValidationError?.(msg);
        return;
      }

      // Show local preview
      const objectUrl = URL.createObjectURL(file);
      setPreviewUrl(objectUrl);

      onUpload(file);
    },
    [onUpload, onValidationError],
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) validateAndUpload(file);
      // Reset input so same file can be selected again
      e.target.value = "";
    },
    [validateAndUpload],
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      const file = e.dataTransfer.files?.[0];
      if (file) validateAndUpload(file);
    },
    [validateAndUpload],
  );

  const displayUrl = previewUrl ?? logoUrl;

  return (
    <div className={cn("flex flex-col gap-2", className)}>
      {/* Hidden file input */}
      <input
        ref={inputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp,image/svg+xml"
        className="sr-only"
        aria-label="Seleccionar archivo de logo"
        onChange={handleInputChange}
        tabIndex={-1}
      />

      {/* Drop zone */}
      <button
        type="button"
        role="button"
        aria-label={
          displayUrl
            ? "Cambiar logo de la clínica (arrastra o haz clic)"
            : "Subir logo de la clínica (arrastra o haz clic)"
        }
        onClick={() => inputRef.current?.click()}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        disabled={isUploading}
        aria-busy={isUploading}
        className={cn(
          "relative flex min-h-[100px] w-full flex-col items-center justify-center gap-2",
          "rounded-lg border-2 border-dashed transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          isDragOver
            ? "border-primary bg-primary/5"
            : "border-border bg-muted/20 hover:border-primary/50 hover:bg-muted/40",
          isUploading && "cursor-not-allowed opacity-60",
        )}
      >
        {displayUrl ? (
          <div className="flex flex-col items-center gap-2 p-3">
            <div className="relative h-14 w-14 overflow-hidden rounded-lg border border-border bg-muted">
              <Image
                src={displayUrl}
                alt="Logo de la clínica"
                fill
                className="object-contain"
                sizes="56px"
              />
            </div>
            <span className="text-xs text-muted-foreground">
              {isUploading ? "Subiendo..." : "Haz clic o arrastra para cambiar"}
            </span>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-1.5 p-4 text-center">
            {/* Upload icon */}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="text-muted-foreground"
              aria-hidden="true"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <p className="text-sm font-medium text-foreground">
              Agrega el logo de tu clínica
            </p>
            <p className="text-xs text-muted-foreground">
              PNG, JPEG, WebP o SVG · Máximo 5 MB
            </p>
          </div>
        )}
      </button>

      {/* Validation error */}
      {validationError && (
        <p
          role="alert"
          aria-live="polite"
          className="text-xs text-destructive"
        >
          {validationError}
        </p>
      )}

      {/* Change / remove actions when a logo exists — juntas, no en el fondo de la página */}
      {displayUrl && !isUploading && (
        <div className="flex items-center gap-1">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="text-xs text-muted-foreground"
            onClick={() => inputRef.current?.click()}
          >
            Cambiar logo
          </Button>
          {onDelete && logoUrl && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="text-xs text-destructive hover:text-destructive"
              onClick={onDelete}
              disabled={isDeleting}
              aria-label="Eliminar logo de la clínica"
            >
              {isDeleting ? "Eliminando..." : "Eliminar logo"}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

LogoDropZone.displayName = "LogoDropZone";

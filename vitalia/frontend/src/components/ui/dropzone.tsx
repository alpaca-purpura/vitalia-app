// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
"use client";
/**
 * dropzone.tsx — Accessible file dropzone component (Shadcn-style).
 *
 * Based on diragb/shadcn-dropzone pattern (native drag-and-drop + HTML file input).
 * No external react-dropzone dependency — uses browser DragEvent + FileList APIs.
 *
 * Features:
 *   - Multi-file support
 *   - Click-to-select files
 *   - Drag-and-drop
 *   - Lists files: name / size / remove button
 *   - Accept filter (e.g., "image/*", ".pdf,.jpg,.png,.docx")
 *   - Max file size validation (maxSizeBytes)
 *   - Accessible: keyboard operable, aria-live region for file list
 *
 * Spanish copy: "Arrastra o haz clic para subir · {accept} · hasta {maxSizeMb} MB"
 *
 * Used by:
 *   - AvatarUploader (image/*, 10MB)
 *   - BioRepoInputs (PDF/JPG/PNG/DOCX, 10MB)
 *
 * T-FE-2 vitalia-fase2-lisa-doctores
 * spec_anchor: 03-arch-fe.md § Dropzone install + 01-spec.md § Microcopy
 * downstream-regression-na: brand-local vitalia UI component
 */

import {
  useRef,
  useState,
  useCallback,
  type DragEvent,
  type ChangeEvent,
} from "react";
import { cn } from "@/lib/utils";

// ── Types ─────────────────────────────────────────────────name──────────────────

export interface DropzoneFile {
  file: File;
  /** Client-only ID for stable key in lists */
  id: string;
  /** Validation error message (if any) */
  error?: string;
}

export interface DropzoneProps {
  /** Accepted MIME types / extensions — passed to <input accept=""> */
  accept?: string;
  /** Max file size in bytes (default: 10MB) */
  maxSizeBytes?: number;
  /** Whether multiple files are allowed (default: true) */
  multiple?: boolean;
  /** Callback when files change (includes all current accepted files) */
  onFilesChange?: (files: File[]) => void;
  /** Additional className for the dropzone area */
  className?: string;
  /** Description text shown in the drop area */
  description?: string;
  /** Disabled state */
  disabled?: boolean;
}

const DEFAULT_MAX_SIZE = 10 * 1024 * 1024; // 10MB

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

let idCounter = 0;
function nextId(): string {
  return `dz-${++idCounter}`;
}

// ── Component ─────────────────────────────────────────────────────────────────

export function Dropzone({
  accept,
  maxSizeBytes = DEFAULT_MAX_SIZE,
  multiple = true,
  onFilesChange,
  className,
  description,
  disabled = false,
}: DropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<DropzoneFile[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = useCallback(
    (newFiles: FileList | null) => {
      if (!newFiles || newFiles.length === 0) return;

      const toAdd: DropzoneFile[] = [];
      for (const file of Array.from(newFiles)) {
        const error =
          file.size > maxSizeBytes
            ? `Archivo demasiado grande (máx. ${formatBytes(maxSizeBytes)})`
            : undefined;
        toAdd.push({ file, id: nextId(), error });
      }

      const updated = multiple ? [...files, ...toAdd] : toAdd.slice(0, 1);
      setFiles(updated);
      onFilesChange?.(updated.filter((f) => !f.error).map((f) => f.file));
    },
    [files, maxSizeBytes, multiple, onFilesChange],
  );

  const removeFile = useCallback(
    (id: string) => {
      const updated = files.filter((f) => f.id !== id);
      setFiles(updated);
      onFilesChange?.(updated.filter((f) => !f.error).map((f) => f.file));
    },
    [files, onFilesChange],
  );

  // Drag event handlers
  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (!disabled) setIsDragging(true);
  }, [disabled]);

  const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);
      if (disabled) return;
      addFiles(e.dataTransfer.files);
    },
    [addFiles, disabled],
  );

  const handleInputChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      addFiles(e.target.files);
      // Reset input so the same file can be re-added after removal
      if (inputRef.current) inputRef.current.value = "";
    },
    [addFiles],
  );

  const handleClick = useCallback(() => {
    if (!disabled) inputRef.current?.click();
  }, [disabled]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if ((e.key === "Enter" || e.key === " ") && !disabled) {
        e.preventDefault();
        inputRef.current?.click();
      }
    },
    [disabled],
  );

  const defaultDescription =
    description ?? `Arrastra o haz clic para subir · hasta ${formatBytes(maxSizeBytes)}`;

  return (
    <div className="space-y-2">
      {/* Drop area */}
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label="Área para subir archivos"
        aria-disabled={disabled}
        data-testid="dropzone-area"
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "relative flex flex-col items-center justify-center gap-2",
          "rounded-lg border-2 border-dashed border-border/60 p-6",
          "text-center cursor-pointer transition-colors",
          "hover:border-primary/50 hover:bg-primary/5",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
          isDragging && "border-primary bg-primary/5",
          disabled && "opacity-50 cursor-not-allowed pointer-events-none",
          className,
        )}
      >
        <div className="text-2xl" aria-hidden="true">
          📎
        </div>
        <div className="text-sm text-muted-foreground">{defaultDescription}</div>
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          className="sr-only"
          tabIndex={-1}
          onChange={handleInputChange}
          disabled={disabled}
          aria-hidden="true"
        />
      </div>

      {/* File list */}
      {files.length > 0 && (
        <ul
          className="space-y-1"
          aria-label="Archivos seleccionados"
          aria-live="polite"
        >
          {files.map((df) => (
            <li
              key={df.id}
              className={cn(
                "flex items-center justify-between gap-2 rounded-md px-3 py-2 text-sm",
                "bg-muted/50 border border-border/40",
                df.error && "border-destructive/50 bg-destructive/5",
              )}
            >
              <div className="flex items-center gap-2 min-w-0">
                <span aria-hidden="true" className="text-base">
                  📄
                </span>
                <div className="min-w-0">
                  <p className="truncate font-medium">{df.file.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatBytes(df.file.size)}
                    {df.error && (
                      <span className="ml-2 text-destructive">{df.error}</span>
                    )}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile(df.id);
                }}
                className={cn(
                  "flex-shrink-0 rounded-full p-0.5 text-muted-foreground",
                  "hover:text-foreground hover:bg-muted transition-colors",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                )}
                aria-label={`Eliminar ${df.file.name}`}
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

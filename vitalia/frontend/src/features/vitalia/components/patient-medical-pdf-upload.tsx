// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * PatientMedicalPdfUpload — file upload component for medical PDF ingestion.
 *
 * Converts File to base64, calls usePatientUploadPdf mutation.
 * Shows upload state: idle / uploading / success / error.
 *
 * @architecture-group vitalia-ui-strings
 */
"use client";

import { useState, useRef, useCallback } from "react";
import { cn } from "@/lib/cn";
import { usePatientUploadPdf } from "@/features/vitalia/api/use-patient-upload-pdf";

export interface PatientMedicalPdfUploadProps {
  patientId: string;
  onSuccess?: (jobId: string) => void;
  className?: string;
}

type UploadStatus = "idle" | "reading" | "uploading" | "success" | "error";

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      // Strip data URI prefix: "data:application/pdf;base64,..."
      const base64 = result.split(",")[1] ?? result;
      resolve(base64);
    };
    reader.onerror = () => reject(new Error("Error leyendo el archivo"));
    reader.readAsDataURL(file);
  });
}

export function PatientMedicalPdfUpload({
  patientId,
  onSuccess,
  className,
}: PatientMedicalPdfUploadProps) {
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const mutation = usePatientUploadPdf(patientId);

  const processFile = useCallback(
    async (file: File) => {
      if (file.type !== "application/pdf") {
        setErrorMessage("Solo se aceptan archivos PDF.");
        setStatus("error");
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        setErrorMessage("El archivo no puede superar 10 MB.");
        setStatus("error");
        return;
      }

      setStatus("reading");
      setErrorMessage(null);

      try {
        const base64Content = await fileToBase64(file);
        setStatus("uploading");

        const result = await mutation.mutateAsync({
          file_name: file.name,
          content_type: "application/pdf",
          base64_content: base64Content,
        });

        setJobId(result.extraction_job_id);
        setStatus("success");
        onSuccess?.(result.extraction_job_id);
      } catch (err) {
        const msg =
          err instanceof Error ? err.message : "Error al subir el archivo.";
        setErrorMessage(msg);
        setStatus("error");
      }
    },
    [mutation, onSuccess],
  );

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        void processFile(file);
        // Reset input so same file can be re-selected after error
        e.target.value = "";
      }
    },
    [processFile],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files?.[0];
      if (file) {
        void processFile(file);
      }
    },
    [processFile],
  );

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleClick = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const handleReset = useCallback(() => {
    setStatus("idle");
    setErrorMessage(null);
    setJobId(null);
  }, []);

  const isProcessing = status === "reading" || status === "uploading";

  return (
    <div className={cn("flex flex-col gap-3", className)}>
      {/* Drop zone */}
      {status === "idle" || status === "error" ? (
        <div
          role="button"
          tabIndex={0}
          onClick={handleClick}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              handleClick();
            }
          }}
          aria-label="Subir historial médico en PDF. Haz clic o arrastra el archivo aquí."
          className={cn(
            "rounded-lg border-2 border-dashed p-8 text-center cursor-pointer transition-colors",
            "focus:outline-none focus:ring-2 focus:ring-blue-500",
            isDragging
              ? "border-blue-400 bg-blue-50"
              : "border-gray-300 bg-gray-50 hover:border-gray-400 hover:bg-gray-100",
          )}
        >
          <p className="text-sm font-medium text-gray-700">
            Arrastra un PDF aquí o{" "}
            <span className="text-blue-600 underline">
              selecciona un archivo
            </span>
          </p>
          <p className="text-xs text-gray-400 mt-1">PDF — máx. 10 MB</p>
        </div>
      ) : null}

      {/* Processing state */}
      {isProcessing && (
        <div
          className="rounded-lg border border-blue-200 bg-blue-50 p-6 text-center"
          role="status"
          aria-busy={true}
          aria-live="polite"
        >
          <div
            className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-blue-200 border-t-blue-600 mb-2"
            aria-hidden="true"
          />
          <p className="text-sm text-blue-700">
            {status === "reading" ? "Leyendo archivo..." : "Subiendo PDF..."}
          </p>
        </div>
      )}

      {/* Success state */}
      {status === "success" && (
        <div
          className="rounded-lg border border-green-200 bg-green-50 p-6 text-center"
          role="status"
          aria-live="polite"
        >
          <p className="text-sm font-medium text-green-700">
            PDF subido exitosamente.
          </p>
          {jobId && (
            <p className="text-xs text-green-600 mt-1 font-mono">
              Job ID: {jobId}
            </p>
          )}
          <button
            type="button"
            onClick={handleReset}
            className="mt-3 text-xs text-green-700 underline hover:no-underline focus:outline-none focus:ring-2 focus:ring-green-500 rounded"
          >
            Subir otro PDF
          </button>
        </div>
      )}

      {/* Error state */}
      {status === "error" && errorMessage && (
        <div
          className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 flex items-center justify-between"
          role="alert"
          aria-live="polite"
        >
          <p className="text-sm text-red-700">{errorMessage}</p>
          <button
            type="button"
            onClick={handleReset}
            className="text-xs text-red-600 underline hover:no-underline ml-4 shrink-0 focus:outline-none focus:ring-2 focus:ring-red-500 rounded"
          >
            Reintentar
          </button>
        </div>
      )}

      {/* Hidden file input */}
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        onChange={handleFileChange}
        className="sr-only"
        aria-hidden="true"
        tabIndex={-1}
      />
    </div>
  );
}

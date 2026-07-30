// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
"use client";
/**
 * AvatarUploader.tsx — Doctor avatar upload via proxy (D-3).
 *
 * Uses Dropzone (accept="image/*", maxSizeBytes=10MB) → proxy POST to
 * /api/v1/vitalia/assets/upload (kind=avatar) → PATCH doctor avatarKey.
 *
 * Business rule (avatar-presigned-direct-r2 → corrected per D-3):
 *   Proxy upload to /api/v1/vitalia/assets/upload (NOT presigned).
 *
 * T-FE-2 vitalia-fase2-lisa-doctores
 * spec_anchor: 03-arch-fe.md § AvatarUploader + 03-arch.md § D-3
 * downstream-regression-na: brand-local vitalia feature component
 */

import { useState, useCallback } from "react";
import Image from "next/image";
import { useAvatarUpload } from "../../../api/staff";
import { Dropzone } from "@/components/ui/dropzone";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface AvatarUploaderProps {
  doctorId: string;
  currentAvatarUrl: string | null;
  onSuccess?: (avatarUrl: string) => void;
  className?: string;
}

const AVATAR_MAX_SIZE = 10 * 1024 * 1024; // 10MB

export function AvatarUploader({
  doctorId,
  currentAvatarUrl,
  onSuccess,
  className,
}: AvatarUploaderProps) {
  const [showDropzone, setShowDropzone] = useState(false);
  const [localPreview, setLocalPreview] = useState<string | null>(null);

  const uploadMutation = useAvatarUpload(doctorId);

  const handleFilesChange = useCallback(
    (files: File[]) => {
      const file = files[0];
      if (!file) return;

      // Local preview
      const objectUrl = URL.createObjectURL(file);
      setLocalPreview(objectUrl);
      setShowDropzone(false);

      // Upload
      uploadMutation.mutate(file, {
        onSuccess: ({ url }) => {
          URL.revokeObjectURL(objectUrl);
          setLocalPreview(null);
          onSuccess?.(url);
        },
        onError: () => {
          URL.revokeObjectURL(objectUrl);
          setLocalPreview(null);
        },
      });
    },
    [uploadMutation, onSuccess],
  );

  const displayUrl = localPreview ?? currentAvatarUrl;
  const isUploading = uploadMutation.isPending;

  return (
    <div className={cn("flex flex-col items-center gap-2", className)}>
      {/* Avatar circle */}
      <button
        type="button"
        onClick={() => setShowDropzone((s) => !s)}
        aria-label={
          isUploading ? "Subiendo imagen..." : "Cambiar foto de perfil"
        }
        className={cn(
          "relative w-20 h-20 rounded-full overflow-hidden",
          "border-2 border-border/60 hover:border-[var(--agent-lisa)] transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
          "group cursor-pointer",
        )}
      >
        {isUploading ? (
          <Skeleton className="w-full h-full rounded-full" />
        ) : displayUrl ? (
          <Image
            src={displayUrl}
            alt="Avatar del integrante"
            fill
            className="object-cover"
            sizes="80px"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-[color-mix(in_srgb,var(--agent-lisa)_15%,transparent)]">
            <span
              className="text-2xl text-[var(--agent-lisa)]"
              aria-hidden="true"
            >
              👤
            </span>
          </div>
        )}
        {/* Overlay on hover */}
        <div
          className={cn(
            "absolute inset-0 bg-black/40 flex items-center justify-center",
            "opacity-0 group-hover:opacity-100 transition-opacity",
          )}
          aria-hidden="true"
        >
          <span className="text-white text-xs font-medium">Cambiar</span>
        </div>
      </button>

      {/* Error state */}
      {uploadMutation.isError && (
        <p className="text-xs text-destructive" role="alert">
          Error al subir imagen. Vuelve a intentarlo.
        </p>
      )}

      {/* Dropzone (conditional) */}
      {showDropzone && (
        <Dropzone
          accept="image/*"
          maxSizeBytes={AVATAR_MAX_SIZE}
          multiple={false}
          onFilesChange={handleFilesChange}
          description="Arrastra o haz clic · JPG, PNG, WEBP · hasta 10 MB"
          className="w-full min-w-[220px]"
        />
      )}
    </div>
  );
}

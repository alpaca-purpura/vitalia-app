// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * ImageAnalysisCard.tsx — Stub image analysis card for inbox messages (Slice 1).
 *
 * Slice 1: shows image preview + "Adrián está analizando la imagen…" placeholder.
 * Slice 2 will replace with real analysis output.
 *
 * Note: uses <img> via Next.js Image if available for optimization,
 * falls back to native img with safe alt text.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import Image from "next/image";
import { cn } from "@/lib/cn";
import { INBOX_COPY } from "../../lib/copy";

export interface ImageAnalysisCardProps {
  /** CDN URL for the image */
  mediaUrl: string;
  className?: string;
}

/**
 * ImageAnalysisCard — stub UI for Slice 1 image messages.
 */
export function ImageAnalysisCard({
  mediaUrl,
  className,
}: ImageAnalysisCardProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-2 rounded-xl overflow-hidden border vt-border",
        "vt-bg-muted max-w-xs",
        className,
      )}
      role="figure"
      aria-label={INBOX_COPY.multimedia.imagePlaceholder.ariaLabel}
    >
      {/* Image preview */}
      <div className="relative w-full aspect-video bg-black/5 overflow-hidden">
        <Image
          src={mediaUrl}
          alt={INBOX_COPY.multimedia.imagePlaceholder.ariaLabel}
          fill
          className="object-cover"
          sizes="(max-width: 320px) 100vw, 320px"
        />
      </div>

      {/* Stub analysis placeholder */}
      <div className="px-3 pb-3 flex flex-col gap-1">
        <p className="text-xs font-semibold vt-text">
          {INBOX_COPY.multimedia.imagePlaceholder.heading}
        </p>
        <p className="text-xs vt-text-muted">
          {INBOX_COPY.multimedia.imagePlaceholder.body}
        </p>
      </div>
    </div>
  );
}

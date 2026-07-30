// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * MobileBottomSheet.tsx — Sheet side="bottom" wrapper for mobile (<md).
 * T-16 vitalia-fase2-valeria-agenda
 *
 * Renders a bottom drawer occupying 95vh on mobile viewports.
 * Drag-handle visible at top for discoverability.
 * Desktop: delegates rendering to its consumer (returns children directly).
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 03-arch.md § 3.2 + 06-tickets.yaml T-16
 */

import * as React from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface MobileBottomSheetProps {
  /** Controls whether the sheet is open. */
  open: boolean;
  /** Callback when the sheet requests closure (overlay click, Esc). */
  onOpenChange: (open: boolean) => void;
  /** Accessible sheet title (required for screen readers). */
  title: string;
  /** Optional description shown below title for screen readers. */
  description?: string;
  /** Content rendered inside the sheet. */
  children: React.ReactNode;
  /** Additional className for the SheetContent wrapper. */
  className?: string;
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * MobileBottomSheet — wraps Shadcn Sheet in a bottom-drawer 95vh layout.
 *
 * Usage:
 * ```tsx
 * <MobileBottomSheet
 *   open={open}
 *   onOpenChange={setOpen}
 *   title="Nueva cita"
 * >
 *   <CrearCitaForm ... />
 * </MobileBottomSheet>
 * ```
 */
export function MobileBottomSheet({
  open,
  onOpenChange,
  title,
  description,
  children,
  className,
}: MobileBottomSheetProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="bottom"
        className={cn(
          // 95vh height, max-height guard for very tall content
          "h-[95vh] max-h-[95vh]",
          // Remove default p-6 and handle layout manually
          "p-0 overflow-hidden",
          // Rounded top corners (sheet comes from bottom)
          "rounded-t-2xl",
          className,
        )}
        aria-describedby={description ? "mobile-sheet-description" : undefined}
      >
        {/* Drag handle visual cue — accessibility: decorative */}
        <div
          className="flex justify-center pt-3 pb-1"
          aria-hidden="true"
        >
          <div className="w-10 h-1 rounded-full bg-muted-foreground/30" />
        </div>

        {/* Visually hidden header for screen readers */}
        <SheetHeader className="sr-only">
          <SheetTitle>{title}</SheetTitle>
          {description && (
            <SheetDescription id="mobile-sheet-description">
              {description}
            </SheetDescription>
          )}
        </SheetHeader>

        {/* Scrollable content area */}
        <div className="h-full overflow-y-auto overscroll-contain">
          {children}
        </div>
      </SheetContent>
    </Sheet>
  );
}

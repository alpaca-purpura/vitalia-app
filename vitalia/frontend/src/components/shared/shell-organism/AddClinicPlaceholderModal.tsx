// cap: shell-organism.shell-vitalia
// story-origin: vitalia-fase1-s3-TBD
"use client";

/**
 * AddClinicPlaceholderModal — "Agregar clínica" placeholder dialog.
 * F1-S3 vitalia-fase1-tenant-switcher — T-6
 *
 * Client Component ("use client") — uses useState for open/close.
 * Uses Shadcn Dialog (installed in this story via `npx shadcn add dialog`).
 *
 * Microcopy verbatim (01-spec.md § 9):
 * - Trigger: "Agregar clínica"
 * - Title: "Próximamente"
 * - Body: "Próximamente: agregar nueva clínica desde Configurar → Mi cuenta"
 * - Close CTA: "Entendido"
 *
 * This is a placeholder — full clinic onboarding flow is deferred to Fase 2.
 *
 * 03-arch.md § 2.6 — implementation verbatim.
 * Named export (no default export) per FSD-Lite enforce.
 * HIPAA-lite: no-phi-scope — no patient data involved.
 * Spanish neutro: no voseo.
 *
 * downstream-regression-na: brand-local shell-organism component; no cross-brand consumers
 */

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

export interface AddClinicPlaceholderModalProps {
  /** Children rendered as trigger element (receives onClick handler) */
  children: React.ReactNode;
}

/**
 * AddClinicPlaceholderModal — controlled dialog wrapper.
 * Renders children as trigger; opens Dialog on click.
 * Client Component.
 */
export function AddClinicPlaceholderModal({
  children,
}: AddClinicPlaceholderModalProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* Trigger — clone children with onClick handler */}
      <span
        role="button"
        tabIndex={0}
        onClick={() => setOpen(true)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") setOpen(true);
        }}
        className="contents"
      >
        {children}
      </span>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Próximamente</DialogTitle>
            <DialogDescription>
              Próximamente: agregar nueva clínica desde Configurar → Mi cuenta
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="default"
              onClick={() => setOpen(false)}
              data-testid="add-clinic-modal-close"
            >
              Entendido
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

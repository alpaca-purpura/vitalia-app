// cap: sales_agent.inbox-handler-mode-occ
// story-origin: TBD
/**
 * ContactSidebar — patient contact details panel for clinical workflows.
 *
 * PHI fields (name, phone, email) are wrapped in PiiMaskedSpan per HIPAA-lite.
 * Per design-system.md: card recipe (vt-bg-surface vt-border).
 *
 * All colors via vt-* CSS classes from globals.css (no hsl literals in TSX).
 */

import { cn } from "@/lib/cn";
import { PiiMaskedSpan } from "../phi/PiiMaskedSpan";
import type { ReactNode } from "react";

export interface ContactInfo {
  /** Patient display ID (hash, not PHI) */
  patientId: string;
  /** Patient name (PHI — will be masked) */
  name?: string | null;
  /** Patient phone (PHI — will be masked) */
  phone?: string | null;
  /** Patient email (PHI — will be masked) */
  email?: string | null;
  /** NPS score (non-PHI) */
  npsScore?: number | null;
  /** Status tag (non-PHI) */
  statusTag?: string | null;
}

export interface ContactSidebarProps {
  /** Contact information to display */
  contact: ContactInfo;
  /** Optional additional children (e.g. action buttons) */
  children?: ReactNode;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Compact contact info panel. PHI fields are masked via PiiMaskedSpan.
 */
export function ContactSidebar({
  contact,
  children,
  className,
}: ContactSidebarProps) {
  return (
    <section
      className={cn(
        "vt-bg-surface vt-border",
        "border rounded-[var(--radius-lg)] p-5 shadow-sm",
        className,
      )}
      aria-label="Información de contacto del paciente"
    >
      <h2 className="text-sm font-semibold vt-text mb-4">Contacto</h2>

      <dl className="space-y-3">
        {contact.name && (
          <div className="flex flex-col gap-0.5">
            <dt className="text-xs vt-text-faint">Nombre</dt>
            <dd>
              <PiiMaskedSpan value={contact.name} fieldType="name" />
            </dd>
          </div>
        )}

        {contact.phone && (
          <div className="flex flex-col gap-0.5">
            <dt className="text-xs vt-text-faint">Teléfono</dt>
            <dd>
              <PiiMaskedSpan value={contact.phone} fieldType="phone" />
            </dd>
          </div>
        )}

        {contact.email && (
          <div className="flex flex-col gap-0.5">
            <dt className="text-xs vt-text-faint">Correo</dt>
            <dd>
              <PiiMaskedSpan value={contact.email} fieldType="email" />
            </dd>
          </div>
        )}

        {contact.statusTag && (
          <div className="flex flex-col gap-0.5">
            <dt className="text-xs vt-text-faint">Estado</dt>
            <dd>
              <span
                className={cn(
                  "inline-flex px-2 py-0.5 text-xs font-medium rounded-[var(--radius-pill)]",
                  "vt-bg-muted vt-text-muted vt-border border",
                )}
              >
                {contact.statusTag}
              </span>
            </dd>
          </div>
        )}
      </dl>

      {children && (
        <div className="mt-4 pt-4 border-t vt-border-soft">{children}</div>
      )}
    </section>
  );
}

// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * AppointmentDrawerAccionesAvanzadasSection.tsx — "Acciones avanzadas" section.
 * T-14 vitalia-fase2-valeria-agenda
 *
 * Renders:
 *   - WhatsApp reminder button (via useSendNotificationMutation)
 *   - Reassign doctor (disabled Q7, Tooltip "Próximamente")
 *   - Change duration (disabled Q7, Tooltip "Próximamente")
 *
 * WhatsApp reminder: POST /api/v1/notify/reminder with template_id="appointment_reminder_24h".
 * BE ComplianceService validates channel — FE shows result (sent/blocked).
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 03-arch.md § 6.6 + § 5.1 + 06-tickets.yaml T-14
 */

import { useState } from "react";
import { MessageSquare, UserCog, Timer, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { Appointment } from "../../types/agenda.types";
import { useSendNotificationMutation } from "../../api/notify";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AppointmentDrawerAccionesAvanzadasSectionProps {
  /** Full appointment detail. */
  appointment: Appointment;
  /** Tenant ID for API calls. */
  tenantId: string;
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * Acciones avanzadas section — WhatsApp reminder + future reassign/duration actions.
 *
 * WhatsApp: ComplianceService on BE may block if channel is not compliant.
 * FE shows success/error accordingly.
 */
export function AppointmentDrawerAccionesAvanzadasSection({
  appointment,
  tenantId,
}: AppointmentDrawerAccionesAvanzadasSectionProps) {
  const [reminderSent, setReminderSent] = useState(false);
  const sendNotification = useSendNotificationMutation(tenantId);

  function handleSendReminder() {
    sendNotification.mutate(
      {
        templateId: "appointment_reminder_24h",
        scheduledFor: new Date().toISOString(),
        locale: "es-419",
      },
      {
        onSuccess: () => {
          setReminderSent(true);
        },
      },
    );
  }

  const isTerminalStatus =
    appointment.appointmentStatus === "COMPLETED" ||
    appointment.appointmentStatus === "CANCELLED" ||
    appointment.appointmentStatus === "NO_SHOW";

  return (
    <div
      className="flex flex-col gap-4"
      data-testid="acciones-avanzadas-section"
    >
      {/* WhatsApp reminder */}
      <div className="flex flex-col gap-2">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Recordatorio
        </span>

        {reminderSent ? (
          <div className="flex items-center gap-2 text-sm text-[color:var(--vitalia-success-color)]">
            <CheckCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
            <span>Recordatorio enviado por WhatsApp</span>
          </div>
        ) : (
          <>
            <Button
              variant="outline"
              size="sm"
              disabled={
                sendNotification.isPending ||
                isTerminalStatus ||
                !appointment.patientPhoneMasked
              }
              onClick={handleSendReminder}
              aria-busy={sendNotification.isPending}
              className="flex items-center gap-2 w-fit"
            >
              <MessageSquare className="h-4 w-4" aria-hidden="true" />
              Enviar recordatorio WhatsApp
            </Button>

            {!appointment.patientPhoneMasked && (
              <p className="text-xs text-muted-foreground">
                El paciente no tiene teléfono registrado.
              </p>
            )}
          </>
        )}

        {/* Error feedback from BE (compliance block or send failure) */}
        {sendNotification.isError && (
          <Alert
            variant="destructive"
            className="py-2"
            role="alert"
            aria-live="assertive"
          >
            <AlertDescription className="text-xs">
              {sendNotification.error?.message ??
                "No se pudo enviar el recordatorio. Intenta nuevamente."}
            </AlertDescription>
          </Alert>
        )}
      </div>

      {/* Advanced actions (disabled — Q7 cement) */}
      <div className="flex flex-col gap-2">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Modificar turno
        </span>
        <div
          className="flex flex-wrap gap-2"
          role="group"
          aria-label="Acciones de modificación del turno (próximamente)"
        >
          {/* Reassign doctor */}
          <Tooltip>
            <TooltipTrigger asChild>
              <span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled
                  aria-disabled="true"
                  className="cursor-not-allowed opacity-50 flex items-center gap-1.5"
                >
                  <UserCog className="h-3.5 w-3.5" aria-hidden="true" />
                  Reasignar médico
                </Button>
              </span>
            </TooltipTrigger>
            <TooltipContent side="top">
              Reasignar médico — próximamente disponible
            </TooltipContent>
          </Tooltip>

          {/* Change duration */}
          <Tooltip>
            <TooltipTrigger asChild>
              <span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled
                  aria-disabled="true"
                  className="cursor-not-allowed opacity-50 flex items-center gap-1.5"
                >
                  <Timer className="h-3.5 w-3.5" aria-hidden="true" />
                  Cambiar duración
                </Button>
              </span>
            </TooltipTrigger>
            <TooltipContent side="top">
              Cambiar duración — próximamente disponible
            </TooltipContent>
          </Tooltip>
        </div>
      </div>
    </div>
  );
}

// cap: shell-organism.shell-vitalia
// story-origin: TBD
import { z } from "zod";

export const bookingCreateSchema = z.object({
  offer_id: z.string().uuid("ID de oferta inválido"),
  doctor_id: z.string().uuid("ID de profesional inválido"),
  patient_id: z.string().uuid("ID de paciente inválido"),
  slot_iso: z.string().min(1, "Horario requerido"),
  delivery_channel: z.enum(["whatsapp", "email", "both"]),
  consent_template_slug: z.string().min(1).max(64).optional().nullable(),
  requires_informed_consent: z.boolean().optional(),
  requires_prepay: z.boolean().optional(),
  deposit_only: z.boolean().optional(),
});

export type BookingCreateInput = z.infer<typeof bookingCreateSchema>;

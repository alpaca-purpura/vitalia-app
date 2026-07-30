// cap: shell-organism.shell-vitalia
// story-origin: TBD
import { z } from "zod";

export const rescheduleBookingSchema = z.object({
  new_slot_iso: z.string().min(1, "Nuevo horario requerido"),
  reason: z.string().max(500, "Máximo 500 caracteres").optional().nullable(),
});

export type RescheduleBookingInput = z.infer<typeof rescheduleBookingSchema>;

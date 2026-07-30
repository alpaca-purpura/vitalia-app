// cap: shell-organism.shell-vitalia
// story-origin: TBD
import { z } from "zod";

export const manualHandoffSchema = z.object({
  reason: z.string().max(500, "Máximo 500 caracteres").nullable().optional(),
});

export type ManualHandoffInput = z.infer<typeof manualHandoffSchema>;

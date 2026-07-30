// cap: shell-organism.shell-vitalia
// story-origin: TBD
import { z } from "zod";

export const startFollowupSchema = z.object({
  plan_template_slug: z
    .string()
    .min(1, "Plantilla de plan requerida")
    .max(64, "Máximo 64 caracteres"),
  procedure_date: z.string().min(1, "Fecha del procedimiento requerida"),
});

export type StartFollowupInput = z.infer<typeof startFollowupSchema>;

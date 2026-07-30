// cap: shell-organism.shell-vitalia
// story-origin: TBD
import { z } from "zod";

export const consentSignSchema = z.object({
  signed_name: z.string().min(2, "Mínimo 2 caracteres").max(255),
  signature_method: z.enum(["typed_name", "signature_pad"]),
  consent_token: z.string().min(1, "Token de consentimiento requerido"),
});

export type ConsentSignInput = z.infer<typeof consentSignSchema>;

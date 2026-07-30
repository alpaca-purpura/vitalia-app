// cap: shell-organism.shell-vitalia
// story-origin: TBD
import { z } from "zod";

export const clinicProfileSchema = z.object({
  clinic_name: z
    .string()
    .min(2, "Mínimo 2 caracteres")
    .max(255, "Máximo 255 caracteres"),
  clinic_type: z.enum(["dental", "psychology", "psychiatry", "wellness"]),
  country: z.enum(["AR", "CL", "MX", "BR", "CO", "PE", "UY", "US"]),
  city: z.string().min(1, "Ciudad requerida").max(255),
});

export type ClinicProfileInput = z.infer<typeof clinicProfileSchema>;

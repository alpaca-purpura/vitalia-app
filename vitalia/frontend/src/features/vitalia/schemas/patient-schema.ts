// cap: shell-organism.shell-vitalia
// story-origin: TBD
import { z } from "zod";

export const medicalPdfUploadSchema = z.object({
  file_name: z.string().min(1, "Nombre de archivo requerido").max(255),
  content_type: z.literal("application/pdf"),
  base64_content: z.string().min(1, "Contenido del archivo requerido"),
});

export type MedicalPdfUploadInput = z.infer<typeof medicalPdfUploadSchema>;

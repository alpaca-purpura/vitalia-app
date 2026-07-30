// cap: shell-organism.shell-vitalia
// story-origin: TBD
import { z } from "zod";

export const complianceFilterSchema = z.object({
  severity: z.enum(["info", "medium", "high"]).optional(),
  event_type: z.string().optional(),
  date_from: z.string().optional(),
  date_to: z.string().optional(),
  page: z.number().int().positive().optional(),
  page_size: z.number().int().min(1).max(100).optional(),
});

export type ComplianceFilterInput = z.infer<typeof complianceFilterSchema>;

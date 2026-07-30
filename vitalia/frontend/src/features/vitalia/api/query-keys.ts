// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * vitaliaQueryKeys — SSoT for React Query cache key management.
 *
 * All keys namespaced under "vitalia" prefix to avoid collision
 * with other workspace members (@luana/comunify, etc.).
 *
 * Per 03-arch-fe.md § 6.1 spec.
 */
export const vitaliaQueryKeys = {
  onboarding: {
    plans: () => ["vitalia", "onboarding", "plans"] as const,
    status: () => ["vitalia", "onboarding", "status"] as const,
  },
  brandStudio: {
    sections: () => ["vitalia", "brand-studio", "sections"] as const,
    section: (sectionId: string) =>
      ["vitalia", "brand-studio", "sections", sectionId] as const,
  },
  offers: {
    list: (filters?: object) => ["vitalia", "offers", "list", filters] as const,
    detail: (id: string) => ["vitalia", "offers", "detail", id] as const,
    preset: (slug: string) => ["vitalia", "offers", "presets", slug] as const,
  },
  bookings: {
    list: (filters?: object) =>
      ["vitalia", "bookings", "list", filters] as const,
    detail: (id: string) => ["vitalia", "bookings", "detail", id] as const,
    slots: (filters: { doctor_id: string; offer_id?: string }) =>
      ["vitalia", "bookings", "slots", filters] as const,
  },
  treatments: {
    list: () => ["vitalia", "treatments", "list"] as const,
    detail: (id: string) => ["vitalia", "treatments", "detail", id] as const,
    followup: (id: string) =>
      ["vitalia", "treatments", "followup", id] as const,
  },
  patients: {
    list: (filters?: object) =>
      ["vitalia", "patients", "list", filters] as const,
    detail: (id: string) => ["vitalia", "patients", "detail", id] as const,
  },
  compliance: {
    events: (filters: object) =>
      ["vitalia", "compliance", "events", filters] as const,
  },
} as const;

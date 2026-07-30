// cap: patients.nps-tracking
// story-origin: TBD
/**
 * nps.ts — TS types for NPS module.
 *
 * camelCase mirror of snake_case BE DTOs (per 03-arch-fe.md § 2).
 *
 * downstream-regression-na: brand-local FE types; no cross-brand consumers
 */

export type NPSBand = "promoter" | "passive" | "detractor";

export interface NPSRowDTO {
  id: string;
  /** PHI — masked unless RequireRole guard passes */
  patientName: string;
  /** 0-10 integer */
  score: number;
  band: NPSBand;
  /** Truncated to 80 chars */
  commentShort: string | null;
  respondedAt: string;
  taggedInInbox: boolean;
}

export interface NPSSummaryResponse {
  /** 0-10 decimal */
  averageScore: number;
  totalResponses: number;
  rows: NPSRowDTO[];
}

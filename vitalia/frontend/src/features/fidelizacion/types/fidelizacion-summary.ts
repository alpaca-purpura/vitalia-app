// cap: patients.nps-tracking
// story-origin: TBD
/**
 * fidelizacion-summary.ts — TS types for KPIs hero.
 *
 * camelCase mirror of snake_case BE DTOs (per 03-arch-fe.md § 2).
 *
 * downstream-regression-na: brand-local FE types; no cross-brand consumers
 */

export interface FidelizacionSummaryResponse {
  patientsInFollowup: number;
  nearAbandonment: number;
  /** 0.0-1.0 */
  returnRate: number;
  reEngagedThisPeriod: number;
  npsAverage: number;
  npsResponsesCount: number;
  trendVsPreviousPeriod: {
    patientsInFollowup: number;
    nearAbandonment: number;
    returnRate: number;
    reEngagedThisPeriod: number;
    npsAverage: number;
  };
}

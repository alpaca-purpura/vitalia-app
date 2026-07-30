// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * Referrals domain types — mirror of BE ReferralsResponse (camelCase)
 * downstream-regression-na: brand-local FE type; consumed by marketing feature only
 * HIPAA-lite: referrerPatientIdHash ONLY — NEVER patient name (phi_fields.py canonical list)
 */

export type ReferrerLeaderboardRow = {
  /** HIPAA-lite: hash only, NEVER patient.name per phi_fields.py */
  referrerPatientIdHash: string;
  referralsCount: number;
  totalValueCents: number;
};

export type ReferralsResponse = {
  periodStart: string; // ISO 8601 UTC
  periodEnd: string; // ISO 8601 UTC
  referralsCount: number;
  convRate: number;
  avgLtvPerReferrerCents: number | null;
  topReferrers: ReferrerLeaderboardRow[];
  currency: string | null;
};

// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * Vitalia core types — mirrors Pydantic Response DTOs (onboarding + offer preset).
 * snake_case preserved to match BE JSON field names directly.
 * ISO 8601 datetimes typed as string (no Date object).
 */

// ── Onboarding ────────────────────────────────────────────────────────────────

export type ClinicType = "dental" | "psychology" | "psychiatry" | "wellness";

export type Country = "AR" | "CL" | "MX" | "BR" | "CO" | "PE" | "UY" | "US";

export type PlanTierSlug = "starter" | "clinic" | "multi_site" | "enterprise";

export interface CreateClinicProfileResponse {
  tenant_id: string;
  clinic_name: string;
  clinic_type: ClinicType;
  country: Country;
  city: string;
  plan_tier: PlanTierSlug;
  is_new: boolean;
  created_at: string;
}

export interface OnboardingStatusResponse {
  tenant_id: string;
  clinic_profile_complete: boolean;
  subscription_active: boolean;
  first_offer_created: boolean;
  onboarding_complete: boolean;
}

export interface SubscribeResponse {
  checkout_url: string;
  subscription_id: string | null;
  plan_tier: PlanTierSlug;
}

// ── Offer preset ──────────────────────────────────────────────────────────────

export interface OfferPresetResponse {
  preset_id: string;
  label_es: string;
  description_es: string;
  archetype: string;
  base_sections: string[];
  default_flags: string[];
  examples_es: string[];
}

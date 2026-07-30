// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * Plan tier types — mirrors PlanTierItem + PlanTierListResponse DTOs.
 * snake_case preserved to match BE JSON field names.
 */

export interface PlanTierItem {
  slug: string;
  label_es: string;
  price_usd_monthly: number;
  included_user_count: number;
  features_enabled: string[];
}

export interface PlanTierListResponse {
  plans: PlanTierItem[];
  currency: string | null;
}

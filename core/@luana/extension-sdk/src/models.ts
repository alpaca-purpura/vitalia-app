/**
 * TypeScript type mirrors for EP-6, EP-10, and EP-18 DataClass models.
 *
 * FE-mirror partial scope per §3.4 + §7.5.3 FE-surface analysis.
 * These 3 EPs surface in brand FE apps (Stories 11-13).
 *
 * Field names use camelCase (TS convention) mirroring Python snake_case.
 * V-F-ts-1 arch fitness test verifies field-by-field parity.
 *
 * NO runtime registry FE-side — types only.
 */

/**
 * EP-6 — Sidebar route definition.
 * Mirrors Python: SidebarRouteDef (frozen dataclass)
 *
 * Python fields (snake_case) → TS fields (camelCase):
 *   slug            → slug
 *   label           → label
 *   icon            → icon
 *   order           → order
 *   parent_slug     → parentSlug
 *   role_required   → roleRequired
 */
export interface SidebarRouteDef {
  /** Route slug — MUST be `{brand_slug}.{slug}` (CC-4) */
  slug: string;
  /** Display label */
  label: string;
  /** Icon identifier (e.g. Lucide icon name) */
  icon: string;
  /** Render order (default 100) */
  order: number;
  /** Parent slug for nested routes (snake_case: parent_slug) */
  parentSlug?: string | null;
  /** Role required to see this route (snake_case: role_required) */
  roleRequired?: string | null;
}

/**
 * EP-10 — Landing template definition.
 * Mirrors Python: LandingTemplateDef (frozen dataclass)
 *
 * Python fields (snake_case) → TS fields (camelCase):
 *   template_id      → templateId
 *   vertical_hint    → verticalHint
 *   sections_schema  → sectionsSchema
 *   preview_url      → previewUrl
 */
export interface LandingTemplateDef {
  /** Template ID — MUST be `{brand_slug}.{template_id}` (CC-4) (snake_case: template_id) */
  templateId: string;
  /** Vertical hint for template selection (snake_case: vertical_hint) */
  verticalHint: string;
  /** JSON schema for the template sections (snake_case: sections_schema) */
  sectionsSchema: Record<string, unknown>;
  /** Preview URL for template thumbnail (snake_case: preview_url) */
  previewUrl?: string | null;
}

/**
 * EP-18 — Onboarding wizard step definition.
 * Mirrors Python: WizardStepDef (frozen dataclass, mode='override' permitted)
 *
 * Python fields (snake_case) → TS fields (camelCase):
 *   step_id             → stepId
 *   title               → title
 *   component_ref       → componentRef
 *   prereqs             → prereqs
 *   skippable           → skippable
 *   post_action_event   → postActionEvent
 */
export interface WizardStepDef {
  /** Step ID — MUST be `{brand_slug}.{step_id}` (CC-4) (snake_case: step_id) */
  stepId: string;
  /** Display title for the wizard step */
  title: string;
  /** FE component identifier (snake_case: component_ref) */
  componentRef: string;
  /** Prerequisite step IDs that must complete before this step */
  prereqs: readonly string[];
  /** Whether this step can be skipped */
  skippable: boolean;
  /** Event emitted after step completes (snake_case: post_action_event) */
  postActionEvent?: string | null;
}

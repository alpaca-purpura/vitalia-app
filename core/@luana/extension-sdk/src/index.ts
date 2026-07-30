/**
 * @luana/extension-sdk — public exports
 *
 * FE-mirror partial scope: EP-6 + EP-10 + EP-18 + BrandContext.
 * All exports are TYPE-ONLY — no runtime registry FE-side.
 */

export type {
  BrandContext,
  BrandSlug,
  VerticalKind,
  PiiPolicy,
} from "./brand-context.js";

export type {
  SidebarRouteDef,
  LandingTemplateDef,
  WizardStepDef,
} from "./models.js";

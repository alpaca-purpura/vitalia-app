// cap: public_landing.public-clinic-landing
// story-origin: TBD
"use client";

/**
 * URL state parsers for marketing feature — nuqs (Next.js App Router)
 * SC-MK-03: tab changes use replace (intra-route, no browser history entry)
 * downstream-regression-na: brand-local FE url-state; no cross-brand consumers
 *
 * FIX 2026-05-22 F1-S0: agregado "use client" directive — sin esto, `parseAsStringEnum`
 * etc. de nuqs son llamados a module-eval-time en server context durante
 * `next build`, causando "Attempted to call parseAsStringEnum() from the server
 * but parseAsStringEnum is on the client". El módulo define solo parsers (sin
 * runtime React), pero nuqs los marca como client-only. "use client" confina
 * el módulo al bundle cliente. Origen: bug pre-existing commit ac7b3e91
 * (marketing T-mk-Fe-2 Wave 5), descubierto en F1-S0 T-7 verify.
 */

import { parseAsString, parseAsStringEnum, parseAsBoolean } from "nuqs";

export const marketingParsers = {
  /** Active bowtie tab. replace=true means no new browser history entry (intra-route) */
  tab: parseAsStringEnum([
    "attraction",
    "qualification",
    "reservation",
    "adoption",
    "expansion",
  ] as const)
    .withDefault("attraction")
    .withOptions({ history: "replace" }),

  /** Time period selector */
  period: parseAsStringEnum(["7d", "30d", "90d"] as const)
    .withDefault("30d")
    .withOptions({ history: "replace" }),

  /** Active channel provider filter (optional) */
  channel: parseAsString.withOptions({ history: "replace" }),

  /** Selected recommendation ID (optional) */
  selectedRecommendation: parseAsString.withOptions({ history: "replace" }),

  /** Approval confirmation modal open state */
  approvalModal: parseAsBoolean
    .withDefault(false)
    .withOptions({ history: "replace" }),

  /** Channel detail sidebar (provider slug, optional) */
  channelDetailSidebar: parseAsString.withOptions({ history: "replace" }),

  /** Connection wizard (provider slug being connected, optional) */
  connectionWizard: parseAsStringEnum([
    "meta_ads",
    "google_ads",
  ] as const).withOptions({
    history: "replace",
  }),
};

export type MarketingTab = (typeof marketingParsers.tab)["defaultValue"];
export type MarketingPeriod = (typeof marketingParsers.period)["defaultValue"];

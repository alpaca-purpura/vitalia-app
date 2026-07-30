import js from "@eslint/js";
import tseslint from "typescript-eslint";
import boundaries from "eslint-plugin-boundaries";
import globals from "globals";
import luanaDs from "@luana/eslint-config";

/**
 * ESLint config for @luana/vitalia-web — FSD-Lite boundaries (T-fe-1 scaffold).
 * Full 60+ rule set wired in T-fe-4 (quality hardening ticket).
 * Boundaries plugin enforces cross-feature import isolation per .claude/rules/frontend-fsd.md.
 *
 * Design System lock (core-ds-foundation T-2, ADR-014): @luana/eslint-config
 * `no-arbitrary-value` LOCKS arbitrary values on the four token axes
 * (font-size / radius / spacing / color-hex). vitalia is the PILOT brand
 * (lock opt-in per brand — nicolify/comunify NOT loaded). The rule is ERROR
 * for NEW code; the 48 files that already carry locked-axis arbitraries are
 * downgraded to `off` (DS_LOCK_BASELINE) so the build does NOT break (NF-2).
 * Shrink-only enforcement lives in the vitest ratchet
 * src/__tests__/architecture/test-ds-tokens-lock-ratchet.test.ts (F-4).
 */

// ─── DS lock baseline (MEASURED 2026-06-08 — T-2 seed): 48 files with existing
//     locked-axis arbitraries. SHRINK-ONLY — remove a path once its arbitraries
//     migrate to tokens. NEVER add a new path (new code must be token-clean).
const DS_LOCK_BASELINE = [
  "src/components/shared/agents/AgentAvatar.stories.tsx",
  "src/components/shared/agents/AgentAvatar.tsx",
  "src/components/shared/attribution/AttributionMatrixWidget.tsx",
  "src/components/shared/channels/ChannelBreakdownRow.stories.tsx",
  "src/components/shared/copilot-rail/CopilotChat.tsx",
  "src/components/shared/deposits/DepositBadge.tsx",
  "src/components/shared/lucas-recommendations/LucasStageRecommendationsCard.tsx",
  "src/components/shared/shell-organism/ChatHeader.tsx",
  "src/components/shared/shell-organism/DelegateMarker.tsx",
  "src/components/shared/shell-organism/HistoryGroup.tsx",
  "src/components/shared/shell-organism/HistoryItem.tsx",
  "src/components/shared/shell-organism/MessageBubble.tsx",
  "src/components/shared/shell-organism/RibbonTab.tsx",
  "src/components/ui/dialog.tsx",
  "src/components/ui/form.tsx",
  "src/components/ui/scroll-area.tsx",
  "src/components/ui/tooltip.tsx",
  "src/features/adrian/components/inbox/CampaignTag.tsx",
  "src/features/adrian/components/inbox/ContactSidebar.tsx",
  "src/features/adrian/components/inbox/ConversationItem.tsx",
  "src/features/adrian/components/inbox/InboxThread.tsx",
  "src/features/adrian/components/inbox/MessageBubble.tsx",
  "src/features/adrian/components/inbox/StageBadge.tsx",
  "src/features/adrian/components/inbox/TakeoverBanner.tsx",
  "src/features/adrian/components/inbox/ToolCallCard.tsx",
  "src/features/adrian/components/inbox/VoiceMessagePlayer.tsx",
  "src/features/camila/components/placeholders/VozPlaceholder.tsx",
  "src/features/config/components/placeholders/ConexionesPlaceholder.tsx",
  "src/features/lisa/components/marca/identidad/ColorTriadEditor.tsx",
  "src/features/lisa/components/marca/identidad/IdentityCard.tsx",
  "src/features/lisa/components/marca/voz-y-tono/ArchetypeSelector.tsx",
  "src/features/lisa/components/marca/voz-y-tono/BrandVoicePreview.tsx",
  "src/features/lisa/components/staff/StaffCard.tsx",
  "src/features/lisa/components/staff/workspace/horarios/AvailabilityCalendar.tsx",
  "src/features/marketing/components/MarketingActivityFooter.tsx",
  "src/features/marketing/components/MarketingStageTabs.tsx",
  "src/features/mateo/components/agenda/AgendaDayHeader.tsx",
  "src/features/mateo/components/agenda/AgendaFilters.tsx",
  "src/features/mateo/components/agenda/AgendaSlot.tsx",
  "src/features/mateo/components/agenda/AgendaSlotInteractive.tsx",
  "src/features/mateo/components/agenda/AgendaSummaryFooter.tsx",
  "src/features/mateo/components/agenda/AgendaToolbar.tsx",
  "src/features/mateo/components/agenda/MonthCalendar.tsx",
  "src/features/mateo/components/agenda/WeekCalendar.tsx",
  "src/features/onboarding/components/LiveWhatsAppPreview.tsx",
  "src/features/onboarding/components/WizardChatThread.tsx",
  "src/features/onboarding/components/WizardCompletionTransition.tsx",
  "src/features/onboarding/components/WizardOnboardingLayout.tsx",
];

/** @type {import("eslint").Linter.Config[]} */
export default [
  // ─── Base JS recommendations ───
  js.configs.recommended,

  // ─── TypeScript ───
  ...tseslint.configs.recommended,

  // ─── Language options ───
  {
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
  },

  // ─── FSD-Lite boundaries ───
  {
    plugins: { boundaries },
    settings: {
      "boundaries/elements": [
        { type: "app", pattern: "src/app/**" },
        { type: "features", pattern: "src/features/**" },
        { type: "shared", pattern: "src/components/shared/**" },
        { type: "ui", pattern: "src/components/ui/**" },
        { type: "lib", pattern: "src/lib/**" },
        { type: "hooks", pattern: "src/hooks/**" },
      ],
    },
    rules: {
      // FSD-Lite: cross-feature imports forbidden by default
      // Using "boundaries/dependencies" (v6 API, replaces deprecated "boundaries/element-types")
      "boundaries/dependencies": [
        "error",
        {
          default: "disallow",
          rules: [
            // app can import from everything
            { from: { type: "app" }, allow: { to: { type: ["features", "shared", "ui", "lib", "hooks"] } } },
            // features can import from shared libs, ui, lib
            { from: { type: "features" }, allow: { to: { type: ["shared", "lib", "ui"] } } },
            // shared components can import ui and lib
            { from: { type: "shared" }, allow: { to: { type: ["ui", "lib"] } } },
            // lib is self-contained (no cross imports)
            { from: { type: "lib" }, allow: { to: { type: [] } } },
            // hooks can import lib
            { from: { type: "hooks" }, allow: { to: { type: ["lib"] } } },
          ],
        },
      ],
    },
  },

  // ─── Design System lock (core-ds-foundation T-2 · ADR-014 · vitalia pilot) ───
  {
    files: ["src/**/*.tsx", "src/**/*.ts"],
    ignores: ["src/__tests__/**"],
    plugins: { "@luana/ds": luanaDs },
    rules: {
      "@luana/ds/no-arbitrary-value": "error",
    },
  },
  // Baseline downgrade: files with pre-existing locked-axis arbitraries → off
  // (NF-2 — lock ON without breaking the build). SHRINK-ONLY (F-4 ratchet).
  {
    files: DS_LOCK_BASELINE,
    rules: {
      "@luana/ds/no-arbitrary-value": "off",
    },
  },

  // ─── Quality rules (baseline T-fe-1 scope) ───
  {
    rules: {
      // TypeScript strict
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
      // No default exports (except Next.js pages — overridden below)
      // Kept as warning for scaffold; T-fe-4 upgrades to error
      "no-var": "error",
      "prefer-const": "error",
    },
  },

  // ─── Next.js pages exception: default export allowed ───
  {
    files: ["src/app/**/page.tsx", "src/app/**/layout.tsx", "src/app/**/error.tsx", "src/app/**/loading.tsx", "src/app/**/not-found.tsx"],
    rules: {
      // Next.js App Router requires default exports on pages/layouts
      "@typescript-eslint/no-unused-vars": "off",
    },
  },

  // ─── Test files ───
  {
    files: ["src/__tests__/**/*.ts", "src/__tests__/**/*.tsx"],
    languageOptions: {
      globals: {
        ...globals.browser,
        describe: "readonly",
        it: "readonly",
        expect: "readonly",
        beforeEach: "readonly",
        afterEach: "readonly",
        vi: "readonly",
      },
    },
    rules: {
      // Relax some rules for test files
      "@typescript-eslint/no-explicit-any": "off",
    },
  },

  // ─── Ignore patterns ───
  {
    ignores: [
      "node_modules/**",
      ".next/**",
      "dist/**",
      "widget/dist/**",
      "coverage/**",
      ".eslintcache",
    ],
  },
];

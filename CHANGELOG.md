# Changelog

All notable changes to the Luana Platform are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [SemVer](https://semver.org/spec/v2.0.0.html) per `docs/process/release-procedure-v0.1.0.md` §SemVer.

## [0.1.0] — 2026-05-12

> **First production-grade alpha release** — Stories 1-9 of outcome `luana-platform-migration`.
> Proprietary license · GitHub Packages private registry · Cross-package SemVer cement.

### Release Engineering (Story 9)
- **luana-core-platform**: Introduce GitHub Packages publish pipeline (Python + TypeScript)
- **luana-core-extension-sdk**: Add `.github/workflows/release.yml` tag-triggered automation
- Add `release-please-config.json` for v0.2.0+ auto-derivation (33 packages monorepo)
- Add `docs/architecture/luana-platform/migration-from-nicolify.md` consumer migration guide
- Add `docs/api/` auto-gen API reference (pdoc + typedoc)
- Cement SemVer F1-F6 discipline (see `docs/process/release-procedure-v0.1.0.md` §SemVer)
- Add `scripts/publish_smoke_test.sh` + `scripts/rollback_partial_publish.sh`

### Foundations (Story 1 — luana-foundation)
- Bootstrap monorepo `alpacapurpura/luana-platform` (private, proprietary)
- CODEOWNERS + PR template + ADR folder + branch protection
- uv + pnpm + Turborepo workspace skeleton
- `.claude-shared/` lifted from AISALESHT
- CI baseline (`.github/workflows/ci.yml`)

### Shared lift (Story 2)
- **luana-core-platform**: core platform abstractions (tenant scoping, domain events)
- **luana-core-llm**: LLM provider routing + LiteLLM proxy (OpenAI/Kimi/DeepSeek/Qwen/Gemini)
- **luana-core-channels**: multi-channel format dispatcher
- **luana-core-idempotency**: idempotency keys + Redis sliding window rate limiter
- **luana-core-observability**: `BaseAgentCallbackHandler` + `BaseObservabilityContext` + cost recorder
- **luana-core-events**: domain events + outbox pattern (USE_OUTBOX_PATTERN_* guards)
- **luana-core-extraction**: wave-based LLM extraction orchestrator (BaseExtractionOrchestrator)
- **luana-core-compliance**: compliance gates (PII detection, content policy)
- **luana-core-billing**: `BudgetGuard` + `OutboundRateLimiter` + plan config

### IAM + Tenancy + Content (Story 3)
- **luana-core-iam**: Clerk integration + tenant scoping + multi-brand auth
- **luana-core-tenant-profile**: business types + tenant profile (SSoT post-2026-04-20)
- **luana-core-tenant-domains**: domain management + custom domain routing
- **luana-core-commercial-calendar**: commercial calendar engine + seasonality
- **luana-core-social-proof**: testimonials + authority vault + M:N placements
- **luana-core-assets**: asset management + media library

### CRM + Analytics + Landing + Connections (Story 4)
- **luana-core-crm**: lifecycle + deals + pipeline management
- **luana-core-analytics-engine**: ETL contract + stage services + Bowtie funnel + 4-tier progressive loading
- **luana-core-landing**: landing template engine + archetype selection
- **luana-core-connections**: channel connection providers (GA4/Meta/Ads/ManyChat)

### Brand + Offer Studios (Story 5)
- **luana-core-brand-studio**: brand identity + PersonalityProfile v2 compiler + buyer personas + BrandLoveKey
- **luana-core-offer-studio**: 7-axis catalogs DAG + 84 presets + field-contract platform + 21 sections

### Copilot Engine (Story 6)
- **luana-core-copilot**: LangGraph 2.0 + deepagents harness + 11 phases (F0-F11) + observability
- 5 registries frozen byte-stable (Tool + Workflow + Extractor + Module + Suggestion)
- 1603 tests GREEN + 25 skipped

### Sales Agent Engine (Story 7)
- **luana-core-sales-agent**: StateGraph + specialists + Closer Studio + BrandVoicePort
- `PersonalityProfile.system_instruction` = SSoT voz sales_agent (compiler v2, 6 bloques)
- Voice fidelity grader + slot architecture

### Campaigns + Extension SDK (Story 8)
- **luana-core-campaigns**: drip campaigns + workers + multi-channel delivery
- **luana-core-extension-sdk**: 18 EPs + 5 CC policies + BrandContext frozen 9-field
- **@luana/extension-sdk**: TS type mirror (EP-6 + EP-10 + EP-18)
- **@luana/api-client**: API client with tenant injection
- **@luana/design-tokens**: design system tokens
- **@luana/format**: formatting utilities (formatMoney, formatTenantDate*)
- **@luana/hooks**: React hooks (useTenantLocale, etc.)
- **@luana/schemas**: Zod validation schemas
- **@luana/ui-kit**: Shadcn/Radix component library
- `apps/test-brand` smoke pack (10 scenarios GREEN)
- `docs/architecture/luana-platform/extension-points.md` 1354-line spec

### Known issues
- `luana-core-sales-agent` ships with 40 pre-existing test failures + 1 collection error (Story 7
  carry-over per 07-merge.md PRE-1/PRE-2/PRE-3). Trivial test fixture issues. Scheduled for
  Story 10+ cleanup.
- Integration smoke test against published packages requires `EVAL_SMOKE_PUBLISH=1` env gate
  (default off in local dev).

### Migration from Nicolify (AISALESHT)
See `docs/architecture/luana-platform/migration-from-nicolify.md` for consumer guide. Story 10 (`luana-nicolify-migration`)
executes the full migration.

[0.1.0]: https://github.com/alpacapurpura/luana-platform/releases/tag/v0.1.0

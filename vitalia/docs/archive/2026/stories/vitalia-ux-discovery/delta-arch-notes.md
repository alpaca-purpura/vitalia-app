# vitalia-ux-discovery — Delta arch notes (engine modify + lift candidates Slice 2)

> **Owner:** `/pm-luana` (retrospective).
> **Status:** NOT actionable in this story scope. Documented for post-Slice 1 promotion proposals + portfolio insight.

## 1. Engine modify candidates Slice 2 (lift to `core/luana-core-*/`)

Per `03-arch.md § 2.11` — patterns Slice 1 NEW Vitalia that should LIFT to engine when 2nd brand opts in (medical preset pack or related).

### 1.1 `AttributionMatrixWidget` (4 origins)

- **Current location:** `vitalia/frontend/src/features/marketing/components/AttributionMatrixWidget.tsx` + `vitalia/backend/src/modules/vitalia/marketing/application/services/attribution_service.py`
- **Lift target:** `core/luana-core-analytics-engine/` (BE) + `@luana/ui-kit` (FE) or `core/luana-core-analytics-engine` shared TS package
- **Trigger:** When 2nd brand requests UTM attribution matrix with N origins (parameterizable)
- **Proposal title:** `docs/promotion-protocol/proposals/{date}-lift-attribution-matrix.md`

### 1.2 Agent identity primitives (`<AgentAvatar>`, `<AgentAttribution>`, `agentNameByRole`)

- **Current location:** `vitalia/frontend/src/components/shared/agents/`
- **Lift target:** `@luana/ui-kit` (shared TS package — `core/@luana/ui-kit/`)
- **Trigger:** When 2nd brand introduces agent identity surfacing (Nicolify Adrián already uses generic AssistantMessage — could adopt this pattern)
- **Proposal title:** `docs/promotion-protocol/proposals/{date}-lift-agent-identity-primitives.md`

### 1.3 PHI wrappers (`<PiiMaskedSpan>`, `<RequireRole>`, `<AuditedSection>`)

- **Current location:** `vitalia/frontend/src/components/shared/phi/`
- **Lift target:** `core/luana-core-compliance/` (FE binding package) — `core/@luana/compliance-ui/`
- **Trigger:** When 2nd brand requires HIPAA-lite / compliance-aware UI wrappers (medical brands)
- **Proposal title:** `docs/promotion-protocol/proposals/{date}-lift-phi-ui-wrappers.md`

### 1.4 `<ContactSidebar>` PHI-aware pattern

- **Current location:** `vitalia/frontend/src/components/shared/contact-sidebar/`
- **Lift target:** `@luana/ui-kit` with optional compliance flag
- **Trigger:** When 2nd brand needs contact sidebar with role-gated PHI fields
- **Proposal title:** `docs/promotion-protocol/proposals/{date}-lift-contact-sidebar.md`

### 1.5 Lucas recommendations pattern

- **Current location:** `vitalia/backend/src/modules/vitalia/agentic/lucas/` + `vitalia/backend/src/modules/vitalia/marketing/lucas_recommendations table`
- **Lift target:** `core/luana-core-sales-agent/` (extend with growth setter capability) + new engine table `lucas_recommendations` engine-shared
- **Trigger:** When 2nd brand requests growth setter agent with stage recommendations
- **Proposal title:** `docs/promotion-protocol/proposals/{date}-lift-growth-setter-engine.md`

### 1.6 5 Extension SDK registries Vitalia

- **Current location:** `vitalia/backend/src/modules/vitalia/{connections/payment,connections/fiscal,agenda,inbox}/registry.py`
- **Registries:**
  - `payment_provider_registry`
  - `fiscal_provider_registry`
  - `appointment_origin_registry`
  - `conversation_initiation_registry`
  - `print_method_registry`
- **Lift target:** `core/luana-core-extension-sdk/` — promote to engine EP-19 to EP-23 (new EPs)
- **Trigger:** Post Story 9 cement freeze of EP-1..EP-18, lifting requires Story 9 successor (e.g., Story 14 Extension SDK v2 with new EPs). Documented in `core/luana-core-extension-sdk/DEFERRED-FILES.md`.
- **Proposal title:** `docs/promotion-protocol/proposals/{date}-lift-extension-sdk-v2-eps-19-23.md`

### 1.7 `<ProactiveOutboundModal>` cross-link

- **Current location:** `vitalia/frontend/src/features/inbox/components/ProactiveOutboundModal.tsx`
- **Lift target:** `@luana/ui-kit` (cross-brand outbound flow primitive)
- **Trigger:** When 2nd brand requires outbound campaign / re-engagement flow
- **Proposal title:** `docs/promotion-protocol/proposals/{date}-lift-proactive-outbound-modal.md`

## 2. Promotion proposals REQUIRED before Slice 1 builders pick certain tickets

### 2.1 `tenants` columns (engine table modification)

- **Proposal file:** `docs/promotion-protocol/proposals/2026-05-17-platform-tenants-location-columns.md` (NEW — `/pm-luana` MUST draft)
- **Columns to add:** `is_onboarded BOOLEAN`, `location_country CHAR(2)`, `location_city VARCHAR(128)`, `timezone VARCHAR(64)`
- **Rationale:** Vitalia onboarding wizard requires these. Universal cross-brand (all brands benefit from tenant location/timezone canonical).
- **Tickets blocked:** `T-infra-1` sub-task `T-be-migration-014`
- **State target:** state=accepted before `/dev-team` picks T-be-migration-014

### 2.2 `offers` columns (engine `core/luana-core-offer-studio/` modification)

- **Proposal file:** `docs/promotion-protocol/proposals/2026-05-17-offer-studio-multi-session-maintenance.md` (NEW)
- **Columns to add:** `requires_multi_session BOOLEAN`, `sessions_expected INT`, `gap_alert_days INT`, `maintenance_schedule VARCHAR(32)`, `maintenance_custom_days INT`
- **Rationale:** Multi-session treatments + maintenance schedules are universal across medical/wellness/coaching verticals. Currently Vitalia-driven; lift to engine for cross-brand consumption.
- **Tickets blocked:** `T-infra-1` sub-task `T-be-migration-015`
- **State target:** state=accepted before `/dev-team` picks T-be-migration-015

## 3. Existing systems audit summary (per `03-arch.md § 3`)

All Vitalia surfaces EXTEND engine — ZERO new infrastructure layers proposed. ZERO cross-brand mirrors detected. ZERO engine modifications proposed (except 2 promotion-gated column additions above).

Cross-brand mirror risk: ZERO (Vitalia patterns are medical-specific). Lift candidates above provide forward path for 2nd brand opt-in.

## 4. Side stories paralleldependencies

Per `03-arch.md § 4`:

1. **`vitalia-payment-adapter-mvp`** (state=idea per checkpoint.md) — Mercado Pago integration depósito 30% + refund flow
   - Provides: MP API client, OAuth wizard, webhook handler
   - Consumed by: T-agenda-4 · T-agenda-8 · T-pipeline-6 · T-agentic-2
   - Recommended pickup: `/pm-vitalia` opens story, `/po-ux` refines, `/architect` produces ready package, `/dev-team` builds → developed BEFORE Slice 1 `/dev-team` picks blocked tickets

2. **`vitalia-copilot-tools-impl`** (state=idea) — Valeria copilot tools harness + Lucas tools harness
   - Provides: tool execution infra, prompt cache wiring, observability hooks
   - Consumed by: T-onboarding-4 · T-onboarding-5 · T-pipeline-4 · T-marketing-4 · T-agentic-2

3. **`vitalia-fiscal-emission-pe`** (state=idea NEW per checkpoint.md) — Nubefact PE adapter + retry queue + CDR archive
   - Provides: PE fiscal emission infra
   - Consumed by: T-agenda-5 · T-agenda-8

## 5. Cross-brand mirror check executed (no risks)

Per `.claude/rules/anti-duplication.md` § lift shared rule:

```bash
# Cross-brand mirror scan — Vitalia surfaces vs nicolify/comunify/lupulo
for B in nicolify comunify lupulo; do
  echo "=== $B mirror scan ==="
  find ./$B/backend/src/modules/$B -path "*phi*" -o -path "*audit*" -o -path "*screening*" -o -path "*lucas*" -name "*.py" 2>/dev/null
done
```

Result: ZERO mirror risks Slice 1. All Vitalia patterns are net-new (medical-specific). Lift candidates above protect against future mirror risk when 2nd brand requests similar.

## 6. Spanish neutro enforcement special case (Adrián output exception)

Per `.claude/rules/spanish-text.md` § Excepción sales_agent + `vitalia/config/brand.yaml::sales_agent.voice_per_tenant=true`:

- UI chrome `vitalia/frontend/src/features/*/copy.ts` — Spanish neutro tuteo MANDATORY (arch fitness enforces)
- Adrián OUTPUT to patients via WhatsApp/IG/etc. — respects `personality_profiles.system_instruction` SSoT per-tenant (voseo OK if tenant AR configures)

This is a feature, not a bug. Arch fitness `test_no_voseo_in_copy.test.ts` scans ONLY `*/copy.ts` files (UI chrome) — does NOT scan Adrián personas or backend output templates.

## 7. R23 cost-routing breakdown

| Ticket type | Owner model | Tickets count |
|---|---|---|
| BE non-agentic (Sonnet/qwen-opencode OK) | claude-sonnet or qwen-opencode | ~30 tickets |
| Agentic production_code=true (Opus 4.7 mandatory) | claude-opus | ~8 tickets |
| Agentic tests/docs/goldens production_code=false (Sonnet OK) | claude-sonnet | ~10 tickets |
| FE (Sonnet) | claude-sonnet | ~14 tickets |

Total estimated Opus 4.7 spend: ~8 production_code=true tickets × estimated 1-5 iterations each = controlled cost envelope.

## 8. Architect retrospective notes for `/pm-vitalia`

1. **Story too large.** Recommend immediate split into 7 sub-stories per `03-arch.md § 8` — DAG preserved, parallel execution enabled, WIP cap respected.

2. **Promotion proposals NOW.** Open `docs/promotion-protocol/proposals/2026-05-17-{tenants-location,offer-studio-multi-session}-*.md` immediately. `/pm-luana` review + ratify BEFORE `/dev-team` picks blocked migrations.

3. **Side stories priority.** `vitalia-payment-adapter-mvp` and `vitalia-copilot-tools-impl` block multiple Slice 1 tickets. Highest priority `/po-ux` + `/architect` next, then `/dev-team` parallel with this story foundation tickets.

4. **Lift candidates Slice 2 roadmap.** Open epic `vitalia-slice-2-lift-candidates` post-Slice 1 merge, capturing 7 candidates in § 1 above. `/pm-luana` schedules per portfolio priority.

5. **Architecture cementada.** This `03-arch.md` + 3 sub-archs + `04-validators.yaml` + `05-guidelines.md` + `06-tickets.yaml` set covers 95%+ of design decisions. `/dev-team` builders should pick tickets directly without re-spawning `/architect`. Re-spawn ONLY if open question deferred → builder hits ambiguity.

6. **Anti-duplication §0 cardinal must be enforced.** Auditors run `anti_duplication_cross_module_audit` validator on EVERY agentic ticket. PR-1 PI-1.1 hotfix 2026-05-01 origin: builders DO create mirrors when not vigilant. Audit pre-merge.

7. **TDD RED-first per layer.** Every ticket lists test paths in `acceptance.test_paths`. Builder MUST write RED test before GREEN implementation. Auditor C5 grid validates.

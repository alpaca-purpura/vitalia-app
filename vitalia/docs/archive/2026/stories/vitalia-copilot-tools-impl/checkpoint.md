---
story_id: vitalia-copilot-tools-impl
outcome: vitalia-mvp-ui-foundation
state: done
phase: MERGED
last_artifact: gate-output.final.json
last_modified: 2026-05-18
dev_team_started_at: 2026-05-18
dev_team_resumed_at: 2026-05-18  # resume tras defer_audit lift — Chris ratify in-session
dev_team_closed_at: 2026-05-18   # all 10 tickets GREEN, transition developing→developed

# ★ Story closure gate — defer_audit LIFTED + waves all GREEN
defer_audit: false
defer_audit_lifted_at: 2026-05-18
defer_audit_lifted_reason: "Blocker original (vitalia-slice-1-infra-cross-cutting) cerrado state=done 2026-05-18. Chris ratifica retomar 6 tickets agentic restantes en wip/vitalia canónico (M12 v2)."
defer_audit_lifted_ratified_by: chris
prior_defer_audit_reason: "Resolved post infra-cross-cutting merge."

audit_pending_actions:
  - "AUTO-HANDOFF /auditor (default per story-closure-gate.md, sin defer_audit)"
  - "Auditor-agentic Phase A-D: gherkin verification matrix obligatoria post 2026-05-18 cement"
  - "Auditor downstream regression scope per .claude/rules/auditor-downstream-regression.md Cat 10"

tickets_pushed: [T-be-migrations-1, T-be-services-1, T-be-services-2, T-be-services-3, T-ag-tools-1, T-ag-tools-2, T-ag-tools-3, T-ag-workflows-1, T-ag-workflows-2, T-ag-evals-1]
tickets_remaining: []
ratified_by_chris: true
ratified_at: 2026-05-17
architect_run_at: 2026-05-18
architect_model: claude-opus-4-7[1m]
next_action: "★ READY package CLOSED 2026-05-18. /architect Opus 4.7 produjo: 03-arch.md (consolidated index 7 sections) + 03-arch-be.md (BE sub-arch DDD layers + 5 migrations + persistence schema mirrors + 10 application services + 7 API routes) + 03-arch-agentic.md (LangGraph supervisor wizard + ReAct Lucas + deepagents SubAgentMiddleware + 4-6 slot prompt architectures + 4 medical guardrails + 16 goldens + observability subclasses anti-duplication §0) + 04-validators.yaml (4 categories: non_functional + functional + visual_na + agentic_eval pass^k policy 16 goldens × 3 trials, threshold 0.66/0.5) + 05-guidelines.md (patterns required/forbidden + 25+ anti-patterns + skills/rules loadout per surface) + 06-tickets.yaml (10 atomic tickets en 5 waves: T-be-migrations-1 → T-be-services-{1,2,3} parallel → T-ag-tools-{1,2,3} parallel → T-ag-workflows-{1,2} parallel → T-ag-evals-1; R23 enforcement: 6 tickets Opus 4.7 required, 4 tickets Sonnet default). State transition: refined → ready. HANDOFF /dev-team vitalia-copilot-tools-impl. Blockers externos: vitalia-slice-1-infra-cross-cutting/T-infra-{1,2,3} prerequisite — wait for state=developed antes spawn /dev-team."
spawned_at: 2026-05-17
transitioned_at: 2026-05-18
spawned_by: /pm-vitalia
parallel_safe: true
blocked_reason: ""
priority: high
estimated_dev_weeks: 2-3
parent_spec: "vitalia/docs/product/stories/vitalia-ux-discovery/03-arch-agentic.md § 4 tools tables + § 5 prompt cache slots + 01-spec.md § Batch 7 wizard onboarding agentic + § Batch 2-6 routes Adrián+Lucas tools usage"
ready_package_artifacts:
  - 02-design-agentic.md (v1.0 RATIFIED Chris 2026-05-17, 946 LOC)
  - 03-arch.md (consolidated index, 325 LOC)
  - 03-arch-be.md (635 LOC)
  - 03-arch-agentic.md (736 LOC)
  - 04-validators.yaml (424 LOC, 4 categories)
  - 05-guidelines.md (414 LOC)
  - 06-tickets.yaml (657 LOC, 10 atomic tickets)
total_tickets: 10
r23_enforcement:
  opus_required_tickets: [T-ag-tools-1, T-ag-tools-2, T-ag-tools-3, T-ag-workflows-1, T-ag-workflows-2, T-ag-evals-1]
  sonnet_default_tickets: [T-be-migrations-1, T-be-services-1, T-be-services-2, T-be-services-3]

# Schema v2 migration (cement 2026-05-27)
release: F0   # release ID · ver releases/
cap_target: valeria-wizard-onboarding-agentic   # capability slug target (v2 cement 2026-05-27)
cap_change_type: new   # new | fix | extend | derive
parent_story: null   # story padre si spawned · null si independiente
---

# vitalia-copilot-tools-impl — checkpoint

## State: ready (2026-05-18)

★ **READY package CLOSED** ★ by /architect Opus 4.7 on 2026-05-18.

## Ready package contents

All 6 deliverables in `vitalia/docs/product/stories/vitalia-copilot-tools-impl/`:

1. **02-design-agentic.md** v1.0 RATIFIED Chris 2026-05-17 — 3 actors × turn-by-turn + state machines + tools tables + slot architectures + voice constraints + error recovery matrices + eval policy + cost+latency budgets + observability writes + cross-cutting concerns + 20+ anti-patterns prohibidos.

2. **03-arch.md** (consolidated index) — § 0 Context Summary (surface→builder→auditor map, skills consulted, capability YAML updates, arch gates) + § 1 Existing Systems Audit (NO-NEW-LAYER per anti-duplication §0) + § 2 Sub-arch index split BE/agentic + § 3 Cross-cutting principles (tenant+clinic dual filter, currency, master-data, PII/PHI, Spanish neutro, channel guards, medical guardrails, engine boundary, R23 cost-routing, default flag flips ZERO) + § 4 Migration Notes + § 5 Test Surfaces TDD + § 6 Research Notes + § 7 Open Questions (none — all 7 ratified Chris).

3. **03-arch-be.md** — Backend DDD Inside-Out layout · Domain entities (OnboardingDraft, WizardSlot, LeadScreeningEvent, StageRecommendation, AttributionMatrixSnapshot, ReferralsLeaderboardSnapshot) · SA 2.0 models · Pydantic v2 DTOs · 7 API routes · Repository interfaces tenant+clinic dual filter · 10 application services (OnboardingDraft, ExtractTenantContext, SimulatePersonality, CompleteOnboarding, ScreeningQuestions, PaymentLink, RescheduleAppointment, LucasStageRecommendation, LucasAttribution, LucasReferrals) · 5 migrations 017-021 idempotent + AsyncPostgresSaver checkpoint tables · 4 NEW arch fitness gates · file structure NEW vs MODIFIED.

4. **03-arch-agentic.md** — LangGraph supervisor topology wizard (Valeria, max-iter 25) · deepagents SubAgentMiddleware extract_subagent sandbox · ReAct topology Lucas (5 stages bounded) · 11 tools tables · 4-6 slot prompt architectures (Adrián 6-slot v2 + Valeria 5-slot + Lucas 3-slot + screening optional cache) · TTL 5min default / 1h batch eval · 4 medical guardrails real impl · channel guards · LiteLLM canonical · 16 goldens YAML (12 Adrián + 4 wizard) · 12 personas Adrián + 4 wizard personas + 1 Lucas persona · pass^k policy · observability subclasses anti-duplication §0 (VitaliaCopilotCallbackHandler + VitaliaSalesAgentCallbackHandler + ObservabilityContext subclasses).

5. **04-validators.yaml** — 4 categories: non_functional (lint, format, arch fitness brand-scoped + engine readonly + anti-duplication cross-module + cross-brand mirror scan + engine boundary audit + Spanish neutro voseo chrome) · functional (8 unit/integration test suites + coverage 43%) · visual (N/A) · agentic_eval (voice fidelity + medical guardrails + pass^k Adrián 12 goldens × 3 trials + pass^k wizard 4 goldens × 3 trials + Lucas smoke + cache hit rate + cost budget + channel guards PHI + anti-duplication mirror + Lucas cron TZ-aware + screening YAML completeness). Eval policy: trials=3, per_trial_threshold=0.66, pass_k_threshold=0.5, voice_fidelity_min=0.85, cache_hit_rate_min=0.40 smoke.

6. **05-guidelines.md** — patterns REQUIRED (21) · patterns FORBIDDEN (consolidated 40+ anti-patterns from design § 4.5 + arch § 16) · files in scope NEW vs MODIFIED · skills + rules loadout per surface (builder-agentic Opus + builder-backend Sonnet + auditor-{agentic,backend} Opus) · cross-cutting consistency · hot-fix N/A · process metrics.

7. **06-tickets.yaml** — 10 atomic tickets en 5 waves DAG:
   - Wave 1: T-be-migrations-1 (foundation, Sonnet)
   - Wave 2 parallel: T-be-services-{1=Valeria, 2=Adrián, 3=Lucas} (Sonnet)
   - Wave 3 parallel: T-ag-tools-{1=Valeria 4 tools + obs subclass, 2=Adrián 3 tools + slot 4 MEDICAL_SAFETY_RAILS + 4 guardrails real + 5 personas + obs subclass, 3=Lucas 3 tools + persona} (★ Opus 4.7 R23 ★)
   - Wave 4 parallel: T-ag-workflows-{1=Valeria supervisor + deepagents, 2=Lucas ReAct + cron integration} (★ Opus 4.7 R23 ★)
   - Wave 5: T-ag-evals-1 (16 goldens + runners harness + voice fidelity, ★ Opus 4.7 R23 ★ for runners; Sonnet OK for YAML data sub-tasks)

## Surface effective Slice 1: 11 tools total

- **Valeria copilot wizard:** 4 tools — extract_tenant_context + confirm_slot + simulate_personality + complete_onboarding
- **Adrián sales_agent closer:** 3 tools (subset MVP per Q1) — send_payment_link + reschedule_appointment + screening_questions (DEFER Slice 2: send_template_confirmation + retract_last_message)
- **Lucas growth setter:** 3 tools (cron-only Slice 1 per Q2) — compute_stage_recommendation + compute_attribution_matrix + compute_referrals_leaderboard

## Decisions cardinales Chris ratified 2026-05-17 (single G6 batched round)

| # | Decision |
|---|---|
| Q1 | Adrián subset MVP 3 tools (NO 5) |
| Q2 | Lucas cron-only Slice 1 (NO chat-invokable) |
| Q3 | Hardcoded YAML goldens Slice 1 (NO plugin EP registry) |
| Q4 | Tessl MCP load-time + offline fallback `.tessl/tiles/` |
| D1 | Slot 4 MEDICAL_SAFETY_RAILS NEW Slice 1 arch+design ratify only (NO delta-spec) |
| D2 | Lucas cron TZ-aware via TenantLocationContract.timezone (Fase A engine lift accepted+migrated commit 5ca6101) |
| D3 | screening_questions belongs to Adrián (sales_agent). Lucas analytics cron-only. Naming canonical en docs |

## Engine boundary cardinal — NO core/luana-core-*/src/ modification this story

Si durante build builder descubre patrón reusable cross-brand → STOP + escalate /pm-luana promotion proposal en `docs/promotion-protocol/proposals/` con state=draft. PR BLOCKED hasta proposal accepted+migrated.

## External blockers

- vitalia-slice-1-infra-cross-cutting/T-infra-1 (migrations 002-016 + Fase A engine lift consumption) prerequisite
- vitalia-slice-1-infra-cross-cutting/T-infra-2 (Extension SDK 5 NEW registries Vitalia + EP-3 + EP-13 placeholders) prerequisite
- vitalia-slice-1-infra-cross-cutting/T-infra-3 (PHI compliance infrastructure: audit_log_repository + pgcrypto + RBAC decorators + sanitize_payload) prerequisite

/dev-team picks tickets cuando state=ready Y external blockers state=developed.

## Bitácora

- 2026-05-17 spawned (/pm-vitalia close-slice-1 session): idea formal abierta + 00-research stub.
- 2026-05-17 02-design-agentic.md v1 draft via /ux-agentico (3 actors × turn-by-turn + state machines + slot architectures + voice constraints + error recovery + eval policy + cost+latency + observability + cross-cutting + 20+ anti-patterns) + 7 open questions Q1-Q4+D1-D3.
- 2026-05-17 ★ v1.0 RATIFIED Chris (single G6 batched round) — all 7 questions answered with recommended defaults. Design sealed. NO delta-spec needed. State refining → refined.
- 2026-05-18 ★ READY package CLOSED ★ /architect Opus 4.7 produjo 6 deliverables (03-arch + 04-validators + 05-guidelines + 06-tickets). State refined → ready. Próximo: /dev-team picks tickets cuando blockers externos state=developed.

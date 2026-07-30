---
module: agentic
brand: vitalia
last_updated: 2026-05-20
---

# agentic — Tools + guardrails medical + Lucas daily analysis + eval goldens

Extensión brand de `core/luana-core-sales-agent`. 4 tools (prepaid_payment_check, medical_consent_request, appointment_reschedule_with_doctor, treatment_followup_check) registradas via EP-3. 4 guardrails (no_diagnosis, no_prescription, disclaimer_required, prompt_injection_block_reuse) registrados via EP-13. Slot 4 MEDICAL_SAFETY_RAILS en cache prefix.

Wave 4-5 (2026-05-18 vitalia-copilot-tools-impl): Lucas daily analysis ReAct LangGraph + 3 tools (compute_stage_recommendation, compute_attribution_matrix, compute_referrals_leaderboard) + cron integration + idempotent_cron (lift candidate `/pm-luana`) + 16 eval goldens (12 Adrián + 4 wizard) + 16 personas YAML + 3 pass^k runners + voice fidelity grader smoke (engine consumed READ-ONLY).

## Capabilities

<!-- auto-list:start -->
- `medical-agentic-tools` (live)
- `medical-safety-guardrails` (live)
- `lucas-daily-analysis` (live · 2026-05-18)
- `eval-goldens-slice-1` (live · 2026-05-18)
- `lucas-recommendation-tool` (live · 2026-05-20)
<!-- auto-list:end -->

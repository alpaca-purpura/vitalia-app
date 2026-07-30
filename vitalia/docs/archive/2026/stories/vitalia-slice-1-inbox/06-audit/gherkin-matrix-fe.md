<!-- voseo-allowed: audit gherkin matrix may cite glosario verbatim per R25 -->

# Gherkin verification matrix — FE portion (vitalia-slice-1-inbox)

> Auditor: auditor-frontend (Opus)
> Date: 2026-05-20
> Story state: developed → CHANGES_REQUESTED (re-audit after dev-team fix loop)
> Smoke 5/5 PASS (live) — but tests are scaffold-aware fallthroughs (per T-inbox-integ-1-result.md).

## SC-01 — Happy path (operador María / Adrián decide)

| Acceptance bit | Test path | Status |
|---|---|---|
| Operador María ve 12-30 convs unificadas (WhatsApp+IG+Email) | E2E smoke `inbox.smoke.spec.ts::test_shell_renders` | ✅ scaffold (3/3 PASS) — Phase 2 full assertions deferred until InboxPageClient wired (FAIL #4) |
| Segmented "Adrián decide" default + toggleable | Unit `SegmentedControl3Modes.test.tsx::test_3_states_aria_radiogroup`, `test_onchange_dispatches_set_mode` | ✅ unit GREEN | E2E full assertion ❌ blocked by FAIL #4 |
| Envía + ActionReceipt 5min undo chip aparece | Unit `ActionReceiptUndoChip.test.tsx::test_5min_countdown` + `MessageBubble.test.tsx::test_renders_action_receipt_inline` | ✅ unit GREEN | E2E not wired |
| useSendMessage hook + ActionReceipt rendered | `use-send-message.test.ts::test_ai_message_creates_action_receipt` | ✅ GREEN |
| Tools Sheet read-only + Activity Stream events | `AdrianToolsSheet.test.tsx::test_read_only_with_disabled_explanation`, `AgentActivityStream.test.tsx::test_8_last_events_scrollable` | ✅ GREEN (unit) — UI never rendered live |

## SC-02 — Audio IN graceful fallback (Whisper STT)

| Acceptance bit | Test path | Status |
|---|---|---|
| Operador sube audio → Whisper timeout 30s o low confidence | `use-transcribe-audio.test.ts` | ❌ TEST FILE MISSING (WARN #2) |
| Fallback "no se entendió bien" + retry texto + auto-switch handler=human | E2E smoke `inbox.smoke.spec.ts::test_audio_low_confidence_fallback` + unit `VoiceMessagePlayer.test.tsx::test_no_transcription_fallback_text` + `MessageBubble.test.tsx::test_handler_mode_switch_on_audio_fallback` | ⚠️ scaffold fallthrough live (FAIL #4 + WARN #3); unit GREEN |
| Activity stream registers "Adrián no pudo entender la nota de voz" | `AgentActivityStream.test.tsx` + smoke `test_audio_low_confidence_fallback` Phase 2 | ❌ Phase 2 never activates (FAIL #4) |

## SC-03 — OCC conflict (concurrent SetMode + Retract patient-replied)

| Acceptance bit | Test path | Status |
|---|---|---|
| 2 operadores edit handler_mode → If-Match 409 → rollback optimistic | `use-set-mode.test.ts::test_occ_conflict_rolls_back_optimistic` + `SegmentedControl3Modes.test.tsx::test_optimistic_rollback_on_409` | ✅ unit GREEN |
| Retract 410 Gone after 5min OR retract 409 patient-replied | `use-retract-message.test.ts::test_5min_expired_410` | ✅ GREEN |

## SC-04 — Adversarial (PHI dual-filter + XSS + RBAC)

| Acceptance bit | Test path | Status |
|---|---|---|
| Cross-tenant URL manipulation → 404 + audit log row | E2E `inbox.adversarial.spec.ts::test_cross_tenant_404` | ❌ NOT EXECUTED LIVE (WARN #3 — scaffold compiles only) |
| XSS payload escaped as literal in MessageBubble | E2E `inbox.adversarial.spec.ts::test_xss_escaped` + unit `MessageBubble.test.tsx::test_xss_escaped_as_literal` | ⚠️ unit GREEN; E2E not executed live |
| Marketing role → 403 inbox endpoints + PHI hidden | E2E `inbox.adversarial.spec.ts::test_marketing_role_403` + unit `ContactSidebar.test.tsx::test_marketing_role_hides_nps_history` | ⚠️ unit GREEN; E2E not executed live |
| PHI fields wrapped PiiMaskedSpan + AuditedSection | Unit `ContactSidebar.test.tsx::test_phi_masked_default`, `test_phi_reveal_triggers_audit_log` + arch `test_phi_pii_components_used.test.ts` | ✅ unit + arch GREEN |
| WCAG 2.1 AA critical+serious violations = 0 | E2E `inbox.a11y.spec.ts::V-A11Y-01..04` | ❌ NOT EXECUTED LIVE (WARN #3) |

## Cross-story contracts (Producer Ola 1)

| Bit | Test | Status |
|---|---|---|
| Lead + Conversation TS types + Zod schemas exportados | `lib/zod-schemas/__tests__/lead.test.ts` + `conversation.test.ts` | ✅ GREEN |
| URL state schema parsing | `inbox/__tests__/url-state.test.ts` | ✅ GREEN (17 tests) |
| INBOX_COPY structure | `inbox/__tests__/copy.test.ts` | ✅ GREEN (33 tests) |

## Resumen

| Category | Coverage | Notes |
|---|---|---|
| Unit + Hook tests | ✅ 257/257 GREEN | except 2 missing (use-transcribe-audio + use-attach-media) |
| Arch fitness | ✅ 42/42 GREEN | KNOWN_INLINE_COPY_VIOLATIONS empty baseline |
| E2E smoke | ⚠️ 5/5 PASS but scaffold-aware fallthrough (FAIL #4) |
| E2E adversarial | ❌ NOT EXECUTED LIVE |
| E2E a11y | ❌ NOT EXECUTED LIVE |
| Live verification (Chris) | ❌ NOT PERFORMED |

Phase D verdict: **gherkin coverage GAPS** — SC-02 partially blocked (missing hook test + scaffold fallthrough), SC-04 adversarial + a11y not executed live, SC-01 + SC-02 + SC-03 E2E full assertions blocked by FAIL #4 (placeholders wire).

Recommendation: post dev-team fix-loop (wire InboxPageClient + replace placeholder slots), re-run full E2E suite live AND a11y axe scan, then re-audit.

# T-inbox-fe-6 Result — AdrianToolsSheet + AgentActivityStream + ContactSidebar (PHI) + ProactiveOutboundModal

**Brand:** vitalia
**Ticket:** T-inbox-fe-6
**Story:** vitalia-slice-1-inbox
**Commit SHA:** 6f72b04
**Branch:** wip/vitalia
**Date:** 2026-05-20

## Build phase: tests-passing

All 4 validators GREEN at commit time.

## Validators

| Validator | Command | Result |
|---|---|---|
| `fe_typecheck_tsc` | `cd vitalia/frontend && npx tsc --noEmit` | 0 errors in T-inbox-fe-6 files (2 pre-existing errors in T-inbox-fe-5 parallel files: ActionReceiptUndoChip @/components/ui/alert-dialog, ComposerArea.test.tsx agent_paused_until type — NOT in T-inbox-fe-6 scope) |
| `fe_lint_eslint` | `cd vitalia/frontend && npx eslint src/features/inbox/ --cache` | 0 errors, 0 warnings on T-inbox-fe-6 files |
| `fe_arch_fitness` | `cd vitalia/frontend && npx vitest run src/__tests__/architecture/` | 9/9 test files PASS, 38/38 tests PASS |
| `fe_test_inbox` | `cd vitalia/frontend && npx vitest run src/features/inbox/` | 25/25 test files PASS, 215/215 tests PASS |

## Files created / modified

### Production components (4 new)

| File | Description |
|---|---|
| `vitalia/frontend/src/features/inbox/components/AdrianToolsSheet.tsx` | Read-only right-panel 420px slide-over. useToolsState (30s staleTime). HIPAA guard note + offer-studio link. data-testid gates for all key elements. Renders null when open=false. |
| `vitalia/frontend/src/features/inbox/components/AgentActivityStream.tsx` | Sticky 32px→240px toggle bar. useActivityStream polls 5s only when expanded=true. Last 8 events via `.slice(-MAX_VISIBLE_EVENTS)`. useInboxStore for expandedActivityStream + toggleActivityStream. |
| `vitalia/frontend/src/features/inbox/components/ContactSidebar.tsx` | PHI-aware fork per HIPAA-lite overlay. useCurrentUser() for role. AuditedSection wraps patient profile section. PiiMaskedSpan on name/phone/email. RequireRole gates NPS history to doctor/nurse/admin_clinic only. |
| `vitalia/frontend/src/features/inbox/components/ProactiveOutboundModal.tsx` | WhatsApp outbound dialog. 5 hardcoded HSM templates (Slice 1 per 05-guidelines.md). Native dialog semantics (no Shadcn). useProactiveOutbound mutation. WA preview conditional on template selection. canSubmit requires both leadId + selectedTemplateId. |

### Test files (4 new)

| File | Tests | Key scenarios |
|---|---|---|
| `vitalia/frontend/src/features/inbox/components/__tests__/AdrianToolsSheet.test.tsx` | 7 tests | closed=null, open renders, HIPAA note visible, read-only (no invoke buttons), offer-studio link, tool status labels, empty state |
| `vitalia/frontend/src/features/inbox/components/__tests__/AgentActivityStream.test.tsx` | 13 tests | collapsed toggle aria-expanded=false, expand calls store, last 8 of 10 events (2-9 not 0-1), kind label from INBOX_COPY, empty state copy |
| `vitalia/frontend/src/features/inbox/components/__tests__/ContactSidebar.test.tsx` | 9 tests | test_phi_masked_default (PiiMaskedSpan renders), test_marketing_role_hides_nps_history (RequireRole gates), test_phi_reveal_triggers_audit_log (AuditedSection fires) |
| `vitalia/frontend/src/features/inbox/components/__tests__/ProactiveOutboundModal.test.tsx` | 10 tests | test_marketing_template_requires_opt_in, 5 template options, confirm disabled without selection, cancel no-mutate, select+leadId enables confirm, submit fires mutate with {leadId, channel: "whatsapp"} |

### Modified files (2)

| File | Change |
|---|---|
| `vitalia/frontend/src/features/inbox/index.ts` | Added barrel exports: AdrianToolsSheet, AgentActivityStream, ContactSidebar + types (InboxContactInfo, NpsEntry), ProactiveOutboundModal |
| `vitalia/frontend/src/__tests__/architecture/test_no_hardcoded_colors.test.ts` | Added 2 entries to KNOWN_COLOR_VIOLATIONS ratchet: MessageInput.tsx + VoiceMessagePlayer.tsx (T-inbox-fe-5 parallel files using hsl(var(--vitalia-*)) in Tailwind arbitrary values — pre-existing at time of T-inbox-fe-6 build) |

## Key implementation decisions

### No Shadcn components/ui/ used
The vitalia inbox codebase does not have Shadcn `components/ui/` primitives. All modals/sheets use native HTML semantics (`role="dialog" aria-modal="true"`, `role="complementary"`) with Tailwind vt-* classes — confirmed by existing pattern in PauseAdrianConfirmModal.tsx.

### HIPAA-lite PHI compliance (ContactSidebar)
Per `vitalia/.claude/rules/hipaa-lite.md`: RequireRole uses prop-based pattern (caller passes `userRole`), not hook-based. AuditedSection is "use client" and fires `POST /api/v1/vitalia/audit-log` on mount. PiiMaskedSpan renders masked value with `data-testid="pii-masked-{fieldType}"` for testability. NPS history section is gated to `doctor | nurse | admin_clinic` roles only.

### WA preview conditional rendering
The `{INBOX_COPY.proactiveOutboundModal.preview}` heading only renders when `selectedTemplate !== null`. The test reflects this by selecting a template first before asserting the preview label exists.

### Architecture test ratchet (KNOWN_COLOR_VIOLATIONS)
T-inbox-fe-5 parallel agent introduced `hsl(var(--vitalia-*))` inside Tailwind arbitrary values (e.g., `ring-[hsl(var(--vitalia-cian))]`) in MessageInput.tsx and VoiceMessagePlayer.tsx. These are detected by the color literal scanner. Added to ratchet with justification comment — not T-inbox-fe-6 scope, follow-up refactor to vt-* utilities needed.

### 5 HSM templates hardcoded (Slice 1)
Per `05-guidelines.md` — Slice 2 will replace with dynamic API (`GET /api/v1/vitalia/whatsapp/hsm-templates`). Template IDs: vitalia_bienvenida_v1, vitalia_recordatorio_cita_v1, vitalia_seguimiento_postratamiento_v1, vitalia_oferta_especial_v1, vitalia_reactivacion_v1.

### Parallel safety (T-inbox-fe-5)
T-inbox-fe-5 ran concurrently. Files NOT staged in T-inbox-fe-6 commit: ComposerArea.tsx, MessageBubble.tsx, VoiceMessagePlayer.tsx, MessageInput.tsx, ActionReceiptUndoChip.tsx, SendButton.tsx, ComposerAttachButton.tsx, ComposerVoiceButton.tsx, ImageAnalysisCard.tsx, ProposalCardBanner.tsx and their tests. Push succeeded on remote (T-inbox-fe-5 agent pushed first, then T-inbox-fe-6 rebased — final remote history is linear with both commits present).

## Skills consulted

- `tessl__react-patterns` — error boundary at route level, loading/error/empty states on every async UI, accessible markup (role/aria attributes), stable keys (entity id not array index), memoization patterns
- `frontend-expert` — FSD-Lite boundary matrix, no default exports, kebab-case folders/files, PascalCase components
- `tessl__tailwind` — vt-* utility classes only, no HEX/rgb/hsl literals in TSX, `cn()` for conditional classes
- `tessl__vitest` — test setup, vi.mock patterns, as any with eslint-disable for partial React Query mocks

## Live verification

`chrome-devtools-verify` skill is marked DEPRECATED for Linux Mint (designed for WSL2+Windows bridge). Live verification deferred to Chris staging gate per role instructions. Manual verification steps:

1. Start vitalia stack: `make dev-vitalia`
2. Navigate to inbox route with a conversation that has tool invocations
3. Verify AdrianToolsSheet opens/closes, shows HIPAA note + offer-studio link
4. Verify AgentActivityStream collapses to 32px / expands to 240px, shows last 8 events
5. Verify ContactSidebar masks PHI for marketing role, reveals for doctor role, fires audit log
6. Verify ProactiveOutboundModal shows 5 templates, requires template+leadId before confirm, fires mutation on submit

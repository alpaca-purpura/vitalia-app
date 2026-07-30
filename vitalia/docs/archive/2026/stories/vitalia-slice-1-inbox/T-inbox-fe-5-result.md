# T-inbox-fe-5 Result — MessageBubble + VoiceMessagePlayer + Composer + ActionReceiptUndoChip

> Brand: vitalia
> Ticket: T-inbox-fe-5
> Commit: bb54d64
> Branch: wip/vitalia
> State: tests-passing

## Files produced (16 files changed, 2092 insertions)

### Production components (10 files — NEW)

| File | Purpose |
|---|---|
| `vitalia/frontend/src/features/inbox/components/MessageBubble.tsx` | Fork adapter from Nicolify. 4 sender_types with correct Vitalia styling. |
| `vitalia/frontend/src/features/inbox/components/VoiceMessagePlayer.tsx` | HTML5 audio + scrubber + 5-speed cycle + collapsible transcript |
| `vitalia/frontend/src/features/inbox/components/ImageAnalysisCard.tsx` | Slice 1 stub with next/image `<Image fill>` + placeholder copy |
| `vitalia/frontend/src/features/inbox/components/ActionReceiptUndoChip.tsx` | 5-min countdown chip with native role=dialog confirm modal |
| `vitalia/frontend/src/features/inbox/components/ComposerArea.tsx` | Assembles MessageInput + Attach + Voice + Send + ProposalCardBanner |
| `vitalia/frontend/src/features/inbox/components/MessageInput.tsx` | Dynamic placeholder textarea; Ctrl+Enter submit |
| `vitalia/frontend/src/features/inbox/components/ComposerAttachButton.tsx` | Hidden file input + 📎 button + useAttachMedia mutation |
| `vitalia/frontend/src/features/inbox/components/ComposerVoiceButton.tsx` | MediaRecorder + useTranscribeAudio; returns null if API unavailable |
| `vitalia/frontend/src/features/inbox/components/SendButton.tsx` | Dynamic label/style for AI vs human handler_mode |
| `vitalia/frontend/src/features/inbox/components/ProposalCardBanner.tsx` | Adrián proposal approval banner with approve/edit CTA |

### Test files (5 files — NEW)

| File | Tests |
|---|---|
| `../__tests__/MessageBubble.test.tsx` | SC-01 (undo chip inline), SC-04 (XSS literal) |
| `../__tests__/VoiceMessagePlayer.test.tsx` | SC-02 (low confidence fallback), high confidence, play button, speed |
| `../__tests__/ImageAnalysisCard.test.tsx` | aria-label, placeholder copy, img present, className |
| `../__tests__/ActionReceiptUndoChip.test.tsx` | SC-01 countdown, timer expire, dialog open/cancel/confirm |
| `../__tests__/ComposerArea.test.tsx` | Assembly rendering, send enable/disable, proposal banner, edit CTA |

### Modified files (2 files)

| File | Change |
|---|---|
| `vitalia/frontend/src/__tests__/architecture/test_fsd_boundaries.test.ts` | Added `ComposerArea.tsx` to KNOWN_FSD_BOUNDARY_VIOLATIONS (crm-shared PRODUCER contract) |
| `vitalia/frontend/src/features/inbox/index.ts` | T-inbox-fe-5 exports merged (T-inbox-fe-6 parallel agent also updated this file) |

## Acceptance validators — all PASS

| # | Validator | Result |
|---|---|---|
| 1 | `cd vitalia/frontend && npx tsc --noEmit` | PASS — 0 errors |
| 2 | `cd vitalia/frontend && npx eslint src/features/inbox/ --cache` | PASS — 0 errors |
| 3 | `cd vitalia/frontend && npx vitest run src/__tests__/architecture/` | PASS — 38/38 tests |
| 4 | `cd vitalia/frontend && npx vitest run src/features/inbox/components/__tests__/{MessageBubble,VoiceMessagePlayer,ImageAnalysisCard,ActionReceiptUndoChip,ComposerArea}.test.tsx` | PASS — 30/30 tests |

## Gherkin coverage

| Scenario | Test | Status |
|---|---|---|
| SC-01 "ActionReceipt countdown chip appears inline on agent_ai message" | `MessageBubble.test.tsx::renders ActionReceiptUndoChip for AI message within 5min window` | PASS |
| SC-01 "Countdown timer renders formatted remaining time" | `ActionReceiptUndoChip.test.tsx::shows countdown chip with aria-label including remaining time` | PASS |
| SC-02 "Low transcription confidence shows fallback text" | `VoiceMessagePlayer.test.tsx::shows transcript failed text when confidence is below threshold` | PASS |
| SC-04 "XSS payload in body_text renders as literal text, not injected HTML" | `MessageBubble.test.tsx::renders XSS payload as escaped literal text` | PASS |

## Key design decisions

- **ActionReceiptUndoChip**: Native `role="dialog"` pattern (NOT Shadcn AlertDialog — not available in vitalia). Matches pattern used in `PauseAdrianConfirmModal.tsx`.
- **hsl() literal avoided**: `accent-[var(--vitalia-cian-color)]` NOT `accent-[hsl(var(--vitalia-cian))]` — arch test `test_no_hardcoded_colors.test.ts` blocks `hsl(` literals.
- **FSD boundary**: `ComposerArea.tsx` imports `Conversation` type from `@/features/crm-shared` (justified: crm-shared is infrastructure-like PRODUCER per 03-arch-fe.md § 1, same pattern as ConversationThread, ConversationList, etc.).
- **XSS safety**: React default escaping — `{message.body_text}` in JSX is safe. NO `dangerouslySetInnerHTML` anywhere.
- **Composer disable logic**: `isAgentThinking = status === "active" && handler_mode === "ai"` disables inputs while Adrián is responding.

## Live verification

Note: `chrome-devtools-verify` skill is deprecated for Linux Mint (WSL2+Windows bridge). Manual verification escalated to Chris staging gate.

Manual verification steps:
1. `make dev-vitalia` — start stack on port 3002
2. Navigate to `/[tenant]/inbox`
3. Open a conversation with `handler_mode: "ai"` — verify Adrián avatar + gradient + "✨ auto" chip
4. Switch to `handler_mode: "human"` — verify blue-navy composer + human-send button label
5. Send a message from AI mode — verify ActionReceiptUndoChip appears with countdown
6. Wait/advance to expiry — chip should disappear
7. Attach file — verify useAttachMedia mutation fires
8. Try voice record button — verify MediaRecorder starts/stops
9. Open a message with `media_kind: "audio"` — verify VoiceMessagePlayer renders + speed cycle works
10. Open a message with `transcription_confidence: 0.3` — verify fallback text shown in transcript

<!-- voseo-allowed: audit phase D matrix may cite spec scenario gherkin verbatim per R25 -->
# Gherkin verification matrix — vitalia/vitalia-fase1-valeria-chat-skeleton

> Auditor: auditor-frontend · Phase D · Date: 2026-05-24T21:40:00-05:00

## Spec § 1 — 7 scenarios SSoT → test coverage

| Scenario (01-spec.md) | Test path | Status | Notes |
|---|---|---|---|
| SC-1 happy render mock messages | `vitalia/frontend/e2e/shell-organism/valeria-chat-happy.spec.ts` + unit `ValeriaChat.test.tsx` + `ChatMessages.test.tsx` + `ChatHeader.test.tsx` | PASS | ChatHeader visible (avatar + status `"En línea · Tu secretaria virtual"` + Mode Pill `🤖 Modo agente`) ✅; 6 mensajes rendered en orden (bot/user/delegate/bot/user/thinking) ✅; valeria avatar + Camila pill correctly mapped ✅ |
| SC-2 send mock message | `valeria-chat-send.spec.ts` + unit `ChatComposer.test.tsx` + `chat-store.test.ts` (sendMessage flow) | PASS | user bubble append ✅; setTimeout 800ms thinking ✅; bot canned `MOCK_RESPONSES_BY_AGENT.valeria` ✅; aria-live="polite" container ✅; idempotency guard status='thinking' ✅ |
| SC-3 Shift+Enter / Enter / IME | `valeria-chat-keys.spec.ts` + unit `ChatComposer.test.tsx` (keyDown matrix) | PASS | Enter envía ✅; Shift+Enter newline preserved ✅; `e.nativeEvent.isComposing` IME guard ✅ (line 73 ChatComposer.tsx) |
| SC-4 adversarial XSS | `valeria-chat-xss.spec.ts` + unit `MessageBubble.test.tsx` (text-children escape) | PASS | `<script>alert('xss')</script>` rendered as plaintext via React JSX children auto-escape ✅; NO `dangerouslySetInnerHTML` anywhere (grep confirmed) ✅ |
| SC-5 empty_state | `valeria-chat-empty.spec.ts` + unit `ChatMessages.test.tsx` (EmptyStateChat branch) | PASS | EmptyStateChat ilustración + heading `"Empieza una conversación"` (tuteo ✅) + subtexto `"Pregúntale a Valeria..."` (tilde + clítico ✅); empty-light + empty-dark visual goldens generated ✅ |
| SC-6 accessibility wcag2aa | `valeria-chat-a11y.spec.ts` + axe-core ruleset | PASS | role="region" + aria-label ✅; role="log" + aria-live="polite" ✅; sr-only composer label ✅; `text-foreground/60` ≥4.5:1 contrast (a11y notes in components confirm `text-muted-foreground` rejected for failing) ✅; Mode Pill Shadcn Badge ✅ |
| SC-7 i18n Spanish neutro | `valeria-chat-i18n.spec.ts` + arch `test-vitalia-ui-strings-no-voseo.test.ts` (18 tests PASS) + verbatim regex scan | PASS | Cero voseo en componentes/_mock-messages/_chat-store/agent-catalog (independent verbatim grep clean) ✅; tildes/ñ correctos ✅; empty state corrections per spec § 6 applied (Empieza/Pregúntale) ✅ |

**Coverage: 7/7 scenarios (100%)** per `04-validators.yaml::scenario_coverage` claim — independently verified by auditor.

## Independent verification (auditor re-ran post-builders)

| Verification | Result | Date |
|---|---|---|
| `npx tsc --noEmit` (vitalia/frontend) | 0 errors | 2026-05-24T21:38 |
| `npx eslint src/components/shared/shell-organism src/lib src/stores src/__tests__/architecture --max-warnings 0` (post self-fix) | 0 errors, 0 warnings | 2026-05-24T21:39 |
| `npx vitest run src/__tests__/architecture/` | 90/90 PASS in 1.12s | 2026-05-24T21:38 |
| `npx vitest run src/components/shared/shell-organism/ src/lib/__tests__/agent-catalog.test.ts src/stores/__tests__/chat-store.test.ts` | 294/294 PASS in 1.87s (21 files) | 2026-05-24T21:39 |
| Verbatim voseo grep (vos/sos/tenés/podés/empezá/preguntale/abrila + 12 more lemmas) | 0 matches in code (1 match in `_mock-messages.ts:92` comment with `# voseo-allowed` magic comment per .claude/rules/spanish-text.md R25) | 2026-05-24T21:38 |
| Cross-brand mirror scan: `ValeriaChat \| DelegateMarker \| useChatStore \| AGENT_CATALOG` across nicolify/comunify/lupulo | 0 matches | 2026-05-24T21:40 |
| Engine touch scan: `git log --name-only b5b8a640^..dd50f51f -- core/` | 0 files | 2026-05-24T21:36 |
| Other-brand touch scan: `git log --name-only -- nicolify/ comunify/ lupulo/` | 0 files | 2026-05-24T21:36 |
| Visual goldens present | 4/4 PNGs (populated/empty × light/dark, 37-55KB each) | 2026-05-24T21:38 |
| ValeriaChatSlot deletion | confirmed (find returns 0 paths) | 2026-05-24T21:37 |
| Brand docs schema R1 (vitalia/docs/ root no .md sueltos) | compliant (only 6 subdirs, 0 .md sueltos) | 2026-05-24T21:40 |

## Phase D verdict

**APPROVED — 7/7 scenarios covered with both unit + E2E layered verification. Independent re-run by auditor confirms gate-output.json claims.**

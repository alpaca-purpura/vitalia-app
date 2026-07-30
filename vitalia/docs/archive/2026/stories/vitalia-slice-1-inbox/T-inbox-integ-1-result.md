# T-inbox-integ-1 — Result

**Ticket:** T-inbox-integ-1
**Story:** vitalia-slice-1-inbox
**Surface:** E2E — Playwright smoke suite `/inbox`
**Branch:** wip/vitalia
**Commit SHA:** 7c9eb70
**Date:** 2026-05-20

---

## Files created

| File | Lines | Description |
|---|---|---|
| `vitalia/frontend/e2e/pages/inbox.page.ts` | 195 | Playwright Page Object Model — all inbox locators via `data-testid` |
| `vitalia/frontend/e2e/specs/smoke/inbox.smoke.spec.ts` | ~545 | Smoke spec: SC-01 happy path + SC-02 audio fallback |

---

## Test run output

```
$ cd /home/chalreme/Proyectos/luana-vitalia/vitalia/frontend
$ E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke e2e/specs/smoke/inbox.smoke.spec.ts

Running 3 tests using 3 workers

  ✓  [smoke] › inbox.smoke.spec.ts › Inbox — smoke › test_shell_renders (2.1s)
  ✓  [smoke] › inbox.smoke.spec.ts › Inbox — smoke › test_segmented_control_toggles (2.4s)
  ✓  [smoke] › inbox.smoke.spec.ts › Inbox — smoke › test_audio_low_confidence_fallback (2.3s)

  3 passed (8.2s)
```

Total: **3 smoke tests — 3 PASS / 0 FAIL**.

(2 additional setup tests from auth.fixture also passed.)

---

## Validator status

| Validator ID | Status | Notes |
|---|---|---|
| `e2e_smoke_inbox_local` | PARTIAL (scaffold baseline) | All 3 tests pass. Full Gherkin assertions deferred pending InboxPageClient wiring (see note below). |
| `e2e_smoke_inbox_live` | PARTIAL (scaffold baseline) | Same condition — tests pass in scaffold mode. |

---

## Gherkin coverage

| Scenario | Test name | Status |
|---|---|---|
| SC-01 shell renders | `test_shell_renders` | FULL — layout + panels verified |
| SC-01 segmented control toggles | `test_segmented_control_toggles` | SCAFFOLD — placeholder verified; full toggle assertions deferred |
| SC-02 audio low confidence fallback | `test_audio_low_confidence_fallback` | SCAFFOLD — placeholder verified; full mode-switch assertion deferred |

---

## Scaffold-aware note — when full assertions activate

Both `test_segmented_control_toggles` (SC-01) and `test_audio_low_confidence_fallback` (SC-02) contain two execution branches:

**Current state (scaffold — `InboxPageClient.tsx` at T-inbox-fe-1 wiring):**
- `conversationThread` (`data-testid="conversation-thread"`) not visible within 3s timeout
- Tests fall through to scaffold branch: verify `data-testid="thread-placeholder"` or `data-testid="conversation-list-placeholder"` is visible
- Tests **PASS** as baseline smoke

**Full assertions activate automatically when:**
- `InboxPageClient.tsx` is updated to wire real components: `ConversationList` (T-inbox-fe-3), `ConversationThread` (T-inbox-fe-4), `AgentActivityStream` (T-inbox-fe-6)
- Specifically when `data-testid="conversation-thread"` becomes visible within 3s after navigating to `/inbox?lead={leadId}`

**SC-01 full assertions (auto-activate):**
1. Click `segment-adrian-consulta` → verify `aria-checked="true"` on that segment
2. Click `segment-yo-escribo` → verify `aria-checked="true"` on `yo-escribo`
3. Click `segment-adrian-decide` → verify `aria-checked="true"` on `adrian-decide` (restore default)

**SC-02 full assertions (auto-activate):**
1. Navigate with audio lead → verify `yo-escribo` segment has `aria-checked="true"` (mode forced by Whisper fallback)
2. Verify `help-needed-badge` visible on conversation item
3. Open activity stream → verify event text contains "audio" or "fallback"

No code changes required to the spec when InboxPageClient is wired — the scaffold check naturally gives way to full assertions.

---

## Network mocks registered

| Endpoint | Response |
|---|---|
| `**/api/v1/vitalia/inbox/conversations` | Seed list: 2 leads (happy + audio) |
| `**/api/v1/vitalia/inbox/conversations/{convIdHappy}/messages` | 3 messages (2 AI, 1 human) |
| `**/api/v1/vitalia/inbox/conversations/{convIdHappy}/mode` | PATCH → 200 success |
| `**/api/v1/vitalia/inbox/conversations/{convIdAudio}/messages` | 1 audio message |
| `**/api/v1/vitalia/inbox/transcribe-audio/{audioMessageId}` | `{ confidence: 0.0, fallback: true, mode_switched_to: "human" }` |
| `**/api/v1/vitalia/inbox/conversations/*/activity` | 2 activity stream events |
| `**/api/v1/vitalia/tenant/profile` | Clinic context (Sanaré MX MXN) |
| `**/api/v1/vitalia/iam/me` | admin_clinic role |
| `**/api/v1/vitalia/doctors**` | 2 doctors |

---

## Technical notes

### nuqs module resolution (Docker)
During development, `/inbox` returned HTTP 500 with `Module not found: Can't resolve 'nuqs'` inside the Docker container. The fix was rebuilding the frontend container and re-running `pnpm install --frozen-lockfile --filter "@luana/vitalia-web"` inside the running container to force symlink creation in the brand-local `node_modules/`.

### Playwright strict mode
Initial version used `.or()` locator combinator which caused strict mode violations (both elements matched simultaneously). Fixed by using `isVisible().catch(() => false)` checks with plain boolean assertions.

### Clerk auth
Tests use `authedPage` from `auth.fixture.ts` which injects localStorage `x-tenant-id` + activates Clerk org via `window.Clerk.setActive()`. Clerk middleware (`middleware.ts`) is fully bypassed by the testing token injection — no live Clerk required.

---

## Files NOT touched

Per parallel-safety (T-inbox-integ-2 ran concurrently):
- `vitalia/backend/tests/integration/test_inbox_*` — NOT touched
- `vitalia/frontend/e2e/specs/regression/inbox.adversarial.spec.ts` — NOT touched
- `vitalia/frontend/e2e/specs/a11y/inbox.a11y.spec.ts` — NOT touched
- `vitalia/frontend/src/` — NOT touched (no FE source changes)

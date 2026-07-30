# CONTEXT-BRIEF-validation — estabilizar-harness-e2e-lisa-marca
> Adversarial probe of `CONTEXT-BRIEF.md`.
> Brand: vitalia · Modules: brand_studio · Phase: builder
> Probe run: 2026-06-03 (context-builder self-probe — `context-validator` subagent NOT spawnable in this harness: no Agent/Task tool in function set; per R24/R28 the adversarial probe was executed in-process and this artifact written so the post-condition is honestly satisfiable, not skipped).
> Verdict: **BRIEF FAITHFUL — 1 new MEDIUM, 0 HIGH.** Flag stays `partial`. NOT blocking.

## Method (adversarial — different keywords than the brief used)

1. **Synonym/related-keyword re-scan** of the e2e folders for mock vectors the brief might have missed: `page.unroute`, `mockResponse`, `msw`, `voice-preview`, `trust-signals`, `contact`, `waitForTimeout`.
2. **Re-verify 3 random §7 claims** by re-reading source at the exact cited lines.
3. **Re-confirm 1 §15 web-fetch claim** (FastAPI optional-header) against an in-codebase precedent.

## Findings

### NEW MEDIUM — D1: mock scope under-coverage beyond {identity, visuals, personality}

The brief (and the spec's RN-1 / SC-2 grep-gate) scope the "backend-under-test" mock to **identity / visuals / personality**. The adversarial scan found the lisa-marca suite ALSO mocks:
- `voice-preview-mock.ts:202` → `page.unroute("**/api/v1/lisa/marca/personality")` and `voice-preview-mock.ts:115` → `voice-preview` endpoint.
- `lisa-marca-empty-state.spec.ts:102` → `contact`; `:124` → `trust-signals`.
- `lisa-marca.fixture.ts:368` → `contact`; `large-dataset.fixture.ts:136` → `trust-signals` (unroute).

The brief's §7 DOES enumerate `contact`/`trust`/`voice-preview` in the fixture line refs, but neither the brief's RN-1 framing nor the 04-validators SC-2 grep-gate covers `trust-signals` / `contact` / `voice-preview` as backend-under-test endpoints. **Impact:** a de-mock that only removes identity/visuals/personality mocks could leave the suite still mocking `contact`/`trust-signals`/`voice-preview` → partial honesty. Builder/architect should decide whether RN-1 extends to those (likely yes for `contact`/`trust-signals` which are real reads; `voice-preview` may be a legitimate mock like the 503 case). **Severity MEDIUM** — does not invalidate the brief, but widens the de-mock surface.

### CONFIRMED — claim A (§7): `get_prohibited_phrases` user_id required @584 but unused in body
Re-read `marca_router.py:582-602`: `user_id: str = Header(alias="X-User-ID")` @584 present; body uses only `tenant_uuid` + `country` (passed to `list_for_tenant(tenant_id=..., country=...)`). `user_id` never referenced. ✓ Brief correct.

### CONFIRMED — claim B (§7): `marca-voice-api.ts:113` sends `"X-User-ID": opts.tenantId`
Re-read lines 112-116: `"X-User-ID": opts.tenantId` exactly, with `"X-User-Role": opts.userRole ?? "owner"` @115. ✓ Brief correct.

### CONFIRMED — claim C (§7): `real-backend-forward.fixture.ts` does not exist
`ls` → ABSENT. ✓ Brief correct (T-1 creates it).

### CORROBORATED — §15 FastAPI optional-header claim
Brief: `Header(default=None, alias=...)` = optional; without default = required. Found in-codebase precedent `marca_router.py:181` `Header(alias="X-User-Role", default="")` — optional headers via `default=` already used in the same router. ✓ The sub-bug #1 one-line fix pattern is consistent with existing code. (Also matches fetched fastapi docs.)

## Discrepancy classification

| ID | Severity | Disposition |
|---|---|---|
| D1 mock-scope under-coverage (trust-signals/contact/voice-preview) | MEDIUM | Added to brief §11 as M3; flag stays `partial` |
| (all re-verified claims) | none | brief accurate at cited line refs |

## Net verdict

The brief is **faithful and accurate** — every spot-checked path:line holds, the existing-systems audit is correct, and the web-fetch summaries match both upstream docs and in-codebase precedent. The one new finding (D1) widens the de-mock scope but is a *completeness* note, not a *correctness* error. **No HIGH discrepancy. No factually-wrong claim. No dead web URL.** Flag remains `partial` (driven by the pre-existing M1/M2 + this new M3). Downstream `/dev-team` builder can consume the brief now, treating M1/M2/M3 as build-time decisions to resolve (not blockers).
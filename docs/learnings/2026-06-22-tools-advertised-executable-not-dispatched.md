# Tools advertised + executable ≠ the agent autonomously dispatches them

**Date:** 2026-06-22 · **Scope:** cross-brand (engine `core/luana-core-sales-agent` + any brand registering EP-3 tools) · **Severity:** 🟡 (end-state gap, not a crash) · **Origin:** /pm-vitalia self-paced lift loop, F-path verification of `vitalia-fase2-adrian-canal-inbound` OLA-2.

## What happened

After ESC-17 (the EP-3 handler ABI) was fixed and `share_doctor_profile` + `match_service_and_specialist` were proven to **execute live** (real registry + real dev DB → real URLs/recommendations), the F-path tried to verify the *end-state*: that Adrián (the sales_agent LLM) **dispatches** those tools in a real conversation.

It does not. Across 3 increasingly-explicit Telegram turns — ending with "recomendame el especialista para blanqueamiento y mandame el link de su perfil" — the specialist LLM emitted **zero `[TOOL_REQUEST]` blocks**. It answered conversationally (and at least once off-topic). The tools were:

- **advertised** — `application/prompts/compose.py::_extension_tools_hint` renders all 3 brand tools into the (cacheable) prompt, verified at runtime;
- **executable** — dispatch via `node_tool_executor → merged_tools()[name](state, db)` returns real results, verified in-container;
- **dispatchable in any stage** — `node_tool_executor` does not stage-gate.

…and yet the LLM never called them.

## The lesson (durable, promotable)

There is one more rung on the "registered ≠ executable" ladder (ESC-17 / `verification-real-not-200`):

> **registered → advertised → executable → _autonomously dispatched_.**

ESC-17 fixed *executable*. But a tool that is registered, advertised in the prompt, and callable under the engine ABI is **still not used** until the model actually emits the tool-call in conversation. For a text-protocol tool-call (`[TOOL_REQUEST: {...}]`) on a Chinese-first model (DeepSeek/Kimi), that is **not free** — it is an agentic-behavior property that must be **tuned and verified with eval goldens** (`tool-trajectory`, `G-objection-trust`), not assumed because the wiring is green.

**Rule:** a tool seam's end-state is verified by an eval golden that asserts the agent *emits the tool-call for the triggering intent* — not by proving the handler executes when called directly. "I dispatched it by hand and it worked" ≠ "the agent uses it." Treat autonomous-dispatch as its own gate (deterministic via pass^k goldens), owned by sales-agent-expert / builder-agentic flagship (stake-asymmetric: a prompt nudge without goldens can overfit one phrasing and regress others).

## Deeper diagnosis (2026-06-22, second pass — root located, fix path)

Drilled into WHY the agent doesn't dispatch. Ruled out the cheap causes, located the real one:

1. **Wiring is correct.** `build_specialist_system_prompt` (compose.py) assembles `STATIC_TOOLS_HINT`
   (`_TOOLS_HINT ⊕ _extension_tools_hint()` — engine ⊕ brand tools, verified rendering share/match) +
   the specialist body (`_render_static_specialist_body` → `prompt_loader.render("specialist_<role>")`).
   The brand tools ARE in the runtime prompt the model receives.
2. **No DB shadowing.** `prompt_versions` has 0 `specialist_*` rows → the file templates are what render
   (not a stale DB override).
3. **Structural gap (contributing, real).** Of the 3 specialist templates, only `specialist_closer.j2`
   has tool guidance — and it's HARDCODED engine tools with **concrete imperative examples**
   (`Para enviar link de pago: [TOOL_REQUEST: {"tool":"send_payment_link"}]`). `specialist_qualifier.j2`
   (discovery) and `specialist_product_expert.j2` (presentation) — the stages where share/match are
   scoped — have **zero** tool guidance. So the discovery/presentation specialists are never told they
   can act.
4. **Root: model + text-protocol.** Adding a *generic* tool-use directive to those specialists (verified
   present in the runtime prompt) did NOT make deepseek emit `[TOOL_REQUEST]` (still 0). The closer works
   because of **concrete few-shot examples**, not an abstract directive. So the deepseek specialist needs
   either concrete per-tool examples or native function-calling to reliably tool-call via the text protocol.

**Why no quick ship.** A generic directive (unverified) was REVERTED — shipping an agent-behavior change to
4 brands without pass^k goldens is exactly the stake-asymmetric anti-pattern this learning warns about
(LLM dispatch is stochastic — one webhook ≠ proof). "Best practices" for stochastic agent behavior = measure
with goldens, then tune — not a blind prompt change.

**Fix path (principled, gated by goldens — a focused builder-agentic effort):**
- Build the `tool-trajectory` / `G-objection-trust` eval goldens (the measurement: does the agent emit the
  tool-call for "who attends / recommend a specialist" at pass^k?).
- Then iterate against them, cheapest lever first: (a) make `_extension_tools_hint` render each brand tool
  as a **concrete imperative example** (hexagonal — derived dynamically from the brand tool's description,
  no engine hardcoding; mirrors the closer's working pattern) + add the directive to qualifier/product_expert;
  (b) if still flaky, **native function-calling** (`tools=` param) instead of the text `[TOOL_REQUEST]`
  protocol (larger engine change); (c) model selection for the specialist role.
- The structural gap (#3) is a genuine fix but must land WITH the goldens so its effect is measured.

## Measured outcome (third pass — lever applied + live-measured)

Built a **live-dispatch measurement** (the goldens-driven gate the synthetic pass^k runner lacks): K fresh-chat
webhook trials with a "who attends / share the profile" message → count real `share/match` dispatches in logs.
(The existing `test_pass_k_evaluation.py` is a *synthetic* grader — it scores the SCRIPTED golden turns, never
runs the graph live; `tool-trajectory` just checks `expected_tools_trajectory` is non-empty. So it cannot catch
this — the embudo. A live trajectory eval is the missing piece.)

Applied lever (a): `_extension_tools_hint` now renders each brand tool as a **concrete imperative
`[TOOL_REQUEST]` example** (args derived dynamically from the tool schema, hexagonal) + a stronger "USALA"
header — in the shared `STATIC_TOOLS_HINT` slot, so it reaches all 3 specialists (no per-template edit needed;
cache-safe, 65 compose tests green). Committed `98304184` → promoted to main `b84aacdf` + sync-all.

**Result: 0/4 → 1/4 dispatches.** Real improvement, but **below the pass^k bar (0.5)**. The text-`[TOOL_REQUEST]`
protocol on deepseek caps here — concrete examples help but don't make it reliable.

**Conclusion: reliable autonomous dispatch needs native function-calling** (pass `tools=` to the LLM call,
parse `tool_calls` from the structured response, drop the text-`[TOOL_REQUEST]` parsing) — a **core agent-loop
refactor** touching the specialist LLM call site + response parsing + the `[TOOL_REQUEST]` prompt instructions,
shared by ALL brands. Stake-asymmetric → ESCALATED to Chris as its own focused builder-agentic effort, gated by
the live-dispatch eval (target ≥0.5 pass^k). The concrete-example lever stays (strictly-better; it's the
tool-description form native-calling also consumes).

## Native function-calling (fourth pass — mechanism built, real bottleneck found)

Built native function-calling (`fe02df19`, on wip/vitalia, NOT promoted): `llm.base.ToolCallResult`
+ `generate_with_tools` (additive, text fallback) · litellm provider `bind_tools` + `AIMessage.tool_calls`
parsing · `tools/registry.extension_tool_schemas(stage)` (brand tools → OpenAI schemas, hexagonal) · the 3
specialists offer their stage's brand tools natively, serializing native `tool_calls` → `[TOOL_REQUEST]` so
the existing routing dispatches (no routing change). 0 net-new test failures; llm 67 green.

**Feasibility: isolated `bind_tools` dispatches 3/3** (right tool + args, across deepseek-reasoner /
deepseek-chat / kimi) — the native mechanism works perfectly. **But live graph dispatch ≈ 30%** (noisy K=5:
text-examples 1/4, native 2/5, native+directive 1/5 — all within noise of ~30%).

**The real bottleneck is NOT the tool mechanism — it is the multi-agent graph:**
- The supervisor (NANO) routes turn-1 of a fresh conversation to the **qualifier** (discovery), whose role
  prompt is "SPIN discovery — NO pitchees, máximo 1 pregunta, DA ANTES DE PEDIR" → it **asks a question
  instead of acting**, even when the lead directly asks "who attends / share the profile". `product_expert`
  (presentation) is the one that shares — but the conversation has to be routed there.
- A generic "respond to direct requests with a tool" directive on qualifier/product_expert did NOT move the
  needle (within K=5 noise) → reverted (don't ship unverified).

**Conclusion — reliable autonomous dispatch (≥0.5 pass^k) needs, on top of native-calling:**
1. **Supervisor-routing tuning** — route "who attends / show me the doctor / recommend a specialist" to a
   tool-acting specialist (presentation) instead of qualifier (discovery-asks).
2. **Specialist role-prompt rework** — so a direct request is honored with a tool without breaking the
   discovery "don't pitch" discipline.
3. **A larger-K live eval** (K≈15–30, ~15–30 min/run) — K=5 is too noisy to distinguish levers; the
   routing/persona tuning MUST be measured against a stable eval, not single noisy runs.
This is a focused builder-agentic continuation (stake-asymmetric, graph-behavior). Native-calling (the correct
mechanism) is held on wip/vitalia as its foundation; the concrete-example lever (`98304184`) is on main and
helps the text fallback. End-state demo now dispatches ~30% of the time (vs 0%) — not yet reliable.

## Root cause located + FIXED (fifth pass — native dispatch reliable)

The fourth-pass conclusion ("real bottleneck = multi-agent graph routing") was **WRONG**.
Direct, probe-instrumented live measurement found native function-calling **never ran in the
live graph at all** — three wiring bugs in the `fe02df19` foundation masked it entirely.
The "~30%" was pure text-`[TOOL_REQUEST]` fallback; the isolated "3/3" used un-namespaced
names so it never hit the real blocker.

**The three bugs (all engine, all in the native-calling path):**

1. **`MultiRoleLLMRouter` did not override `generate_with_tools`.** The live specialist service
   IS the router (`_get_llm_service` → `MultiRoleLLMRouter`), which inherited `BaseLLMService`'s
   **text-only fallback** → `bind_tools` was never called, brand tools never offered to the LLM.
   Fix: router override delegates to `self._resolve(role).generate_with_tools(...)` (`router.py`).
2. **Dotted tool names → DeepSeek/OpenAI 400.** EP-3 tools are namespaced `{brand}.{tool}`
   (`vitalia.share_doctor_profile`); the providers require function names to match
   `^[a-zA-Z0-9_-]+$` — a **dot is rejected**. Every native call 400'd and silently fell back to
   text. Fix: `_sanitize_tool_name` (`.`→`-`, both valid) in `extension_tool_schemas` +
   `desanitize_tool_name` before registry dispatch in `nodes._specialist_content` (`registry.py`,
   `nodes.py`). No tool name contains a literal `-`, so the round-trip is lossless.
3. **The live-dispatch metric undercounted.** The brand tool only logs on the data-success path;
   a dispatch with an unseeded `service_intent` (e.g. "blanqueamiento dental") returns `not_found`
   **without logging** → real dispatches looked like zero. Fix: a durable `sales_agent.tool_dispatched`
   seam log in `node_tool_executor` (fires once per execution, post per-turn dedup, regardless of
   data outcome) + per-conversation rate = distinct `user_id`.

Once the dot was sanitized, **all three models (deepseek-reasoner / deepseek-chat / kimi) emit
`tool_calls` reliably with the FULL persona prompt** — the reasoner "narrates instead of calling"
symptom was the 400-fallback, not a model limitation. **No supervisor-routing change, no persona
rework, no model swap, no prompt directive was needed** (all experimented with and reverted —
the qualifier dispatches fine with tools bound).

**Measured (live, durable seam metric, default REASONING model, no extra levers):**
- explicit "recomendame el especialista y mandame el link" → **20/20 conversations dispatched (1.00)**
- softer "quiero hacerme una limpieza dental, ¿qué recomiendan?" → **12/12 (1.00)**
- share-focused "pasame el perfil del odontólogo con su link" → **8/12 (0.67)** (≈0.89 among processed)

vs **0** before. Bar (≥0.5 pass^k) met robustly across phrasings. Tools: `router.py` +
`registry.py` + `nodes.py`; regression tests `test_router_litellm_dispatch.py::...delegates_to_provider`
+ `test_extension_tool_schemas.py`; live harness `core/luana-core-sales-agent/scripts/live_dispatch_eval.sh`.

**Durable lesson — append to the dispatch ladder:**
> registered → advertised → executable → **wired through the runtime service (not just the leaf
> provider)** → **the tool NAME is provider-valid** → autonomously dispatched.
> "Isolated `bind_tools` works 3/3" ≠ "it runs live": the live service may be a wrapper/router that
> doesn't expose the native method, and a namespaced tool name a unit test never sends will 400 in prod.
> A "graph routing / persona" conclusion drawn while the mechanism silently falls back is a phantom —
> instrument the actual call (did it take the native branch? how many `tool_calls` came back? did the
> provider 400?) before tuning behavior. The live-trajectory eval is what exposed it; the synthetic
> pass^k runner never could.

## Refs

- `vitalia/docs/product/stories/vitalia-fase2-adrian-canal-inbound/demo-script.md` § F-path finding (the live evidence + the seam-exercise proof)
- `docs/learnings/2026-06-22-ep3-tool-handler-abi-mismatch.md` (ESC-17 — the *executable* rung)
- `[[verification-real-not-200]]` · `[[embudo-imagined-contract-never-integrated]]`
- Eval goldens (deferred): `04-validators.yaml` agentic_eval `tool-trajectory` + `G-objection-trust`

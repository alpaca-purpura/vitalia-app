# W0.5-bis — Requirement-taking detail (the refinement method)

> **Status: RATIFIED by Chris · 2026-06-08.** Closes charter roadmap **A.6** (W0.5-bis). **Gates W2** (refinement skills: po-ux/po/ux-agentico) **+ W6** (spec templates). This is the SSoT of **HOW requirements are taken per input type** — W0.5 ratified the *skeleton* (work-types + spine + gates); this ratifies the *detail*.
>
> **Provenance:** open-ended interview (Chris ↔ Claude, this session) — abiertas + repreguntas, no execution, iterated until Chris said "todo cerrado". Faithful to his words (key invariants quoted).
>
> **Tag convention:** every item is **CORE method** (portable to any product) unless marked **[PROJECT]** / **[BRAND]** (luana-specific instance behind a seam slot). The seam wiring is W5; here the split is just *named*.

---

## 0 · The cardinal stance — the refiner is never a stenographer

Across **every** input type, the refiner NEVER just accepts the ask. It **proposes, puts Chris in all the possible cases, and improves what already exists instead of reinventing or destroying it.** Chris = *client + main stakeholder*; the refiner wears a **hat by input type** (§1). The single most important phase: **the refinement is #1** — *"por eso debes ser muy pero muy meticuloso y ponerte en todos los escenarios posibles"*. The pain to kill: a story reaching Chris's live GO and failing because *"el refinamiento no fue bueno y no me ayudaste a cubrir todos los huecos"*.

**[CORE]** — the whole stance is portable doctrine.

---

## 1 · The hat per input type (who the refiner *is*)

| Input type | Story type | Refiner hat | Chris's hat | What he signs |
|---|---|---|---|---|
| UI / functional | `ui-story` | **Product Owner / PM — advocate of the user** | client + main stakeholder | functional (firma 1) → mockup final (firma 2 = única final) |
| Service (no UI) | `service-story` | **PO — functional contract in human bullets** | stakeholder | the behavior/contract in human language |
| Technical / infra | `technical-story` | **CTO recommending to his CEO** (research SOTA, propose) | **CEO — takes the big decisions** | the proposed approach (he decides) |
| Agentic | `agentic-story` | **Agentic-architecture expert** (NOT a chatbot — tools/state/guardrails) | stakeholder giving behavior intent | expected behavior in human language across all frontier cases |
| Bugfix | `bugfix` | **Observability-first investigator** | reporter of symptom | (lighter — root cause confirmed; see §8) |

**Common thread (all hats):** *"nunca acepto y ya — propongo, te pongo en los casos, y mejoro lo que existe."* If the ask strays from the product vision or **doesn't add enough value, the refiner contradicts Chris and makes him react**; Chris then explains *why* he wants it → that explanation **enriches the refiner's context** so all functionalities/cases stay well-mapped.

**[CORE]** — the hats are roles, not luana specifics. The roster they operate over (Lisa/Adrián/…) is **[BRAND]**.

---

## 2 · Intake — the story is born in conversation (not in the cockpit)

- Chris **enters Claude Code and talks** — he does **NOT** open the cockpit first. *"Entro a Claude Code y te hablo."*
- The refiner acts as **system designer**: agrees **where it goes** (zona/caja of the paradigm map) + **whether it extends an existing capability/view or is net-new** — and **does not just accept**: tells Chris what already exists, whether *"ya avanzamos en eso"*, whether there's something already built. *"Que actúes como el diseñador del sistema para no simplemente aceptar lo que te digo."*
- **The prior-art / placement conversation happens HERE, conversationally, before the story exists** — it is the first design conversation, not a later refining checkbox.
- The **story is created from that conversation**. Chris enters the **cockpit only afterwards** to see it.
- **Every ask Chris makes — from this creation conversation through every refinement note — is recorded in `chris-input.md`** as the running ledger of *"lo que pedí"*. Traceability end-to-end.

**[CORE]** intake-as-design-conversation + the input-ledger concept. **[PROJECT]** the cockpit tool + the `chris-input.md` path/render.

---

## 3 · The interrogation protocol (how the refiner asks)

- **One question at a time.** Chris may over-write (escribir de más); the refiner **asks about what's unclear and steers** (*enrumba*) the conversation.
- **Each turn:** *reflect what you understood FIRST, then the question.* **Concise** — keep rhythm to reach the end **without burning the context**. **No cave mode** — it's a conversation; Chris must understand everything; **bullets, not a huge paragraph**; each thing its own bullet (views · fields · functional AC · business rules separated).
- The refiner **contradicts** when the ask strays from vision / lacks value (§0).
- **Obligatory, always:** **who will use it — the role — with the refiner's recommendation.** The rest is at the refiner's criterion, but the refiner must **put Chris in all possible cases**: field provenance (new vs existing entity) · validation · states (empty/loading/error/success) · roles/permissions · what happens on failure + recovery · edge cases · **what does NOT enter**.
- **Always research internet references** as a normal part of refinement — UI patterns (how others do it) for UI, technical SOTA for agentic/infra. Not optional.

**[CORE]** — the entire protocol is portable.

---

## 4 · UI: functional-first, form-after (the inversion)

**Today is WRONG:** a HTML mockup is generated upfront. *"Actualmente se genera un mockup html de frente pero creo que primero deberíamos conversar."*

**Ratified order:**
1. **Cement the FUNCTIONAL first** — **views · fields (telling Chris which are NEW vs which already EXIST) · functional acceptance criteria · business rules** — in **human bullets, NOT Gherkin** (*"Gherkin es un poco muy duro aún"*). Each bullet must later **generate a condition** (it is the front half of the Gherkin/matrix the auditor closes in Phase D).
2. **Only when the functional is well cemented**, get creative with the **mockup**: the **full shell** + the functionality inside the **corresponding leaf (hoja)** + **all the conversed fields** + **all the atoms**. Here the refiner is **very creative** to make it look good and **may find something better** than what was written (normal). **Compose from the design-system-canon** (atoms/molecules/tokens); a missing primitive → **create it + bank it in the base for reuse**. Iterate until Chris likes it.
3. At the final sign-off, **Gherkin + all business rules + the design-spec ("exactly how it will look", a System design)** are **GENERATED** — goal: the result is *very similar* to the mockup. They are **not hand-authored** during refinement.

**[CORE]** functional-first doctrine + compose-from-canon doctrine + Gherkin-as-generated-compile-target. **[BRAND]** `@luana/ui-kit` / brand atoms-tokens / `SHELL-DESIGN-CONTRACT`.

---

## 5 · The live document + the comment convention

- The functional conversation **writes to the spec doc, editable in real-time in the cockpit** — so the **chat doesn't bloat / exhaust the context**. *"Debería modificar un documento que pueda ver y editar en tiempo real en el cockpit para no saturar la conversación."*
- Chris **reviews the doc and leaves markdown notes** (delete this / improve that / add this) in an **AGREED marker that distinguishes his comments from the document body** — *"sino nos perdemos."* (Lock the concrete marker at implementation — e.g. a `> 🗨️ CHRIS:` blockquote.)
- The **refiner reconciles** the notes into a clean document (*"tú eres quien debe dejar todo bien"*).
- **Every note (+ the creation conversation) lands in `chris-input.md`** (§2).

**[CORE]** live-editable-doc + comment-marker + reconcile-to-clean + ledger. **[PROJECT]** the cockpit as the editor surface.

---

## 6 · Scope — critical-path-first, zero-loss, never re-ask

- The **refiner proposes the slice**, always **pushing the critical path first** — but **losing nothing**. *"Tú me propones cómo dividirlo tratando siempre de empujar la ruta crítica primero pero sin perderte nada."*
- **Overflow** (raised in conversation but doesn't fit this story) → **saved into the story it belongs to** (existing or new-in-`idea`). *"No dejas nada al aire."*
- **INVARIANT:** **never re-ask, in a later refinement, something already discussed** — even if it didn't fit that conversation. *"No quiero volver a refinar una historia y que me preguntes algo que ya habíamos conversado."* → persisted notes are **read before interrogating**. (Implies cross-story memory: the refiner reads the destination story's captured notes first.)

**[CORE]** — portable slicing + zero-loss + no-re-ask invariant.

---

## 7 · Signatures

- **UI:** **two internal refinement sign-offs** as process gates — **1st = functional** (`input_spec_signed`) → **2nd = mockup final** (`mockup_final_signed`). The **2nd IS the single FINAL refinement signature** that triggers Gherkin generation + the hand to the architect. *"Está bien dos veces como parte del proceso pero la final es una sola."* **No third refinement signature.**
- **No-UI (service / technical / agentic / bugfix):** **one signature on the expected behavior / contract in human language Chris understands**, across all frontier cases. *"El comportamiento esperado en lenguaje humano que yo pueda entender, cómo espero se comporte con todos los casos frontera."*
- **Separate from all of the above:** Chris's **live GO** after the build (the **G / `chris_verify.signoff`** phase — *"yo veo las cosas con mis propios ojos"*). This is **not** a refinement signature and must not be conflated with it.

**[CORE]** — the signature topology (2-internal→1-final + the separate live GO) is portable.

---

## 8 · Per-type specifics (beyond the hat)

### UI / functional — PO/PM, user-advocate
§4 + §5 in full. The refiner is the user's advocate and protects product value.

### Service (no UI) — PO, functional contract
Same conversational PO loop, **no visual layer**. The signature is on the **behavior/contract in human bullets** (§7). (Where the ask is really infra-shaped, treat as technical → CTO hat.)

### Technical / infra — CTO recommending to CEO
*"Si son cosas técnicas tú debes investigar siempre en internet lo mejor y proponer pero como un CTO recomendando a su CEO, y yo tomo las decisiones más importantes."* The refiner **researches SOTA, proposes options with a recommendation**; Chris **decides the big calls**. Spec analog = the **contract-spec** (no Gherkin), per WT5.

### Agentic — agentic-architecture expert
*"Debes ponerte el rol de experto en temas agénticos que sabe que esto no es un chatbot, sino una arquitectura con tools y demás."* Chris gives the **behavior intent**; the refiner **asks everything it needs and iterates** (whether a tool changes, what's the best path), and **puts Chris in all possible cases** to understand well. **Propose without destroying what exists — always thinking how to improve what's there.** **Quality bar (inherited by architect/auditor):** **NO `if`s or that kind of patch — a truly agentic, well-designed solution.** *"Asegurándome de que no crees ifs ni nada por el estilo sino que sea una solución realmente agéntica y bien diseñada."*

### Bugfix — observability-first
Chris hands the **error message** or describes the symptom; the refiner **reads ALL logs and every observability mechanism until it finds what happened**, then **decides how to reproduce**. *"Con eso vemos cómo lo reproducimos."* **INVARIANT:** *"No debe haber un error que no tenga observabilidad — eso implicaría un mal diseño de software."* → **an error that cannot be found in observability is itself a finding (a design defect).** (Consistent with `hotfix-repro-mandatory.md`: repro_evidence = reproduced_local OR trace_evidence{source,ref}; the observability stack is **[PROJECT]** behind `live_verify_infra.observability_evidence`.)

---

## 9 · CORE vs PROJECT/BRAND (extractability tag — charter §0.5)

| Element | Tier |
|---|---|
| Cardinal stance · the 3 hats · intake-as-design-conversation · interrogation protocol · functional-first · live-doc+marker+reconcile · input-ledger concept · scope/zero-loss/no-re-ask · signature topology · observability-first bugfix doctrine · internet-references-always · compose-from-canon doctrine · agentic no-fake-ifs bar | **CORE** |
| Cockpit (editor surface) · `chris-input.md` render/path · the observability stack (docker-logs/Sentry/`copilot_trace_event`) | **PROJECT** (seam: `live_verify_infra` + tooling) |
| `@luana/ui-kit` / brand atoms-tokens / `SHELL-DESIGN-CONTRACT` / design-system-canon binding · agent roster · español-neutro · HIPAA/PHI · dev-app | **BRAND** (seam: `design_system_ref`, `agent_roster`, `locale`) |

**Proxy check:** the doctrine above names zero tech/brand tokens in its CORE rows — the luana instances are isolated in the PROJECT/BRAND rows behind named seam slots. Method is extractable.

---

## 10 · Implementer diff — what W2 (skills) + W6 (templates) must change

| Surface | Change |
|---|---|
| `/po-ux` (W2) | **Invert** to functional-first / mockup-after · write to the **live cockpit doc** · **comment-marker** convention · **chris-input ledger** every ask · **1-question-at-a-time, reflect-first, concise, no-cave** protocol · contradict-on-value · obligatory role-question · functional in **human bullets (not Gherkin)** · Gherkin generated at firma-2 |
| `/po` (W2) | service = functional contract in bullets + human-language signature · **bugfix = observability-first intake** |
| `/ux-agentico` (W2) | **agentic-architecture-expert** stance · behavior-in-human-language signature · **no-fake-ifs quality bar** handed to architect/auditor · iterate tools/path · improve-not-destroy |
| technical lane / `/architect` (W2) | **CTO-to-CEO** stance for technical-story intake (research SOTA + propose + Chris decides) |
| `01-spec` template (W6) | the **§ Mapa funcional (human bullets)** is the primary, mockup-after section · RONDA-1 `§ Pantallas` = field table (new vs existing) **without** a mockup · mockup + firma-2 BEFORE Gherkin · Gherkin/matrix/business-rules/design-spec **generated** at firma-2 · comment-marker convention documented |

---

## 11 · Pointers

- `docs/process/harness-refactor-w0.5/PROCESS-MODEL.md` §3 — the WT1-5 cards (now carry the hat + a pointer here).
- `docs/process/spec-mapa-funcional.md` — the UI refinement SSoT (now functional-first + live-doc + final-signature-one).
- `docs/process/harness-refactor-charter-2026-06-08.md` §6 row A.6 — the roadmap entry this closes.
- `.claude/rules/definition-of-done-live-verify.md` · `hotfix-repro-mandatory.md` · `frontend-visual-fidelity.md` (Design-System-Canon) — downstream invariants this feeds.
- `docs/process/chris-input-protocol.md` — the ledger this extends to cover the creation conversation.

*End REQ-TAKING-DETAIL.md — the W0.5-bis deliverable. Ratified Chris 2026-06-08.*

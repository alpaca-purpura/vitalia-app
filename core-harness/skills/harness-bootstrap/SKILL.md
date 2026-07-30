---
name: harness-bootstrap
description: Bootstrap the extractable dev-process harness into a fresh product repo — copy the core rules into .claude/rules/, write a project.config.yaml stub, run a DETECTION SWEEP over the repo's lockfiles/build-files that PROPOSES seam values with provenance (the operator signs; nothing is written unsigned), and run the doctor to certify. Use when dropping core-harness/ into a new repo, or when the user asks to "bootstrap the harness", "set up the process kit", "install core-harness", "instancia el arnés", or "qué le falta al harness en este proyecto".
---

# /harness:bootstrap — install the dev-process kit into a new product

> **The extraction-bootstrap (program DoD).** Runs in the ADOPTER's repo after `core-harness/` is dropped in. Inert in the source product (whose harness is already live natively via `.claude/`); shipped via the `harness` plugin for OTHER products. The kit (`core-harness/rules,skills,agents,hooks,templates,process,scripts`) is populated and W8-verified (extraction-test passing).

## What this does (the "detect what's missing + fill it" step)

A new product drops `core-harness/` + an empty `project.config.yaml` into its repo. This skill:

1. **Re-expose the core to Claude Code** (the ratified Option-C mechanism · see `core-harness/README.md`):
   - **rules** → `ln -s` each `core-harness/rules/*.md` into `.claude/rules/` (symlink is DOCUMENTED-SAFE for `.claude/rules/`; recursive, circular-safe).
   - **agents** → copy `core-harness/agents/*` into `.claude/agents/` (agents-symlink is undocumented — copy is safe).
   - **skills** → the harness plugin already namespaces them; OR copy into `.claude/skills/`.
   - **hooks** → ensure `settings.json` (or the plugin `hooks.json`) points at `core-harness/hooks/*` (incl. the SessionStart slim-rule injector).
   - **templates / process-docs / scripts** → symlink-back at the conventional path (read-by-path → OS resolves).
2. **Write a `project.config.yaml` stub** (all slots `__FILL_ME__`) at the repo root if absent.
3. **DETECTION SWEEP (the instanciador v1 — KIT-04/KIT-02).** The install stops being a
   photocopier and becomes surveyor + notary: read the repo's EVIDENCE and propose seam
   values — the lockfiles are the SSoT, never a static language→tooling table.
   - **Detect:** walk the repo root for the ecosystem's own EVIDENCE files — dependency
     manifests, lockfiles, build descriptors, container/CI descriptors. Propose ONLY
     what those files DECLARE: the exact test/lint/typecheck/build commands, frameworks
     and versions the client's repo itself evidences (declared scripts, dev-dependency
     trees, target-framework fields). The CLASS never carries a language→tooling table
     and never names stacks (I-52 · KIT-02 corrección (a)); the repo's files are the
     sole source of tool names — quote them verbatim as provenance.
   - **Propose per slot, WITH PROVENANCE:** for each detectable slot (`toolchain` ·
     `domain_modules` (top-level src dirs/packages) · `engine_prefix` (shared-code
     scope/module prefix if visible)), present the proposed value naming the exact file
     that evidences it. Undetectable slots (locale · live_verify_infra ·
     design_system_ref · agent_roster · value_stream · sistemas/vertical) stay
     `__FILL_ME__` — the doctor keeps declaring them; do NOT guess business facts.
   - **Sign (automatic ≠ unsigned):** present the proposals via AskUserQuestion (one
     question per slot or grouped). A rejected proposal is NOT written — record the
     operator's correction instead. NEVER write a seam value without a signature.
   - **Write:** signed values replace their `__FILL_ME__` only. Slots already filled are
     NEVER overwritten by a re-run (re-instanciación segura); propose changes to filled
     slots only if the operator explicitly asks to re-survey.
   - The sweep fills VALUES and selects — it NEVER generates per-client component code
     (that would fork the CLASS and break upstream propagation).
4. **Run the doctor:** `python core-harness/scripts/harness_config.py --doctor` → it walks the schema and lists every unfilled slot (toolchain · sistemas · locale · engine_prefix · live_verify_infra · design_system_ref · domain_modules · agent_roster · value_stream · wip_caps). Exit 3 while any `__FILL_ME__` remains.
5. **Telemetry smoke (if installed as the plugin):** confirm `~/.prenter/telemetry/<project>/trazas.jsonl` gains a span after this session's first Stop — the harness is born MEASURABLE (KIT-03). No egress config = local sink only (expected default).
6. **Report** the unfilled slots + a one-line "fill these, then idea→done runs without editing the CORE" (multisistema = `sistemas.active` with a single entry).

## The contract (what the adopter fills, what the core never names)

The CORE reads the **seam** (`project.config.yaml`) for every tech/sistema/locale/engine/live-env fact. The adopter fills the slots; the CORE rules/skills/agents/hooks/templates/process stay byte-identical across products. A new tech stack = new `toolchain`/`domain_modules` slot values; a single-sistema product = `sistemas.active: [one]`. **No core file is edited to adopt the harness.**

## Pointers
- `core-harness/README.md` — the kit structure + the Option-C re-expose mechanism + the extraction procedure.
- `core-harness/scripts/harness_config.py --doctor` — the slot-gap detector (the W8 extraction-test gate).
- `docs/process/harness-refactor-charter-2026-06-08.md §8` — the program DoD (the extraction test).

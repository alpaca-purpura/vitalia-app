# W5a — DIP seam: `project.config.yaml` loader mechanism (date-aware research)

> **Date:** 2026-06-09 · **Model:** Opus 4.x via Claude Code CLI · **Env:** `yq` NOT installed, PyYAML present, bash already shells `${WS}/.venv/bin/python`.
> **Method:** verified against OFFICIAL Claude Code docs (`code.claude.com/docs`) fetched 2026-06-09, not model memory.

---

## TL;DR verdicts per consumer class

| Class | Consumer | Verdict on the seam |
|---|---|---|
| **D** | markdown instruction files (rules/skills/agents/templates, loaded as CONTEXT) | **NO native interpolation of arbitrary config in plain `.md`/rules/`CLAUDE.md`.** Use a **CONVENTION** (`{slot}` plain text + "resolved from `project.config.yaml`" note → model reads the yaml on demand). **One genuine native exception exists for SKILLS only**: `` !`<cmd>` `` dynamic context injection inlines a command's OUTPUT at skill-load time, and a hook's `additionalContext` can inject values — neither works in bare rules/CLAUDE.md. |
| **A** | bash + git-hooks | **Option (a): a python helper `harness_config.py`, called `.venv/bin/python -m harness_config <slot>`.** Single parser, single store, zero drift. NOT a generated `.env` (second store → drift). |
| **C** | Next.js 16 cockpit (TS) | `js-yaml` parsed in a **server-only lib loader**, typed against an interface, path via `process.cwd()`. No build-step coupling; one App-Router gotcha (below). |
| **Q4** | file location/format | **Root `project.config.yaml`, YAML.** Good for an extractable kit. Reasons + doctor pattern below. |

---

## Q1 — markdown loaded as context (the critical one)

### Does Claude Code interpolate `{placeholder}` / `${VAR}` / `@import` inside `.claude/rules/*.md` / skills / `CLAUDE.md`?

**No general-purpose interpolation of an external config value in plain instruction markdown.** The four mechanisms that exist, and exactly what each does:

**1. `@path` imports (CLAUDE.md only) — inject CONTENT, do NOT reduce tokens, md-oriented.**
Official memory doc:
> "CLAUDE.md files can import additional files using `@path/to/import` syntax. Imported files are expanded and loaded into context at launch alongside the CLAUDE.md that references them." — <https://code.claude.com/docs/en/memory>

> "Splitting into `@path` imports helps organization but **does not reduce context, since imported files load at launch.**" — same page, "My CLAUDE.md is too large".

- It injects the **whole file body inline** as text. It is **string concatenation, not interpolation** — there is no `{slot}` substitution; the importer cannot pull a single value out, it gets the entire file.
- The doc's examples are `@README`, `@package.json`, `@docs/git-instructions.md`. A yaml import would dump the raw YAML text verbatim into context (the model would then have to parse it). There is no documented yaml-aware import; it is "expand file content as text."
- **Cost-negative for our goal:** importing `project.config.yaml` into `CLAUDE.md` would burn tokens on every session for values most rules never need. Imports only live in `CLAUDE.md`/`CLAUDE.local.md` — **rules in `.claude/rules/*.md` do NOT support `@import`** (the doc describes imports solely as a CLAUDE.md feature).

**2. settings.json `env` — NOT visible to the model.**
The model never sees `env` vars in its context. They reach Bash/hooks only:
> "Settings rules are enforced by the client... CLAUDE.md instructions shape Claude's behavior." Settings table routes "Environment variables and API provider routing" to managed settings `env`, while "Behavioral instructions for Claude" go to CLAUDE.md. — <https://code.claude.com/docs/en/memory> (managed-settings table)

The context-window doc confirms the inverse boundary for stdout/env: plain hook stdout on exit 0 "is written to the debug log only," it does not enter context. — <https://code.claude.com/docs/en/context-window>
→ **An `${VAR}` written in a rule is just literal text to the model; the model does not resolve settings env.**

**3. Skills `string substitution` — a CLOSED set, NOT arbitrary config.**
Skills support substitution, but only for this fixed table (no "read slot X from config.yaml"):
> `$ARGUMENTS`, `$ARGUMENTS[N]`, `$N`, `$name` (declared args), `${CLAUDE_SESSION_ID}`, `${CLAUDE_EFFORT}`, `${CLAUDE_SKILL_DIR}`. — <https://code.claude.com/docs/en/skills> ("Available string substitutions")

There is **no `${config:...}` / `${project.X}` token.** So a skill cannot natively interpolate `project.config.yaml.engine_prefix`.

**4. ★ Skills `!`<command>`` dynamic context injection — the ONE real native escape hatch (skills only).**
> "The `` !`<command>` `` syntax runs shell commands before the skill content is sent to Claude. The command output replaces the placeholder, so Claude receives actual data... This is preprocessing, not something Claude executes. Claude only sees the final result." — <https://code.claude.com/docs/en/skills> ("Inject dynamic context")

This **is** genuine native interpolation of a computed value at load time. A skill could write:
```
Engine package prefix for this project: !`${WS}/.venv/bin/python -m harness_config engine_prefix`
```
and the model receives the resolved value inline, never the command. Caveats: (a) **skills only** — not rules, not `CLAUDE.md`; (b) runs **every time the skill loads** (recurring token cost, but tiny for one value); (c) can be globally disabled via `disableSkillShellExecution: true` (managed-settings kill-switch) — so a kit must not *depend* on it for correctness; (d) substitution runs once, output is not re-scanned.

**5. (adjacent) Hook `additionalContext` — injects into context, but it is a hook not a markdown file.**
> "A PostToolUse hook... reports back via `hookSpecificOutput.additionalContext`. **That field enters Claude's context.** Plain stdout on exit 0 does not." — <https://code.claude.com/docs/en/context-window>
A `SessionStart`/`InstructionsLoaded` hook could read `project.config.yaml` and inject resolved slots as `additionalContext`. Real, but that's the class-A python-helper path wearing a hook hat, not markdown templating.

### CONCLUSION (Q1)
**For bare rules / `CLAUDE.md` / agents / templates loaded as context, there is NO native interpolation. The seam MUST be a CONVENTION:**

> The markdown writes the slot as plain prose, e.g. *"the engine lives under `{engine_prefix}/` (resolved from `project.config.yaml` → `engine_prefix`)"*, and the MODEL reads `project.config.yaml` with the Read tool when it needs the concrete value.

This is robust, kit-portable, and kill-switch-proof. **Optionally**, for hot paths inside *skills* (e.g. a PM/architect skill that always needs `brands[]` or `engine_prefix`), upgrade the convention to native resolution with one `` !`python -m harness_config <slot>` `` line — same helper as class A, zero second store. Keep that as an enhancement, never a dependency (it can be policy-disabled).

**Doc citations:** memory (imports = inline content, no reduce, CLAUDE.md-only; env not in context) <https://code.claude.com/docs/en/memory> · skills (closed substitution set; `` !`cmd` `` injection) <https://code.claude.com/docs/en/skills> · context-window (env/stdout not in context; additionalContext is) <https://code.claude.com/docs/en/context-window>.

---

## Q2 — bash reads YAML with no `yq`

**Recommend (a): a python helper module `harness_config.py`, invoked `${WS}/.venv/bin/python -m harness_config <slot>`.**

Rationale (DRY / single-parser / no-second-store):
- **One parser.** Bash and python read the SAME `project.config.yaml` through the SAME PyYAML `safe_load` (PyYAML docs: always `safe_load` for config — `load()` allows arbitrary code exec). Python scripts already `import yaml`; the helper IS the python read path, so bash and python can't diverge.
- **No second store.** Option (b) generates a derived `.env`/shell file from the yaml at install time. That creates a **second copy** of the truth that goes stale the moment someone edits the yaml without re-running the generator — exactly the drift the DIP seam exists to kill. (Acceptable only as an opt-in perf cache, regenerated by a hook, never the source.)
- **No N copies of the parse incantation.** Option (c) inline `python -c "import yaml..."` duplicates the load+navigate+error-handling logic across every hook/script → unmaintainable, no typed errors, no "unfilled slot" diagnostics.

Helper contract (sketch — load-bearing bits):
```python
# scripts/harness_config.py  (or core-harness/loader/harness_config.py)
# Usage: python -m harness_config <dotted.slot>   -> prints value, exit 0
#        missing/unfilled slot                     -> stderr + exit 3 (doctor-detectable)
import sys, yaml, pathlib
def load():
    p = pathlib.Path(__file__).resolve()
    # walk up to repo root holding project.config.yaml
    for d in [p, *p.parents]:
        cfg = d / "project.config.yaml"
        if cfg.exists():
            return yaml.safe_load(cfg.read_text()) or {}
    sys.exit("project.config.yaml not found", )
```
Bash call site stays a one-liner:
```bash
ENGINE_PREFIX="$("${WS}/.venv/bin/python" -m harness_config engine_prefix)" || exit 1
```
This also gives class D its native upgrade for free (`` !`python -m harness_config engine_prefix` `` in skills) and class A its hook-injection option (`SessionStart` hook shells the same module). **One module, three consumers, one parser, one store.**

**Doc/source:** PyYAML `safe_load` guidance <https://python.land/data-processing/python-yaml>, <https://realpython.com/python-yaml/>.

---

## Q3 — Next.js 16 / TS cockpit reads the root yaml

**Confirmed clean pattern:** `js-yaml` in a **server-only lib loader**, typed against an interface, file read with Node `fs` + `process.cwd()`.

```ts
// lib/projectConfig.ts   — server-only (cockpit is filesystem-as-DB, no client bundle)
import 'server-only';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import yaml from 'js-yaml';

export interface ProjectConfig {
  engine_prefix: string;
  brands: string[];
  live_verify_infra?: { /* ... */ };
}
let cache: ProjectConfig | null = null;
export function getProjectConfig(): ProjectConfig {
  if (cache) return cache;
  const raw = readFileSync(join(process.cwd(), 'project.config.yaml'), 'utf8');
  cache = yaml.load(raw) as ProjectConfig;   // cast to the interface (js-yaml is untyped)
  return cache;
}
```
Called from a Server Component / route handler (default in App Router) — never from a `"use client"` module.

**Gotchas with Next 16 App Router reading a file OUTSIDE the app dir:**
1. **`process.cwd()` vs static path.** Resolve from `process.cwd()` (repo root where cockpit runs) — works in dev and in a Node server. Known footgun: `path.resolve(process.cwd(), x)` buried in a util is sometimes not traced by Next's static file inclusion; `process.cwd()` join in the loader is the reliable form. (<https://github.com/vercel/next.js/discussions/32236>) For the cockpit this is moot — it's a **filesystem-as-DB Node process, not a Vercel serverless/edge bundle**, so `fs` + `cwd` Just Works and there's no read-only-FS limitation.
2. **Keep it server-only.** `fs`/`js-yaml` must never reach a client component (use `import 'server-only'` to fail the build if it does). The config is repo-edge truth, not client data.
3. **Module-level cache is fine** for a long-lived dev process; if Chris edits the yaml live and wants hot reload, drop the cache or stat-mtime it (cockpit already watches the filesystem).
4. **Don't rely on `next.config` yaml-import webpack loaders** (`next-yaml`/`next-plugin-yaml`) — they couple parsing to the build/bundler. A plain server-side `fs`+`js-yaml` loader keeps the "no build-step coupling" property the cockpit wants.

**Sources:** <https://vercel.com/kb/guide/loading-static-file-nextjs-api-route>, <https://medium.com/@sangimed/typescript-parsing-a-yaml-file-the-right-way-0240b75917af>, <https://github.com/vercel/next.js/discussions/14102>.

> **Cross-class note:** TS uses `js-yaml`, python/bash use PyYAML. That is **two parsers but still ONE store** (`project.config.yaml`). The single-source invariant holds (the file); the "single parser" ideal can't span runtimes (TS can't call PyYAML cheaply per-request). Mitigate drift with a tiny shared **schema fixture test**: one test in each runtime asserts the loaded config matches the documented interface/shape, so a yaml edit that breaks one consumer fails CI.

---

## Q4 — root `project.config.yaml` vs `.harness/config.yaml` vs `pyproject.toml [tool.harness]`

**Recommend: root-level `project.config.yaml`, YAML format.** It is a GOOD idea for an extractable core kit; the alternatives are worse:

| Option | Verdict | Why |
|---|---|---|
| **`project.config.yaml` (root)** | ✅ **recommended** | Discoverable at repo edge by all 4 consumers with a trivial `cwd`/parent-walk; obvious "fill me in" artifact for a fresh repo; format-agnostic to language; doctor can detect unfilled slots. |
| `.harness/config.yaml` | ⚠️ acceptable but worse | Dot-dir hides the one file a new adopter MUST fill — defeats "drop kit + fill config." Also invites the kit to sprawl other state into `.harness/`. If you want a namespace, prefer a top-level `harness:` KEY inside the root yaml over a hidden dir. |
| `pyproject.toml [tool.harness]` | ❌ reject | (1) Couples a polyglot harness (bash+TS+md) to a Python build file — TS/cockpit reading `pyproject.toml` needs a TOML parser, and the kit's premise is language-neutral config. (2) `pyproject.toml` is owned by the *project's* packaging; the kit must not co-own it (extraction friction, merge conflicts). (3) Doctor "unfilled slot" UX is muddier inside a tool-table than a dedicated, commented template file. |

**Why YAML over JSON/TOML for the file:** comments (each slot gets an inline "# fill: e.g. luana_core_") — critical for the doctor/onboarding story; multiline blocks for infra strings; both PyYAML and js-yaml are first-class and already in-house (PyYAML present; js-yaml is the cockpit-side standard).

**Extractable-kit pattern (the goal):**
- Ship `core-harness/` + a **`project.config.template.yaml`** (or `project.config.yaml` with every value as a sentinel like `__FILL_ME__`).
- A **doctor** (`python -m harness_config --doctor`, reusing the same loader) walks the schema, flags any slot still at sentinel/empty, and prints `unfilled: engine_prefix, brands, live_verify_infra.dev_app_url`. Same module as Q2 → one loader, one schema, one doctor.
- Root location + sentinel values = a fresh repo fails the doctor loudly until filled, which is exactly the desired "drop-in then configure" gate.

---

## Consolidated recommendation (the seam)

1. **Store:** ONE `project.config.yaml` at repo root (YAML, commented, sentinel defaults).
2. **Loader:** ONE python module `harness_config.py` (`safe_load`, parent-walk, `<slot>`/`--doctor` CLI) — the single parser for classes A & D-native, and the doctor.
3. **Class A (bash/hooks):** call `python -m harness_config <slot>`. No generated `.env` store.
4. **Class C (TS cockpit):** server-only `js-yaml` loader typed to an interface; `process.cwd()` read; second parser but same store; guard with a cross-runtime schema test.
5. **Class D (markdown):** **CONVENTION** — write `{slot}` + "resolved from `project.config.yaml`" and let the model Read the yaml on demand. **Optional native upgrade inside skills only** via `` !`python -m harness_config <slot>` `` (never a hard dependency — `disableSkillShellExecution` can kill it).
6. **No native interpolation exists for rules/`CLAUDE.md`/agents/templates** — confirmed against official docs; do not design the seam expecting one.

---

### Sources (fetched 2026-06-09)
- Claude Code — Memory (`@import` = inline content, "does not reduce context", CLAUDE.md-only; env not in model context): <https://code.claude.com/docs/en/memory>
- Claude Code — Skills (closed substitution set `$ARGUMENTS`/`${CLAUDE_SESSION_ID}`/`${CLAUDE_SKILL_DIR}`; `` !`<command>` `` dynamic context injection; `disableSkillShellExecution`): <https://code.claude.com/docs/en/skills>
- Claude Code — Context window (settings env / plain stdout NOT in context; hook `additionalContext` IS in context; what reloads after compaction): <https://code.claude.com/docs/en/context-window>
- PyYAML `safe_load` best practice: <https://python.land/data-processing/python-yaml> · <https://realpython.com/python-yaml/>
- Next.js file reads (`process.cwd()`, static-path footgun, server-side fs): <https://vercel.com/kb/guide/loading-static-file-nextjs-api-route> · <https://github.com/vercel/next.js/discussions/32236>
- js-yaml + TS typed parse / Next yaml: <https://medium.com/@sangimed/typescript-parsing-a-yaml-file-the-right-way-0240b75917af> · <https://github.com/vercel/next.js/discussions/14102>

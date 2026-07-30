# Plugin & Marketplace Distribution — W7 research

> **Scope:** can the reusable software-dev PROCESS harness be packaged as a Claude Code **plugin** + distributed via a **marketplace**, including cross-account (Chris's 2nd Claude account) and across other-tech single-brand projects?
> **Fetched:** 2026-06-09 (UTC). Docs current — latest CC version per changelog is **2.1.170, June 9 2026**.
> **Established going in (not re-researched):** plugins contribute skills/agents/hooks/commands/MCP but CANNOT ship always-on `.claude/rules/`. **CONFIRMED by docs** — see Q5.

All claims cite a fetched URL. Where docs are silent → "UNDOCUMENTED".

---

## Q1 — Where does a marketplace physically live? (source types)

A marketplace is just a git repo (or local dir / served file) containing `.claude-plugin/marketplace.json`. There is **no required hosting service** — "Push to GitHub, GitLab, or another git host." Two layers of "source" exist and are independent (plugin-marketplaces.md, "Marketplace sources vs plugin sources"):

- **Marketplace source** (where the catalog `marketplace.json` is fetched) — set via `/plugin marketplace add`. Supports `ref` (branch/tag) but **not** `sha`.
- **Plugin source** (where each individual plugin is fetched) — the `source` field of each entry in `marketplace.json`. Supports both `ref` and `sha`.

**Marketplace `add` sources** (discover-plugins.md "Add marketplaces" + plugin-marketplaces.md "Plugin marketplace add"):
| `add` form | Example |
|---|---|
| GitHub `owner/repo` shorthand | `/plugin marketplace add anthropics/claude-code` |
| GitHub shorthand + ref | `acme-corp/claude-plugins@v2.0` (append `@ref`) |
| Git URL (any host: GitLab/Bitbucket/self-hosted), HTTPS or SSH | `https://gitlab.com/company/plugins.git` / `git@gitlab.com:company/plugins.git` |
| Git URL + ref | `…plugins.git#v1.0.0` (append `#ref`) |
| Local path (dir or direct file) | `./my-marketplace` / `./path/to/marketplace.json` |
| Remote URL to a served `marketplace.json` | `https://example.com/marketplace.json` |

**Plugin `source` field types** (plugin-marketplaces.md "Plugin sources" table): relative path `"./dir"` (must start with `./`, resolved from marketplace root, git-only); `github` object (`repo`,`ref?`,`sha?`); `url` object (any git URL); `git-subdir` object (`url`,`path`,`ref?`,`sha?` — sparse partial clone, **purpose-built for monorepos**); `npm` object (`package`,`version?`,`registry?`). The git-based types are `github`, `url`, `git-subdir`.

⚠️ Caveat (plugin-marketplaces.md "Relative paths" Note): relative `./` plugin sources **only resolve when the marketplace is added via Git**. A URL-based marketplace only downloads the JSON, not the plugin files — use `github`/`url`/`npm`/`git-subdir` plugin sources for URL-served catalogs.

Source: `code.claude.com/docs/en/plugin-marketplaces`, `code.claude.com/docs/en/discover-plugins`.

---

## Q2 — Public vs private; is there a central registry?

**A private git repo works as a marketplace.** Docs section "Private repositories" (plugin-marketplaces.md):
- Manual install/update uses **your existing git credential helpers** — "HTTPS access via `gh auth login`, macOS Keychain, or `git-credential-store` works the same as in your terminal. SSH access works as long as the host is already in your `known_hosts` … and the key is loaded in `ssh-agent`."
- **Background auto-updates** (run at startup, no interactive prompts) need a token env var instead: `GITHUB_TOKEN`/`GH_TOKEN` (GitHub), `GITLAB_TOKEN`/`GL_TOKEN`, `BITBUCKET_TOKEN`. For private GitHub, the token needs `repo` scope; GitLab needs `read_repository`.

**Is there an Anthropic-hosted central public registry?** Partially, and **NOT mandatory**:
- `claude-plugins-official` — curated by Anthropic, auto-available in every install, inclusion at Anthropic's discretion, no application process.
- `claude-community` (`anthropics/claude-plugins-community`) — public, added manually, third-party submissions land after automated validation + safety screening; each plugin pinned to a commit SHA.
- Neither is required. "To distribute plugins independently, create your own marketplace and share it with users." **Confirmed: NO mandatory public listing** — every marketplace is just a git repo you point Claude Code at.

Source: `code.claude.com/docs/en/plugin-marketplaces` (Private repositories), `code.claude.com/docs/en/discover-plugins` (Official/Community marketplace), `code.claude.com/docs/en/plugins` (Submit to community marketplace).

---

## Q3 — Cross-account sharing (Chris's 2nd Claude account)

Critical: a Claude **account** (login) is the identity for the *model/API*. Marketplace access is gated by **git credentials**, not the Claude account. So "sharing to my 2nd account" = "make the git repo reachable from the machine/credentials that 2nd account runs on." All paths below work; pick by how the repo is reachable.

| Path | Works? | Auth / access requirement |
|---|---|---|
| **(a) Private GitHub repo + add 2nd account as collaborator** | ✅ Yes | The 2nd account's machine must hold git creds that can read the repo. `/plugin marketplace add owner/repo` works once `gh auth login`/SSH/HTTPS-token grants read. The "2nd Claude account" is irrelevant to git auth — it's the OS git identity that matters. For background auto-update on that machine, set `GITHUB_TOKEN` with `repo` scope. |
| **(b) GitHub org** | ✅ Yes | Same as (a); org membership grants read. Cleaner for >1 repo / future contributors. |
| **(c) Make the repo public** | ✅ Yes, simplest | No auth at all. `/plugin marketplace add owner/repo`. Trade-off: harness is world-readable. |
| **(d) `extraKnownMarketplaces` in settings.json** | ✅ Yes — **registers, doesn't authenticate** | **Travels with the repo IF placed in project `.claude/settings.json` at `project` scope and committed.** When a collaborator trusts the folder, CC prompts to install. State is stored per-user in `~/.claude/plugins/known_marketplaces.json` (not per-project) once added. It only auto-*registers* the marketplace name→source; the underlying git fetch still needs (a)/(b)/(c) auth. Pair with `enabledPlugins` to auto-enable specific plugins. |
| **(e) Enterprise/managed distribution** | ✅ Exists, overkill for solo | `managed` scope via managed-settings.json: `extraKnownMarketplaces` (+ `autoUpdate:true`) to push a marketplace org-wide; `strictKnownMarketplaces` to allowlist/lock-down sources; `enabledPlugins` to force-enable. Requires managed-settings infra (MDM/org). Not needed for a solo dev with 2 personal accounts. |

**Recommended for Chris:** private GitHub repo (a/b) if he wants it closed, or public (c) for zero-friction. The 2nd account just needs git read access on its machine. `extraKnownMarketplaces` (d) at project scope is the auto-register layer on top.

Source: `code.claude.com/docs/en/plugin-marketplaces` (Require marketplaces for your team; Managed marketplace restrictions), `code.claude.com/docs/en/discover-plugins` (Configure team marketplaces), `code.claude.com/docs/en/plugins-reference` (Plugin installation scopes).

---

## Q4 — Install / update / dev mechanics (matter for a "ported process")

- **Copied to cache, NOT read in-tree.** "Claude Code copies the plugin directory to a cache location" → `~/.claude/plugins/cache`. "Each installed version is a separate directory in the cache." Consequence: a plugin **cannot reference files outside its own dir** (`../shared-utils` fails post-install); share within a marketplace via symlinks (dereferenced into the cache if target is inside the same marketplace). (plugins-reference.md "Plugin caching and file resolution")
- **`@skills-dir` plugins are the exception — discovered in place, not cached.** A folder under `~/.claude/skills/` or `<cwd>/.claude/skills/` with a `.claude-plugin/plugin.json` loads as `<name>@skills-dir` "with no marketplace and no install step … discovered in place rather than copied." (plugins-reference.md "Skills-directory plugins"; changelog 2.1.157.)
- **Update path for an adopter:** `/plugin marketplace update [name]` (refresh catalog) then `/reload-plugins` (apply without restart). Auto-update can run at startup per-marketplace (official = on by default; third-party/local = off by default). `claude plugin update <plugin>` for a single plugin. **Version gotcha:** if `plugin.json` sets `"version"`, you MUST bump it for adopters to get changes; omit `version` and the git commit SHA becomes the version so **every commit = an update** (ideal for an actively-developed internal harness). (plugin-marketplaces.md "Version resolution"; plugins-reference.md "Version management"; discover-plugins.md "Configure auto-updates".)
- **Live dev:** `claude --plugin-dir ./my-plugin` (also accepts a `.zip`, CC ≥2.1.128); `claude --plugin-url https://…/plugin.zip` for a hosted archive (session-only). `--plugin-dir` of a same-named installed plugin **takes precedence for that session**. `claude plugin init <name>` scaffolds a `@skills-dir` dev plugin that auto-loads. `/reload-plugins` picks up edits mid-session. (plugins.md "Test your plugins locally"; "Develop a plugin in your skills directory".)
- **`${CLAUDE_PLUGIN_ROOT}`:** yes — hook commands, MCP/LSP/monitor configs use it for absolute paths into the cached install dir. "This path changes when the plugin updates" → never write state there; use **`${CLAUDE_PLUGIN_DATA}`** (`~/.claude/plugins/data/{id}/`) for state that survives updates. Also `${CLAUDE_PROJECT_DIR}`. (plugins-reference.md "Environment variables".)
- **Container/CI seeding:** `CLAUDE_CODE_PLUGIN_SEED_DIR` pre-populates marketplaces+plugins at image build (read-only, auto-update disabled). (plugin-marketplaces.md "Pre-populate plugins for containers".)

Source: `code.claude.com/docs/en/plugins-reference`, `code.claude.com/docs/en/plugins`, `code.claude.com/docs/en/plugin-marketplaces`, `code.claude.com/docs/en/discover-plugins`.

---

## Q5 — The always-on-rules gap + workaround (ranked)

**CONFIRMED the gap, verbatim** (plugins-reference.md "Plugin directory structure"):
> "A `CLAUDE.md` file at the plugin root is **not loaded as project context**. Plugins contribute context through skills, agents, and hooks rather than CLAUDE.md. To ship instructions that load into Claude's context, put them in a [skill]."

So a plugin's `CLAUDE.md` and a plugin-shipped `.claude/rules/` will NOT auto-inject. Workarounds, ranked for a portable process:

**Rank 1 — plugin `SessionStart` hook that emits the rules as `additionalContext` (de-facto always-on injection).** WORKS and is documented: for `SessionStart` (and `UserPromptSubmit`, `UserPromptExpansion`) "stdout is added as context that Claude can see and act on," and `hookSpecificOutput.additionalContext` is "String added to Claude's context at the start of the conversation, before the first prompt." (hooks.md). **HARD limit:** `additionalContext`/`systemMessage`/plain stdout are **capped at 10,000 characters**; overflow is "saved to a file and replaced with a preview and file path" — so the model gets a pointer, not the body. Implication: a plugin SessionStart hook can reliably inject a **slim always-on rule core (≤10k chars)** at every session start; the always-on slim-stub model the harness already uses fits this budget. The hook can `cat` rule files bundled under `${CLAUDE_PLUGIN_ROOT}` to stdout. (Bonus: 2.1.152 added `SessionStart … reloadSkills:true`.) This is the closest equivalent to native always-on rules and travels inside the plugin.

**Rank 2 — adopter bootstrap copies/symlinks rules into THEIR `.claude/rules/` (non-plugin).** Gets true native always-on behavior (real `.claude/rules/*.md` auto-load, with the `InstructionsLoaded` hook event firing). Cost: it is **not** delivered *by* the plugin — needs a documented one-time bootstrap step (a plugin skill like `/harness:bootstrap` can perform the copy on demand). No 10k cap. Best when the rule corpus exceeds 10k chars or must be editable per-project. Pairs well with Rank 1 (hook injects the slim core; bootstrap drops the full corpus into the adopter's tree).

**Rank 3 — ship the rules as a SKILL (description always-on, body on-invoke).** Documented as the official "ship instructions" path, BUT: only the skill *description* is always in context; the rule *body* loads when the skill fires. **Insufficient for genuinely always-on rule BODIES** (e.g. anti-duplication grep-before-write, tenant-isolation) that must constrain every action regardless of invocation. Use for opt-in/contextual guidance, not for invariants.

**Verdict:** Rank 1 (SessionStart hook → `additionalContext`, slim core ≤10k) for the always-on invariants that fit, + Rank 2 (bootstrap-skill drops the full `.claude/rules/` into the adopter's tree) for the long tail. Rank 3 only for contextual/conditional rules.

Source: `code.claude.com/docs/en/hooks` (SessionStart stdout / additionalContext / 10k cap), `code.claude.com/docs/en/plugins-reference` (CLAUDE.md not loaded; skills), `code.claude.com/docs/en/changelog`.

---

## Q6 — Blessed pattern for distributing a reusable dev-workflow/process?

No single "distribute your dev process" recipe page, but the docs explicitly frame plugins+marketplaces as the **team/workflow standardization mechanism**:
- "Use plugins when … you want to share functionality with your team … reusable across projects … version control and easy updates." (plugins.md "When to use plugins vs standalone")
- The official marketplace ships a **"Development workflows"** category (`commit-commands`, `pr-review-toolkit`, `agent-sdk-dev`, `plugin-dev`) — Anthropic's own examples of process-as-plugin. (discover-plugins.md)
- **Monorepo/`git-subdir`** is first-class: `git-subdir` "clones sparsely to minimize bandwidth for monorepos," and `--sparse` on `add` limits checkout. (plugin-marketplaces.md)
- **Versioning** for an internal/active harness: omit `version` → commit-SHA versioning, every push is an update; or explicit semver + `CHANGELOG.md` for stable releases. Release channels (stable/latest) via two marketplaces on different refs assigned through managed settings. (plugins-reference.md "Version management"; plugin-marketplaces.md "release channels".)
- **Team auto-prompt:** `extraKnownMarketplaces` + `enabledPlugins` in project `.claude/settings.json` (committed) is the documented "Require marketplaces for your team" pattern. (plugin-marketplaces.md)

UNDOCUMENTED: a prescriptive "package your full SDLC process as one plugin" guide. The pieces (skills+agents+hooks+commands, SessionStart context injection, git-SHA versioning, project-scoped marketplace registration) are all blessed; assembling them into a process harness is left to the author.

---

## Bottom line (for a solo dev porting a PROCESS to other-tech single-brand projects)

**The distribution model is: one git repo = a marketplace catalog (`.claude-plugin/marketplace.json`) listing one "harness" plugin (skills + agents + hooks + commands), versioned by commit-SHA (omit `version`), with a `SessionStart` hook that injects the slim always-on rule core (≤10k chars) as `additionalContext` plus a `/harness:bootstrap` skill that copies the full `.claude/rules/` corpus into each adopter project's tree.** This is the right model because (1) marketplaces are *just git repos* needing no Anthropic listing — keep it private with `gh`/SSH creds or public for zero-friction, and the 2nd Claude account only needs git read access on its machine; (2) commit-SHA versioning means `git push` ships updates and adopters pull them with `/plugin marketplace update` + `/reload-plugins`; (3) it cleanly works the documented gap — plugin `CLAUDE.md`/`.claude/rules/` are NOT auto-loaded, so the SessionStart-hook-injection (always-on, capped) + bootstrap-copy (full corpus, native auto-load) combo is the only way to deliver "always-on process rules" portably across other-tech, single-brand projects. For other tech stacks, the harness ships tech-agnostic process (states/gates/roles); stack-specific rules stay in each adopter's own `.claude/rules/`, dropped by the bootstrap step.

---

### URLs fetched (all 2026-06-09)
- https://code.claude.com/docs/en/plugins
- https://code.claude.com/docs/en/plugin-marketplaces
- https://code.claude.com/docs/en/plugins-reference
- https://code.claude.com/docs/en/discover-plugins
- https://code.claude.com/docs/en/hooks
- https://code.claude.com/docs/en/changelog
- https://code.claude.com/docs/en/release-notes → **404 (does not exist; use /changelog)**

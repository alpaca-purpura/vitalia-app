# Claude Code — capacidades junio 2026 (línea base de modernización del harness)

> Catálogo curado del research 2026-06-01 (agente `claude-code-guide` + docs oficiales) **cruzado con el toolset real de la sesión**. Sirve de baseline para la auditoría exhaustiva del harness. **Confianza marcada por ítem.** Nada se aplica sin ratificación de Chris (catalog+propose). Origen: sesión homologación técnica 2026-06-01. Claude Code v2.1.159.

## Leyenda de confianza

- ✅ **CONFIRMADO** — la herramienta existe en mi toolset de esta sesión (evidencia directa), o coincide exacto con mi system prompt.
- 🟡 **ALTO (verificar doc)** — plausible + coherente, pero hay que confirmar nombres/campos exactos contra doc oficial antes de mass-edit.
- ⚪ **REPORTADO (sin verificar)** — el agente lo flageó como no verificado en docs.

## 1. Workflows (orquestación multi-agente por script)

- ✅ **CONFIRMADO** — tengo la herramienta `Workflow`. Modelo: script JS que Claude escribe, `agent()/parallel()/pipeline()`, cap 16 concurrentes / 1000 total por run, verificación adversarial built-in, resumible en misma sesión, `ultracode` mode existe.
- Uso para nuestro harness: auditorías cross-brand, migraciones masivas, research con verificación adversarial, N-way drafting con voto.
- Doc: https://code.claude.com/docs/en/workflows.md

## 2. Subagents / Agent tool

- ✅ **CONFIRMADO** — `isolation: "worktree"` (sandbox git por agente), `run_in_background`, `SendMessage` (continuar agente), `model` override por call, `agentType` custom, schema StructuredOutput.
- 🟡 **ALTO** — frontmatter `.claude/agents/*.md` con `model`, `tools`, `disallowedTools`, `permissionMode`, `maxTurns`, `skills` (preload), `mcpServers`, `hooks`, `memory: user|project|local`, `background`, `effort`, `isolation`, `color`, `initialPrompt`. (Tenemos 11 agents; varios campos ya los usamos — verificar los nuevos: `isolation`, `memory`, `skills`-preload.)
- Aplica: `isolation: worktree` en `builder-*` para builds paralelos sin colisión; `model` explícito por agente (cost-routing).
- Doc: https://code.claude.com/docs/en/sub-agents.md

## 3. Skills (SKILL.md)

- 🟡 **ALTO (verificar antes de mass-edit 47 SKILL.md)** — campos frontmatter reportados: `description` (req, cap ~1536 chars con `when_to_use`), `paths` (glob auto-load), `model`/`effort`, `context: fork` + `agent`, `hooks` inline, `disable-model-invocation`, `user-invocable`, `allowed-tools`/`disallowed-tools`, `argument-hint`, `arguments`.
- 🟡 Substituciones: `$ARGUMENTS`, `$name`, `${CLAUDE_SESSION_ID}`, `${CLAUDE_EFFORT}`, `${CLAUDE_SKILL_DIR}`, `` !`cmd` `` (inyección dinámica).
- 🟡 Live reload mid-sesión; descubrimiento anidado on-demand.
- Aplica: `paths` glob para reducir ruido de auto-trigger (ej. `/pm-vitalia` solo en `vitalia/**`); `SKILL.md` < 500 líneas (ya lo hacemos con references/).
- Doc: https://code.claude.com/docs/en/skills.md

## 4. Hooks

- 🟡 **ALTO** — reportados ~27 eventos. NUEVOS relevantes: `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `WorktreeCreate`, `WorktreeRemove`, `TeammateIdle`, `InstructionsLoaded`, `PreCompact`/`PostCompact`. Handler types: command, http, mcp_tool, prompt, **agent** (subagente verifica condición).
- Tenemos 4 hooks (`auto-chain-detect`, `claude-md-overlay-check`, `contract-guard`, `learning-detect`) + 2 git-hooks. Oportunidad: gate `SubagentStart` (audit trail builders + bloquear módulos forbidden), `TaskCreated` (validar schema ticket), cleanup `WorktreeRemove`.
- Doc: https://code.claude.com/docs/en/hooks-guide.md
- ⚠️ Verificar nombres exactos de eventos contra doc antes de escribir hooks.

## 5. Plugins / marketplace

- 🟡 **ALTO** — estructura `.claude-plugin/plugin.json` + `skills/` + `agents/` + `hooks/` + `.mcp.json` + `monitors/` + `bin/` + `settings.json`. Skills namespaced `/plugin:skill`. Marketplace oficial + community.
- Aplica (P1): empaquetar el harness (59 skills + agents + hooks) como plugin `luana-harness` versionado → distribución + versionado. **Decisión de Chris** (puede ser overkill solo-operador, o muy útil para versionar).
- Doc: https://code.claude.com/docs/en/plugins.md

## 6. Memory / CLAUDE.md

- ✅ Jerarquía root + overlay + rules (ya lo hacemos canónico). Memory file-based `~/.claude/.../memory/` (ya lo uso).
- 🟡 `@imports` recursivos (max 5 hops, cargan al startup = sin ahorro de tokens → preferir skills para conocimiento selectivo). Nested CLAUDE.md reload on-demand.
- Doc: https://code.claude.com/docs/en/memory.md

## 7. Modelos + cost-routing (junio 2026)

- ✅ **CONFIRMADO (= system prompt):** `claude-opus-4-8`, `claude-sonnet-4-6`, `claude-haiku-4-5-20251001`. Opus 4.8 soporta effort `xhigh`/`max`. Variantes `[1m]` (1M ctx), `opusplan`, `ultracode`.
- Routing recomendado: PM/Architect/Auditor/builder-agentic → **opus**; builder-be/fe + PO → **sonnet**; explore/grep/gate-runner/context-* → **haiku**. (Coincide con nuestra cost-routing ya cementada.)
- Doc: https://code.claude.com/docs/en/model-config.md

## 8. Otros (ergonomía 2026)

- ✅ Background tasks (`run_in_background`), scheduled/cron agents (`CronCreate`), `Monitor`, `ScheduleWakeup`, `TaskCreate/Get/List`.
- 🟡 Prompt caching automático (CLAUDE.md+rules+skills) — crítico con nuestro harness grande; invalidación al switch model/effort/MCP/plugins/compact. Checkpoints + `/rewind`. Status line. Remote/cloud sessions.

## Tabla de adopción (prioridad sugerida — RATIFICA Chris)

| Prio | Feature | Esfuerzo | Impacto |
|---|---|---|---|
| P0 | Cost-routing modelo explícito por agente/skill | bajo | -20% tokens |
| P0 | `isolation: worktree` en `builder-*` | bajo | builds paralelos sin colisión |
| P0 | Workflows para auditorías/migraciones cross-brand | medio | escala + menos contexto |
| P1 | Hook gates nuevos (SubagentStart/TaskCreated/WorktreeRemove) | medio | audit trail + validación pre-exec |
| P1 | `paths` glob en skills brand-specific | bajo | menos ruido auto-trigger |
| P1/P2 | Empaquetar harness como plugin `luana-harness` | bajo-medio | versionado/distribución |
| P2 | Orquestar /pm→/architect→/dev-team→/auditor como workflow | alto | meta-orquestación repetible |

## A verificar contra doc oficial ANTES de mass-edit (Phase 0 de la auditoría)

1. Schema exacto de frontmatter de SKILL.md (campos 🟡 sección 3).
2. Nombres exactos de hook events (sección 4).
3. Frontmatter de agents: `isolation`, `memory`, `skills`-preload (sección 2).
4. Estructura de plugin.json (sección 5).

## Referencias

- Reporte completo: este doc (curado). Docs oficiales: ver URLs por sección.
- `.claude/rules/learning-capture.md` — este doc es tooling reference (`docs/learnings/tooling/`).
- Baseline harness inventory: 59 skills · 11 agents · 74 rules · 4+2 hooks · cockpit · 23 process + 25 templates + 22 ADRs.

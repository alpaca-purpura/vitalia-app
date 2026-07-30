// harness-audit-2026 — workflow reutilizable de auditoría del harness Claude Code de luana-platform.
// Promovido a comando permanente 2026-06-01 (HLP §8). Invocar: Workflow({name: 'harness-audit-2026'})
// (== meta.name abajo; el filename queda harness-audit.js por compat con refs en HLP/backlog).
// ★ proceso v5 (2026-06-05): este workflow es el DEEP-SWEEP del ritual /harnesses-improvement
// (CIL · docs/process/continuous-improvement.md) — reachable vía ese skill, NO un comando suelto.
// Su salida alimenta el carril L1 (harness-backlog). NO edita (produce catálogo ratificable).
// NOTA: los SCHEMA_* embebidos son un SNAPSHOT verificado 2026-06-01. Refrescar (re-fetch docs
// oficiales + actualizar docs/learnings/tooling/claude-code-2026-capabilities.md) cuando salgan features CC nuevas.

export const meta = {
  name: 'harness-audit-2026',
  description: 'Auditoría exhaustiva del harness Claude Code de luana-platform (skills/agents/rules/hooks/cockpit/process/templates/adr) vs schemas CC junio-2026 VERIFICADOS + consistencia interna + staleness + punteros rotos + overlap. Produce catálogo ratificable. NO edita nada.',
  phases: [
    { title: 'Enumerate', detail: 'glob + chunk de todos los archivos del harness', model: 'haiku' },
    { title: 'Audit', detail: 'auditoría paralela por lote vs schema verificado + consistencia', model: 'sonnet' },
    { title: 'Synthesize', detail: 'dedupe + priorizar → catálogo ratificable', model: 'opus' },
  ],
}

const SCHEMA_SKILLS = "SKILL.md frontmatter (VERIFICADO docs 2026-06-01): todos OPCIONALES salvo 'description' recomendado. Validos: description (cap 1536 chars COMBINADO con when_to_use, se trunca en el listing), when_to_use, argument-hint, disable-model-invocation(bool), user-invocable(bool), allowed-tools, disallowed-tools, context: fork, agent (subagent type cuando context:fork). Substituciones: $ARGUMENTS, ${CLAUDE_SESSION_ID}, ${CLAUDE_SKILL_DIR}, inyeccion dinamica con backtick-cmd. Guia: SKILL.md < 500 lineas, detalle a references/. PRESUPUESTO: las 59 skills comparten un budget de listado por char -> descripciones verbosas cuestan contexto; flag descripciones largas; recomendar skillOverrides name-only para skills de baja prioridad. NO recomendar campo 'paths' (sin confirmar en docs). NO recomendar 'model'/'effort'/'hooks' en skills salvo que el archivo ya los use (sin confirmar).";

const SCHEMA_AGENTS = "Subagent .claude/agents/*.md frontmatter (VERIFICADO docs 2026-06-01): name, description, prompt, tools, disallowedTools, model, permissionMode (default|acceptEdits|auto|dontAsk|bypassPermissions|plan), mcpServers, hooks, maxTurns, skills (preload full content al startup), initialPrompt, memory (user|project|local -> .claude/agent-memory/<name>/), effort (low|medium|high|xhigh|max), background(bool), isolation: worktree (copia git aislada, branch desde default branch, auto-cleanup si no hay cambios), color. Plugin subagents IGNORAN hooks/mcpServers/permissionMode. Oportunidades: builders -> isolation: worktree; model routing explicito; skills-preload para builders/auditors; memory:project para auditors que acumulan learnings.";

const SCHEMA_HOOKS = "Hook events (VERIFICADO 2026-06-01, 30): SessionStart, Setup, UserPromptSubmit, UserPromptExpansion, PreToolUse, PermissionRequest, PermissionDenied, PostToolUse, PostToolUseFailure, PostToolBatch, Notification, MessageDisplay, SubagentStart, SubagentStop, TaskCreated, TaskCompleted, Stop, StopFailure, TeammateIdle, InstructionsLoaded, ConfigChange, CwdChanged, FileChanged, WorktreeCreate, WorktreeRemove, PreCompact, PostCompact, Elicitation, ElicitationResult, SessionEnd. Handlers: command, http, mcp_tool, prompt, agent(experimental). Config settings.json hooks.{Event}[].{matcher, if, hooks:[{type, command/url/server+tool/prompt, timeout, async}]}. Oportunidades: SubagentStart gate (audit builders + bloquear modulos forbidden), TaskCreated (validar schema ticket), WorktreeRemove (cleanup), type:agent para verificacion condicional.";

const SCHEMA_GENERAL = "Modelos 2026: opus=claude-opus-4-8 (xhigh/max), sonnet=claude-sonnet-4-6, haiku=claude-haiku-4-5-20251001. Cost-routing: opus para PM/architect/auditor/builder-agentic; sonnet para builder-be/fe + PO; haiku para explore/grep/gate-runner/context-*. Workflows JS multi-agente para auditorias/migraciones/research. Convenciones harness: pointer-first (MEMORY pointer + detalle en file), slim-stub rules (.claude/rules/*.md stub -> docs/rules-detail/*.md on-demand), anti-duplication (cross-brand mirror ban), spanish-neutro user-facing, story lifecycle 10 estados.";

function schemaFor(cat) {
  if (cat === 'skill') return SCHEMA_SKILLS;
  if (cat === 'agent') return SCHEMA_AGENTS;
  if (cat === 'hook') return SCHEMA_HOOKS;
  return "(sin frontmatter schema — auditar consistencia de contenido, staleness, punteros rotos, overlap, alineacion con paradigma actual)";
}

const INV_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    batches: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        label: { type: 'string' },
        category: { type: 'string', enum: ['skill','agent','rule-root','rule-brand','rule-detail','hook','cockpit','process','template','adr'] },
        files: { type: 'array', items: { type: 'string' } },
      }, required: ['label','category','files'],
    } },
  }, required: ['batches'],
};

const FINDINGS_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    batch_label: { type: 'string' },
    findings: { type: 'array', items: {
      type: 'object', additionalProperties: false,
      properties: {
        file: { type: 'string' },
        category: { type: 'string' },
        issues: { type: 'array', items: {
          type: 'object', additionalProperties: false,
          properties: {
            type: { type: 'string' },
            severity: { type: 'string', enum: ['LOW','MEDIUM','HIGH'] },
            summary: { type: 'string' },
            proposed_change: { type: 'string' },
            risk: { type: 'string' },
          }, required: ['type','severity','summary','proposed_change','risk'],
        } },
        cc2026_opportunities: { type: 'array', items: {
          type: 'object', additionalProperties: false,
          properties: { feature: { type: 'string' }, change: { type: 'string' }, effort: { type: 'string' } },
          required: ['feature','change','effort'],
        } },
        broken_pointers: { type: 'array', items: { type: 'string' } },
        overlap_candidates: { type: 'array', items: { type: 'string' } },
        stale: { type: 'boolean' },
      }, required: ['file','category','issues','cc2026_opportunities','broken_pointers','overlap_candidates','stale'],
    } },
  }, required: ['batch_label','findings'],
};

const CATALOG_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    catalog_markdown: { type: 'string' },
    summary: {
      type: 'object', additionalProperties: false,
      properties: {
        total_files: { type: 'number' }, total_issues: { type: 'number' },
        high: { type: 'number' }, medium: { type: 'number' }, low: { type: 'number' },
        top_recommendations: { type: 'array', items: { type: 'string' } },
      }, required: ['total_files','total_issues','high','medium','low','top_recommendations'],
    },
  }, required: ['catalog_markdown','summary'],
};

phase('Enumerate');
const inv = await agent(
  "Enumera los archivos del harness Claude Code de luana-platform para auditoria exhaustiva. Corre desde el repo root (cwd actual). Usa bash/glob. Arma lotes de ~6 archivos (NUNCA >8). Cubri EXACTAMENTE estas superficies (archivos PRIMARIOS — para skills lista el SKILL.md, NO references/*):\n" +
  "- .claude/skills/*/SKILL.md -> category 'skill'\n" +
  "- .claude/agents/*.md -> category 'agent'\n" +
  "- .claude/rules/*.md -> category 'rule-root'\n" +
  "- {vitalia,nicolify,comunify,lupulo}/.claude/rules/*.md -> category 'rule-brand'\n" +
  "- docs/rules-detail/*.md -> category 'rule-detail'\n" +
  "- .claude/hooks/* + .claude/settings.json + scripts/git-hooks/* -> category 'hook' (UN solo lote)\n" +
  "- tools/luana-cockpit/README.md + tools/luana-cockpit/*.md -> category 'cockpit' (UN solo lote)\n" +
  "- docs/process/*.md -> category 'process'\n" +
  "- docs/specs/templates/* -> category 'template'\n" +
  "- docs/architecture/luana-platform/*.md -> category 'adr'\n" +
  "Cada archivo de esos globs debe aparecer en EXACTAMENTE un lote. label = '<category>-<n>'. Devolve {batches:[{label,category,files}]}.",
  { schema: INV_SCHEMA, label: 'enumerate', phase: 'Enumerate', model: 'haiku' }
);

phase('Audit');
const findings = await parallel((inv.batches || []).map((b) => () =>
  agent(
    "Audita un lote de archivos del HARNESS Claude Code de luana-platform. SOLO LECTURA — no edites nada; produci hallazgos estructurados.\n" +
    "Lote: " + b.label + " (category: " + b.category + "). Archivos: " + (b.files || []).join(', ') + ".\n" +
    "Usa Read/Grep/Glob/Bash para inspeccionar cada archivo Y verificar que sus punteros citados existan (glob/test).\n" +
    "Schema CC junio-2026 VERIFICADO para esta categoria: " + schemaFor(b.category) + "\n" +
    "Facts generales del harness: " + SCHEMA_GENERAL + "\n" +
    "Para CADA archivo, reporta hallazgos sobre: (1) FRONTMATTER vs schema verificado — campos invalidos/deprecados/utiles-faltantes (solo skill/agent). (2) OPORTUNIDADES CC-2026 (agents: isolation:worktree para builders, model routing, skills-preload, memory:project; skills: trim description<1536/precision auto-trigger, name-only baja-prioridad, context:fork; hooks: eventos nuevos SubagentStart/TaskCreated/WorktreeRemove, handler type:agent). (3) STALENESS — refs a archivos/skills/rules/paths que ya no existen (VERIFICAR via bash/glob), model IDs viejos, fechas/facts vencidos. (4) PUNTEROS ROTOS — path/skill/rule citado que no existe (verificar). (5) CONSISTENCIA — contradicciones con otras rules/skills. (6) OVERLAP/DUPLICACION con otra skill/rule. (7) CALIDAD — skills: SKILL.md >500 lineas; rules: integridad slim-stub (cita rules-detail correcto); calidad de description para auto-trigger.\n" +
    "Cada issue: {type, severity LOW/MEDIUM/HIGH, summary, proposed_change concreto, risk}. Citá file:line donde puedas. Salta categorias que no apliquen (ej. frontmatter en rules/process/template/adr). Se CONCISO (resumenes, no ensayos).",
    { schema: FINDINGS_SCHEMA, label: 'audit:' + b.label, phase: 'Audit', model: 'sonnet' }
  )
));

phase('Synthesize');
const valid = findings.filter(Boolean);
const catalog = await agent(
  "Sos el lead de sintesis de una auditoria exhaustiva del harness Claude Code de luana-platform. Recibis hallazgos de " + valid.length + " lotes cubriendo TODO el harness. Produci un CATALOGO RATIFICABLE (markdown) para que Chris apruebe ANTES de cualquier edit.\n" +
  "Hallazgos (JSON): " + JSON.stringify(valid) + "\n" +
  "Tareas: deduplicar hallazgos solapados; agrupar por superficie (skills/agents/rules/hooks/cockpit/process/templates/adr); dentro de cada grupo ordenar por severity. Cada entrada del catalogo = {issue/oportunidad -> archivo(s) afectado(s) -> cambio propuesto concreto -> risk -> effort}. Incluir seccion '## Quick wins (bajo riesgo, alto impacto)' al frente y '## Necesita decision de Chris (stake/criterio)'. Incluir al final un '## Roadmap de adopcion priorizado' mapeado a features CC-2026 (workflows, isolation:worktree, hook events nuevos, plugin packaging, cost-routing, skill-listing budget). Denso y escaneable. Devolve catalog_markdown (el doc completo, en español neutro) + summary stats.",
  { schema: CATALOG_SCHEMA, label: 'synthesize', phase: 'Synthesize', model: 'opus' }
);

return catalog;
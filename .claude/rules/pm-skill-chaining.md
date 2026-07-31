# PM Skill Chaining — handoff programático

> **Slim stub (context-rot pass 2026-05-30 · materializada single-brand 2026-07-31).** Cuerpo operativo replicado en `.claude/skills/pm-vitalia/SKILL.md § Auto-chain rule` — ya cargado en contexto cuando el PM corre. **Origen:** caso F1-S4 2026-05-23. **Cement-date:** 2026-05-23.

## Regla cardinal

Cuando `/pm-vitalia` determina que la acción siguiente es invocar una skill secundaria (`/po-ux`, `/po`, `/ux-agentico`, `/architect`, `/dev-team`, `/auditor`), el modelo MUST invocar `Skill` tool inline al final del turno actual — NO devolver mensaje textual pidiendo al usuario que tipee la slash-command manualmente.

## Triggers / excepciones (quick-reference)

**Encadenar cuando:** Chris escribió literal `/skill-X` en args del PM · Chris escribió "invocá/spawnea/arranca /skill-X" · Step 0 GREEN + state-machine permite una sola transición · `next_action` del checkpoint cita la skill + Chris confirma.

**NO encadenar cuando:** WIP cap del estado destino agotado · deps hard faltantes · story OPEN sin `defer_audit: true` (story-closure-gate) · state-machine no permite la skill pedida · falta input obligatorio del skill destino.

## Anti-patterns (top 3 — lista completa en la SKILL.md del PM)

- ❌ Emitir "Chris, invocá `/po-ux ...`" cuando Chris ya pidió la chain (caso origen F1-S4)
- ❌ Hacer el handoff via Agent tool — `/po-ux`, `/architect`, `/dev-team`, `/auditor` son SKILLS, no AGENTS
- ❌ Encadenar sin Step 0 closure gate (rompe story-closure-gate)

## Referencias

- `.claude/skills/pm-vitalia/SKILL.md` § Auto-chain rule — **SSoT + cuerpo operativo**
- `.claude/hooks/auto-chain-detect.sh` — hook UserPromptSubmit detection
- `.claude/rules/story-closure-gate.md` — gate Step 0 que precede el chain

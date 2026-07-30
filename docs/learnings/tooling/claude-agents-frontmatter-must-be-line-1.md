<!-- voseo-allowed: learning de tooling interno, no user-facing -->
---
title: "Agent .md frontmatter DEBE empezar en línea 1 (nada arriba, ni comentarios)"
date: 2026-05-29
type: tooling
brands_affected: [vitalia, nicolify, comunify, lupulo]
origen: "sesión 2026-05-29 — error 'Agent type builder-frontend not found' durante /dev-team autonomous chain"
ratified_by: chris
tags: [claude-code, agents, frontmatter, yaml, voseo-allowed, agent-registry, dev-team, builder]
---

# Agent .md frontmatter DEBE empezar en línea 1

## Contexto

Durante un `/dev-team` autonomous chain (story `vitalia-cockpit-live-reconciliation`), el spawn de `builder-frontend` falló con `Agent type 'builder-frontend' not found`. Los 3 `builder-{frontend,backend,agentic}.md` SÍ existían en `.claude/agents/`, pero NO estaban registrados como agent types en la sesión (solo `auditor-*`, `architect-orchestrator`, `context-*`, `gate-runner`, `grep-bot` lo estaban).

## Aprendizaje

**El frontmatter YAML de un agent `.md` (`.claude/agents/*.md`) DEBE empezar en la línea 1 con `---`.** Cualquier contenido arriba — incluso un comentario HTML `<!-- voseo-allowed -->` — rompe el parseo del frontmatter y el agent NO se registra (falla silenciosa: el archivo existe pero `Agent type not found` al spawnar).

**Causa raíz del caso:** el commit `dc97c6c7` (machinery hardening) metió `<!-- voseo-allowed: doc interno de maquinaria -->` como **línea 1**, arriba del `---`, en los 3 builders (para pasar el pre-commit hook de voseo). Los `auditor-*` no recibieron ese comentario → siguieron registrándose. Por eso la sesión tenía auditors pero no builders. Antes funcionaba (chain lisa-marca 27-may) porque fue ANTES de ese commit.

**Doble efecto del snapshot:** el registry de agents se snapshotea al **inicio de sesión**. Aunque se arregle el archivo a mitad de sesión, los builders NO aparecen hasta una **sesión nueva**. Fix → commit → reiniciar sesión.

## Aplicación práctica

- **Cuándo aplica:** cada vez que se edita/crea un `.claude/agents/*.md` o `.claude/skills/*/SKILL.md` (mismo principio — frontmatter en línea 1).
- **Cómo aplica:** el magic comment `<!-- voseo-allowed -->` (u cualquier otro) va **DEBAJO** del frontmatter (después del `---` de cierre) o dentro del body. El hook de voseo (`spanish-text.md`) lo busca en **cualquier línea**, así que abajo satisface parser + hook simultáneamente.
- **Verificación rápida:** `for f in .claude/agents/*.md; do [ "$(head -1 "$f")" = "---" ] || echo "ROTO: $f"; done`
- **Síntoma a reconocer:** `Agent type 'X' not found` + el archivo `.claude/agents/X.md` existe → revisar línea 1.

## Ejemplo

```
❌ ROMPE registro:                    ✅ CORRECTO:
<!-- voseo-allowed: ... -->           ---
---                                   name: builder-frontend
name: builder-frontend                ...
...                                   ---
---                                   <!-- voseo-allowed: ... -->
```

## Referencias

- Commit causa raíz: `dc97c6c7` (machinery hardening Fase 3-7, 2026-05-28)
- Commit fix: `2f63b70f` (2026-05-29 — mueve comentario debajo del frontmatter en los 3 builders)
- [Rule voseo magic comment](.claude/rules/spanish-text.md) § Magic comment escape (R25) — "debe aparecer en cualquier línea (no anchored a top)"
- Story origen: `vitalia/docs/product/stories/vitalia-cockpit-live-reconciliation/`

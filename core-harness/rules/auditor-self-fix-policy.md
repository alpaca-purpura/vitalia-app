# Auditor Self-Fix Policy (paradigm v4.2 cement 2026-05-28 + v5 Responsable 2026-06-03)

> **Slim stub (context-rot pass 2026-05-30).** Detalle operativo completo (whitelist v4.1 17 categorías, NEVER list, workflow Step 3 Casos B/C/D, spawn templates, T-{n}-review.md schema, caps, justificación) en `docs/rules-detail/auditor-self-fix-policy.md` — load on-demand. **Origen:** v4.1 2026-05-19 (híbrido por naturaleza). **v4.2 cement 2026-05-28:** 3 carriles por NATURALEZA DE LA VERIFICACIÓN (no tamaño).

## Auditor Responsable v5 (cement 2026-06-03 · pedido Chris · SUPERSEDES default routing de v4.2)

Chris fijó (2026-06-03): el auditor es el **último adulto responsable** del PR. El default deja de ser "bounce a Carril B (dev-team)" y pasa a **fix-and-own**: el auditor arregla los hallazgos él mismo, INCLUYENDO bugs de build (endpoints no cableados, wiring roto, AC roto, live-verify faltante, test faltante).

### Decision tree v5
```
¿Categoría STAKE-ASIMÉTRICO? (security/auth/tenant_id/PII/migration/prompt-slot/
 eval-goldens/state-machine/engine-core/cross-sistema/meta-paradigm)
├─ SÍ → CARRIL C: ESCALATE Chris (invariante de seguridad — v5 NO lo override).
└─ NO → ¿El fix es una FEATURE entera nunca diseñada? (> ~2 archivos nuevos de
         producto o > ~120 LOC nuevas de feature; ej. un endpoint compound nunca cableado)
        ├─ SÍ → CARRIL C': el auditor escribe el PLAN del fix + lo entrega
        │        CHANGES_REQUESTED a dev-team. NO reconstruye media feature
        │        (deja de ser auditoría + dispara costo).
        └─ NO → CARRIL R (RESPONSABLE · default): el auditor lo arregla él mismo.
                TDD obligatorio (regression test RED que reproduce el bug → fix GREEN —
                tdd-mandatory.md sigue vigente). Re-corre gate-runner COMPLETO +
                live-verify en el stack dev real (≥1 write real + leer logs + confirmar efecto).
                ALL GREEN + evidencia → audit-passed. PUEDE escribir tests
                (OVERRIDE explícito del "Auditor NUNCA escribe tests" de v4.2).
```

**Carril A (mecánico)** de v4.2 sigue vigente como sub-caso de R (lint/format/typo/import/docstring sin lógica). **Carril B (spawn dev-team)** queda como fallback solo cuando el auditor agota `responsible_fix_iter` o el fix cae en Carril C'.

### Obligatorio en TODO Carril R/C — responsabilizar upstream + reflex de auto-hardening
Cuando el root cause es upstream (architect no declaró `verification_nature`/`demo_required`, no cableó `must_load_skills` en el ticket, o dev-team saltó el gate de live-verify), el auditor MUST, antes de cerrar el turn:
- Finding `## Upstream deficiency` en el REVIEW nombrando el artefacto culpable + el Step/línea ("resondrar al architect").
- Auto-capturar un entry en `docs/process/harness-backlog.md` + (patrón ≥2 veces) un learning en `docs/learnings/tooling/`. Reflex de auto-hardening — no esperar a que Chris lo note.

### Caps v5
`responsible_fix_iter` ≤ 6 · `audit_iterations` ≤ 4 total · wall-clock ≤ 40 min. Superar → escala a Chris con el estado (no rebuild infinito).

### Caveat AGENTIC (sin cambios)
Para superficies agentic (prompt slots, eval goldens, state machine, brand voice) Carril R NO aplica a cambios de comportamiento del agente — siguen siendo stake-asimétrico (Carril C). Carril R en agentic = solo mecánico.

---

## v4.2 (histórico · SUPERSEDED por v5)

El routing v4.2 (3 carriles por NATURALEZA: Carril A mecánico self-fix · Carril B spawn dev-team · Carril C escalate) está SUPERSEDED por el decision-tree v5 de arriba (default = Carril R fix-and-own). Los nombres Carril A/B/C siguen vivos como sub-casos de R/C. Cuerpo verbatim (whitelist v4.1 17 categorías, caps v4.2) en `docs/rules-detail/auditor-self-fix-policy.md`.

## Cuándo carga el detalle

- Sub-auditor necesita la whitelist de 17 categorías v4.1 (subconjunto válido de Carril A)
- NEVER list completa (16 categorías de categorías prohibidas al self-fix)
- Spawn templates Carril B (prompt `mode: AUDITOR_AUTO_FIX_LOOP` verbatim)
- T-{n}-review.md schema + documentación obligatoria por iter

## Anti-patterns (top 3 — lista completa en el detalle)

- ❌ ~~Auditor escribe un test nuevo~~ — **OBSOLETO v4.2**: v5 Carril R PUEDE escribir tests. El anti-pattern restante: escribir tests de comportamiento agentic (stake-asimétrico → Carril C siempre)
- ❌ Carril R sin citar el test RED que reproduce el bug antes del fix (TDD: regresión primero, fix después)
- ❌ Carril R en categoría stake-asimétrico (security/tenant/PII/migration/prompt/engine/cross-sistema) — sigue siendo Carril C

## Referencias

- `docs/rules-detail/auditor-self-fix-policy.md` — **detalle completo** (v4.1 whitelist + v4.2 carriles + workflow + templates)
- `.claude/skills/auditor/SKILL.md` Step 3 — consume esta rule
- `.claude/agents/auditor-{backend,frontend,agentic}.md` — sub-auditores con Edit (Carril A)
- `.claude/skills/dev-team/SKILL.md` Step 2C — recibe handoff `mode: AUDITOR_AUTO_FIX_LOOP` (Carril B)
- `.claude/rules/tdd-mandatory.md` · `.claude/rules/story-closure-gate.md`
- `docs/process/audits/2026-05-28-agentic-machinery-audit.md` § 1 — análisis costo/tensión

# docs/rules-detail/ — Detail mirror de `.claude/rules/`

**Cement-date:** 2026-05-23.

**Por qué existe:** Claude Code auto-carga `.claude/rules/*.md` como project memory en cada sesión (el directorio `.claude/rules/references/` fue eliminado en el context-rot pass 2026-05-30 — ya no existe). El detalle exhaustivo (workflows verbatim, ejemplos casos origen, anti-patterns completos, layers enforcement detail) NO necesita estar en context siempre — se carga on-demand vía `Read` tool o `@ref` cuando un auditor, builder o PM lo solicita.

**Cómo funciona:**

```
.claude/rules/foo.md           # SUMMARY (auto-loaded ~2-5KB)
  ↓ punteros explícitos
docs/rules-detail/foo.md       # DETAIL (load on-demand vía Read tool, ~10-20KB)
```

Cada `.claude/rules/X.md` post-slim contiene:
1. Header + 1-liner cardinal rule
2. Pointer absoluto al detail doc en línea 3-5
3. Tablas/diagramas críticos para operación inline
4. Top 3-5 anti-patterns inline (lista completa en detail)
5. Sección "Referencias" con detail doc + cross-references

## Cómo cargar el detail (per agent type)

**Auditores (`auditor-{backend,frontend,agentic}`)**:
```
Si tocás surface listada en .claude/rules/auditor-downstream-regression.md,
leé docs/rules-detail/auditor-downstream-targets.md (tabla SSoT 9 secciones)
para downstream test paths cross-engine + cross-brand.
```

**Builders (`builder-*`)**:
```
Si paradigm v4 / story-closure-gate / repro-mandatory aplica al ticket,
leé docs/rules-detail/{story-closure-gate,hotfix-repro-mandatory}.md
ANTES de spawn.
```

**PM (`/pm-vitalia`)**:
```
Si hay duda sobre flujo merge / capability promotion / archive pattern,
leé docs/rules-detail/{story-closure-gate,brand-docs-schema}.md.
```

## Inventario actual

| Slim rule | Detail doc | Notas |
|---|---|---|
| `auditor-downstream-regression.md` | `docs/rules-detail/auditor-downstream-regression.md` + `auditor-downstream-targets.md` | Tabla SSoT 9 secciones (A-I) en target doc |
| `story-closure-gate.md` | `docs/rules-detail/story-closure-gate.md` | 07-merge schema verbatim + gherkin_coverage examples |
| `auditor-self-fix-policy.md` | `docs/rules-detail/auditor-self-fix-policy.md` | Whitelist 17 + NEVER 16 + spawn templates verbatim |
| `brand-docs-schema.md` | `docs/rules-detail/brand-docs-schema.md` | R1+R2+R3 cement detail + 12 paths auto-gen SSoT |
| `hotfix-repro-mandatory.md` | `docs/rules-detail/hotfix-repro-mandatory.md` | Caso origen verbatim + 4 steps workflow |
| `anti-default-flip-audit.md` | `docs/rules-detail/anti-default-flip-audit.md` | Ejemplos CORRECTO/INCORRECTO commit body |
| `_CLAUDE-original-backup.md` | `docs/rules-detail/_CLAUDE-original-backup.md` | CLAUDE.md pre-slim (31KB) — federate docs schema, paradigm v4 full, 10 brands catalog detail, cost-routing, bootstrap completo |
| `_AGENTS-original-backup.md` | `docs/rules-detail/_AGENTS-original-backup.md` | AGENTS.md pre-slim (8.5KB) — skills SSoT, modules detail, defaults legacy single-brand |
| `learning-capture.md` | `docs/rules-detail/learning-capture.md` | Template canónico + clasificación por tipo + promotion path learning→rule + cleanup MEMORY.md |
| `github-actions-deferred.md` | `docs/rules-detail/github-actions-deferred.md` | Tabla workflows status + 13 secciones pre-commit hook + test invocation manual + reactivación procedure |
| `claude-md-overlay.md` | `docs/rules-detail/claude-md-overlay.md` | Estructura root (15 secciones) + overlay (10 secciones) + tabla detection por cwd + bootstrap brand nueva |
| `git-safety.md` | `docs/rules-detail/git-safety.md` | Flujo completo + procedimiento sync wip↔main + Fase solo-bootstrap detalle + tabla CI/CD |
| `anti-duplication-refining.md` | `docs/rules-detail/anti-duplication-refining.md` | Scan verbatim ejecutable + decision matrices (prior-art + cap_change_type) + tabla fuentes + enforcement |
| `spanish-text.md` | `docs/rules-detail/spanish-glossary.md` | Glosario voseo→neutro completo (50+) + magic comment detalle |

## Variante skill-owned (context-rot pass 2026-05-30)

Reglas phase-specific cuyo cuerpo vive en el skill DUEÑO (carga sólo cuando ese skill se activa), no en `docs/rules-detail/`. La rule en `.claude/rules/` queda como stub que apunta a:

| Slim rule | Cuerpo en skill |
|---|---|
| `architect-autonomous-mode.md` | `.claude/skills/architect/references/autonomous-mode.md` |
| `anti-orphan-integration.md` | `.claude/skills/architect/references/anti-orphan-integration.md` |
| `test-design-doctrine.md` | `.claude/skills/dev-team/references/test-design-doctrine.md` |
| `frontend-visual-fidelity.md` | `.claude/skills/frontend-expert/references/visual-fidelity.md` |
| `git-haiku-delegation.md` | `.claude/skills/commit-push/references/haiku-delegation.md` |
| `backend-ddd.md` (§ schema-mirror) | `.claude/skills/backend-expert/references/schema-mirror-exception.md` |
| `pm-skill-chaining.md` | ya replicado en `.claude/skills/pm-*/SKILL.md § Auto-chain rule` |

Resultado pass 2026-05-30: `.claude/rules/` 3484 → 1584 líneas (−55%, ~52k tokens menos always-loaded). Cuerpos preservados verbatim.

## Mantenimiento

Cuando cambia una regla:
1. Update SLIM (`.claude/rules/X.md`) si cambió el cardinal o las tablas críticas
2. Update DETAIL (`docs/rules-detail/X.md`) siempre — fuente de verdad histórica + examples completos
3. NO duplicar contenido — slim referencia detail, detail expande

Cuando agregás nueva rule grande (>5KB):
1. Crear `.claude/rules/X.md` con summary (~2-3KB)
2. Crear `docs/rules-detail/X.md` con contenido completo
3. Agregar row a tabla inventario en este README

## Savings totales (2026-05-23)

| Métrica | Antes | Después | Δ |
|---|---|---|---|
| CLAUDE.md + AGENTS.md + 8 rules + references/ deleted | 142.4 KB | 56.3 KB | **-86.1 KB** |
| Tokens auto-loaded | ~40k tokens | ~16k tokens | **-24k tokens (~60% reducción)** |

Sin pérdida de información: detalle preservado al 100% en `docs/rules-detail/` + skills `auditor` / `dev-team` saben dónde buscar.

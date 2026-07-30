# Spanish Text (UI user-facing)

**Alcance (acotado 2026-06-01 — Chris):** el neutro/anti-voseo aplica **SOLO a interfaces de usuario** — web UI (frontend) + output agéntico (lo que el agente le dice al usuario final). **NUNCA** al harness interno, docs, instrucciones, tooling o tests. El enforcement automático (`scripts/git-hooks/pre-commit` §1) escanea solo código de producto `.py`/`.ts`/`.tsx`; **NO escanea markdown, `.claude/`, `docs/`, `scripts/`, `tools/` ni tests**. El output agéntico se valida aparte con arch tests en `core/` (`test_*_voseo_compliance.py`, `test_system_prompt_neutro_latam.py`).

Aplica: React components, form-runtime schemas (labels/hints/placeholders), BE catalogs user-facing, DTOs messages, prompts LLM output user, emails, notificaciones.
NO aplica (voseo LIBRE): el harness (`.claude/{skills,rules,agents,hooks}`), toda la documentación (`docs/`, `*.md`), `scripts/`, `tools/` (cockpit), logs internos, errores técnicos, comentarios, variables, tests. Chris escribe en voseo y el harness/docs lo reflejan — es interno, no se restringe.

## R1 — Ortografía
Tildes + ñ + apertura `¿`/`¡`. Ej: días, Campaña, Inversión, Conversión, Configuración, Atracción, Nutrición, Adopción, Expansión, activación, adquisición, retención, ubicación.

## R2 — Español LatAm neutro (sin voseo)

Tuteo (`tú`). PROHIBIDO voseo (`vos/sos/tenés/podés/mirá/dejá`) + léxico marcado (`laburo/quilombo/pibe/dale/che/bárbaro/fijate`). Voseo excluye MX/CO/PE/CL/EC.

**Subset alta-frecuencia (glosario completo en `docs/rules-detail/spanish-glossary.md`):**

| Voseo | Neutro | Voseo | Neutro |
|---|---|---|---|
| vos / sos | tú / eres | tenés / podés | tienes / puedes |
| mirá / dejá | mira / deja | poné / usá | pon / usa |
| seleccioná / agregá | selecciona / agrega | configurá / revisá | configura / revisa |
| guardá / escribí | guarda / escribe | elegí | elige |
| cambiá / volvé | cambia / vuelve | activás / desactivás | activas / desactivas |
| dale (imperativo) | asígnale/ponle/define | fijate | revisa/ten en cuenta |

## Checklist pre-commit
1. Imperativo voseado (`-ás/-és/-ís`) → tuteo · 2. Léxico regional → neutro · 3. Tildes/eñes/¿¡

## Excepción sales_agent
Output sales_agent respeta voz tenant (puede tener voseo si tenant AR). Ver `sales-agent-expert`.

## Magic comment escape (R25 — obsoleto para archivos internos desde 2026-06-01)
Tras acotar el enforcement a UI/agentic, los archivos internos (markdown, `.claude/`, `docs/`, `scripts/`, `tools/`, tests) **ya NO se escanean** → **NO necesitan** comentario mágico. El `# voseo-allowed` / `<!-- voseo-allowed -->` queda solo como escape residual para el caso raro de un archivo de **código de producto user-facing** (`.py`/`.ts`/`.tsx`) que a propósito muestre voseo (ej. copy de un tenant AR). Los ~73 comentarios mágicos heredados en docs/skills son ahora ruido inofensivo (limpieza opcional, Wave 3). Variantes: `docs/rules-detail/spanish-glossary.md § Magic comment`.

## Referencias
- `docs/rules-detail/spanish-glossary.md` — **glosario completo (50+ conversiones) + magic comment detalle**

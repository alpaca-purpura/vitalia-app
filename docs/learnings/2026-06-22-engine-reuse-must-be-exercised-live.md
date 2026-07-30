---
date: 2026-06-22
type: técnico-transversal
brands_affected: [vitalia, nicolify, comunify, lupulo]
promotable: candidate
origin_story: vitalia/docs/product/stories/vitalia-fase2-adrian-canal-inbound
related:
  - vitalia/docs/learnings/2026-06-04-embudo-imagined-contract-never-integrated.md
  - .claude/rules/definition-of-done-live-verify.md
applied: pending
---

# Un "mapa de reuso" con path:line es necesario pero NO suficiente: el engine reusado hay que EJERCERLO live en la marca antes de declararlo "montable"

## Qué pasó

La story `vitalia-fase2-adrian-canal-inbound` (loop inbound de Adrián) se diseñó como
**"MONTA sobre el engine `core/luana-core-sales-agent` — reuso ≈90%, cero engine edit"**, con un
mapa de reuso detallado (`02-design-agentic.md §2`) que citaba **cada pieza con `path:line`** ("el
supervisor ya rutea", "el TOOL_REGISTRY despacha", "el SchedulerProvider routea por tenant", "el
engine ya honra la instrucción del operador"). El spec/diseño se ratificó sobre ese mapa.

Al **ejercer el grafo live** (mensaje real por Telegram contra el stack dev) cascadearon **6 muros de
engine + 3 de entorno** que el mapa asumió resueltos y NO lo estaban — porque **el grafo sales_agent
NUNCA se había ejercido dentro de un proceso de marca** (el loop "nunca se cableó"):

- **ESC-1** scheduler_provider_for_tenant hardcodea `"internal"` (`providers.py:447`, `_ = tenant_id # reserved`)
- **ESC-2** TOOL_REGISTRY estático no mergea tools EP-3 (`tools.py:107` + `nodes.py:402`)
- **ESC-3** STAGE_TOOL_SCOPE hardcodeado (`registry.py:56`)
- **ESC-4** `LeadModel.messages = relationship("MessageModel")` string pelado → ambiguo con el MessageModel de marca → "Multiple classes found" → mapper init falla (`crm.py:209`)
- **ESC-5** `templates_dir` hardcodeado al layout monolítico pre-multibrand (`prompts/base.py:32`)
- **ESC-6** `PromptVersion` sin `tenant_id`
- **HB-92** la instrucción del operador: el engine lee `checkpoint.resume_objective`, NO el `metadata_info` que el diseño asumió (se cazó construyendo, no diseñando)
- Entorno: Redis caído (buffer `NoneType.rpush`), tabla `channel_connections` inexistente en vitalia_dev, env `VITALIA_TELEGRAM_*` con nombres que no matchean `.env.dev`

Cada uno: el path **EXISTÍA** (el mapa no mentía sobre su presencia) — pero **no FUNCIONABA** cuando se
invocaba desde el contexto de una marca.

## Por qué (la trampa)

**Verde en aislamiento ≠ integrado.** Todo estaba verde: unit tests, arch fitness, hasta los 5 goldens
agentic (que corrieron contra Postgres real). Pero **ninguno ejercía el grafo end-to-end en el proceso
de la marca** — corrían piezas aisladas o por code-paths distintos al webhook→orchestrator→grafo→persistencia.
La integración real (dos registries SQLAlchemy coexistiendo, el grafo resolviendo el tenant, los prompts
cargando en el layout multibrand, el provider routeando) **nunca se ejecutó** hasta la live-verify.

Citar que un símbolo del engine **existe** (`path:line`) prueba presencia, no funcionalidad-desde-la-marca.
El `≈90% reuso` era una estimación sobre presencia, no sobre integración ejercida.

## Cómo aplicarlo

1. **DoD #37 aplica al REUSO, no solo al código nuevo.** Cuando un diseño dice "MONTA sobre el engine
   (reuso ≈N%)", la afirmación es una hipótesis hasta que se **ejerce el path reusado live desde el
   contexto de la marca**. El % de reuso es estimación hasta ese smoke.
2. **Para engines agénticos: corré el grafo end-to-end en el proceso de la marca UNA vez antes de
   estimar reuso / cerrar el diseño.** Un mensaje real → reply, leyendo logs. Eso habría cazado
   ESC-4/5/6 + Redis + channel_connections en el refinamiento, no en el build/G.
3. **El prior-art scan del architect debe verificar reachability+funcionalidad, no solo presencia**:
   "este registry/provider/relationship, ¿está EXERCISED por algún consumer hoy, o es un seam declarado
   pero nunca corrido?" Un `# reserved for future` / un default monolítico / un `_not_implemented_yet`
   son señales de seam-no-ejercido → tratarlos como muros, no como reuso.
4. **Un engine compartido que ningún brand ejerció todavía = riesgo de integración latente.** El primer
   brand que lo cablea paga la deuda de los 4. Vale un smoke de integración temprano (no esperar al G).

## Evidencia

- 03-arch.md § Engine-boundary escalations (ESC-1/2/3, hallados por el architect en el re-scan).
- chris-input.md 2026-06-22 (ESC-4/5/6, hallados por la live-verify del grafo).
- Proposal `docs/promotion-protocol/proposals/2026-06-22-sales-agent-multibrand-graph-runtime.md` (el lift que cierra los 6).
- Es la **2da vez** de la misma trampa: la 1ra fue `[[embudo-imagined-contract-never-integrated]]`
  (FE↔BE camelCase imaginado, 2026-06-04). Ahí fue contrato FE↔BE; acá es reuso brand↔engine. Misma raíz:
  contrato/seam declarado, nunca ejercido cruzando el límite real.

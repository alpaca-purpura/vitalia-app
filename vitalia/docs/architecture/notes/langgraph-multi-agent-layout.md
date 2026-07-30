---
status: pending-investigation
created: 2026-05-21
follow_up_when: "Sesión dedicada a refactor LangGraph multi-agente (post shell-organism shipping)"
ratified_by: chris
---

# Nota — Layout LangGraph multi-agente (Valeria router + 4 specialists)

## Contexto

Vitalia adopta paradigma de 5 agentes-empleado visibles + 1 sección configurar:

- **Lisa** (Mi Clínica — marca + escalera de valor + tratamientos + doctores + compliance + landing)
- **Lucas** (Atraer — growth + campañas + creatividades + tendencias mercado)
- **Adrián** (Vender — inbox + pipeline + reservas + cualificación + outbound)
- **Valeria** (Operar — agenda + pacientes activos + tratamientos en curso + tareas + check-in/out)
- **Camila** (Mantener — testimonios + reseñas + NPS + ausencia + referidos + reputación online)
- **Configurar** (ícono genérico, sin agente)
- **Mateo** (transversal — landing + diseño futuro, sin tab)

**Cement importante (Chris 2026-05-21):** los dueños agéntico son etiquetas conceptuales para
NAVEGACIÓN + UX + MARKETING. El backend DDD se mantiene (modules `compliance`, `marketing`,
`fidelizacion`, `sales_agent`, `crm`, `clinics`, etc.). El frontend FSD se mantiene
(`features/{inbox,marketing,fidelizacion,...}`).

## Visión final (norte)

> "Como una secretaria real. El dueño de la clínica le habla a Valeria por WhatsApp y le pide
> información o acciones sin entrar al sistema. Valeria delega internamente a Lisa/Lucas/Adrián/
> Camila según corresponda."

El sistema web existe para ser **manejado por los agentes** (eventualmente). La cara web es
solo visualización de lo que los agentes ejecutan.

## Decisión pendiente

Cuando llegue el momento de refactorizar la parte LangGraph del backend:

### Opción 1 — Carpeta única `agents/` con sub-agentes dentro
```
core/luana-core-sales-agent/src/luana_core_sales_agent/agents/
├── router/                          # Valeria como router orquestador
├── lisa/                            # specialist marca + offer
├── lucas/                           # specialist growth
├── adrian/                          # specialist closer (ya existe)
├── camila/                          # specialist retention
└── shared/                          # tools cross-agent
```

### Opción 2 — Cada agente como módulo separado
```
core/luana-core-{agent-name}/src/...
├── luana-core-agent-router/         # Valeria
├── luana-core-agent-lisa/
├── luana-core-agent-lucas/
├── luana-core-agent-adrian/         # ya existe como sales-agent
└── luana-core-agent-camila/
```

### Opción 3 — Híbrido (subagent-as-tool)
```
core/luana-core-sales-agent/        # mantiene contenido existente
└── ...
core/luana-core-orchestrator/       # NUEVO — Valeria router + handoff registry
└── handoffs/{lisa,lucas,camila}.py # cada specialist invocado como tool
```

## Criterios para decidir (cuando toque)

1. **Cost de tokens** — minimizar prompt overhead. Router debe ser mínimo (no recargar todo el contexto cada turno).
2. **Cache prefix Anthropic** — slot architecture compatible con 5 minutos / 1 hora TTL.
3. **Latencia** — handoff agent→agent debe ser <500ms.
4. **Observabilidad** — cada hop agent debe trazar `copilot_trace_event` con qué agente atendió.
5. **Eval goldens** — la suite debe distinguir fallas de router vs fallas de specialist.
6. **Reuso engine** — Lisa/Lucas/Camila pueden compartir tools de inventory/booking/notify sin duplicar.
7. **Multi-brand** — el patrón debe servir también para comunify/nicolify (cada brand tendría sus propios specialists pero el orchestrator pattern es shared).

## Skills a cargar durante investigación

- `sales-agent-expert` (current state Adrián)
- `copilot-expert` (current state Valeria onboarding)
- `claude-api` (cache + cost optimization)
- `tessl__langgraph` (multi-agent supervisor pattern oficial)

## Investigación pre-decision recomendada

- LangGraph official "multi-agent supervisor" pattern (date-aware research)
- Anthropic agentic computer-use pattern (cache prefix multi-agent)
- DeepAgents subagent isolation (cuando aplica vs cuando es overkill)
- Cost benchmarks reales router con N specialists

## Lo que SÍ está cementado hoy

- Backend modules existentes NO se rearman (compliance, marketing, fidelizacion, etc. siguen igual)
- Frontend features NO se rearman (FSD intacto)
- Atom ownership es etiqueta navegacional, no estructural
- Mateo es transversal — sin módulo backend dedicado, se invoca como tool desde otros agentes cuando aplique (futuro)

## Follow-up

Cuando se abra story tipo "vitalia-langraph-multi-agent-router" o "luana-core-orchestrator-bootstrap":
1. Leer esta nota
2. Hacer date-aware research con skills mencionados
3. Producir ADR formal (probablemente `vitalia/docs/architecture/ADR-vitalia-002-multi-agent-langraph-layout.md`)
4. Decidir entre las 3 opciones (o variante nueva descubierta)

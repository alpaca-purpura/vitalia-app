# Client Simulator — Luana quality tool

Engine compartido para simular conversaciones cliente ↔ `sales_agent` cross-brand. Detecta problemas de calidad, regresiones de voz, fallos de tool dispatch, y oportunidades de mejora.

**Origen:** sub-app `client_simulator/` creada para Nicolify pre-multibrand reorg (`/home/chalreme/Documentos/ap_sales_agent/client_simulator/`). Recuperada y promovida a `apps/client-simulator/` como engine cross-brand 2026-05-16 (decisión: una sola tool, escenarios per-brand).

## Filosofía: engine compartido + escenarios per-brand

```
apps/client-simulator/                              ← engine (Python LangGraph + docker-compose)
  src/simulator/                                    — graph, customer_node, agent_bridge, termination
  src/infrastructure/                               — db, repositories
  src/domain/                                       — models
  pyproject.toml, docker-compose.yml, Dockerfile
  .env.example                                      — config template (BACKEND_URL per brand)

{brand}/backend/tests/agentic_evals/simulator/      ← escenarios per-brand
  scenarios/
    happy_path.yaml                                 — conversación nominal
    edge_cases/*.yaml                               — edge cases brand-specific
    regressions/*.yaml                              — bugs históricos como tests
  personas/                                         — reusa o extiende fixtures brand
  README.md                                         — instrucciones brand-scoped
```

**Por qué este diseño:**
- Engine es **una sola tool de calidad** (similar a pytest engine compartido). LangGraph state machine + customer node + agent bridge son infraestructura cross-brand.
- Lo que cambia per-brand: persona del cliente simulado, voice esperada, KB pack del agente, tools disponibles, rubric de evaluación, idioma/dialecto.
- Brands cargan sus escenarios via `--brand {slug}` y el simulator instancia el `sales_agent` correspondiente con sus assets.

## Uso (cuando esté integrado al stack multimarca)

```bash
# Levantar brand stack target primero (per docs/process/docker-dev-multibrand.md)
make dev-vitalia       # o vitalia, comunify, lupulo

# Configurar .env desde template
cp apps/client-simulator/.env.example apps/client-simulator/.env
# editar: BRAND_SLUG=vitalia, BACKEND_URL=http://luana-vitalia-backend-dev:8002

# Run simulator (ejemplo — comandos finales TBD post-integración)
cd apps/client-simulator
python -m src.simulator.cli --brand vitalia --scenario happy_path
python -m src.simulator.cli --brand vitalia --scenario edge_cases/no_show_followup
python -m src.simulator.cli --brand comunify --scenario regressions/cohort_capacity_race
```

## Estado actual — integración pendiente

Post recovery 2026-05-16, el engine vive aquí pero **no está integrado al stack multimarca**:

- ⚠️ `src/simulator/agent_bridge.py` apunta a endpoints monolito Nicolify pre-reorg
- ⚠️ Imports + paths necesitan refactor para consumir engine `luana-core-sales-agent` + brand extensions
- ⚠️ Falta CLI parametrizable por `--brand`
- ⚠️ Falta loader de scenarios desde `{brand}/backend/tests/agentic_evals/simulator/scenarios/`

**Cuándo integrar:** próxima story de calidad agentic cross-brand. Trabajo estimado: M (~3-5 días) — requiere:
1. Refactor `agent_bridge.py` para usar brand resolver
2. Implementar scenario loader desde brand-scoped paths
3. Conectar a observability eval bucket (`eval_simulator_*` tablas — ya existen en snapshot)
4. CLI args + sub-comandos
5. Docs de cómo crear scenarios per-brand

Mientras tanto, el código está preservado y disponible para inspección/referencia.

## Estructura interna engine

```
src/
├── config.py                — env config loader
├── domain/
│   └── models.py            — Conversation, Turn, Persona, EvaluationResult dataclasses
├── infrastructure/
│   ├── database.py          — SQLite local (data/simulator.db, gitignored)
│   └── repositories.py      — Conversation + Turn persistence
└── simulator/
    ├── graph.py             — LangGraph StateGraph entrypoint
    ├── customer_node.py     — LLM-driven customer turn generator
    ├── agent_bridge.py      — Connection to sales_agent under test (refactor pendiente)
    ├── state.py             — Conversation state TypedDict
    └── termination.py       — Conversation termination policies (timeout, goal_met, error)
```

## Excluded from commit

Per `.gitignore`:
- `data/` (local SQLite db)
- `.env` (secrets — usar `.env.example`)
- `__pycache__/`, `*.pyc`, `.ruff_cache/`

## Referencias

- Promotion proposal candidato (futura story): cuando se integre al multimarca, lift a `core/luana-core-sales-agent/eval_simulator/` si la engine se vuelve cross-pkg generalizable
- Tests eval simulator schema (eval_simulator_* tables): viven en `001_initial_snapshot.py` post Story 10 T-10 consolidación
- Per-brand simulator scenarios entrypoint: `{brand}/backend/tests/agentic_evals/simulator/scenarios/README.md`
- Decisión arquitectónica: `docs/architecture/luana-platform/04-pending-migrations.md` § client_simulator

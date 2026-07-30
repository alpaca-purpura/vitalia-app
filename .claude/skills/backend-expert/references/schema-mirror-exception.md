# Schema-mirror exception — backend-ddd detail (moved from .claude/rules/ 2026-05-30, load on-demand)

Origen R5 process-improvement 2026-05-05. Lo lee on-demand `builder-backend` / `auditor-backend` cuando una engine migration introduce tabla y el model class debe vivir en el módulo consumer per-brand.

## Regla

`builder-backend` MAY touch `{brand}/backend/src/modules/{brand}/copilot/persistence/models/` AND `{brand}/backend/src/modules/{brand}/sales_agent/persistence/models/` SOLO para schema mirror desde engine migration (`core/luana-core-observability/`, `core/luana-core-copilot/`, etc.). Cero juicio caso-a-caso auditor.

**Contexto:** business engine packages (`core/luana-core-observability/src/luana_core_observability/persistence/`) introducen tabla → SQLAlchemy model class debe vivir en módulo consumer per-brand (`{brand}/backend/src/modules/{brand}/{copilot,sales_agent}/persistence/models/`) para mantener domain ownership por brand. Builder-backend genera/modifica esos archivos para reflejar DDL nuevo SIN tocar `domain/`, `application/`, ni `api/` del módulo agentic per-brand.

**Permitido bajo esta exception:**
- Add/modify SQLAlchemy `Mapped[]` columns matching engine migration DDL
- Add/modify table indexes matching engine migration
- Add/modify foreign keys hacia tablas creadas por engine migration
- Mark deprecated columns con `# DEPRECATED:` comment

**NO permitido bajo esta exception:**
- Tocar `{brand}/backend/src/modules/{brand}/{copilot,sales_agent}/{domain,application,api,observability}/` — sigue jurisdicción `builder-agentic`
- Cambiar comportamiento runtime del módulo agentic per-brand (sólo schema)
- Crear nueva tabla SOLO en módulo agentic per-brand (debe nacer en engine `core/luana-core-*/` con consumer mirror per brand, no al revés)
- Modificar `personality_profiles.system_instruction` o cualquier otro field semantic-load del módulo

**Audit:** auditor-backend debe APPROVE estos cambios sin escalate. Auditor-agentic NO audita schema mirror (es business migration ripple, no agentic logic). Si schema change introduce regression cross-surface → R3 downstream regression scope captura.

**Caso origen:** PI-12 S1 T-1 (cost_recorder canonicalization). Builder necesitaba mirror nuevas columnas `cost_usd`, `cache_read_tokens`, `provider_canonical` en `modules/{copilot,sales_agent}/persistence/models/copilot_llm_call.py` (era single-brand; post-reorg vive en cada `{brand}/backend/src/modules/{brand}/copilot/persistence/models/`). Auditor inicialmente flagged "out-of-scope" — Chris ratificó exception. Codificada para evitar re-litigation.

# 03-arch.md — platform-lift-sales-agent-graph-runtime (Phase 1: ESC-4/5/6 runtime)

> **technical-story · engine lift · `/architect` = refiner (WT5).** Contract-spec = la proposal accepted §4 + esta arch.
> `verification_nature: técnica`. Bar = **efecto runtime** (grafo corre en vitalia).
> **Scope = Phase 1 (ESC-4/5/6 runtime).** Phase 2 (ESC-1/2/3 features) = package separado.
>
> ★ **Los 3 fixes están EMPÍRICAMENTE PROBADOS por el architect (spike RED→GREEN + no-regression en aislamiento).**
> Ver § Spike verification. El dev-team **aplica los diffs verificados** (copy-paste exacto) bajo TDD; no inventa nada.

---

## TL;DR para el dev-team (los 3 diffs, ya probados)

| ESC | Archivo | Cambio EXACTO (probado) | Test |
|---|---|---|---|
| ESC-4 | `core/luana-core-platform/.../infrastructure/models/crm.py` L210 | `"MessageModel"` → `"luana_core_sales_agent.infrastructure.models.message_model.MessageModel"` (**solo** esta línea) | arch test subprocess (abajo) |
| ESC-5 | `core/luana-core-sales-agent/.../infrastructure/prompts/base.py` `__init__` | default `templates_dir=None` → `Path(__file__).resolve().parent/"templates"` + override branch | arch test subprocess |
| ESC-6 | `core/luana-core-sales-agent/.../infrastructure/models/prompt_version_model.py` | + `tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)` | arch test (import) |

★ **CORRECCIÓN vs proposal/v1 (probado):** ESC-4 es **UNILATERAL** — solo `crm.py`. NO se toca `message_model.py:46`
(`MessageModel.lead → "LeadModel"`): `LeadModel` es **único** (solo platform; vitalia NO define homónimo de LeadModel,
solo de MessageModel). Qualificar el otro lado sería innecesario + agregaría acoplamiento de path platform→sales-agent inverso.

---

## Surfaces involved

| Surface | Toca | Editable (worktree core) |
|---|---|---|
| BE engine — `core/luana-core-platform` | crm.py relationship target (ESC-4) | ✅ |
| BE engine — `core/luana-core-sales-agent` | prompts/base.py (ESC-5) · prompt_version_model.py (ESC-6) | ✅ |
| AGENTIC runtime | el grafo consume lo anterior (mapper init + prompt load) — **sin cambio de comportamiento** | indirecto |
| Brand migrations | ESC-6 ALTER idempotente | ⛔ **brand-authored** (`migration_notes.md`) |

**Constraint dura (learning 2026-06-16):** validación in-place SIEMPRE con
`PYTHONPATH=${WS}/core/luana-core-sales-agent/src:${WS}/core/luana-core-platform/src` (el `.venv` symlinkea a main).

---

## Contract-spec (análogo del spec · NO Gherkin)

**Contrato expuesto (subset Phase 1 del §4 del proposal):**
1. Relationships del engine resuelven sin ambigüedad cuando una marca define un modelo homónimo (`MessageModel`) sobre el mismo `Base` (ESC-4).
2. Prompts del engine resuelven independiente del cwd y sin duplicar templates por marca; variantes por tenant vienen de DB (ESC-5 + ESC-6).
3. **CERO cambio al `AgentState` TypedDict** ni al comportamiento del agente.

**Consumers (anti-isla CONN):** el grafo `sales_agent` de las 4 marcas (vitalia = 1er consumidor live).
**Invariante:** un engine compartido por N marcas NUNCA rompe su mapper init / prompt load porque una marca registre un homónimo o corra desde otro cwd/layout.
**Verificación-por-efecto:** grafo end-to-end en vitalia — mensaje Telegram real → reply de Adrián + fila conversación/trace/costo en DB + cero traceback. Post merge+sync (Chris).

---

## ★ Spike verification (architect-proven · RED→GREEN + no-regression)

Todo corrido en este worktree con PYTHONPATH override (modelos reales, SQLAlchemy 2.0.49). Diffs aplicados → probados → **revertidos** (repo queda en RED para el TDD del dev-team).

### ESC-4 — PROBADO
- **RED** (spike: platform LeadModel + engine MessageModel + un 2º MessageModel sintético tipo-vitalia → `configure_mappers()`):
  `InvalidRequestError: Multiple classes found for path "MessageModel" in the registry of this declarative base.` ← **idéntico al error live**.
- **GREEN** (aplicado el diff de 1 línea en crm.py): `configure_mappers() OK` con el set realista COMPLETO
  (platform `LeadModel`/`SaleModel`/`CustomerProfileModel` + sales-agent `MessageModel` + scheduling `AppointmentModel` + iam `TenantModel` + offer-studio `ProductModel` + homónimo sintético `MessageModel`). **Sin ambigüedad residual.**
- **Confirmado one-sided:** NO hizo falta tocar `message_model.py:46` (`"LeadModel"` único).

### ESC-5 — PROBADO
- **RED** (spike: `os.chdir(/tmp)` + `PromptLoader()` + `get_template("message_completeness.j2")`):
  `TemplateNotFound: ...'/tmp/src/modules/sales_agent/infrastructure/prompts/templates'` ← **idéntico al error live**.
- **GREEN** (aplicado el diff engine-relative): `get_template OK`; `templates_dir` resuelto a
  `.../core/luana-core-sales-agent/src/luana_core_sales_agent/infrastructure/prompts/templates` desde cwd=/tmp.

### ESC-6 — PROBADO
- **RED** (spike): `hasattr(PromptVersion,'tenant_id') == False` → `AttributeError: type object 'PromptVersion' has no attribute 'tenant_id'` ← **idéntico al error live**.
- **GREEN** (aplicada la columna): `tenant_id` presente; ambas ramas del query de `base.py` (specific-override `== tid` y system-default `IS NULL`) construyen sin error.

### No-regression — PROBADO (decisivo)
Subset DB-persistencia (`tests/application/tools/payment/` + `scheduling/test_scheduling_tools.py`) corrido **en aislamiento determinístico** (proceso fresco, set de modelos fijo): **baseline (sin edits) = edited (con edits) = 3 failed / 37 passed, IDÉNTICO failure set**. ⇒ mis fixes causan **CERO regresión**.

> Las 3 fallas persistentes son pre-existentes y ajenas a los ESC: `sqlite3.OperationalError: no such table: booking_links` (gap de `create_all`/fixture del env PYTHONPATH-hack).

---

## ★ Realidad del entorno de tests (CRÍTICO para el dev-team)

Correr la suite COMPLETA de sales-agent vía PYTHONPATH-override en este worktree es **NO CONFIABLE**. Comprobado: full-suite arrojó 38 fallas (sin mis edits) vs 67+34err (con mis edits), pero el subset en aislamiento dio IDÉNTICO. La diferencia es **ruido de estado global**:

1. **`configure_mappers()` es global + lazy + cacheado.** El set de modelos registrados al primer trigger depende del ORDEN de imports de la sesión → fallas no determinísticas.
2. **Fragilidad pre-existente del conftest** `core/luana-core-sales-agent/tests/conftest.py:~187`: define un `AppointmentModel` **sintético** sobre el `_Base` cuando la tabla no está reclamada. Si además se importa el `AppointmentModel` real (scheduling) → 2 `AppointmentModel` → `Multiple classes found for path "AppointmentModel"` en cascada (el 34-error que vi). **Tech-debt del conftest, NO de este lift.**
3. **Test stale de colección:** `tests/orchestrator/test_chat_orchestrator_snapshot.py:27` importa `tests.modules.sales_agent.orchestrator...` (layout monolítico pre-multibrand) → `ModuleNotFoundError: No module named 'tests.modules'` → bloquea la colección. **Pre-existente.**
4. **Tests que necesitan tablas reales** (`booking_links`, etc.) fallan en sqlite-memoria sin el `create_all` correcto.

**Conclusión de diseño (afecta 04-validators):**
- El gate confiable **in-worktree** = los **arch tests por ESC, aislados en SUBPROCESO** (como los spikes — set de modelos controlado, determinístico).
- La suite completa + downstream regression ×4 = correr en **entorno canónico** (`make ci-parity` / uv editable + Postgres real), realísticamente **post-merge**. NO son gate confiable vía PYTHONPATH-hack.
- El test stale (#3) y la fragilidad del conftest (#2) → `/harness-issue` (tech-debt; no bloquean este lift). El dev-team corre las suites con `--ignore` del stale + `--continue-on-collection-errors`.

---

## ★ Clean architecture / cohesión-acoplamiento (lente que pidió Chris)

- **ESC-4 (acoplamiento):** `LeadModel` (platform, shared-kernel ORM) declara `messages → MessageModel` (sales-agent). El docstring de `crm.py` justifica el shared-kernel: "estos modelos viven acá para que sales_agent/analytics puedan JOIN sin importar de `luana_core_crm.*` (violaría DDD)". El string es **late-bound** (sin import Python → sin ciclo). Qualificarlo **MEJORA cohesión** (el engine declara su target explícito, autocontenido) **sin agregar acoplamiento de import**. ⚠️ **Deuda arquitectónica conocida (no expandir):** que un modelo de platform tenga relación a un modelo de sales-agent es un acople kernel→higher-level. Lift futuro podría mover esa relación; **este lift NO la expande** (solo desambigua).
- **ESC-5 (cohesión↑ acoplamiento↓):** templates co-locados con su loader (alta cohesión) + cero dependencia de cwd/layout de marca (bajo acoplamiento). Mejora neta. (Smell residual: `prompt_loader = PromptLoader()` singleton módulo-level — estado global; refactor a DI fuera de scope.)
- **ESC-6 (acoplamiento↓):** `tenant_id` **sin FK** a `tenants` (igual que `MessageModel.tenant_id`) → el modelo de persistencia del engine NO depende duro del schema de platform (hexagonal: el adaptador de persistencia no se ata a la tabla de otro paquete). Decisión consciente, consistente con el patrón vigente.

---

## ESC-4 — relationship module-qualified (BLOCKER PRIMARIO) · UNILATERAL

**Causa (verificada):** dos clases `MessageModel` sobre el mismo `Base` (`luana_core_platform.domain.base_entity.Base`):
engine `core/luana-core-sales-agent/.../message_model.py` (`messages`) + vitalia `vitalia/.../crm/.../message_model.py` (`vitalia_messages`). `crm.py:210` resuelve `"MessageModel"` por nombre simple → ambiguo. **vitalia NO define `LeadModel` homónimo** (solo `LeadActivityModel`, `LeadStageTransitionModel`, `ConversationModel`) → el lado `MessageModel.lead → "LeadModel"` es único → **no se toca**.

**Diff EXACTO (probado · solo crm.py):**
```python
# core/luana-core-platform/.../infrastructure/models/crm.py  — LeadModel.messages (~L209-213)
    messages = relationship(
-       "MessageModel",
+       "luana_core_sales_agent.infrastructure.models.message_model.MessageModel",
        back_populates="lead",
        cascade="all, delete-orphan",
    )
```

**NO tocar:** columnas/FKs/`back_populates`; `message_model.py:46` (`"LeadModel"`, único); `appointments`/`tenant` (ver Latent finding).

**Arch test (RED-first, SUBPROCESO):** ver `test_esc4_relationship_module_qualified.py` en 04-validators — registra el set realista + homónimo sintético `MessageModel` **en un subproceso** (estado de import limpio, determinístico) → `configure_mappers()` sin `InvalidRequestError`. RED reproduce el error antes del fix.

---

## ESC-5 — templates_dir engine-package-relative (cwd-independiente)

**Causa (verificada):** `base.py:32` default monolítico `"src/modules/sales_agent/..."` + `base.py:36` `Path.cwd()` → resuelve relativo al cwd del proceso de marca (no existe). El singleton `prompt_loader = PromptLoader()` (L220) hereda el default roto.

**Diff EXACTO (probado):**
```python
# core/luana-core-sales-agent/.../infrastructure/prompts/base.py — PromptLoader.__init__
    def __init__(
        self,
-       templates_dir: str = "src/modules/sales_agent/infrastructure/prompts/templates",
+       templates_dir: str | None = None,
    ) -> None:
        """Initialize instance."""
        # 1. Configurar File System Loader (Fallback)
-       base_path = Path.cwd()
-       self.templates_dir = templates_dir
-       full_path = str(base_path / templates_dir)
+       # Default: templates shipped WITH the engine package — cwd-independent, multibrand-safe.
+       # Override (explicit param): absolute as-is, relative resolved against cwd (back-compat).
+       if templates_dir is None:
+           full_path = str(Path(__file__).resolve().parent / "templates")
+       else:
+           _p = Path(templates_dir)
+           full_path = str(_p if _p.is_absolute() else Path.cwd() / _p)
+       self.templates_dir = full_path
```

**Verificado seguro:** `self.templates_dir` solo se consume dentro de `base.py` (grep). El override branch preserva back-compat para callers que pasan dir relativo (`copilot` pasa dir explícito a SU propio loader — paquete distinto, no afectado). **Mismo bug-class en `core/luana-core-platform/.../prompts/base.py:23` (default `"src/modules/copilot/..."`+cwd, singleton L195) — FUERA de scope** (paquete distinto; copilot lo cablea aparte) → `/harness-issue`.

**Arch test (RED-first):** `PromptLoader()` desde cwd arbitrario (tmp) → `get_template("message_completeness.j2")` sin `TemplateNotFound`.

---

## ESC-6 — prompt_versions.tenant_id (modelo + migración brand-authored)

**Causa (verificada):** `prompt_version_model.py` no declara `tenant_id`, pero `base.py:90,109` ya filtran `PromptVersion.tenant_id`. Con `PROMPT_SOURCE=HYBRID` (default) la rama DB se ejecuta → AttributeError.

**Diff EXACTO — modelo (probado · este worktree):**
```python
# core/luana-core-sales-agent/.../infrastructure/models/prompt_version_model.py — tras metadata_info
+   # Tenant scoping (ESC-6): NULL = system default (fallback path in PromptLoader._get_from_db).
+   # No FK to tenants (engine model stays decoupled from platform tenants table — matches MessageModel).
+   tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
```

**Migración (brand-authored):** cada brand agrega en SU alembic un `CREATE TABLE IF NOT EXISTS prompt_versions (...)` + `ADD COLUMN IF NOT EXISTS tenant_id` + índice. Backfill no-op (NULL = system default). DDL exacto en `migration_notes.md`. **No se autorea acá** (cero marca en worktree core; no hay alembic en `core/`).

**Arch test (RED-first):** `hasattr(PromptVersion,'tenant_id')` + el query specific-override/system-default construye sin AttributeError. DB-level deferido a brand-migration + efecto runtime.

---

## ★ Latent finding (NO en scope · documentado para no romper algo) — `appointments`

`LeadModel.appointments = relationship("AppointmentModel", foreign_keys="AppointmentModel.lead_id")` (crm.py:214) es **la misma clase de ambigüedad** que ESC-4: si 2 `AppointmentModel` se registran sobre el `Base` → `Multiple classes found for path "AppointmentModel"`.

- **En producción HOY (vitalia): SEGURO.** vitalia NO define `AppointmentModel` homónimo (usa `vitalia_bookings`). Mi spike probó `configure_mappers()` limpio con el `AppointmentModel` real (único, de scheduling) — el `appointments` resuelve OK.
- **Dónde aparece:** solo en la suite de tests (conftest sintético). Es **fragilidad del conftest**, no de prod.
- **Riesgo futuro:** una marca que defina `AppointmentModel` homónimo (o el lift de Story 8) re-dispara el bug.
- **NO tocar en este lift:** el `foreign_keys="AppointmentModel.lead_id"` es stub-targeted (Story 8 pending). Qualificar el target sin el lift completo podría romper el stub. Respetá el scope del proposal.
- **Recomendación (Phase 2 / Story 8):** cuando se liftee appointments, aplicar el mismo patrón module-qualified + considerar una arch-fitness rule que exija targets qualified para relationships del engine cuyo modelo brands homonyman (guardrail escalable contra esta clase entera de bug).

---

## Cross-cutting decisions
- **Tenant isolation:** ESC-6 AÑADE tenant-awareness a prompts (specific override + system-default NULL). Refuerza aislamiento.
- **PII:** ninguna superficie nueva expone PII.
- **Comportamiento del agente:** CERO cambio (AgentState/prompts-content/tools/voz intactos).
- **Semver:** `minor` en `core/luana-core-sales-agent` (+ `core/luana-core-platform` por ESC-4) — additivo + bugfix.

## Integration design (CONN)
- **Reachability:** marca recibe mensaje → grafo arranca → **mapper init** (ESC-4) → **prompt load** (ESC-5 templates + ESC-6 tenant override DB) → specialist responde → fila DB.
- **Consumers:** grafo `sales_agent` de vitalia (live) + nicolify/comunify/lupulo (mismo engine).
- **Registration points:** N/A nuevos — fixes en el call-path EXISTENTE (registry de mappers + singleton loader).
- **Home:** zona **Infraestructura** → caja **motor-agentico**. `cap_target: null` (engine-hardening · gate HB-34 no exige cap YAML para `fix`).

## Downstream regression (R3)
Engine compartido por 4 marcas. Gate confiable = entorno canónico post-merge (`ci-parity` + Postgres). En worktree, el arch test ESC-4 (subproceso, con homónimo) cubre el caso que rompió live. lupulo = placeholder (skip documentado).

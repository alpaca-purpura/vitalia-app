---
proposal_id: 2026-05-19-purge-nicolify-defaults-core-config
state: migrated
opened_date: 2026-05-19
opened_by: /pm-luana
ratified_by: Chris
ratified_date: 2026-05-19
migrated_date: 2026-05-19
migrated_commit: b869eaf152400dd632e33cc03a008a8e2ceb7361
wip_branch_commit: a73a1e6
auditor_review: REVIEW.md (verdict WARN approve-to-merge=true, ephemeral en worktree pre-cleanup)
gate_output: gate-output.json (verdict READY_FOR_MERGE 6/6, ephemeral en worktree pre-cleanup)

# Origen
origin_learnings: []  # detectado durante auditoría /pm-luana 2026-05-19 (admin-iam-adoption outcome), no learning pre-existente
origin_stories:
  - vitalia/docs/product/stories/vitalia-auth-base-functional/HANDOFF-next-session.md (smoke admin reveló phantom code)
origin_brands: [vitalia]  # detectado en vitalia, pero defecto cross-brand
detected_by: /pm-luana auditoría core packages post 1-semana carve-out (2026-05-19)

# Target
target_package: core/luana-core-platform
target_module: src/luana_core_platform/core/config.py
target_ep: null  # no introduce EP, purga defaults

# Impact assessment
semver_bump: minor                       # nuevos defaults vacíos + ConfigError explícito si missing; cambia comportamiento pero fail-fast no breaking semánticamente
breaking_change: false                   # nicolify .env.dev ya tiene override explícito (verificado), vitalia/comunify/lupulo también — solo fail si brand olvida override
brands_affected_consumers:
  - nicolify                             # ya tiene env vars seteadas en .env.dev (verificar pre-merge)
  - vitalia                              # debe agregar las 4 vars a vitalia/.env.dev + vitalia/.env.dev.template
  - comunify                             # idem
  - lupulo                               # idem
  - saasora                              # futuro bootstrap, template seteará defaults brand-specific
  - inmoflow                             # idem
  - retailly                             # idem
  - fixia                                # idem
  - guestly                              # idem
  - fitflow                              # idem
brands_at_risk_regression: [nicolify]    # único brand con valores hoy = nicolify; verify env vars set in .env.dev antes merge

# Lift plan
lift_estimated_effort: "2-4h (config edit + 4 brand .env.dev updates + arch fitness R3 cross-brand)"
lift_owner: /dev-team builder-backend post Chris APPROVED
arch_test_downstream_required: true       # R3 mandatory — corre arch fitness todos brands shipped
migration_notes_required: true            # documentar en core CHANGELOG + handoff brand PMs para verificar .env
---

# Promotion Proposal — Purge Nicolify-specific defaults de core/config.py

## 1. Patrón a purgar

`core/luana-core-platform/src/luana_core_platform/core/config.py` (Settings class, ~300 líneas) tiene 4 defaults hardcoded con valores nicolify-specific:

| Línea | Variable | Default hardcoded | Brand leak |
|---|---|---|---|
| L48 | `FRONTEND_URL` | `"https://app.nicolify.com"` | nicolify production domain |
| L45 | `COPILOT_TELEGRAM_BOT_USERNAME` | `"nicolify_copilot_bot"` | nicolify Telegram bot username |
| L185 | `QDRANT_COLLECTION` | `"visionarias_knowledge"` | nicolify legacy Qdrant collection name (pre-rename "visionarias" → "nicolify") |
| L240 | `LITELLM_BASE_URL` | `"http://visionarias_litellm:4000/v1"` | nicolify legacy container name |

Estos defaults son herencia pre-multibrand reorg (2026-05-15). Durante el carve-out 1-semana fueron migrados al engine `luana-core-platform` pero los valores brand-specific NO fueron purgados — quedaron como defaults silenciosos.

**Implicación:** cualquier brand consumer del engine (vitalia, comunify, lupulo, saasora futuro, etc.) que olvide override en su `.env.dev` hereda silenciosamente Nicolify defaults. Riesgo concreto:

- Frontend redirects van a `app.nicolify.com` (no `app.vitalialat.com`)
- Copilot Telegram intenta autenticar contra `nicolify_copilot_bot` (token diferente)
- Qdrant queries van a colección `visionarias_knowledge` (data Nicolify) en vez de `vitalia_knowledge` → data mixing tenant-cross-brand (gravísimo HIPAA-lite)
- LiteLLM proxy intenta conectar a container `visionarias_litellm` que no existe en network vitalia

## 2. Por qué cross-brand

Es defecto del engine que afecta cross-brand. **Engine packages deben ser brand-agnostic per ADR-001 multimarca.** Defaults con valores brand-specific violan ese principio fundacional.

| Brand | Aplicabilidad | Razón |
|---|---|---|
| nicolify | ya override implícito | tiene env vars seteadas en `nicolify/.env.dev` (verificar pre-merge) |
| vitalia | falta override explícito | hoy: hereda defaults Nicolify si olvida → data mixing risk HIPAA-lite |
| comunify | falta override | hoy: idem |
| lupulo | falta override | hoy: idem |
| saasora | template requirement | bootstrap futuro debe setearlos como mandatory en `.env.dev.template` |
| inmoflow | idem | idem |
| retailly | idem | idem |
| fixia | idem | idem |
| guestly | idem | idem |
| fitflow | idem | idem |

10/10 brands afectadas. **Justificación cross-brand fortísima** + cement del patrón brand-agnostic para 6 brands pendientes bootstrap.

## 3. Análisis técnico

### Schema actual (con hardcodes nicolify)

```python
# core/luana-core-platform/src/luana_core_platform/core/config.py

class Settings(BaseSettings):
    # L45
    COPILOT_TELEGRAM_BOT_USERNAME: str = "nicolify_copilot_bot"

    # L48
    FRONTEND_URL: str = "https://app.nicolify.com"

    # L185
    QDRANT_COLLECTION: str = "visionarias_knowledge"
    QDRANT_COLLECTION_HYBRID: str = "visionarias_hybrid"   # mismo defect, agregar a fix

    # L240
    LITELLM_BASE_URL: str = "http://visionarias_litellm:4000/v1"
```

### Schema propuesto (brand-agnostic, fail-fast)

```python
# core/luana-core-platform/src/luana_core_platform/core/config.py

class Settings(BaseSettings):
    # Brand-specific config — brand MUST override en {brand}/.env.dev / .env.prod
    # Engine no asume brand. Si brand olvida override → ConfigError explícito en startup.
    COPILOT_TELEGRAM_BOT_USERNAME: str = ""           # required if copilot Telegram enabled
    FRONTEND_URL: str = ""                            # required for OAuth redirects, email links
    QDRANT_COLLECTION: str = ""                       # required for RAG features
    QDRANT_COLLECTION_HYBRID: str = ""                # required for hybrid search

    # LITELLM proxy URL: convencion canonical brand-agnostic
    # default localhost:4000 dev-local; per-brand override en docker compose service
    LITELLM_BASE_URL: str = "http://localhost:4000/v1"

    # Optional: agregar validator post-init para flagear defaults vacíos críticos
    @model_validator(mode='after')
    def validate_brand_specific_config(self):
        # Solo enforce si feature relevante está enabled
        if not self.QDRANT_COLLECTION and self.ENABLE_RAG:
            raise ConfigError("QDRANT_COLLECTION required when ENABLE_RAG=True. Set en {brand}/.env.dev")
        if not self.FRONTEND_URL and self.ENABLE_EMAIL_NOTIFICATIONS:
            raise ConfigError("FRONTEND_URL required when ENABLE_EMAIL_NOTIFICATIONS=True. Set en {brand}/.env.dev")
        return self
```

**Alternativa más simple (sin validators):** defaults vacíos `""` + brand `.env.dev` mandatory override. Brand consumer queries: si `settings.FRONTEND_URL == ""` → raise explícito en código que lo necesita (Qdrant client init, etc.). Más targeted que validators globales.

Recomendación implementación: defaults `""` + raise donde se consume (no validators globales — menos sorpresa).

### Updates brand `.env.dev.template` + `.env.dev` requeridos

Cada brand consumer debe agregar a su `.env.dev.template`:

```bash
# Brand-specific config (engine consume desde aquí, requiere override per brand)
FRONTEND_URL=https://app.{brand}lat.com           # production frontend domain
COPILOT_TELEGRAM_BOT_USERNAME={brand}_copilot_bot # Telegram bot username (registrar Bot por brand)
QDRANT_COLLECTION={brand}_knowledge               # Qdrant collection per brand (data isolation)
QDRANT_COLLECTION_HYBRID={brand}_hybrid           # Qdrant collection hybrid per brand
LITELLM_BASE_URL=http://luana-{env}-{brand}_litellm-1:4000/v1   # LiteLLM proxy container per brand
```

Mismo `.env.dev` real (con valores reales gitignored):

```bash
# nicolify/.env.dev
FRONTEND_URL=https://app.nicolify.com
COPILOT_TELEGRAM_BOT_USERNAME=nicolify_copilot_bot
QDRANT_COLLECTION=visionarias_knowledge          # mantener legacy name para no romper data existente
QDRANT_COLLECTION_HYBRID=visionarias_hybrid
LITELLM_BASE_URL=http://visionarias_litellm:4000/v1

# vitalia/.env.dev
FRONTEND_URL=https://dev-app.vitalialat.com
COPILOT_TELEGRAM_BOT_USERNAME=vitalia_copilot_bot
QDRANT_COLLECTION=vitalia_knowledge
QDRANT_COLLECTION_HYBRID=vitalia_hybrid
LITELLM_BASE_URL=http://luana-dev-vitalia_litellm-1:4000/v1   # cuando litellm-proxy se agregue
```

### Migration path per consumer brand

1. **Pre-merge engine fix:** auditar `nicolify/.env.dev` actual — confirmar que ya tiene las 4 vars seteadas explícitamente (presumido pero verify)
2. **Engine modify:** /dev-team aplica edit a `core/luana-core-platform/src/luana_core_platform/core/config.py` cambiando defaults a `""`
3. **Brand .env.dev.template update:** /dev-team agrega bloque "brand-specific config" a `{brand}/.env.dev.template` x4 brands shipped (nicolify + vitalia + comunify + lupulo)
4. **Brand .env.dev update:** /dev-team coordina con cada `/pm-{brand}` para agregar override en `.env.dev` real (gitignored — Chris ejecuta localmente)
5. **R3 downstream regression:** `make arch-test` (engine + 4 brands shipped) + smoke test brand-by-brand para detectar consumers que rompieron por defaults vacíos
6. **Future bootstrap brands:** template `_pm-brand-template/.env.dev.template` ya incluye el bloque desde el inicio (PM template update)

### Risk assessment

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Brand consumer rompe en startup porque olvida setear env var post-merge | Media | Failfast con error explícito mejor que silent data leak. Documented en CHANGELOG + handoff PMs |
| Nicolify NO tiene `.env.dev` con override explícito (asumido pero unverified) | Media | **Verificar pre-merge.** Si nicolify no tenía override y dependía del default → agregar override + verify smoke pass |
| Tests engine pueden tener fixtures que asumen defaults nicolify | Baja | grep `visionarias_knowledge` + `nicolify_copilot_bot` + `app.nicolify.com` en `core/luana-core-*/tests/` — corregir fixtures |
| Producción brand X con env var no seteada → service down | Alta (caso prod) | Failfast en startup = degraded health check = autoscaling no marca healthy = rolling deploy aborta. Esto es FEATURE no bug (mejor que silent contamination) |
| Brand consumers in-flight (vitalia auth-base, comunify wip recovery) tienen tests que rompen | Baja | Tests in-flight aún no tocan estos paths críticos — verify pre-merge cuáles dependen |

## 4. Lift plan

### Pre-lift checklist

- [ ] Verify nicolify `.env.dev` tiene las 4 vars seteadas explícitamente (grep)
- [ ] Verify vitalia `.env.dev` actual tiene QDRANT_COLLECTION distinto a `visionarias_knowledge` (else data leak existente)
- [ ] Verify comunify `.env.dev` idem
- [ ] Verify lupulo `.env.dev` idem (placeholder pero seguro)
- [ ] Search tests engine para fixtures hardcodeadas: `grep -rn "visionarias_knowledge\|nicolify_copilot_bot\|app.nicolify.com" core/luana-core-*/tests/`
- [ ] Search tests brands idem cross-brand

### Lift execution (orden)

1. **Step 1 (audit env vars actuales):** /dev-team verifica que cada brand `.env.dev` ya tiene las 4 vars seteadas explícitamente. Si NO → agregar primero antes del engine fix.
2. **Step 2 (engine fix):** /dev-team edita `core/luana-core-platform/src/luana_core_platform/core/config.py` cambiando 4 defaults a `""` (+ `LITELLM_BASE_URL` a `localhost:4000` como dev default genérico)
3. **Step 3 (engine docs + semver):** bump `core/luana-core-platform/pyproject.toml::version` minor (e.g., 0.2.0 → 0.3.0) + agregar entry CHANGELOG.md
4. **Step 4 (brand templates):** /dev-team actualiza `{brand}/.env.dev.template` x4 brands con bloque "brand-specific config" (mismo schema verbatim)
5. **Step 5 (R3 arch test downstream):** `make arch-test` engine + 4 brands shipped, smoke test admin/auth/copilot per brand
6. **Step 6 (rollback path):** revert engine commit + revert brand template commits (env.dev reales no tocados — Chris)

### Post-lift (brands consumer opt-in)

- **Nicolify (legacy default brand):** debería NO requerir cambios (ya tiene `.env.dev` con valores explícitos). Verify smoke pass.
- **Vitalia (origen detección):** `.env.dev` debe tener overrides ya — verify, agregar si missing.
- **Comunify + Lupulo:** mismo flow vitalia.
- **6 brands futuras bootstrap:** template `_pm-brand-template/.env.dev.template` actualizado con bloque mandatory — bootstrap pattern correcto desde día 1.

## 5. Decisión

**Recomendación /pm-luana:** APPROVED

**Razón:**
- Patrón violatorio del principio brand-agnostic (ADR-001 multimarca)
- 10/10 brands afectadas (4 shipped + 6 pendientes bootstrap)
- Riesgo data leak silencioso (vitalia HIPAA-lite escribiendo a Qdrant collection Nicolify es worst-case scenario)
- Costo lift ≤ 4h (config edit + 4 template updates + arch fitness R3)
- Failfast > silent contamination (engineering principle alignment con directiva Chris "esto es ingeniería")
- Cement del patrón "brand defaults viven en {brand}/.env, engine vacío" antes del bootstrap de 6 brands futuras

**Ratificación Chris:** _pending hasta state=accepted_

## 6. Bitácora

- 2026-05-19: opened by /pm-luana durante auditoría exhaustiva core packages post 1-semana carve-out. Caso detectado: HANDOFF vitalia-auth-base-functional → smoke admin Streamlit reveló phantom tables + audit core/config.py reveló 4 hardcodes Nicolify. State: proposed.
- 2026-05-19 (misma sesión post commit 03065cf): Chris ratifica APPROVED — "Ratifico el documento, usa sub agentes para el desarrollo, auditoría merge y cierre, todo aquí, de forma autonoma a menos que sea algo que impacte al negocio". State: proposed → accepted.
- 2026-05-19 (pre-lift verification cross-worktree): detectado que NINGÚN brand `.env.dev` (nicolify/vitalia/comunify) tiene las 4 vars seteadas — todos dependían silenciosamente de defaults engine. Risk escalated to Chris → Chris ratificó Opción A (pre-set .env.dev de cada brand antes del engine purge). Ejecutado pre-set:
  - `~/Proyectos/luana-nicolify/nicolify/.env.dev`: agregadas 4 vars con valores legacy nicolify (preserve current behavior — `app.nicolify.com`, `nicolify_copilot_bot`, `visionarias_knowledge`, `visionarias_hybrid`, `http://visionarias_litellm:4000/v1`)
  - `~/Proyectos/luana-vitalia/vitalia/.env.dev`: agregadas 4 vars con valores vitalia (`dev-app.vitalialat.com`, `vitalia_copilot_bot`, `vitalia_knowledge`, `vitalia_hybrid`, `http://localhost:4000/v1`)
  - `~/Proyectos/luana-comunify/comunify/.env.dev`: agregadas 4 vars con valores comunify (`dev-app.comunifyagents.com`, `comunify_copilot_bot`, `comunify_knowledge`, `comunify_hybrid`, `http://localhost:4000/v1`)
  - lupulo: SKIP (no worktree activo — al bootstrap, `_pm-brand-template/.env.dev.template` ya tendrá el bloque actualizado)
- 2026-05-19 (lift en progreso): worktree `wip/core-purge-nicolify-defaults` creado, engine purge ejecutado + 4 brand `.env.dev.template` actualizados + R3 downstream regression PASS:
  - gate-runner gates 1-6 PASS (engine-platform 220 tests + ruff + arch + downstream-copilot 1640 tests + downstream-sales-agent ADVISORY_PASS unrelated infra + downstream-llm 67 tests). Verdict: READY_FOR_MERGE.
  - auditor-backend verdict: WARN approve-to-merge=true conditional on 3 commit-time requirements (SCOPE_GATE_SKIP=1 doc-justified per atomicity, Tests-audited section in commit body, R3 brand backend gap mitigated by zero legacy hardcoded asserts grep). 2 INFO non-blocking: bitácora typo fixed; residual nicolify hardcodes in `core/luana-core-sales-agent/.../payment/providers.py` + `orchestrator/graph.py` → próximo proposal candidate.
- 2026-05-19 (lift cerrado): wip commit `a73a1e6` (worktree `wip/core-purge-nicolify-defaults`) pushed con SCOPE_GATE_SKIP=1 justificado. Squash-merged a `main` commit `b869eaf152400dd632e33cc03a008a8e2ceb7361` pushed origin/main. Pre-commit Section 11 detectó `.git/SQUASH_MSG` y permitió commit a main automáticamente. State: accepted → migrated.
- 2026-05-19 (post-merge): worktree `wip/core-purge-nicolify-defaults` y branch `wip/core-purge-nicolify-defaults` cleanup pendiente (próximo paso /pm-luana session housekeeping). REVIEW.md + gate-output.json eran artifacts efímeros del worktree, se pierden al cleanup (referencia inmutable: commit SHA + CHANGELOG.md core-platform v0.3.0 entry + esta bitácora).

## 7. Cross-references

- Parent outcome: `docs/product/outcomes/admin-iam-adoption-platform.md` (D3 decision)
- Target file: `core/luana-core-platform/src/luana_core_platform/core/config.py` (líneas 45, 48, 185, 240)
- Caso origen smoke: `vitalia/docs/product/stories/vitalia-auth-base-functional/HANDOFF-next-session.md`
- Architecture base: `docs/architecture/luana-platform/01-core-audit.md` + ADR-001 (engine brand-agnostic principle)
- Related rule: `.claude/rules/anti-default-flip-audit.md` (defaults engine pattern análogo)
- Related rule: `.claude/rules/auditor-downstream-regression.md` § engine edit detection (R3 mandatorio)
- Process: `docs/promotion-protocol/README.md`

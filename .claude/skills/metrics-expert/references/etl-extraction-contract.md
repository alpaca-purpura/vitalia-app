---
globs: "{core/luana-core-analytics-engine/**,{nicolify,vitalia,comunify,lupulo}/backend/src/modules/*/analytics/**}/*.py"
description: ETL extraction contract workflow — read/update/verify cycle (multibrand)
---

# ETL Extraction Contract

**Non-negotiable** for analytics ETL changes. Contract = SSoT: what extract, from where, when, how, where lands.

## 2 files, 2 roles

| File | Answers | Runtime? |
|---|---|---|
| `core/luana-core-analytics-engine/src/luana_core_analytics_engine/domain/metric_catalog.py` | "Metric `X` means? ADDITIVE/WEIGHTED_AVG/NON_AGG/SNAPSHOT/DERIVED? Unit, display, interpretation, benchmarks?" | **Yes** — `MetricResolver`, `aggregations.py`, stage services, `/metrics/catalog` |
| `core/luana-core-analytics-engine/src/luana_core_analytics_engine/domain/extraction_contract.py` | "Which provider extracts `X`? From which endpoint? When? Credentials? Channel slug? Issues?" | **No** — docs + test enforcement |

Catalog = semantics. Contract = extraction reality. Arch test `tests/ (suite engine — el arch test dedicado de drift fue retirado en la reorg)` keeps aligned: every catalog metric w/ `providers` tuple listing `X` MUST appear in `X`'s `ChannelOutput` OR allowlisted in `KNOWN_CATALOG_CONTRACT_GAPS` w/ audit ref.

## When READING (ETL questions)

Questions like "what ETL extracts for `<provider>`?", "where `<metric>` comes from?", "when `<provider>` runs?", "why `<channel>` empty?":

**Step 1 (mandatory):** Read `core/luana-core-analytics-engine/docs/extraction-contract.md` first. Auto-gen MD.
**Step 2 (si falta):** `core/luana-core-analytics-engine/src/luana_core_analytics_engine/domain/extraction_contract.py` — `known_issues`, `last_verified`, `notes`, `required_credentials`.
**Step 3 (si step 2 insuficiente):** Actual provider source. Si contract wrong/incomplete, **MUST update before finishing**.

## When UPDATING

Trigger: any change to (engine paths require `/pm-luana` promotion gate; brand opt-ins are brand-scoped):

**Engine (cross-brand — `core/luana-core-analytics-engine/src/luana_core_analytics_engine/`):**
- `.../infrastructure/providers/*.py`
- `.../infrastructure/etl/pipeline.py`
- `.../infrastructure/etl/period_pipeline.py`
- `.../infrastructure/etl/aggregations.py`
- `.../application/services/etl_service.py`
- `.../workers/scheduler.py`
- `.../workers/tasks.py`
- `.../domain/metric_catalog.py`
- `.../workers/settings.py`

**Brand opt-in (`{brand}/backend/src/modules/{brand}/analytics/`):**
- `.../providers/*.py` (brand-specific provider adapters registered via Extension SDK)
- `.../extensions.py` (enabled_metrics, channel_groups opt-in)

### 5-step workflow

1. **Implement** en provider/pipeline/catalog.
2. **Update contract** en `core/luana-core-analytics-engine/src/luana_core_analytics_engine/domain/extraction_contract.py`:
   - Nueva metric → `MetricMapping` en right `ChannelOutput`
   - Nuevo channel → `ChannelOutput` en contract entry
   - Nuevo provider → `_<name>_contract()` factory + register `EXTRACTION_CONTRACTS`
   - Nuevo endpoint → `APIEndpoint` en `api_endpoints`
   - Bug → `known_issues`
   - Bump `last_verified` today.
3. **Si catalog cambió**, re-check metric w/ `providers=("X",)` listed en X's contract.
4. **Regen MD** (mandatory, FINAL):
   ```bash
   # from workspace root (WS = git rev-parse --show-toplevel)
   make extraction-contract
   # or: ${WS}/.venv/bin/python core/luana-core-analytics-engine/scripts/generate_extraction_contract_doc.py
   ```
5. **Arch test** (engine + every brand consumer):
   ```bash
   WS=$(git rev-parse --show-toplevel)
   cd ${WS}/core/luana-core-analytics-engine && ${WS}/.venv/bin/pytest tests/ (suite engine — el arch test dedicado de drift fue retirado en la reorg) -x -q
   # also per brand:
   for B in nicolify vitalia comunify lupulo; do
     cd ${WS}/${B}/backend && ${WS}/.venv/bin/pytest tests/ (suite engine — el arch test dedicado de drift fue retirado en la reorg) -x -q 2>/dev/null || true
   done
   ```

### Commit

Single commit: provider + contract + regenerated MD + tests. Reviewers (future Claude incluido) leen diff entienden.

## 5-step applies EVEN si:
- "Solo" nueva metric en channel existente
- "Solo" rename channel slug
- "Solo" fix parsing bug que cambia API field→metric
- "Solo" `# noqa` probando metric no emitted
- "Solo" cambio cron worker

Every change invalidates piece. Test will fail. Update.

## Best practices extracción

### Reliability
1. Wrap sub-extractors en `_safe_extract` → partial failures en `extraction_runs.sub_extractor_failures`, no sink run.
2. Credential errors → `ConnectionRevokedException` (`RefreshError`, `TransportError`, `invalid_grant`) → worker stops retrying.
3. Nunca swallow exceptions silently. `logger.exception` + Sentry tag `provider`+`sub_extractor`.
4. Commit `ExtractionRun` row ANTES try block. `pipeline.py` + `period_pipeline.py` ya. Sin commit, later `db.rollback()` wipe row → "ExtractionRun not found" oculta real failure.
5. Every query filter by `tenant_id`. Hasta `crm_internal`.
6. Every upsert idempotent. `ON CONFLICT (tenant_id, provider, channel_slug, metric_name, metric_date) DO UPDATE` para `official_metrics`, equivalent natural key para `period_metrics`, `metric_aggregations`.

### Correctness
7. Period-aggregated rows NO en `official_metrics`. Meta `/insights` @ `account/campaign/ad` MUST `time_increment=1`. Arch test `test_meta_provider_invariants.py` enforces. Si genuine period aggregate → `extract_period_metrics` + `period_metrics` table + add to `ALLOWED_PERIOD_FUNCTIONS`.
8. Currency desde data source, nunca hardcoded. Ver `.claude/rules/currency-handling.md`, `master-data.md`. Provider monetary MUST resolve source currency → `ExtractedMetric.currency`.
9. Todos datetimes UTC en DB. `utc_now()` de `shared/domain/datetime_utils.py`. Per-tenant timezones en `TenantLocale`.
10. Channel slugs convention: email → `email-{stage}` (`email-capture`, `email-nurture`). Meta → `ig-organic`, `fb-organic`, `meta-ads`, `meta-pixel`.

### Observability
11. Log every sub-extractor start/complete/fail con `extractor_name`, `provider` tags.
12. Populate `cost_type` via `get_cost_type(channel_slug, stage)` — dashboard groups paid/owned/earned.
13. `extra` JSONB para breakdowns/metadata no fit `value` (top queries, demo, video retention). Document schema en contract entry `notes`.

### Multi-stage
14. Multi-stage (Shopify, MailerLite) itera `PROVIDER_STAGES[name]` en `etl_service.run_extraction`. Cada stage = own channel slugs. Known issue: stage A succeeds + B fails → A committed pero run reports B status. Document en `known_issues` hasta fix.

### Pass-through
15. Algunos (Manychat) pass-through by design. `extract_metrics` returns empty — data via webhooks. Mark `ProviderStatus.PASS_THROUGH`. NO bug — scheduler still sees para cache invalidation.

## Anti-patterns

- ❌ Add provider to `PROVIDER_REGISTRY` sin contract → `test_every_registered_provider_has_contract` fails.
- ❌ Edit `provider_name()` sin update contract key → `test_contract_provider_name_matches_class` fails.
- ❌ Add metric con `providers=("foo",)` cuando foo's contract no emits → `test_catalog_metrics_appear_in_contract` fails.
- ❌ Edit provider + skip `make extraction-contract` → `test_generated_markdown_is_up_to_date` fails.
- ❌ `# type: ignore`/`# noqa` silencing arch test instead of fixing.
- ❌ Bypass "because small change" → no small ETL changes.

## Quick commands

```bash
WS=$(git rev-parse --show-toplevel)

# Read
cat core/luana-core-analytics-engine/docs/extraction-contract.md | less

# Edit (engine SSoT)
$EDITOR ${WS}/core/luana-core-analytics-engine/src/luana_core_analytics_engine/domain/extraction_contract.py

# Regen
make extraction-contract   # from workspace root

# Verify (engine + brand consumers)
cd ${WS}/core/luana-core-analytics-engine && ${WS}/.venv/bin/pytest tests/ (suite engine — el arch test dedicado de drift fue retirado en la reorg) -x -q

# Sample dev query per brand (multibrand)
# Replace {BRAND} and {TENANT_ID} as needed:
docker exec luana-dev-{BRAND}_postgres_dev-1 psql -U postgres -d luana_dev --pset=pager=off \
  -c "SELECT provider, channel_slug, metric_name, COUNT(*) c, MIN(metric_date) min_d, MAX(metric_date) max_d \
      FROM official_metrics \
      WHERE tenant_id='{TENANT_ID}' \
      GROUP BY provider, channel_slug, metric_name ORDER BY provider, channel_slug;"

# LEGACY — pre-reorg (historical reference only, do NOT use):
# ssh root@161.132.41.191 'docker exec visionarias_postgres psql ...'
```

## Anchor

Future Claude: ETL question → **first action** read `core/luana-core-analytics-engine/docs/extraction-contract.md`. Before writing en `core/luana-core-analytics-engine/src/luana_core_analytics_engine/` (or brand opt-in `{brand}/backend/src/modules/{brand}/analytics/`) → **first action** read this + contract. After modifying → **last action** `make extraction-contract && pytest tests/ (suite engine — el arch test dedicado de drift fue retirado en la reorg)`. Sin excepciones.

---

## Ex always-on rule body (evicted W1-Phase2 2026-06-09 — era `.claude/rules/etl-extraction-contract.md`)

Analytics es **ENGINE + BRAND-CONFIG** (ver CLAUDE.md tabla mapping):

| Surface | Path | Owner |
|---|---|---|
| Engine ETL contract + catalog | `core/luana-core-analytics-engine/src/luana_core_analytics_engine/domain/{extraction_contract,metric_catalog}.py` | `/pm-luana` |
| Brand opt-in (enabled_metrics, channel_groups) | `{brand}/config/brand.yaml` + `{brand}/backend/src/modules/{brand}/analytics/extensions.py` | `/pm-{brand}` |
| Auto-gen MD | `core/luana-core-analytics-engine/docs/extraction-contract.md` (NUNCA edit manual) | generator |

**Antes ETL question:** leer `core/luana-core-analytics-engine/docs/extraction-contract.md` PRIMERO.

**Después modificar** providers/pipeline/etl_service/scheduler/workers/catalog en engine: 5-step → implement → update contract → re-check catalog → `make extraction-contract` → arch test (corre en engine + cada brand consumer).

**No-skip:** todo cambio analytics dispara los 5 pasos. Sin excepciones.

### Multibrand awareness (post reorg 2026-05-15)

- Engine cambios → requieren `/pm-luana` promotion gate + revalidación en cada brand consumer activa.
- Brand-specific provider adapters viven en `{brand}/backend/src/modules/{brand}/analytics/providers/` (registrados via Extension SDK).

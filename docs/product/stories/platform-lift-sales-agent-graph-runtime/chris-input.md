---
story_id: platform-lift-sales-agent-graph-runtime
created_at: 2026-06-22T00:00:00-05:00
last_modified: 2026-06-22T00:00:00-05:00
notes_count: 0
refs_count: 4
conversation_count: 1
---

# chris-input.md · platform-lift-sales-agent-graph-runtime

> **Qué es este archivo:** acá Chris escribe notas + referencias + Claude responde con verdicts. Cocina de la story (la conversación) — separada del spec/design/arch.
>
> Doc canónico: `docs/process/chris-input-protocol.md`.

## 💭 Notas

### 2026-06-22
Sin notas adicionales todavía · Chris escribe aquí.

## 📎 Referencias

- **📄 doc** · `docs/promotion-protocol/proposals/2026-06-22-sales-agent-multibrand-graph-runtime.md` (accepted · ⚠️ vive en `wip/vitalia`, no sincronizado a main — leído vía `git show 9c11581f:...`)
- **📖 story-ref** · `vitalia-fase2-adrian-canal-inbound` (wip/vitalia · OLA-1 construida · su G live-verify 2026-06-22 surfaceó ESC-4/5/6)
- **📄 doc** · `core/luana-core-sales-agent/.../infrastructure/{prompts/base.py, models/prompt_version_model.py, models/message_model.py}` + `core/luana-core-platform/.../infrastructure/models/crm.py` (los 3 muros Phase 1, verificados in-tree)
- **📚 learning-ref** · memoria `engine-edits-brand-worktree-invisible-to-venv` (2026-06-16 · PYTHONPATH override obligatorio en worktree core) + `dod-live-verify`

## 💬 Conversación

> Append-only · turn-by-turn cronológico. Verdict labels: ✓ APLICADO · ⚠️ DUDA · ❌ REFUTADO · 💡 PROPONE.

### 2026-06-22 · 👤 Chris · input de creación (lift engine ya ratificado · Phase 1 primero)
> /architect platform — engine lift "sales_agent multibrand-graph-runtime". Worktree core efímero (wip/core-sales-agent-multibrand) para EJECUTAR un lift ya ratificado (proposal accepted). PHASE 1 = ESC-4/5/6 (RUNTIME, testeable) primero; PHASE 2 = ESC-1/2/3 (features) después. Constraints duras: PYTHONPATH override para validar in-place · arch test por ESC + downstream regression ×4 · bar runtime real (grafo corriendo en vitalia, lo verifica Chris post-merge) · CERO tocar marca acá (solo core/) · migración ESC-6 idempotente + notes. autonomous_mode: NO (engine + agentic = stake-asimétrico).

### 2026-06-22 · 🤖 claude · `/architect` (refiner WT5, technical-story) · ✓ APLICADO + 💡 PROPONE
**Package Phase 1 cerrado** (`refined → ready`): `03-arch.md` + `04-validators.yaml` + `05-guidelines.md` + `06-tickets.yaml` (3 tickets) + `dispatch-plan.md` + `migration_notes.md`. Los 3 muros **verificados in-tree** (no confié en el proposal a ciegas): ESC-4 colisión real reproducida (engine `MessageModel`/`messages` + vitalia `MessageModel`/`vitalia_messages` sobre el mismo `Base`) · ESC-5 confirmado (`Path.cwd()` + path monolítico; el engine **ships** sus templates) · ESC-6 confirmado (`PROMPT_SOURCE=HYBRID` default → rama DB referencia `PromptVersion.tenant_id` → AttributeError).

**💡 2 refinamientos de approach (dentro del contrato ratificado · pedís veto antes de /dev-team):**
1. **ESC-4 es BIDIRECCIONAL.** El proposal citó solo `crm.py:209` (`LeadModel.messages → "MessageModel"`). Pero `message_model.py:46` (`MessageModel.lead → "LeadModel"`) **también** es string-pelado y vitalia homonyma `LeadModel` → la colisión persiste del otro lado. **Propongo qualificar ambos** (es el "verificar consumers" del proposal). Sin esto el fix queda a medias.
2. **ESC-5: default engine-package-relative, NO `modules/{brand}/...`.** El proposal sugirió path por marca. Pero el engine **ya ships** sus templates → propongo default `Path(__file__).parent/"templates"` (cwd-independiente, cero duplicación por marca) + param override back-compat. Las variantes por tenant siguen viniendo de DB (`tenant_id`). Estrictamente mejor que copiar templates por marca.

**Forzado por arquitectura (no es decisión, lo informo):** ESC-6 = **modelo acá (columna `tenant_id`) + migración brand-authored**. No hay alembic en `core/` (las 4 marcas dueñas de sus migraciones); + tu constraint "cero marca acá". `migration_notes.md` trae el DDL idempotente exacto (CREATE TABLE IF NOT EXISTS + ADD COLUMN IF NOT EXISTS, porque `prompt_versions` no existe en el alembic de ninguna marca todavía) para que cada brand lo aplique en SU worktree al adoptar. El **efecto runtime** (grafo corriendo) se ejerce en vitalia post merge+sync — tu bar, lo verificás vos.

**Colateral flaggeado (fuera de scope):** copilot tiene el MISMO bug-class de ESC-5 en `core/luana-core-platform/.../prompts/base.py:23` — no lo toco (proposal es sales-agent), candidato a `/harness-issue` cuando se cablee copilot en una marca.

autonomous_mode: false → **no encadeno a /dev-team**. Revisás el package (sobre todo los 2 PROPONE) y arrancás vos `/dev-team platform: T-ESC4`.

### 2026-06-22 · 👤 Chris · "profundizá aún más, dejá todo bien establecido al dev-team"
> Duplicá tu esfuerzo y revisá bien todo antes de que construyamos algo que no funcione o tenga vicios. Vos como architect sos el genio; el dev-team solo sigue tus órdenes. Alta cohesión / bajo acoplamiento, clean architecture + hexagonal → mantenible y escalable.

### 2026-06-22 · 🤖 claude · `/architect` (deep-dive: spike empírico RED→GREEN) · ✓ APLICADO + ❌ REFUTÉ mi propio PR-1
**Probé empíricamente los 3 fixes en este worktree (spike RED→GREEN + no-regression), no diseñé en papel.** Hallazgos:

- **❌ REFUTÉ mi PR-1 (era un vicio):** dije "ESC-4 bidireccional, qualificar ambos lados". **FALSO, probado.** vitalia define `MessageModel` homónimo pero **NO `LeadModel`** (solo `LeadActivityModel`/`LeadStageTransitionModel`). Entonces `"LeadModel"` es único → el lado `message_model.py:46` **NO se toca**. ESC-4 = **una sola línea en crm.py**. Si te hubiera dado el PR-1 original, el dev-team habría tocado un archivo de más + agregado acoplamiento inverso innecesario. Justo lo que pediste cazar.
- **✓ ESC-4 probado:** RED reproduce el error live VERBATIM (`Multiple classes found for path "MessageModel"`); el fix de 1 línea → `configure_mappers()` limpio con el set de modelos REAL completo (platform+sales-agent+scheduling+iam+offer-studio + homónimo sintético). Sin ambigüedad residual.
- **✓ ESC-5 probado:** RED `TemplateNotFound` desde cwd ajeno → fix engine-relative → resuelve. **✓ ESC-6 probado:** RED `AttributeError` → columna → queries construyen.
- **✓ No-regression PROBADO (decisivo):** corrí un subset DB en aislamiento determinístico, baseline vs con-fix = **idéntico** (cero regresión). La suite completa daba números distintos pero es **ruido de estado global** (`configure_mappers` es global + el conftest registra un `AppointmentModel` sintético que contamina el registry según el orden de imports) — NO regresión real. **Conclusión de diseño:** la suite completa vía PYTHONPATH-hack NO es gate confiable en el worktree; el gate real = arch tests por ESC (el de ESC-4 en **subproceso** aislado, código exacto en `verified-arch-tests.md`) + suites en canónico (ci-parity+Postgres) post-merge.
- **💡 Latent finding (no lo toco, lo documento):** `LeadModel.appointments` (crm.py:214) tiene la MISMA ambigüedad latente; **seguro en prod hoy** (vitalia no homonyma AppointmentModel — probado: configure_mappers limpio con el AppointmentModel real único). Abordar en Story 8 lift. NO lo toco (es stub-targeted, romperlo sin el lift completo sería peor).
- **💡 Clean-arch:** ESC-4 qualified = cohesión↑ sin acoplamiento de import (late-bound); NO expando el acople kernel→sales-agent (solo desambiguo). ESC-5 = templates co-locados (cohesión↑) cwd-independiente (acoplamiento↓). ESC-6 = `tenant_id` SIN FK (decouple del schema de platform, hexagonal). Documentado en 03-arch § Clean architecture.
- **3 tech-debts colaterales → /harness-issue** (no bloquean, no los toco): test stale de colección monolítico · conftest sintético AppointmentModel · copilot mismo bug-class ESC-5.

**Spike revertido** → repo en RED limpio para el TDD del dev-team. Package actualizado: 03-arch (diffs exactos + spike proof + clean-arch + latent + realidad-del-entorno), 04-validators (arch tests = gate autoritativo · suites canónico/advisory), 06-tickets (ESC-4 one-sided), 05-guidelines, + **verified-arch-tests.md** (código de los 3 tests, copy-paste, ESC-4 subproceso). autonomous_mode sigue false.

### 2026-06-22 · 👤 Chris · "agregá T-DEBT1, commiteá el package y arrancá el dev-team"

### 2026-06-22 · 🤖 claude · `/architect` · ✓ APLICADO
**T-DEBT1 agregado** (4º ticket): fix import stale `tests.modules.sales_agent.orchestrator` → `tests.orchestrator` (1 línea, L27 de test_chat_orchestrator_snapshot.py). Verifiqué que el import corregido resuelve + el helper expone los símbolos. test-only, production_code:false, builder-agentic/workhorse, independiente. Nuevo validator `suite_collects` (HARD) — hoy RED (ModuleNotFoundError), T-DEBT1 lo pone verde → habilita el gate `sales_agent_suite_canonical` a colectar limpio (sin `--ignore`). #2 (conftest AppointmentModel = stub Story-8 deliberado) y #3 (copilot) quedan flag. Package: 4 tickets, total_tickets:4, scenario_coverage + dispatch + checkpoint actualizados. **Commiteo el package + arranco `/dev-team platform: T-DEBT1` (orden: T-DEBT1 → T-ESC4 → T-ESC5 → T-ESC6).** autonomous_mode:false (Chris ratifica entre developed→auditor).

### 2026-06-22 · 🤖 claude · `/dev-team` (build Phase 1 · builder-agentic) · ✓ APLICADO
`developing → developed`. Commit **5120881a** (FF push wip/core-sales-agent-multibrand). 12 archivos: 3 src + 4 arch tests (incl __init__) + 1 fix import + 4 result md. **4/4 tickets GREEN bajo TDD (RED→GREEN cada uno):**

| Ticket | RED | GREEN (re-corrido por orchestrator) |
|---|---|---|
| T-ESC4 | `Multiple classes found for path "MessageModel"` | 1 passed |
| T-ESC5 | `TemplateNotFound` cwd ajeno | 3 passed |
| T-ESC6 | `AttributeError no attribute tenant_id` | 2 passed |
| T-DEBT1 | `ModuleNotFoundError tests.modules` (colección bloqueada) | colecta 476 tests, 0 errores |

**Verificación independiente del orchestrator (no confié en el stdout del builder):**
- Los 3 diffs committeados = EXACTAMENTE los proven del architect (ESC-4 una línea en crm.py; ESC-5 engine-relative; ESC-6 columna). ✓
- ESC-4 **UNILATERAL confirmado**: `message_model.py` = 0 líneas cambiadas. ✓
- Re-corrí los 4 validators yo mismo → 1/3/2 passed + collect 476. ✓
- **Platform suite verde (exit=0)** = ESC-4 downstream sin regresión. ✓
- Superficies prohibidas intactas: cero marca, sin alembic, sin application/, sin conftest, sin appointments/tenant, sin copilot. ✓

**3 flags fuera de scope (no tocados):** LeadModel.appointments latente (Story 8) · copilot mismo bug-class (/harness-issue) · 4 archivos con ruff-format drift pre-existente en eval_simulator/quality_eval (ajenos al lift).

**autonomous_mode false → PAUSA en developed (no auto-handoff).** Build-claim liberado. El bar runtime real (grafo en vitalia) es post merge+sync. **Recomiendo: Chris ratifica el lift → /auditor (auditor-agentic, engine stake-asimétrico) → /pm-luana migrate (merge main + sync vitalia) → ejercés el grafo live.** Esperando tu go.

### 2026-06-22 · 👤 Chris · ratifica Phase 1 + review arquitectura multimarca + autoriza chain a done
> Ratifico Phase 1. Revisá cohesión/acoplamiento/clean/hexagonal para multimarca (cada marca sus tools sin estorbar; brand-first, no core-first). Andá a auditor hasta el done, hacés el merge y propagás a todas las marcas, luego dame el prompt para terminar el trabajo en vitalia. Al final eliminá este worktree temporal asegurando que todo esté bien.

### 2026-06-22 · 🤖 claude · `/architect` review arquitectura + `/auditor` · ✓ APLICADO
**Review multimarca:** la arquitectura que Chris quiere YA EXISTE y es limpia — **EP-3 Extension SDK** (`sales_agent_tool_register`/`get_sales_agent_tool`, vitalia ya registra tools) + **SchedulerProvider** (`Protocol`+`runtime_checkable`, docstring textbook "resolver never branches on provider_id, new providers add an entry"). **El problema es CABLEADO, no diseño:** el grafo despacha de un `TOOL_REGISTRY` estático (tools.py:107) + `nodes.py:402` sin consultar EP-3 → los tools que vitalia registra no se despachan. Eso es **Phase 2 (ESC-2/3)**. Después de Phase 2: tool de marca = worktree vitalia + EP-3, **cero core, para siempre**. Phase 2 = última tarea core para tools; se maneja brand-first (cablear tool real en vitalia → chocar muro → promover el cableado). Flag estratégico: engine `messages` vs brand `vitalia_messages` (posible split, decidir en modelo multimarca, no este lift).

**Signoff registrado** (`chris_verify.signoff: SATISFIED`) + `reconciled: true` (zero-drift, build == proven verbatim).

**`/auditor` (auditor-agentic) → APPROVED.** Re-audit independiente 8/8 checks con evidencia ejecutada por el auditor (no confió en el self-report del dev): diffs byte-exact al plan proven · ESC-4 unilateral confirmado (`message_model.py` 0 cambios, `LeadModel` único cross core+4 marcas) · superficies prohibidas limpias · **prueba de no-regresión propia del auditor** (revirtió los 3 prod files: pre-lift 24F/40P vs post-lift 22F/42P → +2 passes, 0 fallas nuevas) · **platform downstream 294 passed/0 failed** · ruff clean · suite_collects 476/0. T-ALL-review.md verdict APPROVED. → `/pm-luana` merge + propagar.

### 2026-06-22 · 🤖 claude · `/pm-luana` merge + propagate · ✓ APLICADO
`reviewing → done` (07-merge.md escrito). Merge a main vía `make promote-to-main` (cherry-pick de los commits compartidos del lift — cero brand/**, guard pasa) + `make sync-all` (main → 4 wip/{brand}, el engine hardened llega a vitalia/nicolify/comunify/lupulo). Proposal `2026-06-22-sales-agent-multibrand-graph-runtime` vive en wip/vitalia → se marca `migrated` cuando vitalia mergee (no bloquea el lift). ESC-6 brand-migration NO se corre acá (cada marca la autorea en su worktree; vitalia prioritaria post-sync, DDL en migration_notes.md). Flag: T-DEBT1 revivió el snapshot test → generó `core/snapshots/orchestrator/telegram_new_lead_baseline.json` (artefacto de test, dejado untracked, fuera de scope del lift → decidir si se commitea el golden por separado). Próximo: prompt para Chris terminar el trabajo en vitalia (OLA-1 + migración + live-verify grafo + Phase 2 brand-first) + cleanup de este worktree temporal.

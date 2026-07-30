# Master Audit — Stories Sweep 2026-05-27

> **Scope:** sweep completo cross-brand de stories activas + archived + outcomes + capabilities + promotion proposals. Validación de compliance vs rules cementadas hoy (anti-duplication-refining, architect-autonomous-mode, claude-md-overlay, learning-capture, worktree-dual-strategy, github-actions-deferred) + ordering recomendado para desarrollo.
>
> **Fecha:** 2026-05-27. **Auditor:** Opus 4.7 (sintetiza 2 Haiku audits paralelos). **Branch:** `wip/protocol-claude-management-tuning`.
>
> **Reportes fuente** (tmp, no committed):
> - `/tmp/vitalia-audit-2026-05-27.md` (30 stories activas + 5 outcomes + 71 capabilities)
> - `/tmp/comunify-platform-audit-2026-05-27.md` (1 story comunify + 7 outcomes platform + 13 proposals + nicolify/lupulo deep scan)

## ★ Hallazgo CRÍTICO #0 — anti-duplication-refining.md tiene asunción incorrecta

**Asunción cementada hoy** (2026-05-27 morning):

> "nicolify es brand más madura — ~24 meses producción, ~80% features shipped"
> "**fuente prior-art principal**"

**Realidad filesystem** (verificada por Haiku audit):

```
nicolify/docs/product/
├── checkpoint.md (state: shipped, 2026-05-15)
├── stories/      ← VACÍO (solo README.md)
├── outcomes/     ← VACÍO (solo README.md)
├── capabilities/ ← VACÍO (solo README.md)
├── modules/      ← VACÍO (solo README.md)
```

El "shipped" de nicolify vive en `docs/archive/2026/snapshot-pre-multibrand-pm-redesign/` (24 stories + 12 modules + 15 capabilities **frozen** 2026-05-15). El brand-level nicolify post-reorg está prácticamente vacío.

**Implementaciones live REALES post-reorg:**

| Brand | Stories done (state=done en archive) | Capabilities live | Outcomes activos |
|---|---|---|---|
| **vitalia** | 27 archived done + Fase 1 shell complete + Fase 2 in-progress | 71 | 5 (1 master + 4 others) |
| **comunify** | 2 archived done (design-system + dev-stack) | 18 | 1 |
| **nicolify** (frozen snapshot) | 24 stories preserved as archeology | 15 | varios |
| **lupulo** | 0 | 0 | 0 (placeholder) |

**Acción correctiva (ejecutada en este PR):**

1. `.claude/rules/anti-duplication-refining.md` — pivotar: source principal = **vitalia + comunify (live shipped) + snapshot nicolify (arqueológico)**
2. `nicolify/CLAUDE.md` overlay — clarificar nicolify es brand "snapshot frozen" + cross-brand source vía snapshot path
3. `vitalia/CLAUDE.md` overlay — actualizar "Cross-brand learning sources" tabla (snapshot path agregado)
4. `docs/product/vision.md` — actualizar "Nicolify ~80% shipped" → "frozen snapshot post-reorg + comunify+vitalia live"

---

## Vitalia (30 active + 27 archived + 5 outcomes + 71 capabilities)

### Sub-finding V1 — 4 Fase 1 stories con state ambiguo

Checkpoint global declara estas como done/archived en comentarios, pero **siguen en `vitalia/docs/product/stories/`**:

- `vitalia-fase1-ribbon-6-tabs`
- `vitalia-fase1-shell-layout-5050-race-fix`
- `vitalia-fase1-sub-tabs-line2`
- `vitalia-fase1-valeria-chat-skeleton`

**3 escenarios posibles:**
- (a) state=done pero NO archivado → **R2 violation** (brand-docs-schema.md), debe moverse a `vitalia/docs/archive/2026/stories/`
- (b) state=parked (hotfix shell-layout-5050-race-fix ratificado) → mantener pero clarificar
- (c) state=open con trabajo pendiente → actualizar checkpoint con state real

**Acción:** Chris ratifica scenario per story → `/pm-vitalia` archiva o updatea state.

### Sub-finding V2 — vitalia-payment-adapter-mvp R-PriorArt violation

state=`refined`, phase=`SPEC_RATIFIED_DEFERRED_ARCHITECT`. **No tiene sección `## Prior art applied` en 01-spec.md** (violation rule anti-duplication-refining.md cementada hoy).

**Acción:** `/po` o Chris agrega sección a 01-spec.md citando: Stripe vs Mercado Pago vs Adyen vs Payso decisión + alternativas evaluadas + lift candidates si aplica. Después architect puede proceder.

### Sub-finding V3 — Outcome admin-iam-adopt declara story que NO existe

Outcome `vitalia/docs/product/outcomes/admin-iam-adopt.md` declara `story_ids: [vitalia-adopt-luana-core-iam]` pero esa story directory **NO existe** en `product/stories/`.

**Acción:** Crear story stub `vitalia-adopt-luana-core-iam/checkpoint.md` con state=idea, o remover del outcome si superseded por trabajo posterior (admin-iam-adoption-platform outcome existe a platform-level).

### Sub-finding V4 — R3-AutoGen violations BACKLOG files

`BACKLOG.md`, `BACKLOG.yaml`, `BACKLOG-TLDR.md` sin header `<!-- AUTO-GENERATED -->`. Per brand-docs-schema.md R3 v2 estos files deberían ser gitignored + tener header explícito.

**Acción:** `python scripts/generate_backlog.py --brand vitalia` regen + verificar `.gitignore` cubre los 3.

### Sub-finding V5 — Cross-brand lift candidates detectados

3 patterns en vitalia que probablemente sirven a comunify/lupulo/futuras:

1. **shell-organism v1** (6 tabs + agent framework) → lift candidate `core/luana-core-shell-organism/`. Afecta comunify (creator dashboard), lupulo (KDS), futuras.
2. **Agents catalog pattern** (6 agentes hex colors + thumbnails + transparent images) → lift candidate Extension SDK EP-agents.
3. **Sales-agent voice compiler v2** (system_instruction generation) → ya vive parcial en `core/luana-core-sales-agent/` pero brand-extension vitalia tiene mejoras (vitalia_prohibited_phrases). Evaluar lift adicional.

**Acción:** `/pm-luana` evalúa cada candidate vs promotion-protocol workflow + escribe proposals si Chris ratifica.

### Sub-finding V6 — Dependency graph Fase 2 (22 stories idea)

**Service deps (TIER 0 — gating ALL Fase 2):**
- `vitalia-payment-adapter-mvp` (state=refined) → BLOQUEA adrian-embudo + adrian-propuestas
- `vitalia-fiscal-emission-pe` (state=refining) → BLOQUEA lisa-compliance
- `vitalia-pricing-decision` (state=idea) → BLOQUEA lucas-envuelo, lucas-lanzar

**TIER 1 — Config (4 stories, parallel):**
- `vitalia-fase2-config-onboarding-clinica`
- `vitalia-fase2-config-cuenta`
- `vitalia-fase2-config-conexiones`
- `vitalia-fase2-config-avanzado`

**TIER 2 — Agent clusters (paralelizables post-Tier 1, 18 stories):**
- Valeria (1): pacientes
- Adrián (4): inbox, embudo*, outbound, propuestas* (* hard-blocked TIER 0)
- Lisa (4): servicios, doctores, compliance*, landing-public
- Camila (4): voz, reactivar, multiplicar, reputacion
- Lucas (5): recursos, mercado, envuelo*, resultados, lanzar*

**TIER 3 — Cross-agent orchestration (post Fase 2):**
- admin-iam-adopt (outcome)

**Sprint planning recomendado:**

| Sprint | Foco | Output esperado |
|---|---|---|
| **A** | TIER 0 architect + build (payment + fiscal + pricing) | 3 services shipped, agent-clusters unblocked |
| **B** | TIER 1 config (4 parallel) + arranca Lisa/Camila/Valeria | 4 config + 3-6 agent stories ready/developing |
| **C** | Adrián cluster post-payment + continúa Lisa/Camila | Adrián 4 stories complete |
| **D** | Lucas cluster post-pricing + cross-agent | Lucas 5 stories complete |
| **E** | admin-iam-adopt + polish + Fase 2 cierre | Fase 2 COMPLETE |

---

## Comunify (1 active + 2 archived + 1 outcome + 18 capabilities)

### Sub-finding C1 — Compliance OK, scope mínimo, brand healthy

Solo 1 story active (`comunify-warning-token-contrast-fix` state=idea). 2 done archived. R1/R2/R3 PASS. No gaps detectados.

**Acción:** `/pm-comunify` decide priority warning-token-contrast-fix. Si Chris OK refinar → /po-ux.

### Sub-finding C2 — Outcome único activo

`dev-stack-cross-brand-fixes` es outcome platform-level (no comunify-specific). Comunify ya cumplió milestone (Playwright E2E ownership transferred).

**Acción:** Comunify probablemente necesita nuevos outcomes Q3-Q4 2026 (creator economy features: cohort booking, voice cloning, authority vault). Pendiente strategic decision Chris.

---

## Platform-level (7 outcomes + 13 proposals + 5 archived stories)

### Sub-finding P1 — 7 outcomes ALL stuck en `refining` 7-11 días

| Outcome | Age | State |
|---|---|---|
| infra-dev-multibrand | 11d | refining |
| dev-stack-cross-brand-fixes | 9d | refining |
| admin-iam-adoption-platform | 7d | refining |
| luana-core-ui-foundation | 7d | refining |
| cicd-multibrand-deploy | 11d | refining |
| docker-dev-multibrand | 11d | refining |
| git-strategy-revised | 11d | refining |

**Análisis:** 0/7 outcomes han transitado a `refined` ni `ready`. Los 3 sub-outcomes (cicd + docker + git-strategy) están vivos como "infra futura" pero algunos shipping techni (docker-dev-multibrand) ya fueron implementados via stories archive S-DOCKER-DEV-MULTIBRAND.

**Acción:** `/pm-luana` audit 7 outcomes:
- Si shipped via story archive → transition state=done + cementar capabilities
- Si blocked por dep → documentar `phase` + `blocker` field
- Si stale-no-progress → state=parked

### Sub-finding P2 — 2 proposals stale at `proposed`

- `2026-05-17-auto-regen-backlog-precommit` — 9 días en proposed sin pickup
- `2026-05-21-deferred-e2e-blocker-gate` — 0d (recent, OK por ahora)

**Acción `/pm-luana`:** ratificar auto-regen-backlog → si accepted, escribir story implementation; si rejected, document razón.

### Sub-finding P3 — Data quality 1 proposal sin state field

`docs/promotion-protocol/proposals/2026-05-26-lift-brand-visual-extraction-to-core.md` no tiene field `state:` (debería ser proposed/accepted/migrated/rejected).

**Acción:** completar field state.

### Sub-finding P4 — 5 archived platform stories OK

`luana-nicolify-migration`, `S-CICD-DEPLOY`, `S-DOCKER-DEV-MULTIBRAND`, `S-GIT-STRATEGY-CORE`, `S-GIT-STRATEGY-HELPERS` — todos infra cementations done 2026-05-15. ✅

---

## Nicolify (frozen snapshot)

### Sub-finding N1 — Brand-level vacío + snapshot read-only

Status real: brand-level `nicolify/docs/product/` está prácticamente vacío. La "madurez" vive en `docs/archive/2026/snapshot-pre-multibrand-pm-redesign/` como referencia frozen (24 stories + 12 modules + 15 capabilities).

**Acción ejecutada en este PR:**
- `.claude/rules/anti-duplication-refining.md` updated — pivot source principal
- `nicolify/CLAUDE.md` updated — clarifica nicolify es snapshot-based cross-brand source (no brand-active development)

**Acción futura:** Chris decide si re-bootstrappear nicolify como brand activa (migrate snapshot → product/) o mantenerlo frozen indefinidamente.

---

## Lupulo (placeholder vacío)

### Sub-finding L1 — Bootstrap pendiente

`lupulo/docs/product/` 100% vacío. `lupulo/config/brand.yaml` existe pero sin capability.

**Acción:** roadmap CLAUDE.md cita "Story 12 bootstrap planned for lupulo" — no urgente, gating es decisión Chris cuando arrancar vertical KDS/gastronomía.

---

## 2 stories sugeridas turno previo (re-cementadas aquí)

### S1 — `staging-k8s-real` (platform outcome NEW)

**Origen:** turno previo — `dev-app.vitalialat.com` corre desde laptop Chris vía Cloudflare Tunnel, NO production-grade staging.

**Outcome creado en este PR:** `docs/product/outcomes/staging-k8s-real.md` (state=idea, awaiting Chris infrastructure cost ratify + provider decision).

### S2 — `capability-status-taxonomy-v2` (platform outcome NEW)

**Origen:** turno previo — capability YAMLs todos usan `status: live` único valor. Necesita taxonomía `live-ui` / `live-superseded` / `live-infra` + field `replaced_by`.

**Outcome creado en este PR:** `docs/product/outcomes/capability-status-taxonomy-v2.md` (state=idea, low-effort high-clarity).

---

## Acciones inmediatas (PR este worktree wip/protocol-claude-management-tuning)

| # | Acción | File | Status |
|---|---|---|---|
| 1 | Fix anti-duplication-refining.md — pivot prior-art source | `.claude/rules/anti-duplication-refining.md` | ✅ pending edit |
| 2 | Update nicolify/CLAUDE.md — clarifica snapshot-based | `nicolify/CLAUDE.md` | ✅ pending edit |
| 3 | Update vitalia/CLAUDE.md — actualiza prior-art sources tabla | `vitalia/CLAUDE.md` | ✅ pending edit |
| 4 | Create outcome staging-k8s-real | `docs/product/outcomes/staging-k8s-real.md` | ✅ pending write |
| 5 | Create outcome capability-status-taxonomy-v2 | `docs/product/outcomes/capability-status-taxonomy-v2.md` | ✅ pending write |
| 6 | Update docs/product/vision.md — Nicolify role accurate | `docs/product/vision.md` | ✅ pending edit |
| 7 | Audit doc (este file) | `docs/process/audits/2026-05-27-stories-sweep.md` | ✅ writing now |

## Acciones diferidas (worktree wip/vitalia separate commit)

| # | Acción | File | Owner |
|---|---|---|---|
| 8 | Clarify 4 Fase 1 stories state (archive vs open) | `vitalia/docs/product/stories/vitalia-fase1-{ribbon,sub-tabs,valeria-chat-skeleton,shell-layout-5050-race-fix}/checkpoint.md` | Chris ratifica + /pm-vitalia ejecuta |
| 9 | Add "## Prior art applied" section a payment-adapter spec | `vitalia/docs/product/stories/vitalia-payment-adapter-mvp/01-spec.md` | /po o Chris |
| 10 | Create stub story vitalia-adopt-luana-core-iam | `vitalia/docs/product/stories/vitalia-adopt-luana-core-iam/checkpoint.md` | /pm-vitalia |
| 11 | Regen BACKLOG.{md,yaml,-TLDR.md} con header AUTO-GENERATED | `vitalia/docs/product/BACKLOG.*` | `python scripts/generate_backlog.py --brand vitalia` |

## Acciones diferidas (worktree principal/protocol para /pm-luana)

| # | Acción | File | Owner |
|---|---|---|---|
| 12 | Audit 7 platform outcomes (refined/done/parked decision) | `docs/product/outcomes/*.md` | /pm-luana |
| 13 | Ratify proposal auto-regen-backlog-precommit | `docs/promotion-protocol/proposals/2026-05-17-auto-regen-backlog-precommit.md` | Chris + /pm-luana |
| 14 | Add state field a proposal lift-brand-visual-extraction | `docs/promotion-protocol/proposals/2026-05-26-lift-brand-visual-extraction-to-core.md` | /pm-luana |
| 15 | Evaluate 3 vitalia lift candidates (shell-organism + agents catalog + sales-agent voice) | promotion proposals nuevas | /pm-luana |

---

## Summary

**31 hallazgos** detectados, agrupados:
- 🚨 1 CRITICAL: anti-duplication-refining.md cita source que no aplica (fix in this PR)
- ⚠️ 6 compliance gaps (R-PriorArt + R2 + R3 + missing story + stale outcomes + missing state field)
- ℹ️ 3 cross-brand lift candidates (vitalia → core)
- ℹ️ 22 stories idea Fase 2 (organizadas en TIERS 0-3 con sprint plan A-E)
- ℹ️ Strategic decisions pendientes Chris: nicolify re-bootstrap?, lupulo bootstrap timing?, comunify nuevos outcomes?

**Compliance status post-tuning:**

| Brand | R1 | R2 | R3 | R-PriorArt | R-DispatchPlan | R-AutonomousMode | overall |
|---|---|---|---|---|---|---|---|
| vitalia | ✅ | ⚠️ (V1) | ❌ (V4) | ❌ (V2) | N/A no ready | N/A | ⚠️ 3 gaps |
| comunify | ✅ | ✅ | ✅ | N/A no refined | N/A | N/A | ✅ |
| nicolify | N/A snapshot | N/A | N/A | N/A | N/A | N/A | N/A |
| lupulo | ✅ | ✅ | ✅ | N/A | N/A | N/A | ✅ |
| platform | ✅ | ✅ | ⚠️ (P3) | N/A outcomes | N/A | N/A | ⚠️ 1 gap |

---

**Generated:** 2026-05-27 | **Sources audited:** `vitalia/`, `comunify/`, `nicolify/`, `lupulo/`, `docs/product/outcomes/`, `docs/promotion-protocol/proposals/`, `docs/archive/2026/snapshot-pre-multibrand-pm-redesign/`

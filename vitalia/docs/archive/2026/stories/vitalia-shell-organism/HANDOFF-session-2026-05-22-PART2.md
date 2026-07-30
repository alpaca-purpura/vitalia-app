<!-- voseo-allowed: internal handoff documentation for session continuation -->

# HANDOFF — Sesión /pm-vitalia 2026-05-22 PARTE 2 (Tasks 7-14 cementadas)

> **Cierre completo planning Fase 1+2 outcome master vitalia-mvp-ui-foundation v2.0**
>
> Continuación de `HANDOFF-session-2026-05-22.md` (parte 1 = Tasks 1-6) · Parte 2 (sesión actual) cierra Tasks 7-14.

---

## ✅ Resumen ejecutivo PARTE 2 (Tasks 7-14)

| Task | Output | Files |
|---|---|---|
| #7 — 6 stories F2-S1..F2-S6 Valeria + Adrián | Generadas con detalle completo (frontmatter + scope + AC + Gherkins + deliverables + reuse map + deps + riesgos) | 6 checkpoints NEW |
| #8 — 4 stories F2-S7..F2-S10 Lisa | Generadas | 4 checkpoints NEW |
| #9 — 4 stories F2-S11..F2-S14 Camila | Generadas (incl. 15-triggers SSoT en voz) | 4 checkpoints NEW |
| #10 — 5 stories F2-S15..F2-S19 Lucas | Generadas (incl. Mateo integration en recursos) | 5 checkpoints NEW |
| #11 — 3 stories F2-S20..F2-S22 Configurar | Generadas (incl. multi-step Danger Zone) | 3 checkpoints NEW |
| #12 — Refactor 2 + drop 1 | slice-1-agenda + slice-1-pipeline → `state: dropped` con `superseded_by` apuntando a F2-S1/F2-S4 · slice-1-marketing-integration → `state: dropped` (Tailwind diag absorbido en F1-S0) | 3 checkpoints MODIFY |
| #13 — Service-stories update | payment-adapter-mvp + fiscal-emission-pe updated con `cross_phase_2_consumers` enumerating F2-S1/F2-S4/F2-S6/F2-S20 deps | 2 checkpoints MODIFY |
| #14 — Regen BACKLOG + handoff final | BACKLOG.md regenerado · 0 warnings · este doc | BACKLOG regen + HANDOFF |

**Total artifacts esta parte:**
- 22 stories Fase 2 NEW (F2-S1..F2-S22)
- 3 stories slice-1 dropped/refactored (state changes)
- 2 service-stories deps updated
- 1 HANDOFF final
- 1 BACKLOG regen

**Total combined Parte 1 + Parte 2:**
- 11 stories Fase 1 (Parte 1)
- 22 stories Fase 2 (Parte 2)
- 6 artifacts cementados (Design Contract + Template + shell-organism cierre + outcome v2.0 + 2 HANDOFFs)
- 3 slice-1 superseded/dropped
- 2 service-stories actualizadas

---

## 📋 Estado backlog Vitalia post-cierre completo

```
💡 Ideas (34):
   - 11 × Fase 1 (F1-S0..F1-S10)
   - 22 × Fase 2 (F2-S1..F2-S22)
   - 1 × vitalia-pricing-decision (idea pendiente · no relacionada shell-organism)

🔬 Refining (2 cap-eligible / cap 3): ★ down from 7 ★
   - vitalia-payment-adapter-mvp     [AWAITING_PO_DRAFT_RE_PRIORITIZED]
   - vitalia-fiscal-emission-pe      [AWAITING_PO_DRAFT_RE_PRIORITIZED]
   (3 outcomes legacy en refining excluded from cap: admin-iam-adopt · dev-environment-multibrand · vitalia-mvp-ui-foundation-handoff-cross-story)

✅ Refined (0 / cap 5):     none
📦 Ready (0 / cap 5):       none
🔨 Developing (0 / cap 3):  none
🧪 Developed (0 / cap 10):  none
🔍 Reviewing (0 / cap 2):   none

✅ Done (last 90d, 1):       vitalia-shell-organism (2026-05-22)

❌ Dropped (4):
   - vitalia-slice-1-marketing-integration  (Tailwind absorbido F1-S0)
   - vitalia-slice-1-agenda                 (superseded by vitalia-fase2-valeria-agenda)
   - vitalia-slice-1-pipeline               (superseded by vitalia-fase2-adrian-embudo)
```

**Cap status:** todos los caps respetados (refining ≤ 3 cap-eligible · refined/ready/developing/developed/reviewing all 0). Sistema listo para arrancar refining iterativo de las 33 ideas Fase 1+2.

---

## 🚀 Recomendación próximos pasos (orden ejecución optimal)

### Paso 1 — Service-stories refining BEFORE Fase 2 builds (paralelo a Fase 1)

`payment-adapter-mvp` + `fiscal-emission-pe` (2 service-stories) son blockers HARD de F2-S1 + F2-S4 + F2-S6. Para que `developed` esté ANTES de F2 arranque:

```
Chris ratifica refining: /po vitalia-payment-adapter-mvp + /po vitalia-fiscal-emission-pe
  → produce 01-spec.md service-story (ya tienen scope cementado en checkpoint)
  → Chris ratifica → state refined
  → /architect produce ready package
  → /dev-team build → /auditor → done
```

Estimado: 1-2 semanas paralelas a Fase 1 dev.

### Paso 2 — Fase 1 atomic build (11 stories en cascada)

Strict dependency order per outcome master § Dependency graph Fase 1:

```
F1-S0 stack-stability                      ◀ BLOCKER HARD (Shadcn install + tokens + .vt-* plan + Tailwind v4 verify)
   ↓
F1-S1 design-tokens-theme  ───────────────┐
   ↓                                       │
F1-S2 topbar-global          F1-S5 valeria-rail-history
   ↓                                       │
F1-S3 tenant-switcher         F1-S4 shell-layout-5050
   ↓                                       │
   └── F1-S7 ribbon ─── F1-S8 sub-tabs    │
              ↓                            │
         F1-S9 routing ────────────────────┤
              ↓                            │
         F1-S10 empty-states ──── F1-S6 valeria-chat ─→ Fase 1 DONE
```

Recomendación: refinar bloques en paralelo posible (F1-S5 + F1-S6 valeria paralelo · F1-S7 + F1-S8 ribbon paralelo · etc.) per `parallel_safe: true` en cada checkpoint.

### Paso 3 — Fase 2 priority order (per outcome master)

| Orden | Agente | Stories | Razón |
|---|---|---|---|
| 1 | Valeria | F2-S1 agenda · F2-S2 pacientes | Operación día-a-día · primer valor visible |
| 2 | Adrián | F2-S3 inbox · F2-S4 embudo · F2-S5 outbound · F2-S6 propuestas | Closer + alto reuse |
| 3 | Lisa | F2-S7 marca · F2-S8 doctores · F2-S9 servicios · F2-S10 compliance | Brand + assets · alto reuse |
| 4 | Camila | F2-S11 voz · F2-S12 reactivar · F2-S13 multiplicar · F2-S14 reputacion | Post-revenue CLTV |
| 5 | Lucas | F2-S15 lanzar · F2-S16 envuelo · F2-S17 recursos · F2-S18 resultados · F2-S19 mercado | Growth |
| 6 | Configurar | F2-S20 cuenta · F2-S21 conexiones · F2-S22 avanzado | Admin · poco frecuente |

WIP cap respect: solo 3 stories en `developing` simultaneamente per paradigm v4.

---

## 🎯 Reglas no negociables preservadas (re-cita verbatim)

1. **Cada story usa el template** `vitalia/docs/specs/templates/01-spec-shell-template.md` con TODAS las secciones obligatorias
2. **TODA story cita** `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` como SSoT
3. **REUSE máximo** documentado en cada § Reuse map (Nicolify · core engine · Vitalia shipped · NEW solo cuando justificable)
4. **Playwright visual golden** contra mockup HTML obligatorio per story
5. **Spanish neutro LatAm** (excepto sales_agent voice tenant)
6. **HIPAA-lite enforcement** per `vitalia/.claude/rules/hipaa-lite.md` (dual filter tenant+clinic · audit log · sanitize_payload · channel guards)
7. **R23 Opus 4.7 obligatorio** para agentic production code (F2-S17 Mateo)
8. **Anti-duplication** per `.claude/rules/anti-duplication.md` (lift to engine cuando cross-brand pattern)
9. **Zero deuda técnica** checklist § 9 del template (15+ items por story pre-merge)
10. **Outcome master `vitalia-mvp-ui-foundation` v2.0** es contenedor canónico Fase 1+2

---

## 📦 Artefactos producidos sesión completa (Parte 1 + Parte 2)

### Cementados ratificados (read-only post hoy)

1. `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md` — SSoT atomic design (Parte 1)
2. `vitalia/docs/specs/templates/01-spec-shell-template.md` — Template 14 secciones (Parte 1)
3. `vitalia/docs/product/stories/vitalia-shell-organism/` — Design story cerrada (Parte 1)
4. `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation.md` — Outcome master v2.0 (Parte 1)

### Stories generadas (37 = 11 Fase 1 + 22 Fase 2 + 4 status-changes service+slice-1)

```
Fase 1 (11):
  vitalia-fase1-stack-stability
  vitalia-fase1-design-tokens-theme
  vitalia-fase1-topbar-global
  vitalia-fase1-tenant-switcher
  vitalia-fase1-shell-layout-5050
  vitalia-fase1-valeria-rail-history
  vitalia-fase1-valeria-chat-skeleton
  vitalia-fase1-ribbon-6-tabs
  vitalia-fase1-sub-tabs-line2
  vitalia-fase1-routing-shell
  vitalia-fase1-empty-states

Fase 2 (22):
  vitalia-fase2-valeria-agenda                F2-S1  (refactor de slice-1-agenda)
  vitalia-fase2-valeria-pacientes             F2-S2
  vitalia-fase2-adrian-inbox                  F2-S3  (supersedes slice-1-inbox archived)
  vitalia-fase2-adrian-embudo                 F2-S4  (refactor de slice-1-pipeline)
  vitalia-fase2-adrian-outbound               F2-S5
  vitalia-fase2-adrian-propuestas             F2-S6
  vitalia-fase2-lisa-marca                    F2-S7
  vitalia-fase2-lisa-doctores                 F2-S8
  vitalia-fase2-lisa-servicios                F2-S9  (★ canvas escalera valor)
  vitalia-fase2-lisa-compliance               F2-S10
  vitalia-fase2-camila-voz                    F2-S11 (★ 15 triggers SSoT)
  vitalia-fase2-camila-reactivar              F2-S12
  vitalia-fase2-camila-multiplicar            F2-S13 (★ atomic ownership P1 ratificada — referrals from Lucas→Camila)
  vitalia-fase2-camila-reputacion             F2-S14 (scaffold-mvp)
  vitalia-fase2-lucas-lanzar                  F2-S15
  vitalia-fase2-lucas-envuelo                 F2-S16
  vitalia-fase2-lucas-recursos                F2-S17 (★ Mateo agentic prod code · R23 Opus 4.7)
  vitalia-fase2-lucas-resultados              F2-S18
  vitalia-fase2-lucas-mercado                 F2-S19
  vitalia-fase2-config-cuenta                 F2-S20
  vitalia-fase2-config-conexiones             F2-S21 (★ HUB 6 categorías OAuth)
  vitalia-fase2-config-avanzado               F2-S22 (★ Danger Zone multi-step)

Status changes (4):
  vitalia-slice-1-agenda                 idea → dropped (superseded_by F2-S1)
  vitalia-slice-1-pipeline               idea → dropped (superseded_by F2-S4)
  vitalia-slice-1-marketing-integration  idea → dropped (Tailwind absorbido F1-S0)
  vitalia-payment-adapter-mvp            refining cross_phase_2_consumers updated
  vitalia-fiscal-emission-pe             refining cross_phase_2_consumers updated
```

---

## 🚨 Decisiones cementadas Chris 2026-05-22 (re-citar siempre)

| # | Decisión | Implicancia |
|---|---|---|
| D1 | Shadcn UI install AHORA | F1-S0 ejecuta `npx shadcn@latest init` + 8 primitives |
| D2 | Deprecar `.vt-*` utility classes COMPLETO | Migración progresiva · plan en F1-S0 · drop final F2-S23 (futuro) |
| D3 | Route group paralelo `(shell-organism)/` | Coexiste con `(dashboard)/` legacy hasta Fase 2 completa |
| D4 | Verificar Tailwind v4 empíricamente | F1-S0 incluye `make dev-vitalia` + browser visual check |
| D5 | Atomic design strict | átomos · moléculas · organismos · templates · pages |
| D6 | Playwright golden visual + funcional test obligatorio | Zero deuda técnica desde origen |
| D7 (★ paradigm 2026-05-21) | 15 triggers SSoT en Camila voz | Cementados en F2-S11 |
| D8 (★ paradigm 2026-05-21) | Atomic ownership P1 referrals → Camila | F2-S13 migration desde Lucas |
| D9 (★ paradigm 2026-05-21) | Mateo asistente transversal sin tab | Vive en cards F2-S17 lucas-recursos |

---

## 🎬 Directiva Chris explícita (citar verbatim)

> "Si o si debe haber un tenant_switcher visible · debe haber un switcher claro-oscuro · vamos a priorizar la vista Agentic · historial colapsado y con opción de abrirse (transpuesta copilot Nicolify) · ribbon expansible 2 líneas"
>
> "Detallista en cada átomo, molécula · tomate todo el tiempo necesario · no perder foco durante la elaboración · revisar lo que ya existe en vitalia, core, y código antiguo /home/chalreme/Documentos/ap_sales_agent para no empezar de cero · siempre verificar con playwright funcional + visual contra el mockup · estricto en proceso para no crear deuda técnica · reutilizar en la medida de lo posible siempre que sea técnicamente bien hecho"

---

## 📥 Prompt copy-paste para retomar PRÓXIMA conversación

```text
Retomo /pm-vitalia post planning completo 2026-05-22 (Parte 1 + Parte 2).

Branch: wip/vitalia

LEE PRIMERO (en orden):

1. vitalia/docs/product/stories/vitalia-shell-organism/HANDOFF-session-2026-05-22-PART2.md  ← este doc
2. vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation.md (v2.0)
3. vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md (SSoT atomic design)
4. vitalia/docs/specs/templates/01-spec-shell-template.md (template historias)
5. vitalia/docs/product/BACKLOG.md (auto-gen vista 10 estados)

ESTADO POST-PLANNING:
- Backlog ideas: 34 (11 Fase 1 + 22 Fase 2 + 1 pricing)
- Refining: payment-adapter-mvp + fiscal-emission-pe (priority bump pending)
- Refined/Ready/Developing/Developed/Reviewing: 0 (clean state)
- Dropped: slice-1-agenda · slice-1-pipeline · slice-1-marketing-integration

PRÓXIMOS PASOS RECOMENDADOS (en orden):

OPCIÓN A — Arrancar refining service-stories (BLOCKER Fase 2):
  Chris ratifica priority bump → /po vitalia-payment-adapter-mvp
  Chris ratifica priority bump → /po vitalia-fiscal-emission-pe
  Refining iterativo · ratify → refined → /architect → ready
  Estimado: 1-2 semanas paralelas Fase 1 dev

OPCIÓN B — Arrancar refining Fase 1 atómica (UI layer):
  /po-ux vitalia-fase1-stack-stability     ← F1-S0 BLOCKER HARD
  → refining iterativo Chris
  → ratify → refined
  → /architect produce ready package F1-S0
  → /dev-team build F1-S0 (Shadcn install + tokens + Tailwind v4 verify)
  → /auditor → merge done
  → continúa F1-S1 → F1-S2 → ... cascada
  Estimado: 4-6 semanas Fase 1 completa

OPCIÓN C — Arrancar paralelo Opción A + B (recomendada):
  Service-stories refining EN PARALELO con Fase 1 builds
  → cuando Fase 1 done + service-stories developed → arrancar F2-S1

PREGUNTA CHRIS: ¿qué opción? (recomendada: C)

REGLAS NO NEGOCIABLES (preservadas):
- 15 secciones template obligatorias por story
- Design Contract como SSoT
- Playwright golden visual + funcional test
- HIPAA-lite enforce
- Spanish neutro LatAm
- Zero deuda técnica checklist (15+ items)
- R23 Opus 4.7 para Mateo (F2-S17)
- WIP caps paradigm v4 (refining≤3 · refined≤5 · ready≤5 · developing≤3 · developed≤10 · reviewing≤2)
```

---

## Resumen ejecutivo session completa

| Métrica | Valor |
|---|---|
| Stories generadas Fase 1 | **11** ✅ |
| Stories generadas Fase 2 | **22** ✅ |
| Refactor/drops aplicados | **3** ✅ |
| Service-stories deps updated | **2** ✅ |
| Artifacts cementados | **6** ✅ |
| Total backlog ideas | **34** |
| Decisiones técnicas ratificadas | **D1-D9** ✅ |
| Próximo skill recommended | `/pm-vitalia` ratify next-step Opción A/B/C |
| Modelo recomendado próxima sesión | Opus 4.7 (1M context) |

**Visión norte:** "Como una secretaria real." Vitalia shell-organism agéntico cementado en Design Contract + Template + 33 stories paradigm shell-organism. Todo el camino entre Fase 1 (shell esqueleto navegable) y Fase 2 (sub-tabs activas con valor real) está mapeado, scope cementado, deps cruzadas explícitas. Próxima conversación arranca refining iterativo en paralelo según opción ratificada por Chris.

---

## 🔧 Commit + push recomendado pre-cierre

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}

git status --short

# Stage por nombre exacto (NUNCA git add -A)
git add vitalia/docs/product/stories/vitalia-fase2-*
git add vitalia/docs/product/stories/vitalia-slice-1-agenda/checkpoint.md
git add vitalia/docs/product/stories/vitalia-slice-1-pipeline/checkpoint.md
git add vitalia/docs/product/stories/vitalia-slice-1-marketing-integration/checkpoint.md
git add vitalia/docs/product/stories/vitalia-payment-adapter-mvp/checkpoint.md
git add vitalia/docs/product/stories/vitalia-fiscal-emission-pe/checkpoint.md
git add vitalia/docs/product/stories/vitalia-shell-organism/HANDOFF-session-2026-05-22-PART2.md

# BACKLOG auto-gen (R3 gitignored) — NO se stagea

# Commit con HEREDOC
git commit -m "$(cat <<'EOF'
docs(vitalia): /pm-vitalia planning Parte 2 — Fase 2 + refactor + service-stories deps

Tasks 7-14 cementadas. 22 stories Fase 2 + 3 slice-1 dropped + 2 service-stories updated.

Artefactos:
- F2-S1..F2-S22 (22 stories) con scope + AC + Gherkins + deliverables + reuse map + deps + riesgos
- 3 slice-1 dropped: agenda (superseded F2-S1) · pipeline (superseded F2-S4) · marketing-integration (Tailwind absorbido F1-S0)
- 2 service-stories deps updated: payment-adapter-mvp + fiscal-emission-pe con cross_phase_2_consumers
- HANDOFF-session-2026-05-22-PART2.md (resumen ejecutivo + recomendación próximos pasos Opciones A/B/C)

Backlog post-planning: 34 ideas (11 Fase 1 + 22 Fase 2 + 1 pricing) · 2 refining cap-eligible · 0 refined/ready/developing/developed/reviewing · 1 done · 4 dropped.

Pendiente: Chris ratifica próximo paso (Opción A/B/C) → arrancar refining iterativo paralelo.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"

git push origin wip/vitalia
```

(O usar `/commit-push` skill para delegar a Haiku worker.)

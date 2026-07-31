# Outcome (platform) — Homologación del baseline técnico cross-brand

> Owner: `/pm-luana`. Outcome cross-brand que homologa la **base técnica compartida** que las marcas activas (vitalia, nicolify, comunify) instancian, separándola del **delta propio de cada marca**. Precede y habilita la aplicación del paradigma de historia de usuario (ADR-013 empleados-IA) marca por marca. NO es spec ejecutable — registra el trabajo derivado (promotion de ADRs + paridad por marca).

---
outcome_id: tech-baseline-homologation-platform
type: platform
status: accepted
created: 2026-06-01
owner: /pm-luana
ratified_by: chris
adr: [ADR-013-empleados-ia-auto-extension, ADR-010-orquestacion-agentica]
consumers: [vitalia, nicolify, comunify]   # lupulo + 6 futuras heredan al bootstrap
sequencing: engine-first-then-replication-gate   # revisado Chris 2026-06-01 (ver § Secuencia)
baseline_shape: platform-adrs-individual    # ratificado Chris 2026-06-01
comunify_parity: included                    # ratificado Chris 2026-06-01
depends_on: empleados-ia-auto-extension      # B (motor) + Vitalia instanciado primero — A es gate de replicación
---

## Problema que resuelve

Chris quiere que vitalia, nicolify y comunify estén **homologados** en el uso de skills/herramientas/aprendizajes técnicos y compartan la **misma visión técnica de producto** — cambiando solo lo propio de cada marca (público objetivo + procesos), sobre base **SOLID**. El cockpit queda explícitamente **per-worktree por diseño** (filesystem-as-DB) y NO se homologa.

### Diagnóstico (2026-06-01)

**Ya compartido por diseño del monorepo (1 sola fuente, idéntica para las 3):** 59 skills (`.claude/skills/`), 45 rules (`.claude/rules/`), `PARADIGM.md`, `ADR-013` (paradigma agentic fundacional), capability-protocol + lifecycle 4-ejes + SYSTEM-MAP schema, engine `core/luana-core-*` (26 pkgs), learnings técnicos transversales (`docs/learnings/`). → **El know-how técnico NO se está duplicando.**

**Divergencia real — la instanciación por marca:**

| Superficie | vitalia (ref) | nicolify | comunify | Gap |
|---|---|---|---|---|
| `vision.md` (público — debe ser propio) | ✅ | ✅ | ❌ falta | comunify sin visión |
| `SYSTEM-MAP.yaml` (registro zonas) | ✅ | ✅ | ❌ falta | comunify fuera del mapa |
| Overlay `CLAUDE.md` | 159L | 152L | 75L (incompleto) | comunify a medias |
| Shell-feature architecture (9 secciones) | ADR-vitalia-004 | ADR-nicolify-001 *"hereda vitalia-004"* | ❌ | doctrina cross-brand atrapada en ADR local |
| Mockup-per-component / SSR-store | ADR-003 / ADR-006 | parcial | ❌ | idem |
| `{brand}-design-system` skill | ✅ | ✅ | ❌ (solo `.md`) | comunify sin skill |

**Smell arquitectónico (viola SOLID-DIP + `anti-duplication.md`):** `ADR-nicolify-001` *hereda* `ADR-vitalia-003/004`. Una marca depende de otra. Deben depender ambas de un **baseline platform estable**, no entre sí.

## Qué cementa — modelo de dos capas

```
Capa 1 · BASELINE TÉCNICO PLATFORM (estable, compartido, 1 fuente)   ← se HOMOLOGA
   PARADIGM 3-planos · ADR-013 empleados-IA · shell-feature pattern ·
   mockup protocol · SSR-safe store · DoD live-verify · capability/lifecycle/SYSTEM-MAP schema
        ▲ las marcas CITAN/importan — NUNCA marca→marca
   ┌────┴────┬──────────┐
 vitalia  nicolify   comunify
Capa 2 · DELTA POR MARCA (Liskov — instancia substituible)           ← queda PROPIO
   vision.md (público) · brand.yaml · roster de agentes · compliance profile
   (HIPAA-lite vitalia / creator-funnels comunify / agent-revenue nicolify) ·
   tokens de diseño · contenido de SYSTEM-MAP · cockpit (per-worktree, NO se toca)
```

Es el invariante de ADR-013 aplicado también a la doctrina técnica de UI/arquitectura: *"etapa = interfaz estable (core); roster + procesos = extension (Liskov)"*.

## Inventario — disposición de cada ADR de Vitalia

| ADR vitalia | Disposición | Nota de generalización |
|---|---|---|
| 003 — shell-mockup-per-component | **PROMOVER → platform ADR** | Patrón de gate visual para cualquier shell-organism; vitalia overlay conserva tokens + PHI-specifics |
| 004 — shell-feature-architecture (9 secciones) | **PROMOVER → platform ADR** (el grande) | Sacar PHI/`PhiRepositoryBase`/`vitalia_growth_studio_event` → patrón genérico; overlays añaden su delta (vitalia: dual-filter+audit; nicolify/comunify: su telemetría) |
| 006 — ssr-safe-persisted-store | **PROMOVER → platform ADR** | Patrón FE puro, cero especificidad de marca |
| 008 — dev-app-live-verification-gate | Doctrina YA platform (rule #37) | Cada marca autora su gate ADR citando la rule; promover un **template** del gate |
| 005 — capability-model-4-dimensions | **RECONCILIAR** | Probable redundancia con capability-protocol + lifecycle 4-ejes (platform). Verificar y deprecar si duplica |
| 001 — shared-vs-fork · 002 — vt-deprecation | **QUEDA brand-local** | Decisiones específicas de vitalia |
| 007 — phi-pgcrypto-encryption | **QUEDA brand-local** | HIPAA-lite, vitalia-only |

ADRs nicolify a re-apuntar tras promoción: `ADR-nicolify-001` (re-point a platform), `ADR-nicolify-002 paradigma-zonas` (reconciliar con `paradigm-arquitectura.md` + `PARADIGM.md`).

## Secuencia (revisada Chris 2026-06-01 — motor primero, homologación como gate de replicación)

> **Cambio vs. ratificación inicial:** se descartó "baseline primero". Razón: la base técnica real del sistema agentico es el **motor (B = `empleados-ia-auto-extension`)**, no esta doctrina (A). B es core/brand-agnostic y NO depende de A. Vitalia es la marca **referencia** (ya tiene los patrones homologables) → tampoco necesita A previa. Promover los ADRs ANTES de validar el paradigma agentic en Vitalia arriesgaría cementar doctrina shell vieja. Por eso A entra como **gate de replicación**, después de Vitalia, promoviendo lo YA validado.

```
1. B · Motor agentico   → spike flujos durables + consolidación engine (story empleados-ia · core · cornerstone)
2. Vitalia              → instanciar el paradigma sobre la marca referencia (prueba el modelo end-to-end)
3. A · ESTE outcome     → promover patrones YA VALIDADOS a platform ADRs + comunify a paridad   ◄── gate
4. nicolify / comunify  → replicar sobre base homologada (cero repetición)
```

- **Fase A.1 (post-Vitalia) — Formalizar baseline platform.** `/pm-luana` abre promotion proposals; `/architect` autora los platform ADRs promovidos (003/004/006 generalizados + template del gate 008, **en su forma validada por la instanciación en Vitalia**) en `docs/architecture/luana-platform/`; reconcilia 005.
- **Fase A.2 — Adelgazar overlays + re-apuntar.** Cada overlay de marca queda en su delta; nicolify re-apunta a platform (rompe acople nicolify→vitalia); arch rules de marca citan baseline.
- **Fase A.3 — Comunify a paridad.** `/pm-comunify` + `/po` generan `vision.md`; `/architect` + `/pm-comunify` el `SYSTEM-MAP.yaml`; crear skill `comunify-design-system`; overlay completo citando baseline.
- **Fase A.4 — Replicar paradigma a nicolify/comunify** sobre base homologada.

**Precondición de este outcome:** B instanciado en Vitalia (story `empleados-ia-auto-extension` → derived vitalia). Hasta entonces este outcome queda `accepted` pero en espera.

## Trabajo derivado (handoffs — NO los escribe /pm-luana)

| # | Trabajo | Owner | Estado |
|---|---|---|---|
| 1 | Promotion proposals: shell-feature / mockup / ssr-store / dod-gate-template (vitalia→platform) | `/pm-luana` | pendiente |
| 2 | Autorar platform ADRs generalizados + reconciliar capability-model-005 | `/architect` (platform) | pendiente |
| 3 | Adelgazar overlays + re-apuntar ADR-nicolify-001 al baseline | `/pm-{brand}` por marca | pendiente |
| 4 | Comunify paridad: `vision.md` + `SYSTEM-MAP.yaml` + skill `comunify-design-system` | `/pm-comunify` + `/po` + `/architect` | pendiente |
| 5 | Entrar a Vitalia con el paradigma de historia de usuario (ADR-013) | `/pm-vitalia` → cadena refining | pendiente (Fase 4) |

## Invariantes que el trabajo derivado debe respetar

- **DIP/Liskov:** las marcas dependen del baseline platform, NUNCA marca→marca (mata el acople nicolify→vitalia actual).
- **DRY a nivel doctrina:** un patrón técnico cross-brand vive 1 vez (platform), no se re-deriva por marca.
- **Cockpit per-worktree intacto:** filesystem-as-DB por marca; NO se homologa (por diseño, ratificado).
- **Lo propio queda propio:** vision (público) + compliance profile + roster + tokens + procesos por marca = extension substituible.
- **Anti-creep:** `/pm-luana` propone (outcome + proposals); `/architect` autora ADRs; `/pm-{brand}` + `/po` el delta de marca; builders ejecutan lift.

## Referencias

- `docs/architecture/luana-platform/PARADIGM.md` · `ADR-010-orquestacion-agentica.md` · `ADR-013-empleados-ia-auto-extension.md`
- `docs/product/outcomes/empleados-ia-auto-extension-platform.md` — outcome que esta homologación habilita (Fase 4)
- `.claude/rules/anti-duplication.md` · `anti-duplication-refining.md` — DRY threshold + lift gate
- `docs/promotion-protocol/README.md` — workflow del lift
- `vitalia/docs/architecture/ADR-vitalia-{003,004,006,008}*.md` — fuentes a promover
- `nicolify/docs/architecture/ADR-nicolify-{001,002}*.md` — a re-apuntar/reconciliar

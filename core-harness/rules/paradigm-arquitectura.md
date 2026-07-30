# Paradigma de Arquitectura — trabajadores sobre un sistema (rule enforce-able)

**Origen:** sesión 2026-05-30 — Chris fijó el modelo operativo del producto ANTES de organizar las cajas del cockpit. **Cement-date:** 2026-05-30. **SSoT vivo:** `docs/architecture/{workspace.repo_prefix}-platform/PARADIGM.md`. **Decisión:** `ADR-010-orquestacion-agentica.md`. **Esta rule = la versión enforce-able** (árbol de decisión + anti-patterns + layers) que los skills citan. Si rule y PARADIGM divergen, manda PARADIGM (este file se corrige).

## Regla cardinal

Toda funcionalidad del producto vive en **uno de 3 planos** y aterriza en **una zona/caja del mapa**. Desde la **idea** se declara la caja; se deriva la zona; se valida hasta el merge. Quien refina/diseña/arquitectura/audita una story DEBE aplicar el árbol de decisión de abajo — no improvisar la ubicación.

### Los 3 planos (no confundirlos = no duplicar)

| Plano | Qué es | Quién lo toca |
|---|---|---|
| **1 · Sistema** | Capacidades de negocio (booking, CRM, ofertas, NPS…). Existe sin agentes. Operable a mano. | builder-backend/frontend |
| **2 · Capa de acción** | Cada caso de uso expuesto UNA vez (web + agentes comparten). Protocol-agnostic. | service layer (DDD) |
| **3 · Trabajadores** | Supervisora (Valeria) + especialistas scoped. UN engine. Persona+scope+guardrails. | builder-agentic |

**Invariantes (de PARADIGM §5):** acción única (cero mirror) · los trabajadores orquestan, no reimplementan · un solo engine · audiencia interna(`copilot`)/externa(`sales_agent`) explícita · supervisora única + tab como sesgo de ruteo · el cockpit LEE no genera · navegación sin grep (cap↔código bidireccional) · acción descubrible progresivamente.

## Árbol de decisión — ¿en qué zona/caja va esta capability? (aplicar desde `idea`)

```
¿La funcionalidad la USA el usuario a través de un trabajador concreto
 (un agente la opera por él)?
  └─ SÍ → ZONA AGENTES · caja = {lisa | valeria(→supervisora) | mateo | adrian | lucas | camila}
  └─ NO → ¿El usuario la ATRAVIESA pero NO es de ningún agente
           (entra, se da de alta, ajusta su espacio — se opera a mano)?
           └─ SÍ → ZONA PLATAFORMA · caja = {acceso | onboarding | configuracion}
           └─ NO → ¿Es no-funcional / técnico / atributo de calidad
                    (cifrado, audit, observabilidad, idempotencia, eventos, pagos, engine)?
                    └─ SÍ → ZONA INFRAESTRUCTURA · caja =
                            {seguridad-cumplimiento | observabilidad | plataforma-tecnica | motor-agentico}
                            (user_visible: false)
```

Reglas de desempate:
- **Si toca datos sensibles/regulados o seguridad:** el *enforcement técnico* (cifrado at-rest, audit, dual-filter) va a Infraestructura→Seguridad; la *vista user-facing* (ej. consentimiento que el dueño gestiona) va a su caja user-facing.
- **Motor agéntico (engine copilot/sales_agent, RAG):** Infraestructura→motor-agentico. NO es una caja de feature que compita con los agentes — es su runtime. (Anti-duplicación de PARADIGM §2.)
- **`Acceso` y `Onboarding` NO van en `Configuración`** — son superficies transversales propias.
- La **zona se DERIVA** del registro `{sistema}/docs/architecture/SYSTEM-MAP.yaml` (`zones`), no se escribe a mano por cap (evita campos que se desincronizan).

## Dónde se declara/valida (gates idea → done)

| Fase | Owner | Qué hace con el paradigma |
|---|---|---|
| **idea / refining** | `/pm-{sistema}` · `/po-ux` · `/po` · `/ux-agentico` | Aplica el árbol → declara la caja en checkpoint (`agent_owner`/`cap_target`). Sin caja válida no pasa a `refined`. Para agentic: confirma engine compartido + scope del trabajador (no engine nuevo). |
| **refined → ready** | `/architect` | `03-arch.md § Integration design (CONN)`: reachability entre planos + hogar (zona). Acción única (Plano 2), no mirror. |
| **developing** | `builder-*` | No cruza de plano sin escalar. Trabajador llama acción del Plano 2, no reimplementa. Un solo engine. |
| **developed → reviewing** | `/auditor` | Categoría Connectivity: verifica zona/caja válida + cap↔código + cero isla + cero engine duplicado. |
| **reviewing → done** | `/pm-{sistema}` | Fase F.3: la cap refleja su zona/caja en SYSTEM-MAP; `dev_preview` apunta a código real. |

## Anti-patterns prohibidos (top 4 — lista completa en PARADIGM.md)

- ❌ Un trabajador (agente) que reimplementa lógica de negocio en vez de invocar la acción del Plano 2
- ❌ Crear un engine agéntico por agente o por marca (debe ser un solo engine en `core/`; lift vía `/pm-{platform}`)
- ❌ Cap que llega a `developing` sin caja/zona declarada desde la idea; o escribir `zone` a mano en vez de derivarla del registro SYSTEM-MAP
- ❌ Confundir invariante con implementación (MCP es swappable; la doctrina es "acción única descubrible") · exponer un MCP "gordo" al contexto (usar progressive disclosure)

**Enforcement layers** (7, detalle en PARADIGM.md): auto-load Critical Rule #36 · `capability-protocol.md` deriva zona · refining aplica el árbol · `/architect` § Integration design (CONN) · `/auditor` Connectivity · `SYSTEM-MAP.yaml` registro que lee el cockpit · ⏳ migración caps config/infra→cajas.

## Referencias

- `docs/architecture/{workspace.repo_prefix}-platform/PARADIGM.md` — SSoT vivo (modelo de 3 planos, invariantes, invariante-vs-implementación)
- `docs/architecture/{workspace.repo_prefix}-platform/ADR-010-orquestacion-agentica.md` — decisión registrada
- `.claude/rules/anti-duplication.md` — un solo engine, una sola acción
- `.claude/rules/anti-orphan-integration.md` — nada llega a `done` como isla (la caja es el hogar)
- `docs/process/capability-protocol.md` — schema cap + dimensiones + derivación de zona
- `docs/process/lifecycle.md` — 4 ejes (Release→Story→Capability→Scenario)
- `{sistema}/docs/architecture/SYSTEM-MAP.yaml` — registro zonas→cajas→áreas

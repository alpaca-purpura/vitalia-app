---
story_id: vitalia-fase2-lisa-servicios
doc: 00-research
author: /pm-vitalia
created_at: 2026-06-06
status: ratified-2026-06-06-full-canvas
supersedes_scope_in: checkpoint.md (scope verbatim escrito 2026-05-22 bajo visión pre-agéntica)
---

# 00-research — Re-refinamiento de `lisa-servicios` bajo la visión agéntica

> **Por qué este doc:** la story se escribió (2026-05-22) bajo una visión de producto previa
> ("construir una linda UI de gestión de catálogo"). Chris pidió re-refinarla bajo la visión
> actual — mucho más **agéntica** — revisando lo construido en LISA, su impacto en ADRIÁN, el
> sitemap deseado, el objetivo de Vitalia, el público objetivo (clínicas dentales/estéticas que
> **el cliente busca + conversa antes de decidir**) y los competidores. Este doc es la
> recomendación PM antes de pasar a `/po-ux`.

---

## 0. Ratificación Chris 2026-06-06 (OVERRIDE de §5.2/§5.3)

Chris ratificó dos decisiones que mandan sobre la recomendación lean de §5:

1. **Alcance MVP = CANVAS COMPLETO** (no la versión lean que §5.2 recomendaba). En scope: toggle
   Catálogo|Escalera con **drag-drop** servicio→peldaño · **ladder-slot workspaces** ·
   **analítica de conversión peldaño→peldaño** · tabs **Reseñas + Stats LTV** en el detalle de
   servicio. → §5.3 "diferido" queda **cancelado** salvo los anti-objetivos reales que siguen
   fuera (A/B pricing · imports bulk · AI suggested-pricing).
2. **Hogar del cableado agéntico:** `lisa-servicios` posee la **DATA** (publicar Offers + persistir
   el **link servicio↔doctor**); el tool agéntico `match_service_and_specialist` vive en
   **canal-inbound**. lisa-servicios queda UI-story limpia; canal-inbound consume.

**Lo que NO cambió** (correcciones estructurales fuera del fork — siguen vigentes para `/po-ux`+`/architect`):
- El catálogo = **Offer Studio offers** (consumir engine vía EP-2), **NO** un `Treatment`/`LadderSlot`
  model nuevo en el engine. CERO edit de engine.
- El "peldaño" (rol del slot) = el **`OfferValueLevel`** que el engine YA tiene. Las columnas del
  canvas mapean a `OfferValueLevel` (LEAD_MAGNET·ACTIVACION·TRANSFORMACION·MAXIMIZACION·CORPORATIVO);
  los labels marketing (lead-magnet/tripwire/core/profit-max/return-path) son **etiquetas** sobre
  ese enum, NO un enum nuevo. `/architect` cierra el mapeo fino vía `offer-expert`.
- `pricing_override` + `cta_copy` del slot = campos **brand-level** (proyección sobre la Offer), no
  campos de engine.
- `module: treatments → offer` (colisión con el followup de Camila). `reuse_map` falso corregido.
- Descripciones en **voz de marca** (consume lisa-marca) + **seña/financiamiento** por servicio.

---

## 1. Hallazgo crítico — la premisa de la story es falsa

| La story dice | La realidad (inventario de código 2026-06-06) |
|---|---|
| `reuse_map: "REUSE treatments shipped (vitalia/backend/src/modules/vitalia/treatments/)"` | **No existe** un módulo `treatments/` de catálogo. El `treatments/` shipped es *seguimiento post-tratamiento* (followup + adherence) — entidad de **Camila**, PHI, LangGraph state. |
| `anti-objetivo: "NO duplicar Treatment model shipped"` | No hay `Treatment` model de catálogo que duplicar. La entidad `Treatment` del SYSTEM-MAP es de Camila (followup), no un servicio vendible. |
| `NEW model LadderSlot per offer-expert` | El engine `core/luana-core-offer-studio` **NO tiene** `LadderSlot`. Tiene `OfferValueLevel` (enum: LEAD_MAGNET·ACTIVACION·TRANSFORMACION·MAXIMIZACION·CORPORATIVO) + `ServiceDetails` + `OFFER_LADDER_HINTS` con filas `PROFESIONAL_SALUD`. El "slot" es net-new e innecesario. |
| `view: Catálogo \| Escalera (drag-drop @dnd-kit)` | Vitalia consume **cero** de Offer Studio. La cap `offer_studio/medical-services-offer-preset.yaml` está `status: planned` con preset pack **vacío**. |

**Taxonomía canónica (SYSTEM-MAP `data_ownership`):** el catálogo de servicios = **`Offer`** (`owner_module: offer_studio`, `owner_agent: lisa`, `consumed_by: [lisa, adrian, lucas, mateo]` — *"Catálogo de servicios médicos. Lisa la posee; Adrián la cita en propuestas; Lucas en campañas; Mateo en booking widget"*). **NO** es un `Treatment` nuevo. El `module: treatments` del frontmatter es una colisión de nombre con el módulo de Camila → debe ser `module: offer` / `offer_studio`.

---

## 2. Prior art scan (anti-duplication-refining — MANDATORIO)

| Fuente | Resultado | Decisión |
|---|---|---|
| `core/luana-core-offer-studio/` (engine) | `OfferValueLevel`, `value_level_catalog.py`, `offer.py::Offer`, `details.py::ServiceDetails`, `offer_ladder_hints.py` (filas `PROFESIONAL_SALUD`), `offer_type_preset_catalog.py`. **El catálogo + escalera de valor YA existen como ontología en el engine.** | **CONSUMIR vía Extension SDK EP-2** (preset pack medical-services). NUNCA recrear. CERO edit de engine. |
| `core/luana-core-sales-agent/.../knowledge_builder.py` | `TenantKnowledgeBuilder.build_identity()` ya lee `offer_repo` + preset metadata e inyecta el catálogo en la identidad del agente. | **El agente lee el catálogo SIN plomería nueva** — si Lisa publica servicios como Offers. Esto es el desbloqueo de canal-inbound RN-16. |
| `vitalia/` propio — `treatments/` | followup de Camila (PHI), NO catálogo. | NO reuse como catálogo. Corregir `reuse_map`. |
| `vitalia/` propio — `lisa-marca` (done) | brand voice (slot 5 BRAND_VOICE), arquetipos salud. | **CONSUMIR** — la voz de marca genera las descripciones de cada servicio (diferenciador H1). |
| `vitalia/` propio — `lisa-doctores` (developing) | tabla `vitalia_doctors` + perfiles + `specialty`. | **EXTENDER** — el link servicio↔doctor (RN-17) referencia este roster. |
| `comunify/` live | offer ladder en contexto creator (cursos/cohortes), no clínico. | Patrón análogo, no lift directo. Confirma que la ontología Offer Studio es transversal. |
| `nicolify` snapshot (frozen) | n/a clínico. | — |

**Conclusión scan:** todo lo "difícil" (catálogo vendible + escalera de valor + consumo por el agente) **ya vive en el engine**. Esta story es esencialmente **una capa de configuración brand (preset pack EP-2) + una UI de gestión + el link servicio↔doctor**. NO es net-new de dominio.

---

## 3. El objetivo de Vitalia + el público + los competidores → qué pide el catálogo

**Objetivo Vitalia (vision.md):** SaaS para clínicas electivas LatAm donde *paciente elige + marketing/captación decide + LTV justifica*. Tier 1 = dental cosmético, medicina estética, oftalmología refractiva. Diferenciador #1 (H1): **agente IA captador que CONOCE el catálogo de tratamientos + maneja objeciones + cobra anticipado**. Público que Chris precisó: clínicas que **el cliente busca y conversa** (alta consideración) — NO sick-care de seguro.

**Competidores (research 2026-06-06 · cero.ai · botclinico.cl · rendu.app · Dentalink AI · doctocliq):**
- **Table-stakes (todos):** WhatsApp-first · agenda book/reschedule/cancel · recordatorios no-show · servicio-con-duración para agendar · presupuesto (PDF, autoría staff).
- **El gap compartido:** el catálogo alimenta *scheduling* + un *PDF muerto* — **NO alimenta la conversación de venta**. Catálogo y AI son dos sistemas separados.
- **La frontera (BotClínico):** único cuyo AI **califica→cotiza→cierra** + **sigue presupuestos pendientes** — pero opaco, agencia outsourced, sin self-serve, precio detrás de una llamada.
- **Nadie hace bien:** financiamiento/cuotas presentado conversacionalmente (la palanca real de conversión en ticket alto LatAm) · el presupuesto como objeto conversacional stateful · presentación de paquetes como upsell.

**Lo que esto implica para el catálogo de Vitalia** — cada servicio (Offer) debe cargar **lo que el AGENTE necesita para vender**, no solo lo que una grilla muestra:

| Campo | Para qué | Quién lo consume |
|---|---|---|
| nombre + qué incluye (descripción **en voz de marca**, generada por lisa-marca) | el agente lo lee para explicar | Adrián, landing |
| duración | agendar correctamente | Mateo (agenda) |
| **precio o rango** ("desde $X" — alta consideración cotiza en rangos) + currency (master-data, locale tenant) | cotizar sin inventar | Adrián, Propuestas |
| especialidad / categoría | filtrar + clasificar | todos |
| **value_level** (engine: gancho gratuito → core ancla → premium) | la escalera de valor | Adrián (recomendar siguiente peldaño), Lucas |
| **link servicio↔doctor(es)** | RN-17 match servicio→especialista | **Adrián (canal-inbound)** |
| estado publicado/borrador + "visible en landing" | qué ve el paciente | landing-public, agente |
| seña/depósito + opción cuotas/financiamiento | cobro anticipado (H2) + la palanca que nadie llena | Adrián, Propuestas, Mateo (booking) |

---

## 4. La cadena de valor Lisa→Adrián (lo que Chris pidió entender)

```
lisa-marca (done) ──voz──┐
                          ▼
lisa-servicios (ESTA) = CATÁLOGO SSoT  ── Offers (Offer Studio EP-2) + value_level + link servicio↔doctor
   │                                      ▲
   │ link servicio↔doctor ── lisa-doctores (developing): roster clínico
   │
   ├─▶ Adrián canal-inbound (refined, BLOQUEADO en esta story):
   │      RN-16 entiende necesidad → mapea a servicio (TenantKnowledgeBuilder, plomería existe)
   │      RN-17 servicio → especialista disponible (tool match_service_and_specialist)
   │
   ├─▶ Adrián propuestas (idea, F4): multi-select servicios → total auto → plan de pago → e-firma
   │
   ├─▶ Adrián embudo (developed): "servicio de interés" como atributo del lead (ligero)
   │
   ├─▶ Lucas: campañas por servicio · Mateo: booking widget + duración · Camila: return-path/recall
   │
   └─▶ lisa-landing-public (idea, F6): servicios visibles en la página pública
```

**Esta story es la KEYSTONE de toda la cadena del catálogo.** Sin ella: Adrián canal-inbound no puede matchear (degradación elegante: responde + califica, sin match), Propuestas no tiene line-items, la landing no tiene servicios.

---

## 5. Recomendación PM — qué debería ir en `lisa-servicios`

**Reframe:** de "UI linda de gestión de catálogo" → **"el catálogo es el cerebro compartido que Lisa autora (on-brand, descubrible) y Adrián vende"**. Ese straddle (self-serve + equipo de agentes que SÍ vende el catálogo, con el dueño en control de voz/precio/autonomía) es el hueco vacío del mercado.

### 5.1 — Modelo: Offer Studio, no `LadderSlot`/`Treatment` nuevo
- Servicios = `Offer` de Offer Studio, registrados vía **preset pack EP-2** (`vitalia/backend/.../offer/extensions.py` — hoy stub vacío → materializar). CERO edit engine.
- La "escalera de valor" = el campo **`value_level`** que el engine YA tiene (no un `LadderSlot` con slots). La vista escalera = **visualización** de offers agrupados por `value_level`, no un modelo nuevo.
- Si falta algo real en el engine (ej. el link servicio↔doctor como port), se evalúa con `/pm-luana`; lo más probable es que el link viva brand-level (FK en la tabla brand de offers vitalia → `vitalia_doctors`).

### 5.2 — Scope MVP (lean, agente-first, sirve a Camila):
1. **Catálogo:** lista/grid + crear/editar servicio (form RHF+Zod) con los campos § 3 (incl. **value_level como SELECT simple**, link doctores multi-select, precio/rango+currency, descripción en voz de marca, publicado toggle, seña/financiamiento).
2. **Escalera de valor:** **visualización read-only** (offers agrupados por value_level mostrando la forma del embudo) — **NO drag-drop authoring** en MVP.
3. **Seed preset packs por vertical Tier-1** (dental: evaluación gratis→limpieza→ortodoncia/implante→carillas→mantenimiento; estética: valoración→peeling→botox/fillers→paquete→mantenimiento trimestral). Da head-start a Camila + algo que Adrián matchee desde día 1. Mitiga el riesgo "canvas confuso".
4. **Link servicio↔doctor** persistido (el cable que canal-inbound RN-17 necesita).
5. Detalle de servicio: N3-dyn `[offer-id]` simple (Detalle + Doctores + Plan de pago). **Sin** reviews/stats/LTV tabs ni ladder-slot workspaces en MVP.

### 5.3 — Diferido a story futura (no MVP):
- Drag-drop authoring de la escalera + ladder-slot workspaces.
- Analítica de conversión por peldaño (slot→slot).
- Reviews públicas + stats LTV per servicio.
- A/B pricing, imports bulk, AI suggested-pricing (ya eran anti-objetivos).

### 5.4 — Naming + frontmatter a corregir:
- `module: treatments` → `module: offer` (colisión con followup de Camila).
- `reuse_map` falso → corregir a "CONSUME Offer Studio engine EP-2; EXTEND lisa-marca voz + lisa-doctores roster".
- User-facing: **"Servicios"** (con "tratamiento" como categoría de servicio). Cap `lisa.servicios`.

---

## 6. Decisión abierta (gap que Chris dejó a /architect/Chris en canal-inbound)

**¿Dónde vive el cableado agéntico** (`match_service_and_specialist` + que Adrián lea el roster clínico)?
- **Recomendación PM:** `lisa-servicios` posee la **DATA** (offers publicadas + link servicio↔doctor). El **tool agéntico** `match_service_and_specialist` vive en **canal-inbound** (es brand-extension agéntica, territorio builder-agentic; canal-inbound ya lo specea). Así `lisa-servicios` queda UI-story limpia (builder-frontend/backend) y no mezcla agentic en la caja de Lisa.
- → requiere ratificación Chris (es el gap explícito) + cierre fino en `/architect`.

---

## 7. Próximo paso
Chris ratifica dirección (scope 5.2 + hogar del cableado § 6) → `/pm-vitalia` corrige checkpoint frontmatter → **`Skill(po-ux, "vitalia vitalia-fase2-lisa-servicios")`** para reescribir `01-spec.md` (mapa funcional + Gherkin + mockups per-component shell-fidelity) bajo este reframe.

## Fuentes
- Inventario código: agentes de exploración 2026-06-06 (treatments=followup · offer-studio engine · sales_agent knowledge_builder).
- `vitalia/docs/product/vision.md` · `vitalia/docs/architecture/SYSTEM-MAP.yaml` (data_ownership.Offer).
- `vitalia/docs/product/stories/vitalia-fase2-adrian-canal-inbound/` (RN-16/17 + 00-research-data-foundation.md + decisión Chris 2026-06-05).
- Research competidores: cero.ai · botclinico.cl · rendu.app · Dentalink AI · doctocliq.
- `docs/architecture/luana-platform/ADR-013-empleados-ia-auto-extension.md` (visión empleados-IA sobre un motor).

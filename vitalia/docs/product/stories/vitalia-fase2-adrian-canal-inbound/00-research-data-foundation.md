---
story_id: vitalia-fase2-adrian-canal-inbound
doc: 00-research-data-foundation
author: /pm-vitalia (investigación · Chris 2026-06-05)
date: 2026-06-05
purpose: >
  Responder cómo Adrián entiende la necesidad del paciente + presenta al especialista
  disponible (match first + callbacks) cuando NO hay servicios creados ni doctores
  cableados al agente. Estado real de cimientos de datos + decisión de secuenciamiento.
---

# 00-research — cimientos de datos para el match (servicios + doctores → Adrián)

## TL;DR

La **plomería** para que Adrián conozca servicios + equipo YA existe en el engine
(`TenantKnowledgeBuilder.build_identity()` lee Offer Studio + Brand Studio + prueba social).
Faltan la **data** (servicios = cero creados) y un **cable** (los doctores clínicos NO están
conectados al cerebro de Adrián). **Decisión Chris: secuenciar servicios primero; servicios =
Offer Studio; el match servicio→especialista pasa a in-scope de canal-inbound.**

## Estado real (3 capas)

### 1. Servicios/tratamientos — NO existen como catálogo vendible
- Vitalia tiene **cero** ofertas/servicios creados. El módulo `treatments/` shipped = solo
  *seguimiento post-tratamiento* (followup + treatment_plan), NO un catálogo vendible.
- El catálogo vendible vive en **Offer Studio** (engine `core/luana-core-offer-studio`), surfaceado
  por **`vitalia-fase2-lisa-servicios`** (state=`idea`): sub-tab **Catálogo** (nombre·descripción·
  duración·precio·**doctores**·imagen) + **Escalera de valor** (`LadderSlot`: lead-magnet/tripwire/
  core/profit-maximizer/return-path). El preset `medical-services-offer-preset` = `status: planned`.
- **Consumo por el agente:** `TenantKnowledgeBuilder.build_identity(tenant_id)` lee `offer_repo`
  (ofertas) + enriquece con preset metadata + inyecta en `agent_identity.j2`. → Apenas existan
  servicios publicados, Adrián razona sobre ellos **sin plomería nueva**.
- **Documentos por servicio** (PDFs de tratamiento): el offer schema necesitaría campo docs; Q&A
  profundo sobre el documento = ingestión a **RAG (Qdrant)** = follow-up, no bloquea el loop básico.

### 2. Doctores — ricos para PRESENTAR, sin link a servicios todavía
- `clinics.Doctor` (lisa-doctores, **developing**) tiene: `specialty` (free-text), `years_experience`,
  `languages`, `bio_public` (3 secciones resumen/formación/enfoque), `bio_links` (**adjuntos PDFs/
  imágenes**), `avatar_key`, `visible_en_landing` + disponibilidad (`availability_slot/block_model`).
- → **Suficiente para "hablarle del especialista".** Falta: el **link estructurado servicio↔doctor**
  (hoy solo el `specialty` free-text). Ese link lo trae **lisa-servicios** (campo "doctores" del
  servicio). Con él: "servicio X → doctores [A,B]"; "first-match + callbacks" = rankear por
  disponibilidad/experiencia.

### 3. ★ El gap: los doctores clínicos NO están cableados al cerebro de Adrián
- `agent_identity.j2 § Equipo` se llena con el **team de Brand Studio** (`team_members` de
  `luana_core_social_proof` — marketing), **NO** con el roster clínico `Doctor` (lisa-doctores).
- `clinics`/`Doctor` **no lo importa el sales_agent** (grep confirma). → Aunque existan doctores +
  link, Adrián no los conoce hasta **cablear la data clínica a su conocimiento**.
- **Mecánica recomendada (brand-level, NO toca engine):** un tool `match_service_and_specialist(service)`
  que lee `clinics` (doctores linkeados al servicio) + `availability` → devuelve el especialista
  disponible (first) + callbacks, con `bio_public` + adjuntos para que Adrián lo presente. (Extender el
  `TenantKnowledgeBuilder` con un port clínico sería engine → `/pm-luana`; el tool brand-level lo evita.)

## Decisión de secuenciamiento (Chris 2026-06-05)

- **Secuenciar servicios PRIMERO** (no por capas): `lisa-servicios` se construye antes que el BUILD de
  canal-inbound, para que el loop nazca con el match completo.
- **Servicios = Offer Studio** (escalera de valor), no catálogo plano.
- **Match servicio→especialista = in-scope de canal-inbound** (tool brand-level + presentación).

## Cadena de dependencias del match

```
lisa-servicios (Offer Studio: catálogo + LadderSlot + link servicio↔doctor)   [idea → refinar PRIMERO]
   └─▶ wire doctores clínicos → conocimiento de Adrián (tool match_service_and_specialist, brand-level)
        └─▶ canal-inbound: entender necesidad → match servicio → presentar especialista disponible (first+callbacks)
```

**Gap a asignar hogar (pendiente /architect/Chris):** el "wire doctores+servicios → Adrián" — ¿vive en
`lisa-servicios`, en un slice agentic propio, o dentro de `canal-inbound`? El tool es brand-extension
sales_agent (no engine).

## Referencias
- `core/luana-core-sales-agent/.../application/services/knowledge_builder.py` — `TenantKnowledgeBuilder`
- `core/luana-core-sales-agent/.../infrastructure/prompts/templates/agent_identity.j2` § Equipo (team = Brand Studio, NO clínico)
- `core/luana-core-platform/.../links/ports/social_proof.py` — `resolve_sales_agent_context` (team_members)
- `vitalia/backend/src/modules/vitalia/clinics/domain/doctor.py` — modelo Doctor (campos)
- `vitalia/docs/product/stories/vitalia-fase2-lisa-servicios/` — catálogo Offer Studio (idea)
- `vitalia/docs/product/capabilities/offer_studio/medical-services-offer-preset.yaml` — preset (planned)

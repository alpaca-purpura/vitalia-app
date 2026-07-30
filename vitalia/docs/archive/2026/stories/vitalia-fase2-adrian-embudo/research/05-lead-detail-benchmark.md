# Research 05 — Ficha de detalle del lead: benchmark de CRMs dentales/estéticos

> Investigación web 2026-06-03 (/po-ux). Pregunta: ¿cuántos tabs/secciones merece la ficha de un lead comercial (NON-PHI) y cómo crece en el tiempo? Detonante: Chris sintió que "3 tabs (Datos·Historial·Score) da muchos tabs".

## Tabla — estructura de la ficha de lead por sistema (verificado)

| Sistema | Estructura de la ficha de lead | Fuente |
|---|---|---|
| **HubSpot** (estándar de facto B2B) | 3 columnas. Izq = "About this record" (props + acciones). Centro = tabs, default `Overview` + `Activities` (timeline). **Máx 5 tabs**. Der = sidebar asociaciones (deals, conversaciones, presupuestos). | knowledge.hubspot.com/records/work-with-records |
| **Clientify** (CRM LatAm/ES) | 3 columnas. Datos del contacto (nombre/tel/origen/estado frío-caliente-cliente) · **Timeline/Historial** (emails, llamadas, WhatsApp/IG/FB, cambios de estado, **puntos de lead scoring** mezclados, filtrable) · Datos complementarios (etiquetas, etapa, presupuestos, productos de interés). | clientify.com/blog/ficha-contacto-crm-timeline-guia |
| **Pabau** (estética/dental) | "Single client card" como hub único: demografía + comunicaciones + actividad + pagos en una vista. Leads en pipeline Kanban etapas configurables. | pabau.com/blog/why-a-crm-is-critical-for-your-aesthetics-business |
| **LeadMAX** (dental) | "Lead card" dinámica: cuándo llegó, de dónde, tratamiento de interés, valor potencial, última acción, próximo paso. Activity Timeline. | lead-max.co.uk |
| **Pipedrive** | Registro = props + `Activities` timeline (llamadas/tareas/emails). | support.pipedrive.com/en/article/activities |
| **Doctocliq / Ropofy** (dental LatAm) | Chat unificado WhatsApp+IG+web, embudos, estados de lead. **Estructura granular de tabs NO documentada públicamente** — no se afirma. | ropofy.com, doctocliq.com |
| **Cero / Botclínico / Rendu / Adit** | **No verificable** — sin doc pública de UI de su ficha de lead. No se afirma nada. | — |

## Patrón común observado (la convención)

1. **Casi nadie da >3 zonas, rara vez >3 tabs.** HubSpot limita a 5 y arranca con 2. Layout dominante = **2-3 columnas** (datos · timeline al centro · asociaciones), no "muchas pestañas".
2. **El timeline es el corazón de la ficha**, no un tab secundario. Mezcla mensajes + cambios de etapa + acciones + scoring en una línea cronológica filtrable. Clientify pone el scoring *dentro* del timeline.
3. **La ficha se "llena sola"** — la lead card se actualiza dinámicamente desde el primer contacto. Vacío inicial esperado.
4. **Estado frío/caliente/cliente = campo de cabecera, no tab.**

## Recomendación aplicada al embudo de Adrián (NON-PHI)

**MVP = NO 3 tabs. Cabecera + 2 tabs. El Score NO es tab.**

- **Cabecera (siempre visible):** nombre/alias, canal, etapa, procedimiento, valor estimado, badge hot/warm/cold + score, "última actividad hace X". (= lead-card dinámica de LeadMAX + estado-cabecera de Clientify.)
- **Tab Resumen** = Datos del lead + **Score como bloque/breakdown** (no tab). Fusionar Datos+Score es exactamente la convención (Clientify, HubSpot).
- **Tab Historial (timeline)** = lo único que justifica protagonismo propio; el patrón #1 del rubro.

**Veredicto a las 3 preguntas de Chris:**
- ¿Cuántos tabs MVP? **2 máximo** (Resumen / Historial). 3 era over-engineering para un lead que arranca casi vacío.
- ¿Fusionar Datos+Score? **Sí, rotundo** — es la convención.
- ¿Historial merece tab propio? **Sí** — es el corazón de toda ficha de lead.

**Qué crece en el tiempo:** nace con cabecera + 1 evento de timeline + canal/procedimiento. Historial se llena turn-by-turn; Score aparece/sube al calificar; Presupuesto llega como evento del timeline al presentar el plan. Empty-states honestos ("aún sin presupuesto presentado").

**Mejoras de pipeline detectadas:** hot/warm/cold como dimensión separada de la etapa (la etapa es *dónde está*, el score es *qué tan vivo está*); "última acción / próximo paso" siempre en la card (LeadMAX); Kanban con "última actividad hace X" para detectar enfriamiento visual (Pabau, LeadMAX).

**No verificado (explícito):** estructura de pestañas interna de Cero, Botclínico, Doctocliq, Rendu, Adit. Lo robusto viene de HubSpot/Clientify/Pabau/LeadMAX/Pipedrive, que convergen.

## Impacto en el spec
- V3 colapsado a 2 tabs (Resumen + Historial) + cabecera resumen. RN sin cambio de numeración; § Componentes agrega `LeadSummaryHeader` + `ScoreBreakdown` (bloque).

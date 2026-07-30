# Research 06 — Pipeline: SLA por etapa, auto-freeze (hot vs cold), orden de cards

> Investigación web 2026-06-03 (/po-ux). Chris pidió proponer la regla de tiempo-en-etapa + cómo separar hot del congelado + el orden de las cards.

## TEMA 1 — Time-in-stage / SLA por etapa

**Speed-to-lead:** ventana óptima de primer contacto en leads dentales/healthcare = **0-5 min** (contactar en 5 min ~900% más probabilidad de conversión; calificar dentro de 1h = 60× más probable — HBR). *(Nota: Adrián es IA → speed-to-lead instantáneo; el SLA acá mide avance por etapa, no primer toque.)* Fuentes: webmarketingfordentists.com, healthcarecallcenter.com, protocol80.com.

**Cadencia:** leads calientes → ≥6 intentos en 48h; tibios → 4 intentos en 5 días antes de nurture. Secuencias nurturing healthcare 7-21 días. Fuentes: resources.rework.com, brandingpioneers.com.

**SLA por etapa (días-en-etapa antes de "at-risk")** — benchmarks B2B adaptados (ciclos dentales de ticket alto pueden ser más largos; ciclo total 60-90d):

| Etapa | SLA recomendado | Fuente |
|---|---|---|
| Nuevo/contacto inicial | primer toque 0-5min; calificar <1h | webmarketingfordentists, protocol80 |
| Calificación (interesado) | 7-14 días | rework deal-aging |
| Descubrimiento/necesidades | 14-21 días | rework deal-aging |
| Presupuesto presentado | 14-30 días (seguimiento Día1 y Día2) | rework, protocol80 |
| Negociación | 14-21 días | rework deal-aging |
| Cierre/agendar | 7-14 días | rework deal-aging |
| **Ciclo total** | **60-90 días** | rework deal-aging |

**Definición "stale/aging lead"** (la que dispare primero): sin actividad **14+ días** = estancado (flag a 7-14d en etapas medias/tardías; "muerto" 30+d); o tiempo-en-etapa **1.5-2.0× la mediana histórica** de la etapa. Fuentes: outreach.ai/resources/blog/sales-pipeline-ageing, umbrex.com, rework.

**→ Aplicado al spec (RN-11):** SLA verde≤ por etapa dental: Interesado 7d · Calificando 7d · Consulta agendada 5d · Plan presentado 14d. Ámbar = sobre SLA, rojo = al doble. + señal global sin-actividad 14d.

## TEMA 2 — Hot vs Cold / Frozen

**Cómo lo separan los mejores:** no borran el lead frío; lo **enfrían visualmente y/o lo sacan del pipeline activo** a un nurture/parking reactivable. Pipedrive marca el deal **rojo ("rotting")** al superar N días sin actualizarse, **configurable por etapa**; el reloj **se resetea con cualquier actividad**. GoHighLevel mueve inactivos a lista de re-engagement. Fuentes: support.pipedrive.com/en/article/the-rotting-feature, marketecs.com.

**Regla de auto-freeze propuesta (aplicada RN-13):**
> Pasa a Congelado automáticamente cuando lleva **≥14 días sin actividad/respuesta** en una etapa activa **Y** supera **1.5× la mediana** de su etapa; o duro **30+ días sin actividad**. Presupuesto presentado sin respuesta: freeze a ~15 días (cubre seguimiento Día1/Día2 + margen).

Respaldo: 14d = umbral "stalled" cross-stage; 30d = "muerto"; 1.5-2× mediana = stale. (disqualify a 7d sin contacto existe pero es agresivo para healthcare de ciclo largo.) Fuentes: outreach.ai, rework, lindy.ai, monday.com.

**Reactivación:** drip/nurture que **devuelve el lead al pipeline activo** ante señal de interés (responde/abre/agenda/visita). Sobre 5M leads fríos, ~5.2% responde y ~1.3% califica al re-engagear. Fuentes: ustechautomations.com, verse.ai, gocrm.io.

## TEMA 3 — Orden de las cards en cada columna

**Convención recomendada: por urgencia / antigüedad-en-etapa, NO por fecha de creación.** Pipedrive ordena por next activity priorizando lo que vence (vencido→hoy→sin actividad→futuro). Fuente: support.pipedrive.com/en/article/how-are-deals-ordered-in-the-pipeline-view.

- **Pipedrive:** default next-activity (urgente arriba); dropdown "Sort by" (value, close date, owner). No documenta drag manual de reordenamiento dentro de etapa.
- **HubSpot board:** re-ordena al mover record; "Board Actions → Sort" por cualquier propiedad.
- **Trello/Monday:** drag manual libre; **no recomendado como default** para pipeline comercial (rompe priorización por SLA, no escala).

**→ Aplicado al spec (RN-17):** default **antigüedad-en-etapa descendente** (lo más cerca de vencer SLA arriba) + selector "Ordenar por". **Drag manual = solo cambiar de columna (etapa), NO reordenar dentro.**

## Fuentes
webmarketingfordentists.com · healthcarecallcenter.com · protocol80.com (HBR) · resources.rework.com (deal-aging) · outreach.ai · umbrex.com · support.pipedrive.com (rotting + ordering) · marketecs.com · brandingpioneers.com · lindy.ai · monday.com · ustechautomations.com · verse.ai · gocrm.io · knowledge.hubspot.com (board view).

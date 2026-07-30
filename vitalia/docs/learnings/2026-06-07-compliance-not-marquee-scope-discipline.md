---
brand: vitalia
date: 2026-06-07
slug: compliance-not-marquee-scope-discipline
promotable: candidate
applies_to_other_brands_potentially: [comunify, nicolify, lupulo]
target_core_package: null
origin: refinamiento vitalia-fase2-lisa-compliance (/pm-vitalia → /po-ux)
---

# Compliance no es feature marquee — disciplina de scope vs core agéntico

## Qué aprendimos

Al refinar la historia de la "consola de compliance" de Lisa, el scope se infló a nivel Q4 (gestión full de consentimientos + DSAR + access-log + alertas accionables) **antes de que el core agéntico que gana estuviera construido**. Chris frenó. La revisión de 5 competidores LatAm (cero.ai, botclinico.cl, rendu.app, dentalink contact-center, doctocliq) confirmó tres hechos:

1. **Todos lideran con el agente IA de captación/agenda 24/7** (WhatsApp/voz) — el campo de batalla real, = H1 de la visión Vitalia (#1 ROI).
2. **Ninguno vende compliance como feature.** Lo máximo: un disclaimer legal en footer + "consentimiento informado" como **formulario** (doctocliq) — que Vitalia ya tiene shipped.
3. La propia visión ubica compliance multi-país en **H4 / roadmap Q4** ("te ahorramos el legal" → desbloquea **mid-market** Persona 2), NO en el MVP Q1 (Persona 1 = "setup 1 día, agente que responde+agenda+cobra").

## Why

El enforcement técnico de compliance (audit log, dual-filter, firewall PHI, pgcrypto) es **table-stakes invisible** que ya corre por detrás — NO una vitrina que venda. Construir DSAR/consent-console antes que el agente captador = "construir el airbag antes que el motor". El valor (y la diferenciación) está en el agente; compliance es plumbing hasta que (a) hay actividad agéntica real que mostrar y (b) llega el comprador mid-market que sí lo pide.

## How to apply

- **Antes de refinar una superficie "de soporte/admin/compliance/settings":** chequear (1) qué venden los competidores al respecto (si nadie lo vende como feature → es plumbing, no marquee), y (2) dónde la ubica la visión en el roadmap (si es Q4/mid-market → no compite por turno con el core Q1).
- **El ángulo agéntico no justifica adelantar la vitrina:** una "vista de confianza para delegar en agentes" solo tiene valor cuando los agentes están vivos y hay actividad que mostrar.
- **Cuando el scope se infla en refinamiento:** parar, traer evidencia (competidores + visión), y cortar — parkear con un RESUME doc que preserve lo aprendido en vez de tirar el análisis.
- Sospechá de respuestas "(c) full" en interrogatorios de refinamiento de superficies no-core: suelen empujar a scope de fase tardía.

## Origen

Refinamiento `vitalia-fase2-lisa-compliance` (2026-06-07). Reframe A (vista de confianza) documentado + story parkeada con `RESUME-refinement.md`. Ver `vitalia/docs/product/stories/vitalia-fase2-lisa-compliance/`.

# Vitalia — Product Vision

**Brand:** Vitalia (luana-platform).
**Fecha snapshot:** 2026-05-27.
**Owner:** `/pm-vitalia` (mantiene este file actualizado).
**Status:** v1 cementado from research 2026-05-27 (Chris ratificado).

> Vitalia es la respuesta de luana-platform al mercado de profesionales clínicos electivos en LatAm. NO competimos en emergencias, NO competimos en atención obligatoria; competimos donde **paciente elige + marketing/captación decide + recurrencia o LTV alto justifica inversión SaaS**.

---

## 1. Verticales target (Tier 1-3)

Filtros aplicados: (1) paciente ELIGE el tratamiento (no urgencia), (2) marketing digital es decisivo en la conversión, (3) recurrencia mensual/trimestral o LTV alto justifica inversión en CRM + agente de captación.

### Tier 1 — Foco MVP (3 verticales)

| Vertical | Razón electiva | LTV típico | Canales captación | Regulación específica |
|---|---|---|---|---|
| **Odontología cosmética** (blanqueamiento, ortodoncia invisible, carillas, implantes) | Estética + autoestima; tickets altos (USD 800-8K). Mercado LatAm USD 2.39B (2024) → 3.73B (2034), CAGR 5.1% | USD 1.5K-6K/tratamiento; mantenimiento 6-18 meses | Instagram (antes/después), Google Ads "ortodoncia invisible [ciudad]", referidos, WhatsApp | HCE obligatoria + consentimiento informado digital |
| **Medicina estética** (botox, fillers, peelings, hilos tensores, láser) | 100% electivo, alta sensibilidad precio + branding. Mercado dispositivos LatAm USD 758M (2024) → 1.28B (2032), CAGR 6.8% | USD 400-1.8K/sesión; recurrencia 4-12 meses → LTV 3-5 años: USD 5K-15K | Instagram (pre/post carrusel), TikTok, WhatsApp Business, referidos | Dispositivos clase II/III (ANMAT/COFEPRIS/INVIMA) + consentimiento riesgos |
| **Oftalmología refractiva** (LASIK, lentes intraoculares premium, blefaroplastia) | Decisión deliberada, paciente investiga semanas/meses. Mercado LASIK USD 2.25B (2025E) → 3.77B (2033) | USD 1.2K-4.5K/ojo; oneshot + referrals familiares | Google Ads (alto CPC), email nurturing, financiamiento on-site, ferias salud | HCE + consentimiento quirúrgico |

### Tier 2 — Expansión 6-12 meses (4 verticales)

| Vertical | LTV típico | Diferenciador |
|---|---|---|
| **Psicología clínica** | USD 1K-6K (6-24 meses, sesiones semanales) | Recurrencia altísima post-pandemia; confidencialidad reforzada |
| **Psiquiatría** | USD 1.5K-5K (12-36 meses, sesiones mensuales + receta) | Receta electrónica regulada (psicotrópicos) |
| **Dermatología clínica + estética** | USD 2K-8K (12-24 meses, mix recurrente + electivo) | Hybrid acquisition + recurrence |
| **Nutrición clínica** (incluye boom GLP-1/Ozempic) | USD 600-2.5K (6-18 meses, quincenal/mensual) | Sin regulación pesada; boom semaglutida |

### Tier 3 — Oportunista 12-24 meses (3 verticales)

| Vertical | LTV típico | Diferenciador |
|---|---|---|
| **Fisioterapia/Kinesiología** | USD 250-1.2K/tratamiento (paquetes 10-20 sesiones) | Recurrencia 2-3x/semana × 4-12 semanas |
| **Medicina capilar/Trasplante** | USD 2K-5K (one-shot + follow-ups) | Turismo médico (MX/CO compiten con Turquía) |
| **Fertilidad asistida/IVF** | USD 8K-24K (2-3 ciclos típicos) | Turismo médico (MX USD 4-8K vs USA 12-25K) |

### Verticales DESCARTADOS

- Cardiología, oncología, traumatología pediátrica → no electivos
- Medicina emergencia, UCI → no marketing
- Audiología, podología, terapia ocupacional → mercado chico, evaluar fase 2

---

## 2. Marco regulatorio HIPAA-lite LatAm

LatAm NO tiene una HIPAA equivalente unificada. Adoptó frameworks GDPR-inspired (no healthcare-specific) + leyes de derechos del paciente + normas técnicas HCE por país. Vitalia debe cumplir el "stack" de los 6 países objetivo:

| País | Ley protección datos | Ley derechos paciente / HCE | Obligaciones SaaS Vitalia |
|---|---|---|---|
| **Argentina** | Ley 25.326 (Habeas Data; adecuación UE) | Ley 26.529 (Derechos Paciente, HCE válida desde 2009) | HCE íntegra/autenticable/inalterable; firma digital; paciente dueño de datos; encripción + roles; AAIP autoridad |
| **México** | LFPDPPP (Datos Personales Particulares) | NOM-024-SSA3-2012 (Sistemas Info Registro Electrónico Salud) + NOM-004-SSA3-2012 (Expediente Clínico) | Datos clínicos = sensibles; aviso privacidad; ARCO; certificación NOM-024; logs auditoría; firma autógrafa/electrónica/digital |
| **Colombia** | Ley 1581/2012 + Decreto 1377/2013 | Resolución 1995/1999 + Resolución 1888 (HCE 2026); Ley 23/1981 (ética médica) | Consentimiento previo/libre/expreso/informado digital; SIC autoridad; retención mín 20 años (5 gestión + 15 archivo); logs + encripción at-rest/in-transit; 2FA |
| **Perú** | Ley 29733 (Protección Datos Personales) | Ley 26842 + RENHICE + DS 020-2025-SA | HCE estructurada ICD-10; firma electrónica validez legal; RBAC; logs inmutables; exportable RENHICE; backups + DR |
| **Chile** | Ley 19.628 (Datos Personales) | Ley 20.584 art. 12 (Derechos Pacientes; ficha clínica obligatoria) | Ficha clínica = sensibles; consentimiento informado; nueva Ley 21.719 (GDPR-like) en discusión |
| **Brasil** | LGPD (Lei 13.709/2018) | Lei do Prontuário + Resoluções CFM (2.314/2022 telemedicina) | Saúde = sensíveis; bases legais específicas; DPO obligatorio; multas 2% facturación / R$ 50M; ANPD autoridad; retención + finalidad documentadas |

### Denominador común — obligaciones SaaS día 1

1. **Consentimiento informado digital** (timestamp + firma electrónica + plain language + opción retirar)
2. **Retención 10-20 años** HCE (varía país)
3. **Derecho acceso/rectificación/supresión** (ARCO MX / Habeas Data CO) endpoints API + UI self-service
4. **Encripción at-rest AES-256 + in-transit TLS 1.3**
5. **Logs auditoría inmutables** (quién/qué/cuándo/dónde/razón)
6. **RBAC roles** (médico tratante / asistente / admin / paciente)
7. **Firma electrónica/digital** validez legal HCE
8. **Data residency considerations** (BR + MX preferencia regional)
9. **DPO/Responsable tratamiento** designación + flujos
10. **Notificación brecha datos** obligatoria (BR + CO + PE)

### Implicación arquitectural

"HIPAA-lite" NO es checkbox; es módulo transversal `core/luana-core-compliance/` con policies configurables por país-tenant + auditoría inmutable + DSAR (Data Subject Access Request) endpoints + retention policies. Alineado con doctrina del repo (compliance module en CLAUDE.md tabla brand→core).

---

## 3. Landscape competidores SaaS clínicos LatAm

### Resumen tabla

| Competidor | Verticales | Pricing | Strengths | Weaknesses |
|---|---|---|---|---|
| **Doctoralia (Pro/Clínicas)** | General + dental/estética/salud mental | AR USD 80-250/mes; MX USD 1.4K setup + USD 100/mes + variable por lead | SEO marketplace, agenda 24/7, recordatorios | Marketing engañoso (no es captador real); precio percibido caro; comisión pago 4x tarjeta; soporte deficiente; sin agente IA; one-size-fits-all |
| **Curve Dental** | Dental USA | USD 400-600/mes | Eligibility+, all-in-one, AI automation, charting/imaging | Foco USA; sin marketing nativo LatAm; sin WhatsApp/agente IA |
| **DentalLink/Dentrix/Eaglesoft** | Dental tradicional | Variable on-premise | Funcionalidad clínica madura | Stack legacy, sin cloud nativo, UX desactualizada |
| **Mindbody/Booker** | Estética/spa/fitness | USD 99-500+/mes | Booking robusto, marketplace, multi-location, pagos | Foco USA/EU; pricing alto LatAm; UX wellness no clínica; sin HCE médica regulatoria LatAm |
| **Booksy** | Estética/belleza/peluquería | USD 30-80/mes | Booking app excelente, marketplace | Sin HCE; reporting débil; sin compliance |
| **SaludTools (CO)** | Médico general LatAm | USD 50-150/mes | Compliance Ley 1581 CO, consentimiento digital, HCE local | Solo CO; sin verticalización; sin agente IA |
| **Medesk** | Médico general | USD 50-200/mes | All-in-one PMS+EHR+CRM, telemedicina | No vertical electivo; sin agente IA WhatsApp/Insta |
| **TuoTempo/AgendaPro/ReservaSimple/Klinikare** | Booking + agenda LatAm | USD 20-100/mes | Mercado Pago, WhatsApp recordatorios, cobro anticipado | Solo booking; no HCE robusta; no funnel marketing; no agente IA |
| **Holaa/Mindkar** | Psicología | Variable | Vertical salud mental, telesalud nativa | Nicho; sin marketing engine |
| **Nutrium/Nutrimind** | Nutrición | USD 30-80/mes profesional | Diet planning, tracking | Foco nutrición; sin marketing engine; sin agente |

### Patrones de gap identificados

1. **NINGÚN competidor combina** captación digital + agenda + HCE + seguimiento post-tratamiento en una sola plataforma vertical electiva
2. **Marketing/funnel es el gap más grande**: Doctoralia = directorio, Mindbody/Booksy = booking, SaludTools/Medesk = HCE. Ninguno tiene agente IA captador desde DM/WhatsApp que califique + agende + cobre anticipado
3. **Compliance regulatorio fragmentado**: USA (Curve, Mindbody) no cumple LatAm; locales (SaludTools, AgendaPro) cumple su país pero no multi-país
4. **Seguimiento post-tratamiento ausente**: SaaS olvidan al paciente post-sesión. Sin nurturing recompra (botox 4-6 meses, ortodoncia 6 meses, control psiquiátrico mensual)
5. **Agente IA conversacional**: bots WhatsApp existen pero horizontales, no verticales clínicos con catálogo tratamientos + objection handling + cobro anticipado

---

## 4. Diferenciadores Vitalia (hipótesis cementadas)

### H1 — Agente IA captador multi-canal verticalizado

**Tesis:** WhatsApp penetración LatAm >90% (BR 99%, CO 94%, MX 93%, AR 90%). Clínicas reciben 120-150 mensajes/día cross-canal, 65% resolvibles sin humano. Bots horizontales (Cari, Aurora) no entienden "fillers labiales vs hilos tensores" ni objection handling clínico. Vitalia ofrece agente conocedor del catálogo tratamientos del tenant + scripts calificación específicos por vertical + handoff humano cuando necesario.

**vs Doctoralia:** Doctoralia promete "te conseguimos pacientes con SEO" (directorio). Vitalia ejecuta captación 24/7 desde DMs reales que YA llegan a la clínica.

**Impacto:** captura demand existente desperdiciada (#1 ROI clínica).

### H2 — Reservas prepagadas + Mercado Pago/Stripe nativo

**Tesis:** Cobro anticipado reduce no-shows hasta 80% (ReservaSimple data). Mercado Pago = estándar LatAm. Doctoralia tiene pagos pero comisiones 4x tarjeta + UX mala. Competidores USA no integran Mercado Pago. Vitalia ofrece: seña % o monto fijo configurable, políticas cancelación con reembolso parcial/total automatizadas por especialidad, waitlist automática reagenda slot liberado.

**Diferencial:** no es add-on, es default workflow + agente IA lo cobra automáticamente en conversación.

**Impacto:** ROI inmediato medible (1 no-show evitado = paga plan mensual).

### H3 — Recurrence engine post-tratamiento

**Tesis:** Botox 4-6 meses, fillers 8-12, ortodoncia mantenimiento 6, psicología semanal/quincenal, psiquiatría mensual, nutrición quincenal. NINGÚN competidor SaaS LatAm tiene "recurrence engine" que dispare contacto programado pre-vencimiento con copy verticalizado + agenda directa. Vitalia automatiza: día +90 botox → DM "Tu botox cumple 4 meses, ¿refuerzo?"; día +6 meses ortodoncia → "Control programado"; psicología → "Tu próxima sesión semana próxima, confirmá horario".

**Diferencial:** transforma one-shot en LTV de 3-5 años automáticamente.

**Impacto:** eleva LTV 3-5x (ROI 12 meses, sticky).

### H4 — Compliance multi-país out-of-the-box

**Tesis:** SaludTools cumple CO, Medesk cumple EU, Curve cumple USA. Ninguno cumple los 6 países LatAm con policies configurables. Vitalia ofrece módulo `core/luana-core-compliance/` con policies por país (consentimiento templates, retention, DSAR endpoints, audit logs, encripción defaults), permitiendo clínica multi-sede (MX+CO+CL) operar con UNA plataforma + cumplimiento automático.

**Diferencial:** B2B argumenta "te ahorramos el legal" — venta a cadenas regionales.

**Impacto:** desbloquea ventas mid-market regional.

### H5 — Voz/voice + recordatorios omnichannel personalizados

**Tesis:** Pacientes mayores (oftalmología, fertilidad, psiquiatría adulta) responden mejor a llamada/voz. Pacientes jóvenes (dental cosmético, estética, psicología) prefieren DM. Vitalia ofrece policy engine: agente decide canal según perfil paciente (edad + canal captación + último canal usado) + horario (voz solo de día, DM 24/7). Integración Google Calendar/Outlook (no reemplaza, orquesta).

**Diferencial:** vs Doctoralia (email/WhatsApp/push genérico), Vitalia personaliza canal por paciente automáticamente.

**Impacto:** adopción pacientes 50+ años (oftalmología, psiquiatría).

### Ranking impacto comercial

1. Agente IA captador verticalizado → #1 ROI clínica
2. Reservas prepagadas + Mercado Pago → ROI inmediato medible
3. Recurrence engine → LTV 3-5x (12 meses, sticky)
4. Compliance multi-país → desbloquea mid-market regional
5. Voz/voice + omnichannel → adopción seniors

---

## 5. Buyer personas

### P1 — "Dra. Camila" — Dueña Solo Practice arrancando

- **Demografía:** 28-38 años, mujer, posgraduada (estética/psicología/odontología cosmética). Acaba de abrir consultorio propio o alquila box. Ciudades secundarias o barrios premium capitales LatAm.
- **Contexto:** 30-80 pacientes/mes. Maneja todo sola (Instagram, WhatsApp a las 11pm, agenda Google Calendar, cobros mixtos, facturación en planilla).
- **Pain points:** pierde 30-40% DMs por no alcanzar; 25% no-show sin seña; ROI Instagram Ads difuso; recurrencia perdida (olvida que paciente X se hizo botox en marzo).
- **Valora:** setup 1 día, agente IA responde + agenda, cobro anticipado configurable, precio <USD 80/mes starter.
- **Objeción principal:** "¿Y si agente IA suena robótico y arruina mi marca?" → permitir tono voz personalizable + supervisión humana.
- **CAC:** USD 200-400. **LTV:** USD 1K-2.5K (12-30 meses).

### P2 — "Dr. Fernando" — Dueño Clínica Multi-Doctor establecida

- **Demografía:** 40-55 años, dueño/socio clínica 4-12 profesionales. Ciudad principal LatAm. Facturación USD 30K-150K/mes.
- **Contexto:** secretarias/recepcionistas. Usa Doctoralia/SaludTools/Medesk/planilla mejorada. Marketing tercerizado (USD 1K-3K/mes), descontento.
- **Pain points:** atribución marketing rota; recepcionistas saturadas WhatsApp/Insta; no-shows 15-25%; compliance paranoia sin nunca consultar abogado; sin recurrence engine; sistemas fragmentados.
- **Valora:** all-in-one (agenda+HCE+marketing+cobros), multi-doctor con roles, dashboard atribución por especialista+canal, compliance automático, agente IA descongestiona recepción.
- **Objeción principal:** "Migrar de [sistema actual] me da pánico. Profesionales resistentes." → onboarding asistido + import HCE legacy + training in-app.
- **CAC:** USD 1.5K-3K. **LTV:** USD 15K-45K (24-60 meses). **Sticky alto** post-integración.

### P3 — "Lic. Mariana" — Profesional Individual arrancando

- **Demografía:** 26-36 años, mujer (~80% segmento), recién graduada o 1-3 años post-grado (psicología/nutrición/fisioterapia). Trabaja desde casa, box compartido, online. Post-pandemia >50% online en psico/nutrición.
- **Contexto:** 10-40 pacientes/mes, tickets USD 30-80. Margen ajustado. Marketing 100% orgánico. Cobra Mercado Pago/PayPal/Transferencia.
- **Pain points:** sin presupuesto USD 50+/mes; doble-booking Calendly+WhatsApp; notas en cuaderno (riesgo compliance psicología); marketing abruma; recurrencia perdida.
- **Valora:** plan freemium o <USD 30/mes; móvil-first; HCE simple compliant; cobro anticipado psico (cancela <24h = cobra igual); recurrence sutil.
- **Objeción principal:** "Otro SaaS más que abandonaré en 2 meses." → demostrar ROI primera semana.
- **CAC:** USD 50-150. **LTV:** USD 300-1.5K (6-18 meses; churn alto pero volumen).

### Distribución TAM (estimada)

| Persona | % volumen tenants | % revenue | ARPU mensual |
|---|---|---|---|
| Camila | 50-60% | 25-30% | USD 50-80 |
| Fernando | 10-15% | 50-60% | USD 250-600 |
| Mariana | 25-35% | 10-15% | USD 20-40 |

---

## 6. GTM strategy

- **Beachhead:** Persona 1 (Camila) en Tier 1 verticales (dental cosmético + estética). Pricing USD 60/mes. PLG + Instagram orgánico (clínicas referidas).
- **Mid-market expansion:** Persona 2 (Fernando) tras 100+ Camilas. Demos + sales-led. Onboarding asistido. Pricing USD 300-600/mes.
- **Volume play:** Persona 3 (Mariana) tier freemium para brand awareness. Pricing USD 25-40/mes.

---

## 7. Roadmap implicaciones

Esta vision dicta priorización feature:

1. **Q1 Tier 1 MVP:** agente IA captador WhatsApp (dental + estética + oftalmología) + reservas prepagadas Mercado Pago + HCE basic AR/MX/CO. → cumple H1+H2+H4 parcial.
2. **Q2 expansion:** recurrence engine + Tier 2 verticales (psicología + dermatología + nutrición). → cumple H3.
3. **Q3 mid-market:** multi-doctor roles + dashboard atribución marketing + onboarding asistido (Persona 2 target).
4. **Q4 compliance + voice:** Compliance multi-país completo (6 países) + voice agent (Tier 1 ampliado). → cumple H4 + H5.

Roadmap detallado: `vitalia/docs/product/outcomes/` (owner `/pm-vitalia`).

---

## 8. Sources (research 2026-05-27)

Mercado / verticales:
- [Mercado odontología cosmética LatAm 2024-2034](https://www.informesdeexpertos.com/informes/mercado-latinoamericano-de-odontologia-cosmetica)
- [Mercado dispositivos estéticos LatAm](https://www.databridgemarketresearch.com/es/reports/latam-aesthetic-devices-market)
- [Cirugía refractiva LASIK 2025-2033](https://www.snsinsider.com/reports/mercado-de-cirugia-ocular-lasik-9361)
- [Marketing oftalmológico LatAm](https://franjaocular.com/marketing-en-el-sector-oftalmologico/)
- [Tendencias estética 2026 LatAm](https://lanotaeconomica.com.co/movidas-empresarial/tendencias-de-la-nueva-estetica-pacientes-buscan-tratamientos-mas-naturales-y-preventivos-en-2026/)
- [IVF Mexico medical tourism 2026](https://ovu.com/fertility-insights/ivf-in-mexico-2026-medical-tourism-costs-fertility-clinic-guide)

Regulación:
- [Argentina Ley 26529 HCE](https://www.argentina.gob.ar/justicia/derechofacil/leysimple/salud/historia-clinica-electronica)
- [México NOM-024-SSA3-2012](https://platiica.economia.gob.mx/normalizacion/nom-024-ssa3-2012/)
- [México LFPDPPP guía clínicas](https://www.lunasalud.mx/blog/proteccion-datos-pacientes-mexico-ley-federal-guia-clinicas)
- [Colombia Ley 1581 + Res 1995](https://www.saludtools.com/articulo/proteccion-datos-pacientes-colombia-ley-1581)
- [Perú normativa HCE 2026](https://davix.ai/en/blog/normativa-historia-clinica-electronica-peru-2026/)
- [Chile Ley 20.584 art. 12](https://www.bcn.cl/leychile/Navegar?idNorma=1039348&idParte=10078337&idVersion=2019-12-13)
- [Brasil LGPD na saúde](https://www.amplimed.com.br/blog/lei-geral-protecao-dados-area-medica/)

Competidores:
- [Doctoralia AR precios](https://pro.doctoralia.com/ar/precio)
- [Doctoralia MX precios/cobros](https://pro.doctoralia.com.mx/precios/clinicas)
- [Doctoralia opiniones Capterra/GetApp](https://www.getapp.com/customer-management-software/a/doctoralia-pro/)
- [Curve Dental pricing](https://www.curvedental.com/pricing)
- [Mindbody Pricing](https://www.saasworthy.com/product/mindbody)
- [Booksy alternatives 2026](https://webflow.glossgenius.com/blog/booksy-alternatives)
- [Mercado Pago consultorios cobro seña](https://dpreservas.com/blog/articulos/mercadopago-consultorios-cobro-sena-sesion-paso-a-paso.html)
- [ReservaSimple turnos LatAm](https://www.reservasimple.com/sistema-turnos-reservas-citas-latinoamerica)
- [WhatsApp Business API clínicas LatAm](https://www.aimoova.com/post/whatsapp-business-api-para-clinicas-automatizacion-leads-citas)
- [WhatsApp salud LatAm Davix](https://davix.ai/es/blog/whatsapp-canal-salud-latam/)
- [SaludTools consentimiento digital CO](https://www.saludtools.com/articulo/consentimiento-informado-digital-colombia)
- [Tendencias IA conversacional WhatsApp LatAm 2026 Chattigo](https://blog.chattigo.com/whatsapp-business/tendencias-de-ia-conversacional-en-latinoam%C3%A9rica-para-2026-el-auge-del-agente-aut%C3%B3nomo-en-whatsapp)

---

## Maintenance

Este file lo actualiza `/pm-vitalia` cuando:
- Nuevo vertical Tier 1/2/3 detectado validar (research + Chris ratify)
- Nuevo país regulatorio (expansión LatAm)
- Nuevo competidor relevante detectado
- Nueva hipótesis diferenciador validada (post user research)
- Cambio buyer persona (descubrimiento post-ventas)

Update workflow: refresh file + cementar learning si surge insight (`docs/learnings/` o `vitalia/docs/learnings/`) + commit en mismo PR.

## Referencias

- `vitalia/CLAUDE.md` — overlay brand auto-load
- `vitalia/docs/product/checkpoint.md` — state brand
- `vitalia/docs/product/outcomes/` — roadmap detallado
- `core/luana-core-compliance/` (cuando se materialice) — HIPAA-lite engine
- `.claude/rules/anti-duplication-refining.md` — prior-art scan obligatorio refining

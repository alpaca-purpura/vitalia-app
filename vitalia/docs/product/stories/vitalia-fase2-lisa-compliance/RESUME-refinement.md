# RESUME — refinamiento vitalia-fase2-lisa-compliance

> **Para retomar en una conversación nueva.** Leé este archivo + `checkpoint.md` + `00-pm-recommendation.md` y tenés TODO el contexto sin re-investigar.
> **Estado:** `parked` (2026-06-07, por Chris). **Última sesión:** `/pm-vitalia` → `/po-ux`, 2026-06-07.

---

## Cómo retomar (3 pasos)

1. `cat vitalia/docs/product/stories/vitalia-fase2-lisa-compliance/{checkpoint.md, 00-pm-recommendation.md, RESUME-refinement.md, chris-input.md}`
2. Verificá precondiciones de **unpark** (abajo). Si no se cumplen → la story sigue parkeada, no la refinás todavía.
3. Si se cumplen → `/pm-vitalia` unpark (`parked → refining`) → `/po-ux vitalia vitalia-fase2-lisa-compliance`. Arrancás en el **Batch 2** (preguntas abiertas abajo) — el Batch 1 ya está decidido.

---

## Precondiciones de UNPARK (las dos)

1. **Core agéntico vivo** — `canal-inbound` + `embudo` + (`outbound`/`propuestas`) construidos y con **actividad real** (bloqueos PHI de Adrián, consentimientos solicitados, accesos a PHI). Sin actividad, la vista de confianza no tiene qué mostrar.
2. **Mid-market a la vista** — se acerca Persona 2 ("Dr. Fernando", clínica multi-doctor) o un cliente pide compliance explícito. La visión ubica compliance en **H4 / Q4**, no en el MVP Q1 (Persona 1 "Camila").

Mientras tanto: el enforcement técnico (audit log, dual-filter, firewall PHI, pgcrypto) **ya corre live en infra** — no necesita vitrina.

---

## Por qué se parkeó (evidencia, no opinión)

Chris frenó el over-scope. Revisamos 5 competidores LatAm. Hallazgo:

| Competidor | Vende fuerte | Compliance como feature |
|---|---|---|
| botclinico.cl | Agentes IA voz+chat (llaman/califican/agendan 24/7) | ❌ nada |
| rendu.app | Agente WhatsApp IA + agenda + ficha + inbox + CRM | ❌ solo disclaimer "no certificado" |
| dentalink (contact center IA) | Asistente IA 24/7 WhatsApp+llamadas+agenda+pagos | ❌ solo "nos ocupamos de la seguridad" |
| doctocliq | PMS + IA WhatsApp + ficha + facturación + marketing | 🟡 solo "consentimiento informado" = formulario (Vitalia YA lo tiene shipped) |
| cero.ai | AI agent clínico (SPA, no leíble al fetch) | n/a |

**3 hechos duros:** (1) todos lideran con el **agente IA de captación 24/7** (= H1 de la visión, #1 ROI); (2) **ninguno** vende una consola de compliance (cero DSAR, cero audit-viewer, cero retention editor); (3) la visión Vitalia pone compliance en **Q4 / mid-market**, no en el MVP. → Construir DSAR/consent-console antes que el agente captador = construir el airbag antes que el motor.

---

## Decisiones YA tomadas (Batch 1 — NO re-preguntar)

Dirección **A** (vista de "Confianza y cumplimiento" del dueño, NO consola técnica). Más:

| # | Pregunta | Respuesta Chris |
|---|---|---|
| 1 | Ángulo agéntico | **(c)** accionable + entry conversacional, PERO solo dejar los **cables** (acciones = endpoints reusables Plano 2 para que Valeria los invoque luego). **NO** diseñar el flujo copilot ahora. |
| 2 | Profundidad consentimientos | **(c)** gestión full: lista/buscar + reenviar + revocar + ver evidencia de firma + **DSAR** |
| 3 | Log de acceso PHI | **versión dueño** acá (legible, masked); el crudo técnico → Configuración→Avanzado |
| 4 | Attestation PDF | **diferido** → story creada `vitalia-lisa-compliance-attestation` (idea) |

> ⚠️ Nota de disciplina: las respuestas (c)+(c) son las que inflaron el scope a nivel Q4. Al retomar, **reconsiderar** si se entra con scope **mínimo (B)** primero (1 panel read-only que lee data shipped) y se difiere consent-mgmt/DSAR a su propia story. Chris quedó alineado con cortar fuerte.

---

## Preguntas ABIERTAS (Batch 2 — quedaron sin responder, retomar acá)

5. **RBAC** — ¿solo `admin_clinic` (dueño) con acceso full, resto sin acceso? ¿o `doctor`/`nurse` ven algo read-only?
6. **DSAR (ARCO/Habeas Data) — acotar:** (a) registro + acceso (export datos paciente + marcar atendida) · (b) +supresión · (c) full ARCO. Recomendación previa: **(a)** para MVP.
7. **Catálogo de alertas accionables** — ¿cuáles en MVP? (consent pendiente/vencido→reenviar · bloqueos PHI Adrián→ver · retención estado · DSAR abiertas→atender).
8. **Log acceso PHI "versión dueño"** — formato: "Dra. López accedió al historial de M.G. el 6/jun 14:30" (staff + paciente masked + fecha + acción, sin payload técnico), filtrable por paciente/fecha/staff, solo-lectura. ¿OK?

(Batch 3 nunca se llegó: estados visuales · microcopy · responsive · a11y · mockup.)

---

## Scope (reframe A) — IN / OUT / spun-out

**IN (vista de confianza, cuando se unparkee):** panel "tus agentes operan seguro" (lee data shipped) · resumen consentimientos (profundidad a decidir B vs full) · log acceso PHI versión dueño · banner HIPAA-lite · postura 1-línea. NO 7 semáforos técnicos.

**OUT / spun-out:**
- Attestation PDF → story `vitalia-lisa-compliance-attestation` (idea, dep hard a esta).
- Editor de política de retención → `vitalia-fase2-config-avanzado` (ya anotado en su checkpoint).
- Checks técnicos profundos + audit log crudo → Configuración→Avanzado / infra.
- Cron de retención (hoy stub) → story backend infra `seguridad-cumplimiento`.
- Gate opt-out/consent en outbound de Adrián → `vitalia-fase2-adrian-outbound` (ya anotado §7).
- `vitalia-compliance-audit-rbac-gap` → **dropped** (ya fixeado por hotfix `18e10822`).

---

## Data sources (todo SHIPPED — la vista solo LEE)

| Necesita | Fuente | Estado |
|---|---|---|
| Shell + nav slot `lisa/compliance` | `agent-catalog.ts:231` + `CompliancePlaceholder.tsx` | ✅ existe (placeholder) |
| audit log | infra `seguridad-cumplimiento` (`vitalia_audit_log`) | ✅ live |
| consent records | `ConsentService` + `vitalia_consent_records` (HMAC, snapshot inmutable) | ✅ live |
| bloqueos PHI | `inbox/SendMessageService` + `PhiChannelPolicy` (activity `compliance_block_outbound_phi`) | ✅ shipped |
| opt-out | `PatientConsentService` | ✅ live |
| legacy UI a refactorizar | `features/vitalia/components/{compliance-page-client, compliance-stats-cards, consent-signature-modal, compliance-event-row}` + schemas + `use-compliance-events` | ✅ existe (audit-viewer admin) |

**Cap model al cerrar:** cap nueva user-facing `lisa.compliance` que **LEE** la cap infra `seguridad-cumplimiento.compliance` (NO la reemplaza). Release **F3**. Patrón **ADR-vitalia-004** (sub-tab simple, sin N3).

---

## Archivos de esta story (mapa)

- `checkpoint.md` — estado parked + reframe A + scope + AC draft + frontmatter.
- `00-pm-recommendation.md` — análisis completo PM (verdad de campo + inconsistencia 3 vías + los 3 cortes).
- `RESUME-refinement.md` — **este archivo** (punto de entrada para retomar).
- `chris-input.md` — trail conversacional turn-by-turn con verdicts.

## Learning relacionado

- `vitalia/docs/learnings/2026-06-07-compliance-not-marquee-scope-discipline.md`

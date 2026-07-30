---
story_id: vitalia-fase2-lisa-compliance
type: ui-story
agent_owner: lisa
map_zone: agentes
map_box: lisa
module: compliance
capability: lisa.compliance
state: parked
architecture_pattern: ADR-vitalia-004
last_modified: '2026-06-07T03:40:00.000Z'
ratified_by_chris: false
parked_date: 2026-06-07
parked_by: chris
parked_reason: >-
  Evidencia competidores (cero.ai/botclinico/rendu/dentalink/doctocliq) + visión: los 5
  lideran con el agente IA de captación 24/7 (H1) y NINGUNO vende compliance como feature.
  La visión ubica compliance en H4/Q4 (mid-market). El core agéntico que gana aún no está
  construido. El enforcement técnico (audit/dual-filter/firewall PHI) ya corre live en infra;
  no necesita vitrina hasta que los agentes estén vivos + se acerque mid-market. El reframe A
  (vista de confianza) + scope (consent-mgmt/DSAR/access-log) queda documentado para retomar.
parallel_safe: true
priority: high
estimated_dev_days: 2-3
release: F3
cap_target: lisa.compliance
cap_change_type: new
reads_cap: seguridad-cumplimiento.compliance
parent_story: null
scope_reframe:
  date: 2026-06-07
  direction: A
  ratified_by_chris: true
  rationale: >-
    Reencuadre bajo visión agéntica + SYSTEM-MAP v2. La story vieja era una consola
    pesada (semáforo técnico + editor retención + reportes) que mezclaba 3 concerns.
    Dirección A: vista de CONFIANZA del dueño (slim, read-mostly) + spin-outs.
  detail: 00-pm-recommendation.md
dependencies:
  hard:
    - vitalia-fase1-empty-states
    - vitalia-fase1-routing-shell
  soft:
    - vitalia-fase2-adrian-inbox             # firewall PHI + bloqueos outbound que la vista surface
    - vitalia-fase2-config-avanzado   # absorbe editor retención + checks técnicos
blocks_hard: []
blocks_soft: []
reuse_map_summary: >-
  NUEVA cap user-facing lisa.compliance (vista de confianza) que LEE la cap infra
  seguridad-cumplimiento.compliance (live · NO la reemplaza) · CONSUME audit_log +
  consent_records + firewall PHI (PhiChannelPolicy) shipped · NEW vista trust slim +
  resumen consentimientos + log acceso PHI + attestation PDF. NO editor retención
  (→ Avanzado) · NO 7 semáforos técnicos (→ postura 1-línea) · NO cron retención (→ infra)
spawned_at: 2026-05-22T00:00:00.000Z
next_action: >-
  PARKED. Unpark cuando: (1) el core agéntico esté vivo (canal-inbound/embudo/outbound con
  actividad real que mostrar) Y (2) se acerque mid-market (Persona 2 Fernando · visión Q4).
  Al retomar: /po-ux con el reframe A ya documentado + decidir scope final (B mínimo vs full).
---

# F3-S? vitalia-fase2-lisa-compliance — checkpoint

> ⛔ **PARKED 2026-06-07** (Chris) — ver `parked_reason`. **Para retomar el refinamiento en una conversación nueva: leé primero `RESUME-refinement.md`** (punto de entrada: decisiones tomadas + preguntas abiertas + evidencia competidores + precondiciones de unpark).
>
> ★ Reencuadrada 2026-06-07 a dirección **A** (vista de confianza). Análisis completo + verdad de campo + los 3 cortes: **`00-pm-recommendation.md`**. Lo de abajo refleja el scope reframe A; el scope viejo (consola pesada) quedó superseded.

## Goal (reframe A)

Sub-tab **"Confianza y cumplimiento"** de Lisa: la **capa de confianza que hace seguro delegar en agentes autónomos**. Read-mostly. Responde la pregunta real del dueño:

> *"¿Puedo confiar en que Adrián/Camila le escriban a mis pacientes sin romper la ley ni filtrar datos?"*

Es una cap **nueva user-facing (`lisa.compliance`)** que **LEE** la cap infra `seguridad-cumplimiento.compliance` (el stack defensivo, ya live, `user_visible: false`). **NO reemplaza** el enforcement técnico — lo hace **visible y confiable** para el dueño.

## Por qué Lisa (no Configuración ni Infra)

Lisa = "Mi Clínica" (identidad + presencia + **credibilidad**). Una vista de confianza/cumplimiento es un **trust signal** de la clínica → encaja en Lisa. El SYSTEM-MAP v2 ya la declara ahí (`lisa.compliance` = "Vista compliance al cliente", planned F3). Lo **admin/técnico** (editor de retención, checks de infra, audit log crudo) NO es de Lisa → va a Configuración/Avanzado + infra.

## Anti-objetivos

- NO consola técnica pasiva (rompe el paradigma agéntico "el dueño configura, el agente ejecuta")
- NO 7 semáforos técnicos (encryption status, arch-fitness, HTTPS, cron health) → eso es admin/dev → Avanzado/infra. Acá: **postura en 1 línea** + lenguaje llano
- NO editor de política de retención → Configuración→Avanzado
- NO implementar el cron de retención (hoy stub) → backend infra (seguridad-cumplimiento)
- NO tocar `core/luana-core-compliance` (read-only · consume vía API)
- NO sustituir auditoría legal externa (soporte interno, no certificación)

## Scope (PM-level · /po-ux produce el 01-spec)

### ✅ DENTRO de esta story (vista de confianza slim)

1. **Panel "Tus agentes operan seguro"** — evidencia read-mostly de que los agentes operan dentro de las reglas:
   - Firewall PHI activo + **conteo de bloqueos** (ej. Adrián redirigió N mensajes con contenido clínico al portal)
   - Consentimientos respetados / opt-outs honrados antes de outbound
   - Todo acceso a PHI registrado (audit on)
   - Retención activa (estado, no editor)
2. **Resumen de consentimientos** (★ superficie genuinamente faltante hoy): listar/buscar consent records (firmado / pendiente / revocado) + reenviar pendientes. Accionable. Lee `vitalia_consent_records`.
3. **Log de acceso PHI** — quién accedió a qué paciente cuándo (PHI-safe, masked).
4. **Attestation de compliance** export (PDF que el dueño muestra a pacientes/auditores) — snapshot postura + tenant + timestamp.
5. **Banner disclaimer HIPAA-lite** — "Compliance defensivo HIPAA-lite. NO certificación HIPAA US."
6. **Resumen de postura** (1 línea: "Tu clínica cumple X/Y controles defensivos").

### ➡️ FUERA (spin-outs ratificados)

| Pieza | Destino |
|---|---|
| Editor de política de retención (per categoría) | `vitalia-fase2-config-avanzado` |
| Checks técnicos profundos (encryption at-rest, sanitize_payload arch-fitness, HTTPS, cron health) | Config→Avanzado / dashboard infra |
| Inspector de audit log crudo (técnico) | Config→Avanzado |
| Implementación del cron de retención (hoy stub) | story backend infra `seguridad-cumplimiento` (no user-facing) |
| **Gate consentimiento/opt-out en el path de envío OUTBOUND de Adrián** (HARD compliance — hoy solo lo chequea re-engagement) | `vitalia-fase2-adrian-outbound` |

## Reuse map (lee, no recrea)

| Origen | Qué | Adaptación |
|---|---|---|
| `seguridad-cumplimiento.compliance` (cap infra live) | audit log + firewall PHI + dual filter | CONSUME read-only vía API |
| `ConsentService` + `vitalia_consent_records` (shipped) | consent records firmados HMAC | READ + reenviar pendientes |
| `inbox/SendMessageService` + `PhiChannelPolicy` (shipped) | bloqueos PHI outbound (activity `compliance_block_outbound_phi`) | READ para conteo del panel |
| `core/luana-core-compliance` (engine) | ComplianceService | CONSUME (NUNCA editar) |
| Shadcn primitives | Card · Alert · Badge · Dialog · Table | reuse |

## Dependencias reales (★ aclaración 2026-06-07)

**Construible en paralelo — NO depende de `lisa-doctores` ni `adrian-embudo`.** Toda su data-source está shipped (audit_log + consent_records + PhiChannelPolicy blocks + opt-out, todo live en infra/inbox). doctores (staff/bio) y embudo (board CRM) NO aportan dato a esta vista. Coupling suave no-bloqueante: el indicador "opt-outs honored" se enriquece cuando `adrian-outbound` cablee su gate; el "retention status" hoy muestra stub (cron pendiente). Parallel-safe: módulo `compliance` distinto + FE en subdir propio `features/lisa/components/compliance/` → commits por pathspec.

## Inconsistencias a reconciliar al cerrar

- **cap model:** crear cap nueva `lisa.compliance` (user-facing) que `reads_cap: seguridad-cumplimiento.compliance`. Corregir el `replaced_by_story` del YAML deprecated `compliance-hipaa-lite-audit` (NO lo reemplaza; lo expone).
- **release:** F2 → **F3** (alineado a SYSTEM-MAP).
- **`vitalia-compliance-audit-rbac-gap`** (idea) → **drop** (ya fixeado por hotfix `18e10822`).

## Acceptance criteria (draft — /po-ux refina)

| AC | Verificación |
|---|---|
| AC-1 | Page "Confianza y cumplimiento" renderiza panel + consentimientos + log acceso + attestation |
| AC-2 | Panel "agentes operan seguro" muestra conteo bloqueos PHI + estado consent/opt-out/audit/retención live |
| AC-3 | Resumen consentimientos lista firmado/pendiente/revocado + reenviar pendiente funciona |
| AC-4 | Log acceso PHI PHI-safe (masked) |
| AC-5 | Attestation PDF generable + download |
| AC-6 | Banner HIPAA-lite siempre visible |
| AC-7 | RBAC: solo admin_clinic ve la vista (read) · staff sin acceso PHI bloqueado |
| AC-8 | Cross-tenant query bloqueada (dual filter) |
| AC-9 | Postura 1-línea correcta (NO 7 semáforos técnicos) |
| AC-10 | a11y axe pass + mobile responsive (cards stack) |
| AC-11 | Vitest + Playwright + visual goldens |

## Referencias

- **PM recommendation (análisis completo):** `00-pm-recommendation.md`
- **Sitemap deseado:** `vitalia/docs/architecture/SYSTEM-MAP.yaml` (`agentes·lisa·compliance` + `infra·seguridad-cumplimiento·compliance`)
- **Design Contract:** `vitalia/docs/architecture/SHELL-DESIGN-CONTRACT.md`
- **HIPAA-lite overlay:** `vitalia/.claude/rules/hipaa-lite.md`
- **cap infra que lee:** `vitalia/docs/product/capabilities/compliance/compliance-hipaa-lite-audit.yaml`
- **Paradigma:** `.claude/rules/paradigm-arquitectura.md` (enforcement técnico→Infra · vista user-facing→su caja)

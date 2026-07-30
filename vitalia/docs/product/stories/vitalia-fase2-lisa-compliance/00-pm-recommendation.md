# PM Recommendation — vitalia-fase2-lisa-compliance

> **Autor:** `/pm-vitalia` · **Fecha:** 2026-06-07 · **Estado:** refining (sin ratificar)
> **Disparador:** Chris pidió re-evaluar la story bajo la visión agéntica actual, revisando lo desarrollado en LISA + impacto en Adrián + el sitemap deseado (`SYSTEM-MAP.yaml`).

---

## TL;DR

La story fue concebida el **2026-05-22 bajo la visión vieja**: una **consola pesada de compliance** como sub-tab de Lisa (semáforo 7 checks técnicos + **editor de política de retención** + reportes técnicos export + links a Config Avanzado).

Bajo la **visión agéntica actual** + el **sitemap deseado (SYSTEM-MAP v2)**, esa consola **mezcla 3 cosas que el propio mapa ya separó**. Recomiendo **reencuadrar la story a una vista de CONFIANZA del dueño (slim, read-mostly)** y **sacar a otras stories** las piezas admin/técnicas/backend.

---

## Verdad de campo (ground truth — lo que existe HOY)

| Hecho | Detalle | Fuente |
|---|---|---|
| Stack técnico de enforcement **YA LIVE en infra** | dual-filter tenant+clinic, pgcrypto (PHI paciente), audit log sync (`vitalia_audit_log`), **firewall PHI outbound** (`PhiChannelPolicy` + `VitaliaComplianceAdapter`, cableado en `inbox/SendMessageService`), 5 guardrails, `ConsentService` (records firmados HMAC). `user_visible: false`. | `SYSTEM-MAP.yaml` infra·seguridad-cumplimiento · explore code |
| Cron de retención = **STUB** | `audit_log_retention_sweep_monthly` loguea "not yet implemented". El **editor de política de retención NO existe**. | explore code |
| UI legacy de compliance = **admin audit-viewer** | log de eventos + stats + export CSV + modal de consentimiento. Vivía en **Config/dashboard** (`/configurar/compliance/audit`, `(dashboard)/medical-compliance`) — **NUNCA bajo Lisa**. Cap `deprecated`, `ui_paradigm: slice-1-superseded`. | `compliance-hipaa-lite-audit.yaml` |
| Gap RBAC de los endpoints legacy = **YA FIXEADO** | hotfix `18e10822`. La story `vitalia-compliance-audit-rbac-gap` (state=idea) quedó **stale** → cerrar/drop. | git log |
| El **sitemap deseado YA resolvió esto** | `agentes·lisa·compliance` = "**Vista compliance al cliente**" (planned **F3**). `infraestructura·seguridad-cumplimiento·compliance` = stack técnico (**live**). La story dice **F2** → mismatch de release. | `SYSTEM-MAP.yaml` |
| Toda sub-tab de Lisa shipped = **paradigma "el dueño configura, el agente ejecuta"** | autosave-first, generación en punto-de-necesidad (`✨ Generar bio`). Un dashboard pasivo de 7 semáforos técnicos **rompe** ese paradigma. | lisa-marca/doctores/servicios |
| **Consentimiento**: tabla + modal de firma live, pero **CERO UI admin** para browse/auditar consents | gap real y útil. | explore code (`consent_service`, `consent_record_model`) |
| **Gap en Adrián**: el outbound **NO** verifica opt-out/consent de marketing antes de enviar | solo el flujo de re-engagement lo chequea. Es requisito HARD (consentimiento antes de marketing — anti-pattern de marca "recordatorios sin opt-in"). `canal-inbound` (refined) **consume** el firewall PHI. | explore code · canal-inbound checkpoint |

---

## La inconsistencia de 3 vías (a resolver)

```
1. cap YAML   → agent_owner: seguridad-cumplimiento · user_visible: false · "replaced_by lisa-compliance"
2. la story   → caja Lisa · consola user-facing pesada · release F2
3. SYSTEM-MAP → lisa.compliance = vista de confianza slim (F3) · lo técnico vive en infra (live)
```

El paradigma (`paradigm-arquitectura.md`) ya dicta el desempate: *"el enforcement técnico (cifrado at-rest, audit, dual-filter) va a Infraestructura→Seguridad; la vista user-facing (consentimiento que el dueño gestiona) va a su caja user-facing."*

---

## Reencuadre agéntico (por qué "agéntico + útil")

Visión actual = Luana vende **empleados-IA a los que delegás**. Compliance **no es un panel que el dueño vigila** — es la **capa de confianza y seguridad que hace seguro delegar en agentes autónomos**.

La pregunta real del dueño no es *"mostrame 7 semáforos técnicos"* sino:

> **"¿Puedo confiar en que Adrián/Camila le escriban a mis pacientes sin romper la ley ni filtrar datos?"**

Por eso Lisa→Compliance se vuelve **"Confianza y cumplimiento"**: la **evidencia de que los agentes operan dentro de las reglas**.

---

## Recomendación: 3 cortes

### ✅ QUEDA en `vitalia-fase2-lisa-compliance` — vista de confianza del dueño (slim, read-mostly, F3)

1. Panel **"Tus agentes operan seguro"**: firewall PHI activo (conteo de bloqueos de Adrián), consentimientos respetados, opt-outs honrados, todo acceso a PHI registrado, retención activa. Lenguaje llano.
2. **Resumen de consentimientos** (la superficie genuinamente faltante): listar/buscar consent records (firmado/pendiente/revocado) + reenviar pendientes. Accionable.
3. **Log de acceso PHI** (quién accedió a qué paciente cuándo), PHI-safe.
4. **Attestation de compliance** export (PDF que el dueño muestra a pacientes/auditores).
5. **Banner disclaimer HIPAA-lite**.
6. **Resumen de postura** (1 línea: "Tu clínica cumple X/Y") — **NO** 7 semáforos técnicos.

### ➡️ SALE a Plataforma→Configuración→Avanzado (+ infra)

- **Editor de política de retención** (configurable por categoría) → admin, no Lisa → `vitalia-fase2-config-avanzado`.
- **Checks técnicos profundos** (encryption at-rest status, sanitize_payload arch-fitness, HTTPS, salud del cron) → dev/admin → Avanzado o dashboard infra.
- **Inspector de audit log crudo** (técnico) → Avanzado.
- **Implementación del cron de retención** (hoy stub) → story backend en seguridad-cumplimiento (no user-facing).

### 🆕 NUEVO guardrail backend → dominio de Adrián (HARD compliance, habilita outbound autónomo)

- **Gate de consentimiento/opt-out en el path de envío outbound de Adrián** (hoy solo lo chequea re-engagement) → ticket en `vitalia-fase2-adrian-outbound` (o story guardrail chica). **Bloquea** el outbound autónomo hasta estar.

---

## Fix del modelo de capabilities

- Esta story crea una **cap nueva user-facing `lisa.compliance`** (vista de confianza) que **LEE** la cap infra `seguridad-cumplimiento.compliance`. **NO "reemplaza"** la cap infra (que sigue live como enforcement). Corregir el `replaced_by_story` del YAML deprecated.
- Alinear release **F2→F3** (o Chris decide adelantar F3).
- Cerrar/drop `vitalia-compliance-audit-rbac-gap` (idea) — ya fixeado por hotfix `18e10822`.

---

## Decisión que necesito de Chris

Dirección **A / B / C** (ver pregunta del turno). Mi recomendación = **A**.

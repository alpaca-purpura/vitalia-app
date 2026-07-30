# dispatch-plan · vitalia-fase2-config-cuenta

> Plan de despacho para `/dev-team`. Declara autonomous_mode, asignaciones por ticket
> (agente + skills + modelo), y handoff matrix. Architect propone; Chris ratifica.

## autonomous_mode

```yaml
autonomous_mode: true         # ★ Chris ratificó full-unattended 2026-06-11 (D-AUTO · era false)
```

> **Chris override (2026-06-11):** corre full unattended hasta `done`. `demo_required→false`
> (waiva chris_verify.signoff humano). El auditor v5 mantiene su live-verify propio + `dod_evidence`
> (piso técnico no-waivable). Ver `checkpoint.md::demo_required_override` + `ratified_decisions[D-AUTO]`.

**Rationale (false):** story UI funcional con write real (PATCH editable) + HIPAA-lite
(audit log) + datos del tenant (legales/fiscal). `verification_nature: ambas` →
`demo_required: true` → Chris firma en G (`chris_verify.signoff`) ANTES del auditor.
Cambia datos del tenant (razón social, fiscal-id, especialidades que afectan ofertas de
agentes) → amerita verificación humana live. NO candidata a autonomous end-to-end.

Si Chris quiere correr autonomous: ratificar explícito (`autonomous_mode: true` en checkpoint).

## Handoff matrix (ticket → agent → model → costo estimado)

| Ticket | Surface | Agent | Model | Auditor | Costo rel. |
|---|---|---|---|---|---|
| T-2 | BE clinics (campos + validators + endpoints) | `builder-backend` | Sonnet | `auditor-backend` (Opus) | medio |
| T-1 | FE config/cuenta (N3-static + autosave) | `builder-frontend` | Sonnet | `auditor-frontend` (Opus) | medio |

**Sin tickets Opus** (no agentic). R23: ambos production_code non-agentic → Sonnet.

## Build sequence

1. **T-2 (BE) primero** — establece los DTOs reales + endpoints + registra CONTRACT_PAIR.
2. **T-1 (FE) en paralelo o después** — puede arrancar contra `03-arch § 5` (camelCase ya
   especificado) registrando el CONTRACT_PAIR primero, pero la live-verify FE requiere T-2
   mergeado (endpoints reales). Bucket: `code:clinics` (T-2) + `code:config` (T-1) = módulos
   distintos, paralelo same-hub OK (sweep-guard cubre, commit por pathspec).

## Gate de cierre (story-closure-gate)

```
ready → developing → developed
  └─ G (AWAIT_CHRIS_VERIFY): Chris ejerce el kit live (PATCH fiscal + specialties) → chris_verify.signoff
  └─ R (reconcile /pm-vitalia): spec/arch/cap ⟵ realidad
  └─ B (auditor-backend + auditor-frontend): lee docs reconciliados
  └─ APPROVED → /pm-vitalia merge (cap YAML configuracion.cuenta + SYSTEM-MAP status live)
```

## DoD live-verify (mandatory)

dev-app vitalia (`dev-app.vitalialat.com` o `localhost:3002`), admin autenticado:
- PATCH especialidad válida → persiste + reload observa valor + audit_log row en logs.
- PATCH CUIT válido → DB clinic.fiscal_id actualizado + audit row · sin traceback.
- PATCH CUIT inválido → 422 + inline error + NO persiste.
- Rol no-admin → read-only + PATCH 403.

## Open questions (bloquean arranque hasta que PM/Chris confirme — ver 03-arch § Open Questions)

1. Fiscal-id checksum: ¿formato+longitud+checksum estándar, o solo longitud? (MVP scope)
2. Specialty catalog: ¿contenido inicial por país (AR/PE/MX/CL/CO/UY)?
3. DPO data source: ¿`tenant.config_json.compliance.dpo` o empty state?
4. `config` static route segment vs dispatcher `[agent]` — confirmar no-colisión.

> Estas no bloquean el grueso del build (BE entities/endpoints + FE estructura N3), pero
> SÍ el contenido exacto de los catálogos/checksum. El builder puede arrancar con stubs
> documentados + resolver con PM en paralelo, o esperar ratificación. Recomendación:
> arrancar T-2 estructura + T-1 estructura; resolver Q1-Q3 antes de cerrar `developed`.

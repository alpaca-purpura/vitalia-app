# Hot-fix Repro Mandatory

> **Slim stub (context-rot pass 2026-05-30).** Detalle operativo completo (workflow 4 steps verbatim, caso origen detallado T-1.bis, schema `repro_evidence` completo, enforcement layers, multisistema awareness) en `docs/rules-detail/hotfix-repro-mandatory.md` — load on-demand. **Origen:** PI-12 S1 T-1.bis (2026-05-05). Handoff doc misdiagnosed bug → ~$8 USD wasted en builder Opus wrong scope.

## Regla cardinal

ANTES de spawn `builder-{backend|agentic|frontend}` para hot-fix ticket originado en handoff/incident/escalation, `/dev-team` o `/po` MUST **fundamentar el diagnóstico en evidencia** — reproducción local **o** trazas — y validar el scope. Si la evidencia falta (`repro_evidence` ausente) → `/dev-team` REFUSE spawn.

**Repro = evidencia, no solo local (D4 · proceso v5):** el schema canónico es **`repro_evidence`** con dos formas válidas:

```yaml
repro_evidence:                 # story-level (R26 = espejo ticket-level en 06-tickets)
  repro_verified: true
  reproduced_local: true        # forma A: lo reprodujiste en el stack dev real (preferida)
  # —o—
  trace_evidence:               # forma B: incident prod-only / no reproducible local
    source: runtime-logs | apm-alert | copilot_trace_event | conversation-log
    ref: "<id/url/snippet del traceback o traza que ancla el diagnóstico>"
```

La forma B (trace) vale cuando el repro local no es viable; el diagnóstico DEBE quedar anclado a evidencia concreta, nunca al texto del handoff. (CORE declara la abstracción; PROJECT llena las `source` reales vía seam `live_verify_infra.observability_evidence`.)

**Señales hot-fix** (AL MENOS UNA): título contiene `bug/hot-fix/regression/incident/bis/revert/fix forward` · origin menciona `handoff doc/pase-producción-failed/auditor-escalation` · sub-número `T-N.bis`.

**4 steps obligatorios:** (1) reproducir localmente **o** capturar `trace_evidence{source,ref}`, (2) validar diagnosis handoff vs symptom real (match/mismatch/no-repro), (3) citar `repro_evidence` en `06-tickets.yaml`, (4) spawn builder citando `repro_evidence.repro_verified: true`. Bug fix = regression test RED que reproduce el bug PRIMERO (`tdd-mandatory.md`).

## Cuándo carga el detalle

- Commands verbatim de reproducción (sistema-specific vs engine compartido)
- Schema completo `repro_evidence` con todos los fields (`diagnosis_correction`, etc.)
- Caso origen verbatim (T-1.bis: provider fallback ya funcionaba, bug real era fixture `litellm_call_id`)

## Anti-patterns (top 3 — lista completa en el detalle)

- ❌ Builder spawn con scope tomado del handoff doc sin evidencia (ni repro local ni `trace_evidence`)
- ❌ Diagnóstico anclado al texto del handoff en vez de a evidencia concreta (repro/traza)
- ❌ Hot-fix ticket sin `repro_evidence` (`repro_verified` + `reproduced_local`|`trace_evidence`)

## Referencias

- `docs/rules-detail/hotfix-repro-mandatory.md` — **detalle completo** (caso origen verbatim, workflow 4 steps, schema)
- `docs/process/process-improvement-handoff-2026-05-05.md` — handoff misdiagnosis case
- `.claude/skills/{dev-team,po}/SKILL.md` — enforcement points
- `docs/specs/templates/06-tickets-template.yaml` § repro_verified

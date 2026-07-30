# dispatch-plan — Nueva cita usable (D11)

> Consume con `06-tickets.yaml`. Para `/dev-team` (spawn) + `/pm-vitalia` (ratify autonomous).

## autonomous_mode

```yaml
autonomous_mode: false        # default — Chris opt-in al ratificar
```

**Por qué false (HARD):** story funcional con writes PHI reales (citas + pacientes), constraint DB nuevo (anti-doble-booking), reconciliación de enum (origin), engine-boundary (EXCLUDE), y soft-dep de 4 atoms del canon que pasan por `/pm-luana`. Live-verify obligatoria (Rule #37) + demo Chris en G. NO es safe para autonomous end-to-end. El architect propone; Chris ratifica si quiere relajar.

## Precursora P-0 (NO builder · /pm-luana)

`/pm-luana` promotion proposal de los 4 atoms del canon → `@luana/ui-kit`:
- `FormActionBar` · `Badge variant=success|warning` · `PageHeader back-pill` · `EntityPicker.createAction`
- Contrato: `mockups/PROPOSED-CANON-ATOMS.md`
- Proposal a crear: `docs/promotion-protocol/proposals/2026-06-22-ui-kit-nueva-cita-atoms.md`
- **Secuencia:** P-0 idealmente PRIMERO (o en paralelo con el BE). Los tickets FE (T-FE-1..4) consumen los atoms desde el kit. Si el kit no los tiene al arrancar el FE → bloqueo soft: o se ejecuta P-0 antes del FE, o T-FE-1 arranca tras el merge del kit. **NUNCA un ticket de marca edita `core/@luana/ui-kit/src/`.**
- `DayAvailabilityStrip` NO entra en P-0 (es feature scheduling, lift-candidate aparte — no ahora).

## Handoff matrix (ticket → agent → model → costo estimado)

| Ticket | Surface | primary_agent | model | costo rel. | depende |
|---|---|---|---|---|---|
| P-0 | promote | `/pm-luana` | coordinator | bajo | — |
| T-BE-1 | offer DTO | builder-backend | workhorse | bajo | — |
| T-BE-2 | migration EXCLUDE | builder-backend | workhorse | medio | — |
| T-BE-3 | availability endpoints | builder-backend | workhorse | alto | T-BE-2 |
| T-BE-4 | create + origin | builder-backend | workhorse | alto | T-BE-2, T-BE-3 |
| T-BE-5 | patient inline + search | builder-backend | workhorse | medio | — |
| T-FE-1 | ruta + schema | builder-frontend | workhorse | alto | T-BE-1, T-BE-3, T-BE-4, (P-0) |
| T-FE-2 | pickers | builder-frontend | workhorse | medio | T-FE-1, T-BE-5, (P-0) |
| T-FE-3 | disponibilidad | builder-frontend | workhorse | alto | T-FE-1, T-BE-3, (P-0) |
| T-FE-4 | FormActionBar + E2E live | builder-frontend | workhorse | alto | T-FE-1/2/3, (P-0) |

Auditores: `auditor-backend` (BE tickets), `auditor-frontend` (FE tickets) — flagship.

## DAG de ejecución

```
                       ┌─ T-BE-1 ─────────────────────┐
P-0 (/pm-luana) ╌╌soft╌┤                               ├─ T-FE-1 ─┬─ T-FE-2 ─┐
                       ├─ T-BE-2 ─→ T-BE-3 ─→ T-BE-4 ──┤          ├─ T-FE-3 ─┼─→ T-FE-4
                       └─ T-BE-5 ─────────────────────┘          └──────────┘
```

- **Wave 1 (paralelo):** P-0, T-BE-1, T-BE-2, T-BE-5.
- **Wave 2:** T-BE-3 (tras T-BE-2).
- **Wave 3:** T-BE-4 (tras T-BE-2 + T-BE-3).
- **Wave 4:** T-FE-1 (tras BE endpoints + P-0).
- **Wave 5 (paralelo):** T-FE-2, T-FE-3.
- **Wave 6:** T-FE-4 (integración + E2E + live-verify).

Single-hub (ADR-009): bucket `code:scheduling` + `code:crm` + `code:mateo` — paralelizar tickets de módulos distintos OK; mismo módulo serializa. Commit por pathspec.

## Playwright visual scope (D3)

- `story_scope_routes`: `/{tenantId}/mateo/agenda/nueva-cita`.
- `story_scope_components`: NuevaCitaView, ServicePicker, DoctorPicker, PatientPickerWithCreate, AvailabilityChip, DayAvailabilityStrip, FreeDoctorsList, NuevaCitaActions.
- `out_of_mockup_scope`: la grilla de Agenda (solo se verifica que refleja la cita), AppointmentDrawer, CobrarSaldoSubform.
- `render_sanity`: `assertShellMounted(page)` antes de axe/visual sobre el shell (HB-68).
- Smoke nuevo obligatorio (ruta nueva): `e2e/specs/smoke/nueva-cita.smoke.spec.ts`.

## Live-verify gate (Rule #37 · funcional)

- `verification_nature: funcional` → `demo_required: true` + `dev_app_verified.required: true`.
- T-FE-4 ejerce writes reales en dev-app: crear cita (201 + grilla + toast), crear paciente inline (201 + directorio), forzar solape (409). Lee logs BE + confirma efecto DB.
- `dod_live_verified: true` + `dod_evidence` + `verified_at` en checkpoint antes de `developed`.
- Chris firma `chris_verify.signoff` en G (pausa-y-ofrece, no autonomous).

## Soft-dep de los 4 atoms del canon (recordatorio)

Los tickets FE consumen `FormActionBar`, `Badge variant=success|warning`, `PageHeader back-pill`, `EntityPicker.createAction` desde `@luana/ui-kit`. Si P-0 no se completó, el builder-frontend NO los re-implementa local (driftea → auditor CHANGES_REQUESTED). Escalar a `/pm-luana` si el kit no los tiene al arrancar el FE.

---

## DELTA dispatch (G round 1 · disponibilidad día-driven multi-doctor)

> Scope-delta sobre story `developed`. SSoT del diseño: `03-arch-delta-availability.md`. SSoT del requisito: `chris-input.md` comentario G #1. Base (9 tickets) preservada — NO se re-despacha.

### autonomous_mode

```yaml
autonomous_mode: false        # Chris ratifica el swimlane (§6) + ejerce el flujo live en G
```

**Por qué false (HARD):** la decisión de diseño abierta (swimlane N-médicos + fate de la columna derecha) la **ratifica Chris live en G** (es justo lo que `chris_verify.rounds[1]` dejó "in_design"). `verification_nature: funcional` → demo + live-verify. No es safe para autonomous.

### Handoff matrix (ticket → agent → model → costo)

| Ticket | Surface | primary_agent | model | costo rel. | depende |
|---|---|---|---|---|---|
| T-D1 | BE service-day endpoint | builder-backend | workhorse | medio | — (reusa T-BE-2/3 pushed) |
| T-D2 | FE Fecha/Hora split (+ DatePicker PROMOTE) | builder-frontend | workhorse | medio | — |
| T-D3 | FE strip multi-doctor + filtro + re-role | builder-frontend | workhorse | alto | T-D1, T-D2 |

Auditores: `auditor-backend` (T-D1), `auditor-frontend` (T-D2, T-D3) — flagship.

### DAG delta

```
T-D1 (BE service-day) ──┐
                        ├─► T-D3 (FE strip N-médicos + filtro 1c + FreeDoctorsList re-role)
T-D2 (FE Fecha/Hora) ───┘
```

- **Wave D1 (paralelo):** T-D1 (bucket `code:scheduling`-BE) + T-D2 (FE Fecha/Hora — toca NuevaCitaView sección inicio).
- **Wave D2:** T-D3 (FE — toca NuevaCitaView columna disponibilidad + DayAvailabilityStrip + FreeDoctorsList; depende del endpoint T-D1 + serializa NuevaCitaView tras T-D2).
- Single-hub (ADR-009): bucket `code:scheduling`. T-D2 y T-D3 ambos tocan `NuevaCitaView.tsx` → **serializar** (T-D3 depende de T-D2) para evitar colisión de archivo. La otra OPEN (`adrian-canal-inbound` = `code:crm/inbox`) no colisiona. Commit por pathspec.

### Engine boundary (delta)

- **DatePicker (date-only)** = PROMOTE a `core/@luana/ui-kit/src/DatePicker.tsx` + story — **deliverable de T-D2**, el ÚNICO core edit permitido (canon §5: net-new shared = al kit, no local). NO precursora `/pm-luana` separada.
- `TimePicker` ya en el kit (reuse). `DayAvailabilityStrip` = componente feature vitalia (extend in-feature; lift-candidate core NO ahora).
- BE: todo brand-local (`vitalia/backend/src/modules/vitalia/scheduling/` + `offer_service_specialist_links`). **CERO** edit a `core/luana-core-*/src`.

### Playwright visual scope (delta)

- `story_scope_routes`: `/{tenantId}/mateo/agenda/nueva-cita`.
- `story_scope_components`: NuevaCitaView (sección Fecha/Hora + columna disponibilidad), DayAvailabilityStrip (1→N), FreeDoctorsList (re-role), DatePicker (kit, story propia).
- `forbidden`: `components/ui/` shell primitives · la grilla de Agenda · los 9 tickets base.
- `render_sanity`: `assertShellMounted(page)` antes de axe/visual.

### Cierre

Batería delta verde → **vuelve a G** (`developed` + `phase: AWAIT_CHRIS_VERIFY`): Chris ejerce live (servicio+día→strip auto-puebla N médicos→hora filtra→elige médico libre→chip Disponible→Crear) + ratifica el swimlane + firma `chris_verify.rounds[1].status: ratified`. NO auto-handoff a auditor mientras Chris siga dando observaciones G.

# 03-arch DELTA — Availability redesign (G round 1)

> **Scope-delta sobre story ya `developed`.** NO re-arquitectura los 9 tickets base (form shell, hoja leaf, create 201, patient inline, tokens obs#4 — todo preservado en `dod_evidence`). Este doc cubre SOLO el comentario G #1 (disponibilidad día-driven multi-doctor). Tickets nuevos = `T-D1..T-D3` (ids no-colisionan). Base = `03-arch.md` + `03-arch-be.md` + `03-arch-fe.md` (sin cambios).
>
> **Architect run on:** 2026-06-26 · **brand:** vitalia · `architecture_pattern: ADR-vitalia-004` · `adr_004_compliance: full` · `verification_nature: funcional`.
> **SSoT del requisito:** `chris-input.md` comentario G #1 (2026-06-25, líneas 472-473) + `checkpoint.md::chris_verify.rounds[1].delta`.

---

## 0. Context summary

**El cambio (4 sub-cambios + 1 decisión de diseño):**
- **(1a)** Separar **Fecha** de **Hora** (hoy combinados en `SmartDateTimePicker`).
- **(1b)** Al marcar un **día** (+ servicio elegido) → auto-listar la disponibilidad de **TODOS los médicos del servicio** en el grafiquito (`DayAvailabilityStrip` pasa de 1 a N médicos), **sin elegir médico antes** y sin marcar a mano a la derecha.
- **(1c)** Al poner una **hora** → filtrar a los médicos **disponibles a esa hora**.
- **(1d)** Al **cambiar el día** → auto-refresh.
- **Decisión de diseño (la resuelve este architect, Chris ratifica live en G):** visualización N-médicos del strip + fate de la columna derecha (`FreeDoctorsList`). → **§ 6**.

**Surface → builder → auditor mapping** (PM usa para spawnear):

| Surface | Builder | Auditor |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/scheduling/{api,application,infrastructure}/` (endpoint service-day) | `builder-backend` (workhorse) | `auditor-backend` (flagship) |
| `vitalia/frontend/src/features/mateo/components/nueva-cita/**` + `hooks/**` + `types/**` | `builder-frontend` (workhorse) | `auditor-frontend` (flagship) |
| `core/@luana/ui-kit/src/DatePicker.tsx` (PROMOTE date-only atom) | `builder-frontend` (deliverable del ticket FE, **antes del merge** · canon §5) | `auditor-frontend` |

- **Skills consultados:** `backend-expert` (endpoint read-only que reusa repo existente, cero mirror del cómputo free/busy) · `frontend-expert` + `vitalia-design-system` (Fecha/Hora del canon, swimlane sobre componente feature) · `offer-expert` (link servicio→médico vive en `offer_service_specialist_links`, cross-module via tabla, no import directo).
- **CONTEXT-BRIEF source:** brief base existe (`CONTEXT-BRIEF.md` validado en el ready package original); este delta lo gobierna `chris-input.md` G #1 + ground-truth code re-verificado en sesión (BE availability surface + FE nueva-cita + kit TimePicker/Calendar) — sin §7/§8 nuevos del Haiku (delta scope, no re-scan completo).
- **capability YAML afectada (post-merge):** `vitalia/docs/product/capabilities/scheduling/mateo-agenda.yaml` (`cap_change_type: extend` — el form de create gana el flujo día-driven multi-doctor; actualizar `scenarios[]` con los SC nuevos) + `modules/scheduling.md` si la narrativa de "Nueva cita" cambia.
- **Arch gates que deben seguir verdes:** `test_response_model_required.py` · `test_phi_dual_filter.py` · `test_no_phi_in_url_params.py` · `test_audit_log_*` (n/a — endpoint read-only, sin audit write) · `test-semantic-badge-tokens.test.ts` (obs#4) · `test-no-div-layout` / `test-features-no-cross-imports` (FE) · FSD boundaries.

---

## 1. Existing systems audit (NO-NEW-LAYER rule)

### Fuente de evidencia
- [x] Self-run greps + reads (sesión 2026-06-26) — delta scope, scan dirigido a la superficie disponibilidad.

### Sistemas existentes encontrados (todos REUSE/EXTEND — cero capa nueva)

| Sistema | Path (real) | Qué hace hoy | Decisión |
|---|---|---|---|
| Servicio→médicos link | `vitalia/backend/src/modules/vitalia/offer/infrastructure/models/offer_service_specialist_link_model.py` (`offer_service_specialist_links`: `offer_id`→`doctor_id`, tenant-scoped) | mapea oferta (servicio) a sus especialistas | **REUSE** — resuelve "médicos del servicio" (1b). Fallback `list_active_doctors` cuando un servicio no tiene links (seed actual) |
| Working hours por médico/día | `availability_query_repository.py::get_working_hours` | bloques de atención de 1 médico (dual-filter) | **REUSE** (loop per-doctor) |
| Busy ranges por médico/día | `availability_query_repository.py::get_busy_ranges` | citas ocupadas de 1 médico, excluye CANCELLED (RN-6) | **REUSE** (loop per-doctor) |
| Labels de médicos | `availability_query_repository.py::list_active_doctors` (JOIN `vitalia_doctors`, COALESCE nombre real) | nombre profesional real | **REUSE** (resuelve labels del set service-day) |
| Overlap half-open `[s,e)` | `scheduling/domain/availability_check.py` (TimeRange + matrix 4-estados) | autoridad del solape | **REUSE** server + **MIRROR client-side advisory** para el filtro 1c (RN-10: client advisory, server EXCLUDE = garantía) |
| Endpoints availability | `availability_router.py` (`POST /check`, `POST /free-doctors`, `GET /day-strip`) | por-médico-por-slot | **EXTEND** — agrega `GET /service-day` (mismo router, mismo service/repo) |
| `DayAvailabilityStrip` | `features/mateo/components/nueva-cita/DayAvailabilityStrip.tsx` | timeline 1 médico (07–21h, working/busy/selected) | **EXTEND** 1→N (swimlanes) — componente feature, lift-candidate core NO ahora |
| `FreeDoctorsList` | `features/mateo/components/nueva-cita/FreeDoctorsList.tsx` | reasignar a médico libre (server `free-doctors`) | **RE-ROLE** → lista filtrada-por-hora (client-side) |
| `TimePicker` (Hora) | `core/@luana/ui-kit/src/TimePicker.tsx` (story `molecules-timepicker--default`) | hora HH:mm segmentada | **REUSE** (1a) |
| `Calendar` (Fecha base) | `core/@luana/ui-kit/src/calendar.tsx` (story `organisms-calendar--default`) | day-picker raw | base del `DatePicker` a promover |

### Decisión por sistema
- **BE endpoint `service-day`** = **EXTEND** del router/service/repo existentes. Es un **método nuevo que COMPONE métodos existentes** (`get_working_hours` + `get_busy_ranges` por médico, `list_active_doctors` para labels, `offer_service_specialist_links` para el set). **CERO recreación** del cómputo free/busy. No es una capa nueva: es una proyección read-only sobre tablas y métodos ya ttesteados.
- **DatePicker (date-only)** = **NEW shared atom → PROMOTE a `@luana/ui-kit`** (no existe; sólo `SmartDateTimePicker` combinado y `Calendar` raw). Justificación NEW: ningún atom date-only-en-popover existe; es reusable platform-wide (toda hoja con campo fecha). Por canon §5 = se construye en el kit + story, **NO** se re-implementa local-y-olvidado. Fold en el deliverable de `T-D2` (no precursora `/pm-luana` separada — el ticket lo crea en el kit antes del merge).
- **Filtro 1c client-side** = mirror advisory del half-open `[s,e)`. NO crea capa server: el server (`check`/`free-doctors`/EXCLUDE) sigue siendo la autoridad en submit (RN-10).

**Cross-brand mirror check:** ninguno. `offer_service_specialist_links`, `availability_query_repository`, `DayAvailabilityStrip` son todos brand-local vitalia. Cero patrón a liftar a core en este delta.

---

## 2. BE contract — endpoint `service-day` (decisión A)

### A vs B
- **(A) `GET /availability/service-day?serviceId&date`** — un round-trip; server resuelve servicio→médicos + per-doctor working+busy. ✅ **ELEGIDA**.
- **(B) client fan-out** del `day-strip` existente sobre la lista de médicos del servicio — N requests + necesita un endpoint "médicos del servicio" aparte. ❌ rechazada (N+1 round-trips, peor UX en cambio-de-día).

Razón A: una sola llamada al marcar el día (1b/1d), cómputo de pertenencia servicio→médico en el server (no en el cliente), reusa métodos existentes. El **filtro por hora (1c) se computa CLIENT-SIDE** desde los bloques ya traídos → cero round-trip extra al tipear la hora.

### Endpoint
```
GET /api/v1/scheduling/availability/service-day?serviceId={offerId}&date=YYYY-MM-DD
Headers: X-Tenant-ID, X-Clinic-ID, X-User-ID, X-User-Role   (Bearer + dual header)
RBAC: SCHEDULING_PHI_ROLES (@_rbac_check, igual que los otros 3 endpoints)
response_model: ServiceDayResponse
redirect_slashes=False (app-level, ya configurado)
```
- `serviceId` = `offer_id` del servicio elegido (el valor de `ServicePicker`/`selectedServiceId`). NO es PHI (identificador de catálogo).
- `date` en query = identificador de agenda (no PHI; sin paciente). `no_phi_in_url` se mantiene verde.
- **NO migración** (read-only sobre tablas existentes).

### DTOs (Pydantic v2 · `vitalia/backend/src/modules/vitalia/scheduling/api/dtos/availability_dtos.py`)
```python
class ServiceDayDoctor(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    doctor_id: UUID
    doctor_label: str                 # nombre profesional, NUNCA paciente (PHI-safe)
    blocks: list[DayBlockItem]        # REUSA DayBlockItem existente {kind, start, end}

class ServiceDayResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    service_id: UUID
    date: date
    doctors: list[ServiceDayDoctor]   # vacío = servicio sin médicos (empty_state)
```
**PHI:** idéntico a `day-strip` — los bloques cargan sólo `kind + start + end`; `doctor_label` = nombre profesional. **Cero dato de paciente** en cualquier capa.

### Repo (EXTEND `AvailabilityQueryRepository`)
Nuevo método que **COMPONE** lo existente (cero SQL de free/busy nuevo):
```python
async def get_service_day_strips(self, *, tenant_id, clinic_id, offer_id, day) \
        -> list[tuple[UUID, str, list[DayBlockItem]]]:
    # 1. Resolver médicos del servicio (dual: tenant + el clinic-scoping lo da el JOIN a doctors/slots)
    #    SELECT doctor_id FROM offer_service_specialist_links
    #    WHERE tenant_id=:t AND offer_id=:o AND deleted_at IS NULL
    #    → si vacío: fallback a list_active_doctors(tenant, clinic) (servicio sin links seedeados)
    # 2. Labels: reusar el JOIN de list_active_doctors (filtrado al set + dual tenant/clinic)
    # 3. Por cada doctor_id del set (N ≤ ~20 en una clínica):
    #       wh = await self.get_working_hours(...)   # REUSE
    #       busy = await self.get_busy_ranges(...)   # REUSE (excluye CANCELLED, RN-6)
    #    → blocks = [DayBlockItem(working_hours)...] + [DayBlockItem(busy)...] sorted by start
    # 4. Excluir del set los doctor_ids que no son de este clinic (sin slots ⇒ wh vacío;
    #    se incluyen igual con blocks=[] → la lane muestra "Sin horario" — RN-4)
```
- **Anti-duplicación:** loop de los métodos ya testeados (`get_working_hours` + `get_busy_ranges`). Para N grande, optimización opcional follow-up = batched `WHERE doctor_id IN (...)` (no ahora · YAGNI · N pequeño).
- **Service (EXTEND `AvailabilityCheckService`)** o método nuevo `service_day()` que delega al repo y mapea a DTO. Thin router → service → repo (backend-ddd).

### Router (EXTEND `availability_router.py`)
Una ruta nueva `@router.get("/availability/service-day", response_model=ServiceDayResponse, ...)` espejando `get_day_strip` (mismo `_rbac_check`, mismos headers, mismo `_get_db`, validación `date.fromisoformat` → 422). `include_router` ya está (mismo router).

### Edge / sub-categorías (BE)
- **empty_state** servicio-sin-médicos: link vacío **y** `list_active_doctors` vacío → `doctors: []` → FE empty_state.
- **empty_state** día-sin-disponibilidad: médicos existen pero ninguno con working_hours ese día → cada lane `blocks=[]` (FE pinta "Sin horario").
- **adversarial** cross-clinic/cross-tenant: dual filter en cada sub-query (médico de otra clínica ⇒ sin slots ⇒ no aparece / no leak); endpoint sin auth → 403.
- **large_dataset** muchos médicos: N lanes; el server devuelve todos (cap natural ~20/clínica); FE virtualiza/scrollea (§5).

---

## 3. FE contract — Fecha/Hora split (1a)

**Hoy:** `NuevaCitaView.tsx:458` usa `SmartDateTimePicker` (fecha+hora combinado) para `startTime`. **Cambio:** dos controles.

| Campo | Componente canon | Storybook story | Nota |
|---|---|---|---|
| **Fecha** | `DatePicker` (date-only) — **PROMOTE** | `inputs-datepicker--default` (a crear) | NO existe en el kit; sólo `SmartDateTimePicker` (combinado) + `Calendar` raw. PROMOVER: `Calendar` (`mode="single"`) en `Popover` + `Button` trigger con fecha formateada tz tenant. Deliverable de `T-D2` en `core/@luana/ui-kit/src/DatePicker.tsx` + `stories/inputs.DatePicker.stories.tsx` **antes del merge** (canon §5 — net-new shared = PROMOTE, no local). |
| **Hora** | `TimePicker` (existe) | `molecules-timepicker--default` | `value="HH:MM"`, `onChange`. Ya en el kit (commits 0016f65e/3ef49737). |

**Composición (`startTime` ISO se deriva de fecha + hora):**
- `DatePicker` emite `YYYY-MM-DD` (tz tenant) · `TimePicker` emite `HH:MM` → se componen a `startTime` ISO-UTC (mismo helper de normalización tz/DST que ya usa el form; reusar la lógica de `addMinutesToIso`/Intl existente — H1 ya fijó el tz bug).
- `endTime` autocalc (servicio·duración) **se preserva** (lógica de `T-FE-1`/obs intactos): al cambiar fecha **o** hora → recalcular `endTime = start + duration`.
- **NO** `<input type="time/date">` nativo, **NO** `<select>` nativo, **NO** arbitrary-values (canon).
- **Lazy rechazado:** componer la fecha local-en-feature desde `Calendar`+`Popover` → drift (canon §5: "pieza shared net-new local sin promover = deuda"). Por eso PROMOTE.

**Reactividad del split:** el cambio de **fecha** dispara (1d) el refetch del strip multi-doctor + el recálculo de `endTime`. El cambio de **hora** dispara (1c) el filtro client-side. → §4.

---

## 4. FE contract — multi-doctor día-driven (1b/1c/1d)

### 4.1 Tipos nuevos (EXTEND `features/mateo/types/agenda-schema.ts`)
```ts
export const ServiceDayDoctorSchema = z.object({
  doctorId: z.string().uuid(),
  doctorLabel: z.string().min(1),
  blocks: z.array(DayBlockItemSchema),     // REUSA DayBlockItemSchema existente
});
export const ServiceDayResponseSchema = z.object({
  serviceId: z.string().uuid(),
  dateLocal: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  doctors: z.array(ServiceDayDoctorSchema),
});
export type ServiceDayResponse = z.infer<typeof ServiceDayResponseSchema>;
```
Normalizer snake→camel en el hook (igual que `normalizeDayStrip`): `service_id→serviceId`, `date→dateLocal`, `doctor_id→doctorId`, `doctor_label→doctorLabel`.

### 4.2 Hook nuevo (EXTEND `features/mateo/hooks/use-availability.ts`)
```ts
export const availabilityKeys.serviceDay =
  (tenantId, serviceId, dateLocal) =>
    ["mateo","availability","service-day",tenantId,serviceId,dateLocal] as const;

export function useServiceDayStrips({ tenantId, serviceId, dateLocal }) {
  // GET /availability/service-day?serviceId&date  (getToken fresh per-request, T-FE-4 pattern)
  // enabled: Boolean(serviceId) && Boolean(dateLocal) && isLoaded && isSignedIn
  // staleTime 30_000.  key cambia con dateLocal → (1d) auto-refetch al cambiar día.
}
```
- **Disparo (1b/1d):** `enabled` por `serviceId + dateLocal`. **NO requiere `doctorId`** (esa es la inversión). Cambio de día → nueva key → React Query refetch automático.

### 4.3 Filtro por hora client-side (1c · helper nuevo, advisory)
```ts
// features/mateo/utils/availability-filter.ts  (mirror advisory del half-open [s,e))
export function isDoctorFreeAt(blocks: DayStripBlock[], startIso: string, endIso: string): boolean {
  // free ⇔ [start,end) ⊆ algún working_hours block  AND  no overlap con ningún busy block
  // half-open [s,e): back-to-back NO solapa (RN-2). Reusa la semántica de availability_check.py.
}
export function filterFreeDoctors(serviceDay: ServiceDayResponse, startIso, endIso): ServiceDayDoctor[]
```
- Al tipear/elegir **hora** → `filterFreeDoctors` sobre los bloques ya traídos → set de médicos libres a esa hora (cero round-trip).
- **RN-10:** esto es **advisory** (UI). La garantía dura sigue siendo el `availability/check` (al seleccionar médico) + el EXCLUDE en submit. Sin hora puesta → no se filtra (se muestran todos).

### 4.4 `DayAvailabilityStrip` 1→N (swimlanes · EXTEND)
- Nueva prop-shape: en vez de `doctorId` único + `useDayStrip`, recibe `serviceDay: ServiceDayResponse` (o consume `useServiceDayStrips` internamente) + `selectedDoctorId` + `selectedStartIso/EndIso` + `timezone`.
- Render: **una lane (fila) por médico** del set — label (avatar + nombre, `EntityInfoCard`-style compacto) a la izquierda, timeline 07–21h a la derecha reusando `isoToStripMinutes`/`blockToPct`/`minutesToPct` **existentes** (cero recálculo tz nuevo — H1 ya correcto). Bandas: working (verde `--success`), busy (rojo/gris), slot propuesto (amarillo `--agent-mateo`).
- **Time-cursor (1c):** cuando hay hora → línea vertical del `[start,end)` propuesto cruzando TODAS las lanes; lanes con médico libre a esa hora = resaltadas/seleccionables, ocupadas = atenuadas.
- **Selección:** click en una lane (o en la lista filtrada §4.5) → `setSelectedDoctorId` (Zustand). Mantiene el `availability/check` existente para el chip del médico elegido (autoridad).
- Single-doctor `useDayStrip` queda como path legacy del detalle (no se borra; el nuevo flujo usa service-day).

### 4.5 `FreeDoctorsList` re-role (1c · § 6)
- De "reasignar a médico libre vía server `free-doctors`" → **lista filtrada-por-hora client-side**: `filterFreeDoctors(serviceDay, start, end)`.
- Sin hora puesta → hint "Ingresa una hora para filtrar los médicos disponibles" (no lista vacía confusa).
- Con hora → pills 1-clic de los médicos libres a esa hora → selecciona médico (mismo `onReassign`/`setSelectedDoctorId`).
- Estados: empty (ningún libre a esa hora) "Ningún médico libre a las HH:MM — probá otra hora o día".

### 4.6 Data-flow (resumen)
```
elegir SERVICIO ─┐
                 ├─► useServiceDayStrips(serviceId, dateLocal)  [1b]  ──► strip N lanes (todos los médicos del servicio, día completo)
elegir DÍA ──────┘                         ▲
                                           └─ key incluye dateLocal ⇒ cambio de día = auto-refetch  [1d]
poner HORA ──► filterFreeDoctors(blocks, start, end) [client]  [1c] ──► FreeDoctorsList = libres a esa hora + time-cursor en el strip
elegir MÉDICO (lane/pill) ──► availability/check (autoridad) ──► chip + Crear habilitado (RN-10)
submit ──► POST /appointments ──► EXCLUDE 23P01 = garantía dura
```

---

## 5. Integration design (CONN)

- **C (Consumed):** `service-day` consumido por `NuevaCitaView` (vía `useServiceDayStrips` → `DayAvailabilityStrip` + `FreeDoctorsList`). El `DatePicker`/`TimePicker` consumidos por la sección Fecha/Hora del form.
- **O (On the map):** vive en `cap scheduling.mateo-agenda` (extend) — hogar declarado, zona `agentes`/box `mateo`.
- **N (Navigable):** el operador llega por la hoja `/{tenantId}/mateo/agenda/nueva-cita` (ya existe, AC-9); reachability: elige **servicio + día** → el strip se auto-puebla con todos los médicos del servicio (no hay que elegir médico antes). Cero pantalla nueva.
- **N (Notarized):** `GET /availability/service-day` registrado en el `availability_router` ya incluido en `main.py` (`include_router`); `DatePicker` registrado en `@luana/ui-kit` `index.ts` (export) + story; los hooks/components exportados por el index del feature (FSD-Lite public API).
- **Read-side claims:** "engine ya hace X" → N/A (todo brand-local vitalia; `offer_service_specialist_links`, `availability_query_repository`, `DayAvailabilityStrip` son vitalia, no engine).
- **Storybook citation (canon §5):** Fecha=`inputs-datepicker--default` (PROMOTE) · Hora=`molecules-timepicker--default` · chips=`atoms-badge--semanticas` · header médico de la lane=`organisms-entityinfocard--default`. `DayAvailabilityStrip` = componente feature (NO en kit) → extend in-feature, lift-candidate core NO ahora.

---

## 6. Decisión de diseño (recomendación · Chris ratifica live en G)

**(a) Visualización N-médicos = SWIMLANE-POR-MÉDICO.** Cada médico = una fila horizontal (07–21h) con label (avatar + nombre) a la izquierda y su timeline (working verde / busy rojo / slot-nuevo amarillo) a la derecha. Un **time-cursor** vertical marca el `[start,end)` propuesto cruzando todas las lanes cuando hay hora. Click en lane = elige médico.
- *Por qué:* es la respuesta directa a "ver inmediatamente la disponibilidad de todos los médicos del servicio por día sin tantear horas" (1b). Comparar disponibilidad entre médicos de un vistazo = filas apiladas en el mismo eje temporal. Reusa el render del strip actual (cero recálculo tz).
- *Alternativas descartadas:* grid hora×médico (denso, no escala a 14h×N) · heatmap (pierde el detalle de bloques) · acordeón por médico (esconde la comparación = lo que Chris quiere evitar).

**(b) Columna derecha (`FreeDoctorsList`) = SE QUEDA, re-roleada como lista filtrada-por-hora.** NO desaparece.
- *Por qué:* el strip responde "¿quién atiende y cuándo, todo el día?" (1b); la lista responde "¿quién está libre EXACTAMENTE a esta hora?" (1c) — son complementarias, no redundantes. Sin hora → la lista muestra un hint (no vacío confuso) y el strip es el héroe. Con hora → la lista se puebla con los libres + el strip resalta las lanes libres. Fundir todo en el strip dejaría 1c sin un lugar accionable claro (1-clic para elegir el médico libre).
- *Alternativa descartada (fundir en el strip):* válida pero pierde el "elegir el libre de 1 clic" como acción discreta; queda como follow-up si Chris prefiere una sola superficie en G.

---

## 7. Tests (TDD · RED-first) + seam_coverage

### seam_coverage (obligatorio)
| Costura | test_type | Archivo |
|---|---|---|
| código↔DB (service-day: resuelve servicio→médicos + per-doctor blocks dual-filter) | **integration-realdb** | `tests/modules/vitalia/scheduling/test_service_day_strips_realdb.py` |
| FE↔BE (contrato `ServiceDayResponse` shape) | **contract** | `features/mateo/hooks/__tests__/use-service-day.contract.test.ts` |
| componente↔shell (strip N-lanes renderiza en la hoja leaf) | **e2e-live** | `e2e/regression/mateo/nueva-cita.spec.ts` (SC-dia-auto-lista-todos-medicos) |

### Surfaces por capa
- **BE:** domain (n/a — reusa overlap) → infra `test_service_day_strips_realdb.py` (RED: servicio con links → N médicos; servicio sin links → fallback all-active; cross-clinic excluido; CANCELLED no bloquea) → api `test_service_day_router_phi.py` (RED: 403 unauth, dual-filter, response_model sin PHI, no_phi_in_url).
- **FE:** hook `use-service-day` (RED: key cambia con día → refetch) → util `availability-filter.test.ts` (RED: half-open `[s,e)` libre/ocupado, back-to-back libre RN-2) → component `DayAvailabilityStrip.test.tsx` (RED: N lanes, time-cursor, empty/sin-horario) + `FreeDoctorsList.test.tsx` (RED: filtrado-por-hora, hint sin-hora) + Fecha/Hora split en `NuevaCitaView.test.tsx`.
- **E2E:** `nueva-cita.spec.ts` extendido con SC-fecha-hora-split, SC-dia-auto-lista, SC-hora-filtra, SC-cambio-dia-refresh, SC-strip-multidoctor.

---

## 8. Cross-cutting
- **HIPAA-lite:** `service-day` es scheduling-scoped PHI-adjacent → bloques con kind+times only, `doctor_label` profesional, **cero paciente** (igual que `day-strip`). Dual filter tenant+clinic en cada sub-query. RBAC `SCHEDULING_PHI_ROLES`. `response_model=` en la ruta. `no_phi_in_url` (serviceId/date no son PHI).
- **Master-data/tz:** día computado en tz clínica; bloques renderizados tz tenant (reusa `isoToStripMinutes` Intl). UTC en wire/DB. DST-safe (el split Fecha+Hora→ISO reusa la normalización tz existente).
- **Spanish neutro LatAm:** labels/hints UI ("Vista del día", "Ingresa una hora para filtrar", "Sin horario", "Ningún médico libre a las HH:MM").
- **Native-first:** gates nativos host (ruff/pytest/tsc/eslint/vitest).
- **Anti-duplicación:** el filtro 1c mirror del half-open es advisory (RN-10); el server (`check`/EXCLUDE) es la única autoridad. NO se crea servicio de cómputo free/busy paralelo.

---

## 9. Open questions for PM
- Ninguna bloqueante. La única decisión abierta (§6: swimlane + fate de la columna derecha) es **recomendación del architect** — Chris la **ratifica live en G** (es el método que pidió `rounds[1]`). Si Chris prefiere fundir la lista en el strip (alternativa §6b) → ajuste menor de `T-D3`, sin cambio de contrato BE.

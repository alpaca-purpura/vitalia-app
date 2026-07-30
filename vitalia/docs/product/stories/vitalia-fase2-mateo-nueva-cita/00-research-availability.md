# 00-research — Disponibilidad + anti-doble-booking (D11 Nueva cita)

> Investigación pedida por Chris (2026-06-21) antes de diseñar el flujo funcional. 3 subagentes: mapa del código existente + UX de líderes + algoritmia/concurrencia. Citas abajo.

## 1. Qué YA existe en vitalia (code map)

| Componente | Qué hace | Sirve para D11 |
|---|---|---|
| `vitalia_availability_blocks` (clinics) | horarios de trabajo del médico (recurrencia weekly/biweekly, días, excluidos) | base de "horario del médico" |
| `vitalia_availability_slots` (clinics) | slots materializados de 30 min por médico, flag `has_confirmed_appointment` | **free/busy por médico ya consultable** |
| `AvailabilityProjectionService` / `AvailabilityBlockService` | expanden blocks→slots (rrule), CRUD, preservan slots confirmados | reuse para "horario del día" |
| `vitalia_appointments` | `slot_iso` (timestamptz) + `duration_minutes` + `doctor_id` + `status`. **SIN constraint de unicidad/exclusión** | tabla destino; falta la garantía |
| `create_appointment_service` | NO chequea solape; depende de `SchedulingHoldService` que **solo se inyecta para origin=proactivo_adrian** | **walk-in/teléfono = SIN protección hoy (bug latente)** |
| `appointment_reschedule_with_doctor` (agentic tool) | `scheduler_query` + chequeo de ocupación por capacidad | prior-art de query de slots |

**Gap:** no hay endpoint FE "slots libres del médico X en fecha D para duración M". Hay que armarlo (wrapper sobre lo existente). Y NO hay garantía a nivel DB contra doble-booking.

## 2. UX de líderes (Tebra · Jane · Acuity · Cal.com · MS Bookings · Doctoralia)

- **Patrón núcleo (Tebra):** input manual de fecha/hora + **chip de disponibilidad live** junto al selector de médico, reactivo a (médico, fecha, hora, duración): `Disponible` / `Ocupado — se solapa con [cita]` / `Fuera de horario`. Se actualiza antes de guardar. Mantiene la entrada manual (no obliga a slot-picker).
- **Reasignar (Tebra/Cal.com):** si el médico está ocupado → mostrar "médicos disponibles a esta hora" → 1 clic cambia médico + re-chequea.
- **Política de conflicto — el mercado se parte:** las médicas (Jane/Acuity/SimplePractice) **permiten overbooking intencional** (soft warning + override) porque recepción a veces necesita encimar; bloqueo duro solo para recursos físicos (sala/equipo). Jane: provider overlap = modo deliberado gateado; sala = bloqueo duro.
- **Pitfalls:** timezones (store UTC), buffer entre citas, solape parcial (no solo misma hora exacta), bloques all-day/feriados, granularidad vs duración, race conditions (la garantía va en DB, no en el warning).

## 3. Algoritmia + concurrencia

- **Solape:** intervalos half-open `[s,e)`, condición `s1 < e2 AND s2 < e1` (estricto). Back-to-back (10:00–10:30 / 10:30–11:00) NO es solape. Scan lineal por médico/día alcanza (≤30/día); nada de interval trees.
- **Free/busy:** sort-merge-subtract de citas no-CANCELLED contra el horario; grid 15 min opcional; buffer configurable (default 0).
- **Garantía real (DB):** `EXCLUDE USING gist (doctor_id WITH =, tstzrange(slot_iso, slot_iso + duration, '[)') WITH &&) WHERE status <> 'CANCELLED'` + `CREATE EXTENSION btree_gist`. Declarativo, inmune a races. CANCELLED no cuenta (partial). El 2do insert concurrente falla `23P01` → mapear a **409** con mensaje neutro.
- **TZ:** `timestamptz` UTC + convertir con IANA del tenant (`America/Lima`, etc.); DST seguro porque compara instantes absolutos.

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;
ALTER TABLE vitalia_appointments
  ADD CONSTRAINT no_overlap_per_doctor
  EXCLUDE USING gist (
    tenant_id WITH =, doctor_id WITH =,
    tstzrange(slot_iso, slot_iso + (duration_minutes * INTERVAL '1 minute'), '[)') WITH &&
  ) WHERE (status <> 'CANCELLED');
-- migración idempotente: guard con DO $$ IF NOT EXISTS (pg_constraint conname=...) $$
```

## 4. Decisiones de diseño (recomendación)

1. **Garantía = constraint DB EXCLUDE** (mata el doble-book accidental + race — el bug latente de hoy). NO confiar solo en el warning del FE.
2. **Solape de médico = bloqueo duro** (Chris: "no debería poderse"). El flujo "ver médicos disponibles → reasignar" hace el bloqueo indoloro. NO se construye override-de-overbooking ahora (YAGNI; toggle futuro si la clínica lo pide).
3. **Fuera de horario ≠ solape** → propuesta: warning permitido (el médico puede atender excepcional), NO bloqueo. ⟵ a confirmar con Chris.
4. **Duración** del servicio (`initial_appt_duration_minutes`, ya existe); null → 30. Hora-fin autocalc, editable.
5. **Buffer** entre citas: config, default 0 (no se construye UI ahora).

## Fuentes
- UX: Tebra (New/Find Appointment), Jane (double-booking, resource), Acuity (pooling/padding/overlap), Cal.com (round-robin/reassign), MS Bookings, Doctoralia.
- Algo/DB: PostgreSQL rangetypes (EXCLUDE/btree_gist), Cybertec, Daniel Clayton, Amitav Roy, Slotflow (free/busy), asyncpg/SQLAlchemy (23P01→IntegrityError).

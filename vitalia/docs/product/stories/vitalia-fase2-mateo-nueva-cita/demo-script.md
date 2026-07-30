# Demo script — Delta G#1: disponibilidad día-driven multi-doctor

> Guía de tu G (autonomous_mode:false). Ejercé **live** en dev-app y firmá `chris_verify.rounds[1]` + `signoff`. Si algo no cuadra, anotá → fix-loop antes del auditor.

**Setup:** `dev-app.vitalialat.com/.../mateo/agenda/nueva-cita` (o `localhost:3002`) · login `dr.demo@vitalialat.com` · Chrome DevTools MCP / browser. Hard-reload (Cmd/Ctrl+Shift+R) la primera vez.

## Lo que cambió (comentario #1) — qué verificar

| # | Comportamiento nuevo | Cómo verificar | Esperado |
|---|---|---|---|
| **1a** | Fecha y Hora **separadas** | Mirá la sección de inicio del form | Dos controles: **Fecha** (date-only, `dd/MM/yyyy`) + **Hora** (`HH:MM`). NO el combinado de antes. |
| **1b** | Día → auto-lista **TODOS los médicos del servicio** | Elegí un servicio (ej. Botox) + marcá un día (ej. 29-jun) **sin elegir médico** | El grafiquito muestra **N swimlanes** (una fila por médico del servicio, 07–21h, bandas verde=atención / rojo=ocupado). NO hay que tantear. |
| **1c** | Hora → **filtra** a los disponibles | Poné una hora (ej. 09:00) | La columna derecha (`FreeDoctorsList`) muestra **solo los libres a esa hora** + aparece el **cursor de hora** vertical en el strip. 1-clic elige médico. |
| **1d** | Cambio de día → **auto-refresh** | Cambiá el día | El strip se **actualiza solo** con la disponibilidad del nuevo día (sin recargar). |
| **§6** | Diseño a **ratificar** | Mirá el conjunto | Swimlane-por-médico (strip = "todos el día de un vistazo") + columna derecha re-roleada (lista = "quién libre a esta hora"). ¿OK así, o querés **una sola superficie** (fundir la lista en el strip)? |

## Casos borde (opcionales, si querés cubrir)
- **Servicio sin médicos** → empty_state ("sin médicos para este servicio").
- **Médico sin horario ese día** → su lane dice "Sin horario".
- **Endpoint caído** → el strip muestra error + retry (fail-closed).

## Cierre
- Elegí médico → chip de disponibilidad (la **autoridad** sigue siendo `availability/check` + EXCLUDE en el submit; el filtro del strip es advisory) → **Crear cita** (happy path, ya verificado en base).
- **Firmás** `chris_verify.signoff` (result: SATISFIED | SATISFIED_WITH_FOLLOWUPS | REJECTED) + cada corrección entra a `rounds`.

## Pendientes de base (no del delta, los podés cerrar acá también)
409 solape live · toast "Cita creada" + grilla refleja (la sesión expiró tras el 201 la vez pasada).

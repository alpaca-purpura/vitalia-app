<!-- voseo-allowed: doc interno de proceso -->
# WORK-ORDER bug7 round 3 — staff/horarios creación de bloques = clon Google Calendar

> **Para:** `/dev-team vitalia vitalia-fase2-lisa-doctores` (conversación nueva, contexto fresco).
> **Origen:** G round-2 REJECTED por Chris 2026-06-12. Round-1 (`f85c8ce2`) arregló feedback (toasts) pero NO se ejerció live → 3 defectos reales quedaron vivos. **Regla de este round: NADA se declara arreglado sin que VOS lo ejerzas con Playwright real-backend.** (`verification-real-not-200` + Critical Rule #37).

## Estado al escribir esto (2026-06-12)

- Story `vitalia-fase2-lisa-doctores`: `state: developed` · `phase: AWAIT_CHRIS_VERIFY` · `chris_verify.signoff: null` · bug7 en `checkpoint.md::regression_2026-06-12_bug7` (rounds 1-2 documentados).
- Server save **SANO** (evidencia round-1): BE logs `POST /availability-blocks` → 201 (recurrent, slots materializados, phi_audit) + `test_availability_blocks_api.py` 14/14 (incl. one_off). El problema es FE.
- Stack dev UP: FE `localhost:3002` · BE `localhost:8002` (health 200) · tunnel `dev-app.vitalialat.com`.
- Auth e2e: `vitalia/frontend/playwright/.clerk/user.json` (storageState, refrescar si stale) · user `dr.demo@vitalialat.com` · tenant `e69a691d-070e-5caf-a053-6e74642ec100` (Sanaré) · clinic `f035be5b-0ac4-5210-8fc3-395650ca2b83` · doctor con datos: `2464fad7-2124-46a0-9b41-cef9e489cc8d`.
- Specs e2e existentes (patrón a seguir): `vitalia/frontend/e2e/regression/vitalia-fase2-lisa-doctores/*.spec.ts` + fixtures anti-burbuja `vitalia/frontend/e2e/fixtures/base.ts` (NUNCA `@playwright/test` directo). Correr: `cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/regression/vitalia-fase2-lisa-doctores/<spec> --project=smoke` (verificar project en playwright.config).
- Proceso: lock `bash scripts/git/session-lock.sh acquire code:clinics dev-team vitalia-fase2-lisa-doctores` · builders **Sonnet** (mandato Chris `model_mandate_2026_06_12`) · TDD RED-first · commit por pathspec · al cerrar → pausa G round-3 (NO auditor sin signoff Chris).

## Defectos reportados por Chris (G round-2) + diagnóstico previo

### D-1 · Botón Guardar invisible (claro Y oscuro) — ROOT CAUSE CONFIRMADO
`vitalia/frontend/src/features/lisa/components/staff/workspace/horarios/BloquePopover.tsx:1015`:
```
className="h-7 text-xs bg-[--agent-lisa] hover:bg-[--agent-lisa]/90 text-black"
```
- Tailwind es **v4.1** (`package.json`). La sintaxis `bg-[--var]` (shorthand v3) **NO genera CSS en v4** → botón SIN background + `text-black` → invisible en dark, fantasma en light. Esto explica el reporte ORIGINAL "el botón guardar no existe".
- La var además es HSL crudo (`--agent-lisa: 156 100% 41%` en `globals.css:62`) → ni `var()` directo serviría.
- **Fix:** usar el token class existente `bg-agent-lisa hover:bg-agent-lisa/90` (definido `tailwind.config.ts:62` = `hsl(var(--agent-lisa))`; DayChip `:339` ya lo usa bien). Greppear el repo por **otros** `-[--` rotos en horarios/staff y arreglarlos en el mismo pase (canon §0 prohíbe arbitrary values).
- **Test:** Playwright assert `getComputedStyle(btn).backgroundColor` ≠ transparente/rgba(0,0,0,0) en **ambos** themes (toggle dark) + screenshot de evidencia.

### D-2 · Drag-create ROTO (regresión) — REPRO PRIMERO
Chris: "se ha malogrado la creación de bloque arrastrando el mouse — no se seleccionan las celdas y sale el popup; antes funcionaba".
- Sospecha: delta v3 (squash `fdedd706`) tocó `AvailabilityCalendar.tsx` (agregó `DndContext` dnd-kit para occurrences-drag + vista mes). Posible conflicto: dnd-kit captura pointer events → el mousedown/mousemove del drag-to-create (`handleMouseDown`/`setDragDraft` ~:326-365) ya no recibe la secuencia → el click suelto abre el popover sin rango seleccionado.
- **Repro con Playwright**: `page.mouse.down()` en celda → `move` 2-3 horas abajo → `up` → assert: overlay de drag visible durante el gesto + popover abre con `startTime/endTime` = rango arrastrado (no 1 hora default). Escribilo como test RED ANTES de tocar código.
- Comportamiento target = **Google Calendar**: arrastrar pinta el rango en vivo; soltar abre el editor con ese rango; click simple (sin drag) crea bloque de 1 hora en esa celda.

### D-3 · "No guardan correctamente en los distintos escenarios" — MATRIZ COMPLETA
Chris no detalló cuáles — generá y probá **TODA** la matriz (cada caso = un test e2e real-backend que ejerce el write + assert calendario refresca + bloque visible donde corresponde):

| # | Caso | Assert clave |
|---|---|---|
| 1 | Click simple celda → "No se repite" → Crear | POST `one_off` 201 (★ NUNCA visto en logs — path sospechoso) · bloque SOLO esa fecha · no aparece otra semana |
| 2 | Drag 9-12 → "No se repite" → Crear | rango exacto 09:00-12:00 one_off |
| 3 | Drag → "Cada semana el {día}" open_ended → Crear | recurrent interval=1 · aparece semana actual + siguiente |
| 4 | "Todos los días" → Crear | daysOfWeek 7 elementos · pinta L-D |
| 5 | "Cada 2 semanas" → Crear | interval=2 · semana siguiente VACÍA, subsiguiente pintada |
| 6 | "Personalizado" chips L+J interval=2 + termina tras 8 repeticiones → Crear | occurrences=8 · resumen humano exacto · proyección corta a 8 |
| 7 | Recurrente con "termina en fecha" → Crear | end_date inclusivo (último día pinta) |
| 8 | Recurrente occurrences=2 | EXACTO 2 semanas pintadas (regresión D3-C previa) |
| 9 | Editar bloque existente (click → cambiar hora → Actualizar) | PATCH 200 · calendario actualiza |
| 10 | Eliminar bloque | DELETE · desaparece · preservedAppointments msg si aplica |
| 11 | Validación: custom sin días → Crear | toast "Revisa los campos del bloque" · NO POST |
| 12 | Error server (forzá 4xx con payload inválido o doctor ajeno) | toast error · popover queda abierto |
| 13 | Toast success en TODOS los creates | "Bloque guardado" visible |
| 14 | Vista mes refleja lo creado | bloque visible en MonthCalendar |
| 15 | Botón guardar visible + clickeable ambos themes | D-1 |

Cleanup: borrá los bloques creados por los tests al final (DELETE) — no dejar basura en el tenant demo.

## Flujo exigido

1. Lock + leer este work-order + `checkpoint.md::regression_2026-06-12_bug7` (rounds previos).
2. **RED primero**: specs Playwright de la matriz (los que fallan hoy: D-1 computed-style, D-2 drag, casos de matriz rotos). Confirmá RED corriéndolos.
3. Fix D-1 (token class) — trivial. Fix D-2 (investigar conflicto dnd-kit vs drag-create; el fix NO puede romper occurrences-drag ni vista mes — sus specs existentes deben seguir verdes). Fix lo que la matriz destape en D-3.
4. GREEN: matriz completa + suites previas (`horarios.test.tsx`, `month-calendar.test.tsx`, `bloque-popover-save.test.tsx` 3/3, e2e regression existentes) + tsc/eslint 0.
5. **Live-verify #37 vos mismo**: leer `docker logs luana-dev-vitalia_backend_dev-1` post-runs → confirmar 201s (incl. el primer `one_off` de la historia) + `availability_block_created` + phi_audit. Registrar `dod_evidence` nuevas en checkpoint (round 3).
6. Documentar: `T-FIX-bug7-round3-result.md` + update `regression_2026-06-12_bug7` (status, fixes, commits) + entry `chris-input.md` + push.
7. **PAUSA G round-3**: kit de 2 minutos para Chris (qué clickear). NO handoff `/auditor` sin su signoff.

## Anti-patterns de este round
- ❌ Declarar "arreglado" sin correr el spec correspondiente vos mismo (causa de round-2)
- ❌ e2e que mockee el backend (falso verde — base.ts real)
- ❌ Fix D-2 que rompa occurrences-drag/vista-mes (delta v3 shipped)
- ❌ `vitest -u` / regenerar goldens sin revisar diff
- ❌ Tocar `core/` u otros módulos (scope: features/lisa staff/horarios + sus tests)

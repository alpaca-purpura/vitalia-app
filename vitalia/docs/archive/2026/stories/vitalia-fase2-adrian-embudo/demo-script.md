# Demo Script — vitalia-fase2-adrian-embudo
# Embudo de Adrián — supervisión del funnel clínico dental

> **demo_required: true** (story funcional user-reachable)  
> **Derivado de:** 01-spec.md § Gherkin SC-board / SC-nuevo / SC-1 / SC-1b  
> **Entorno:** `https://dev-app.vitalialat.com` (dev-app cloudflared → localhost:3002/8002)

---

## SETUP

**Requisitos previos:**

1. `make dev-app-vitalia` está corriendo (o `docker ps | grep vitalia` muestra los 3 containers UP).
2. Abrir Chrome en `https://dev-app.vitalialat.com`.
3. Iniciar sesión con `dr.demo@vitalialat.com` (contraseña en `vitalia/.env.dev::DEV_APP_TEST_PASSWORD`).
4. Verificar que llega a la pantalla principal (shell-organism con Ribbon de agentes).
5. Verificar en los logs que `/api/v1/crm/board` retorna 200:
   ```bash
   docker logs luana-dev-vitalia_backend_dev-1 2>&1 | grep 'crm/board' | tail -5
   ```

---

## HAPPY PATH (en lenguaje de usuario)

### Paso 1 — Navegar al Embudo de Adrián

1. En el Ribbon (barra de pestañas con los especialistas), hacer click en **"Adrián"**.
2. En la SubTabsBar (barra secundaria), hacer click en **"Embudo"**.
3. **Verificar:** el tablero Kanban aparece con columnas (Interesado, Calificando, Consulta agendada, Plan presentado, Reservado).
4. **Verificar:** la tira de KPIs (total de leads, leads calientes, tasa de conversión) se carga arriba del tablero.
5. **Verificar:** no hay burbuja de error de Next.js (overlay de error → si aparece, es un bug).

### Paso 2 — Crear un nuevo lead

1. Hacer click en el botón **"+ Nuevo lead"** en el header del embudo.
2. Se navega a `/adrian/embudo/nuevo` (URL cambia — es una página con URL propia, no un modal).
3. Completar el formulario con:
   - **Nombre:** `Paciente Demo Chris`
   - **Canal:** seleccionar `WhatsApp` del dropdown
   - **Teléfono:** `+99 9 5555 0001`
   - **Servicio de interés:** `Ortodoncia invisible`
   - **Notas:** `Interesado en Invisalign para boda. Presupuesto: $3000 USD.`
4. Hacer click en **"Crear lead"**.
5. **Verificar:** se redirige al tablero con el lead nuevo resaltado (ring púrpura + animación pulso) en la columna "Interesado".
6. **Verificar en logs:** `POST /api/v1/crm/leads 201 Created` sin Traceback.

### Paso 3 — Mover un lead a la siguiente etapa

1. En el tablero, encontrar un lead en la columna **"Interesado"**.
2. Hacer click en el botón **"›"** (ChevronRight) que aparece en la esquina inferior derecha de la card.
   - Alternativa: arrastrar la card con el mouse hasta la columna **"Calificando"**.
3. El lead se mueve a "Calificando" con un toast de confirmación.
4. **Verificar:** la card aparece ahora en la columna "Calificando".
5. **Verificar en logs:** `PATCH /api/v1/crm/leads/{id}/stage 200 OK` y `funnel_transition_complete from_stage=interesado to_stage=calificando`.
6. Recargar la página (F5) y verificar que el lead sigue en "Calificando" (persistencia).

### Paso 4 — Ver el detalle de un lead

1. Hacer click en el nombre de un lead en cualquier card.
2. Se navega a `/{tenantId}/adrian/embudo/{leadId}/resumen` (URL con el ID del lead).
3. **Verificar:** EntitySubNavBar muestra "← Embudo · [Nombre del lead]" con pestañas **Resumen** e **Historial**.
4. En **Resumen:** ver datos del lead (nombre, canal, score, etapa, etiquetas).
5. En **Historial:** ver el log de actividad (transiciones de etapa, mensajes).
6. Volver al tablero con el enlace "← Embudo".

### Paso 5 — Mover etapa con override (salto de etapa)

1. En el tablero, intentar mover un lead desde "Interesado" directo a "Plan presentado" (salto de 3 etapas).
2. Se abre un diálogo **"Cambio de etapa con override"** que pide la razón.
3. Escribir: `Cliente muy comprometido, tiene reunión con especialista mañana.`
4. Hacer click en **"Confirmar cambio"**.
5. **Verificar:** lead movido. Toast de confirmación. Historial del lead registra el override.

---

## EDGE CASES (reglas de negocio negativas)

### Caso E-1 — Crear lead sin canal (RN-14)
1. Ir a `/nuevo`, completar solo el nombre, NO seleccionar canal.
2. Hacer click en "Crear lead".
3. **Verificar:** error de validación inline "El canal es requerido". El formulario NO envía.

### Caso E-2 — Crear lead sin teléfono ni correo (RN-15)
1. Ir a `/nuevo`, completar nombre + canal, dejar teléfono y correo vacíos.
2. Hacer click en "Crear lead".
3. **Verificar:** error "Ingresa al menos un teléfono o correo". El formulario NO envía.

### Caso E-3 — Intentar mover a "Reservado" por drag (RN-4)
1. Arrastrar una card al área de la columna "Reservado".
2. **Verificar:** toast de warning "🔒 Reservado se alcanza con el depósito. El pago confirma automáticamente esta etapa." El lead NO se mueve.

### Caso E-4 — Ver leads congelados (Recuperar)
1. En la SubTabsBar de Adrián, hacer click en **"Recuperar"** (si existe — sub-tab hermana de Embudo).
2. **Verificar:** lista de leads congelados (sin actividad 14+ días o marcados manualmente).

---

## TEARDOWN

1. El lead de prueba "Paciente Demo Chris" puede quedarse en la DB de dev (no requiere limpieza — es data sintética, no PHI real).
2. Si quieres restaurar el estado inicial, hacer PATCH manual al lead para devolverlo a "Interesado" o eliminarlo vía admin.
3. Backend logs: verificar que no hubo ERROR ni Traceback durante toda la sesión:
   ```bash
   docker logs luana-dev-vitalia_backend_dev-1 2>&1 | grep -E 'ERROR|Traceback' | tail -20
   ```
   Resultado esperado: sin líneas relevantes al demo.

---

## Demo signoff (Chris)

```yaml
demo_required: true
demo_signoff:
  signed_by:
  date:
  result:    # APPROVED | APPROVED_WITH_NOTES | REJECTED
  notes: ""
  open_items: []
```

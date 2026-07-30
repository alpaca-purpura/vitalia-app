# Demo Script — vitalia-fase2-adrian-inbox (★ 2-modos · amendment 2026-06-04)

> **Critical Rule #37 §5 · `definition-of-done-live-verify.md`.** Guion de **product demo** para que Chris valide manualmente la story, paso a paso, contra el MISMO `dev-app` que usó el dev en la live-verify. Lenguaje de usuario (sin curl/tokens/URLs internas). `demo_required: true` por ser UI user-reachable.
>
> Derivado de los Gherkin de `01-spec.md § Gherkin scenarios` **modelo 2-modos** (SC-mode · SC-4 pausa · SC-composer · SC-privacy · SC-1 · SC-2). El full-canvas (SC-5) vive en la story de shell `vitalia-bugfix-shell-nav-scroll-errors` (`done`); el PHI firewall (SC-3) + cross-tenant (SC-10) están cubiertos por tests de backend.

## SETUP (estado inicial)

- **Entorno:** `make dev-app-vitalia` → `https://dev-app.vitalialat.com` (el túnel Cloudflare → stack local; `localhost:3002` **no** sirve `/api`).
- **Usuario de prueba:** `dr.demo@vitalialat.com` (rol **owner** = operador del inbox, tenant Sanaré MX).
- **Datos previos (seed):**
  - Conversación **Carlos Ramírez Ortega** — WhatsApp — modo "Adrián decide" (conv `11111111-1111-5111-8111-111111111111`).
  - Conversación **Persistencia Verificada** — Instagram (conv `22222222-2222-5222-8222-222222222222`).
- **Cómo llegar:** Iniciar sesión → clic en **Adrián** en el Ribbon → clic en **Inbox** en la barra de sub-tabs. (Si el navegador trae chunks viejos: Empty-Cache + Hard-Reload — gotcha de Turbopack.)

---

## HAPPY PATH

### Parte A — Inbox y conversaciones

1. Iniciar sesión con `dr.demo@vitalialat.com` y navegar a **Adrián → Inbox**.
   **Esperado:** el inbox real (no el placeholder gris): lista de conversaciones a la izquierda, thread al centro, ficha de contacto a la derecha. La más reciente (Carlos) se autoselecciona.

2. Observar la lista.
   **Esperado:** cada conversación muestra el nombre del paciente, el **logo real** del canal (WhatsApp / Instagram), el chip de etapa coloreado y el punto de no-leído si corresponde. La conversación seleccionada se resalta (barra cian + fondo suave).

3. Mirar el thread de **Carlos** (WhatsApp).
   **Esperado:** historial de mensajes con burbujas (paciente a la izquierda, Adrián/humano a la derecha) + separadores de día + horas por burbuja; la URL cambió a `?conv=…` **sin** datos del paciente; el fondo del thread tiene el wallpaper crema con el logo de WhatsApp tileado (fijo, no se arrastra al hacer scroll).

### Parte B — Modos (2-modos) — *SC-mode*

4. En la cabecera del thread, ver el **toggle de 2 modos**: `[Adrián decide] [Adrián consulta]`. El segmento activo está en **verde**.

5. Pulsar **"Adrián consulta"**.
   **Esperado:** el cambio se guarda (la red muestra `PATCH …/mode` → 200); el segmento "Adrián consulta" pasa a verde/activo; el modo persiste al recargar.

6. Volver a pulsar **"Adrián decide"**.
   **Esperado:** vuelve a "Adrián decide" verde (`PATCH …/mode` 200 de nuevo).

### Parte C — Pausar Adrián + escribir (reemplaza "Tomar control") — *SC-4 + SC-composer*

7. En el **dock al pie** del thread, ver la barra de estado: dot **verde intermitente** + "Adrián está atendiendo esta conversación", y el botón **"Pausar"** en rojo tenue. Debajo, el **composer** (caja de texto) está montado y habilitado.

8. Pulsar **"Pausar"**.
   **Esperado:** se abre un modal con **exactamente 2 botones** — `[Pausar 60 minutos]` y `[Pausar permanente]` (rojo) — y una X para cerrar. **No** hay campo de comentario/razón.

9. Elegir **"Pausar 60 minutos"**.
   **Esperado:** la pausa se guarda (`POST …/pause` → 200); la barra del dock pasa a "Adrián pausado · escribes tú" (dot apagado); el composer queda para que escribas vos como humano.

10. (Opcional, lo ejerce Chris) Escribir un mensaje en el composer y pulsar **Enviar**.
    **Esperado:** el mensaje sale firmado por el humano y aparece en el thread.

### Parte D — Consulta (propuesta) — *SC-2*

11. Cambiar a **"Adrián consulta"** y, cuando Adrián tenga una propuesta lista, ver el banner **"Adrián tiene una propuesta lista"** con `[Aprobar y enviar]` / `[Editar propuesta]`.
    **Esperado:** ningún mensaje sale sin aprobación humana; al editar y aprobar, el mensaje sale con el texto editado.

### Parte E — Ficha de contacto (leads visibles) — *SC-privacy*

12. Abrir la ficha de contacto (botón **"Perfil"** en la cabecera).
    **Esperado:** nombre, teléfono y correo del lead se ven **completos** (sin `***`) — ej. "Carlos Ramírez Ortega · +52 55 9876 5432". "Servicio de interés" siempre visible (valor o "Aún no detectado"); "Etapa de la venta" como única etiqueta (sin un campo "Estado" duplicado). La X cierra la ficha.

### Parte F — Glass-box — *SC-1*

13. Mirar la parte inferior del thread: el **Activity stream** ("Actividad de Adrián").
    **Esperado:** registra cronológicamente lo que hace Adrián (mensajes, herramientas, cambios de modo, pausas). Ya no hay un ícono 🛠 de herramientas en la cabecera (la actividad vive acá abajo).

---

## EDGE CASES (reglas de negocio negativas)

### RBAC operador — *RN-15*

- **Acción:** con `dr.demo` (owner) cambiar el modo y pausar.
  **Esperado:** ambas mutaciones responden 200 (el owner es operador del inbox). Un usuario `marketing`/`sales`/`patient` recibiría 403 (cubierto por `test_router_mode.py`).

### PHI bloqueada por canal no-encriptado — *SC-3 (cubierto por backend test)*

- **Comportamiento:** si el paciente pregunta por su diagnóstico/resultados por WhatsApp, `ComplianceService` bloquea el outbound y Adrián deriva al portal seguro. Verificado por `test_phi_voice_redirect.py` (13 tests PHI verdes). PHI clínica nunca sale por canal no-encriptado.

### Cross-tenant bloqueado — *SC-10*

- **Acción:** modificar el UUID de `?conv=` para apuntar a una conversación de otro tenant.
  **Esperado:** la API responde 404 sin filtrar datos; el thread muestra su estado de error. (Aislamiento por dual filter tenant+clinic.)

### Estado vacío / error de red — *SC-7 / SC-8*

- **Esperado:** sin conversaciones → empty state explicativo ("Aquí va a aparecer la conversación"); thread con 404/5xx → estado de error + lista usable.

### Full-canvas (foco total) — *SC-5 (story de shell)*

- El botón "Modo conversación" que colapsa a Valeria y su coexistencia con la ficha de contacto se verifica en `vitalia-bugfix-shell-nav-scroll-errors` (`done`).

---

## TEARDOWN

- Las conversaciones de prueba son datos de desarrollo — no requieren limpieza.
- Carlos (conv `11111111-1111-5111-8111-…`) puede quedar **pausado 60 min** tras la prueba de pausa — se auto-expira (demuestra que la pausa funciona).
- El inbox queda en el estado natural del tenant Sanaré MX.

---

## Resultado (firmado por Chris)

```yaml
demo_signoff:
  signed_by: Chris
  date: 2026-06-04
  result: APPROVED_WITH_NOTES
  notes: >-
    Chris probó el inbox live en dev-app (rondas r6-r8: modo 2-estados, pausa
    60/permanente, composer, leads visibles, wallpaper/cursor) y lo da por REVISADO.
    Quedan solo detalles estéticos menores, diferidos.
  open_items:
    - { item: "Detalles estéticos menores (no enumerados) — capturar próxima ronda", severity: low, disposition: defer }
```

<!-- voseo-allowed: template de proceso interno -->

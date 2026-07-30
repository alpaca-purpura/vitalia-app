# Booking Widget — Guía de integración para propietarios de clínicas

> **Versión:** 1.0.0 · **Actualizado:** 2026-05-14
>
> Esta guía explica cómo integrar el widget de reservas de Vitalia en el sitio web de tu
> clínica. Está dirigida a propietarios de clínicas y desarrolladores web.

---

## Índice

1. [¿Qué es el widget de reservas?](#1-qué-es-el-widget-de-reservas)
2. [Snippet de integración (copia y pega)](#2-snippet-de-integración-copia-y-pega)
3. [Protocolo postMessage](#3-protocolo-postmessage)
4. [URL canónica alternativa](#4-url-canónica-alternativa)
5. [CDN y hosting](#5-cdn-y-hosting)
6. [Seguridad y validación de origen](#6-seguridad-y-validación-de-origen)
7. [Opciones de configuración](#7-opciones-de-configuración)
8. [Solución de problemas frecuentes](#8-solución-de-problemas-frecuentes)

---

## 1. ¿Qué es el widget de reservas?

El widget de reservas de Vitalia es una aplicación React embebida que permite a los
pacientes reservar turnos directamente desde el sitio web de tu clínica, sin salir de él.

**Características principales:**

- Selección de tratamiento/oferta disponible
- Visualización de disponibilidad del doctor en tiempo real
- Captura de pago prepago (MercadoPago o Stripe, según tu configuración)
- Formulario de consentimiento informado cuando el tratamiento lo requiere
- Confirmación automática vía email/SMS
- Diseño adaptable (responsive) para móvil y escritorio

**Dos formas de integración disponibles:**

| Opción | Cuándo usarla |
|---|---|
| **Widget iframe** (esta guía) | Tienes un sitio propio y quieres integrar el proceso de reserva directamente en él |
| **URL canónica** | No tienes sitio propio o prefieres derivar el tráfico al subdominio de Vitalia |

---

## 2. Snippet de integración (copia y pega)

Pega este código en el HTML de la página donde quieres mostrar el widget de reservas.
Reemplaza `TU_CLINIC_SLUG` con el identificador de tu clínica (lo encuentras en
Configuración → Perfil de la clínica → Identificador).

### Código completo

```html
<!-- Vitalia Booking Widget — v1.0 -->
<!-- Más información: https://docs.vitalia.health/widget -->

<!-- Contenedor del widget -->
<div id="vitalia-booking-widget" style="width: 100%; min-height: 600px;">
  <!-- El widget se carga aquí automáticamente -->
</div>

<!-- Script del widget (cargado desde CDN de Vitalia) -->
<script
  src="https://cdn.vitalia.health/widget/v1/vitalia-widget.js"
  data-clinic-slug="TU_CLINIC_SLUG"
  data-container="vitalia-booking-widget"
  crossorigin="anonymous"
  async
></script>

<!-- Manejo de eventos del widget (opcional pero recomendado) -->
<script>
window.addEventListener('message', function(event) {
  // IMPORTANTE: siempre verifica el origen del mensaje
  if (event.origin !== 'https://cdn.vitalia.health') return;

  var data = event.data;
  if (!data || !data.type) return;

  switch (data.type) {
    case 'widget:loaded':
      // El widget se cargó correctamente
      console.log('Vitalia widget listo. Oferta disponible:', data.payload.offers_count);
      break;

    case 'widget:resize':
      // El widget solicita cambio de altura (ajuste dinámico)
      var container = document.getElementById('vitalia-booking-widget');
      if (container && data.payload.height) {
        container.style.minHeight = data.payload.height + 'px';
      }
      break;

    case 'widget:booking-confirmed':
      // El paciente completó la reserva exitosamente
      console.log('Reserva confirmada:', data.payload.booking_id);
      // Opcional: redirigir o mostrar mensaje de agradecimiento
      // window.location.href = '/gracias';
      break;

    case 'widget:payment-redirect':
      // MercadoPago o Stripe requieren redirección para completar el pago
      // El widget redirige automáticamente; este evento es informativo
      console.log('Redirigiendo al procesador de pago:', data.payload.provider);
      break;
  }
});
</script>
```

### Integración mínima (sin manejo de eventos)

Si solo necesitas mostrar el widget sin personalizar el comportamiento:

```html
<div id="vitalia-booking-widget" style="width: 100%; min-height: 600px;"></div>
<script
  src="https://cdn.vitalia.health/widget/v1/vitalia-widget.js"
  data-clinic-slug="TU_CLINIC_SLUG"
  data-container="vitalia-booking-widget"
  crossorigin="anonymous"
  async
></script>
```

### Integración con oferta específica

Si quieres que el widget muestre solo un tratamiento particular (por ejemplo, en la página
de un tratamiento específico):

```html
<div id="vitalia-booking-widget" style="width: 100%; min-height: 600px;"></div>
<script
  src="https://cdn.vitalia.health/widget/v1/vitalia-widget.js"
  data-clinic-slug="TU_CLINIC_SLUG"
  data-container="vitalia-booking-widget"
  data-offer-id="OFFER_UUID"
  crossorigin="anonymous"
  async
></script>
```

> Obtén el `OFFER_UUID` en tu panel de Vitalia: Ofertas → [nombre del tratamiento] →
> Configuración → Identificador de oferta.

---

## 3. Protocolo postMessage

El widget se comunica con la página que lo contiene mediante la API estándar `window.postMessage`
del navegador. Todos los mensajes tienen la siguiente estructura:

```json
{
  "type": "widget:{evento}",
  "payload": { ... }
}
```

### 3.1 Eventos emitidos por el widget

#### `widget:loaded`

Disparado cuando el widget termina de cargarse y está listo para recibir interacciones.

```json
{
  "type": "widget:loaded",
  "payload": {
    "clinic_slug": "aurora-dental-ar",
    "offers_count": 6,
    "widget_version": "1.0.0"
  }
}
```

**Cuándo usarlo:** para ocultar un spinner de carga personalizado o activar elementos de
la página que dependen de que el widget esté disponible.

---

#### `widget:resize`

Disparado cuando el contenido del widget cambia de altura (por ejemplo, al avanzar entre
pasos del flujo de reserva). El widget calcula su alto interno y solicita que el contenedor
se ajuste.

```json
{
  "type": "widget:resize",
  "payload": {
    "height": 720
  }
}
```

**Cuándo usarlo:** para evitar barras de desplazamiento dentro del iframe. El snippet de
ejemplo ya incluye el código para esto.

**Nota:** El widget no puede modificar directamente el CSS del padre (restricción de seguridad
de los iframes). Usa este evento para ajustar el contenedor desde tu código.

---

#### `widget:booking-confirmed`

Disparado cuando el paciente completa exitosamente el proceso de reserva (pago confirmado +
consentimiento firmado si aplica).

```json
{
  "type": "widget:booking-confirmed",
  "payload": {
    "booking_id": "b8a3f2e1-4c7d-4e9a-b1f2-3a4c5d6e7f8a",
    "offer_name": "Implante Dental",
    "scheduled_at": "2026-06-10T10:00:00-03:00",
    "payment_status": "confirmed_deposit",
    "amount_paid": 150.00,
    "currency": "USD"
  }
}
```

**Cuándo usarlo:** para registrar la conversión en tu analítica web, mostrar una página
de agradecimiento personalizada o disparar un pixel de seguimiento.

---

#### `widget:payment-redirect`

Disparado cuando el procesador de pago requiere una redirección externa (flujo de pago de
MercadoPago o Stripe). El widget gestiona automáticamente la redirección; este evento es
informativo para que puedas registrarlo.

```json
{
  "type": "widget:payment-redirect",
  "payload": {
    "provider": "mercadopago",
    "booking_id": "b8a3f2e1-4c7d-4e9a-b1f2-3a4c5d6e7f8a"
  }
}
```

**Nota:** Tras completar el pago, MercadoPago/Stripe redirigen de vuelta al widget con el
resultado. El widget emite `widget:booking-confirmed` o muestra el error correspondiente.

---

### 3.2 Verificación del origen del mensaje

**Siempre verifica que `event.origin` sea `https://cdn.vitalia.health`** antes de procesar
un mensaje. Ignorar esta verificación puede exponer tu sitio a ataques de cross-site scripting.

```javascript
// ✅ Correcto — verifica el origen
window.addEventListener('message', function(event) {
  if (event.origin !== 'https://cdn.vitalia.health') return;
  // procesar evento...
});

// ❌ Incorrecto — sin verificación de origen
window.addEventListener('message', function(event) {
  // cualquier página puede enviar mensajes aquí — vulnerabilidad
  var data = event.data;
  // procesar evento...
});
```

---

## 4. URL canónica alternativa

Si no puedes o no quieres integrar el iframe, puedes derivar a los pacientes a la URL
canónica de tu clínica en Vitalia:

```
https://app.vitalia.health/public/{clinic-slug}/booking/
```

Ejemplos:
- `https://app.vitalia.health/public/aurora-dental-ar/booking/`
- `https://app.vitalia.health/public/mindful-santiago-cl/booking/`
- `https://app.vitalia.health/public/sanare-latam-mx/booking/`

### Ventajas de la URL canónica

- No requiere código de integración.
- La experiencia de usuario es idéntica al widget.
- Funciona directamente desde WhatsApp, Instagram, email o cualquier canal.
- La URL canónica es la misma que usa el sales agent al enviar links de reserva.

### Cuándo usar iframe vs. URL canónica

| Situación | Recomendación |
|---|---|
| Tienes un sitio con diseño propio y quieres mantener la experiencia dentro de él | **Iframe** |
| Compartes el link de reserva por WhatsApp, email o redes sociales | **URL canónica** |
| Tu sitio tiene restricciones de Content Security Policy (CSP) que bloquean iframes | **URL canónica** |
| Quieres mayor integración con tu analítica web (eventos postMessage) | **Iframe** |
| No tienes sitio web propio | **URL canónica** |

---

## 5. CDN y hosting

El widget se sirve desde la CDN de Vitalia para garantizar disponibilidad y rendimiento.

### URLs de producción

```
Script principal:   https://cdn.vitalia.health/widget/v1/vitalia-widget.js
Estilos CSS:        https://cdn.vitalia.health/widget/v1/vitalia-widget.css
Mapa de fuentes:    https://cdn.vitalia.health/widget/v1/vitalia-widget.js.map
```

### Versiones disponibles

| URL | Descripción |
|---|---|
| `/widget/v1/vitalia-widget.js` | Versión estable actual (recomendada) |
| `/widget/latest/vitalia-widget.js` | Siempre la versión más reciente (puede tener cambios sin aviso) |

**Recomendación:** usa siempre la URL con versión fija (`/widget/v1/`) para evitar
actualizaciones inesperadas en tu sitio.

### Política de CORS

El widget acepta requests desde cualquier dominio. El atributo `crossorigin="anonymous"` en
el tag `<script>` es requerido para que los mapas de fuente funcionen correctamente en
herramientas de desarrollo.

### Disponibilidad del CDN

- **SLA:** 99.9% disponibilidad
- **Regiones:** CDN con PoPs en Buenos Aires, Santiago, Ciudad de México, São Paulo y Miami
- **Caché:** el widget se cachea en el navegador por 24 horas (Cache-Control: max-age=86400)

### Modo offline del widget

Si el CDN no está disponible, el widget muestra un mensaje de error amigable y proporciona
la URL canónica como fallback:

```
El sistema de reservas está temporalmente fuera de servicio.
Puedes reservar tu turno en: https://app.vitalia.health/public/{clinic-slug}/booking/
```

---

## 6. Seguridad y validación de origen

El servidor de Vitalia valida que los requests del widget provengan de dominios autorizados.

### 6.1 Registro de dominio permitido

Para que el iframe funcione en tu dominio personalizado, debes registrar el dominio en tu
panel de Vitalia:

1. Inicia sesión en tu panel de Vitalia.
2. Ve a **Configuración** → **Widget de reservas** → **Dominios permitidos**.
3. Agrega tu dominio (ej. `clinicadentalaurora.com.ar`).
4. Haz clic en **Guardar cambios**.

Una vez registrado, el servidor agrega tu dominio a la lista de orígenes permitidos en la
cabecera `Content-Security-Policy` del widget.

### 6.2 Cómo funciona la validación

Cuando el widget carga en tu página:

1. El navegador envía el header `Origin: https://tu-dominio.com` al CDN.
2. El CDN verifica que el dominio esté registrado para el `clinic-slug` especificado.
3. Si el dominio está autorizado: el CDN responde con `Access-Control-Allow-Origin: https://tu-dominio.com`.
4. Si el dominio **no** está autorizado: el script carga pero muestra un aviso de seguridad y no procesa reservas.

### 6.3 Headers de seguridad recomendados para tu sitio

Agrega estos headers al servidor de tu sitio para mejorar la seguridad:

```
Content-Security-Policy: frame-src https://cdn.vitalia.health; script-src 'self' https://cdn.vitalia.health
X-Frame-Options: SAMEORIGIN
```

### 6.4 HTTPS obligatorio

El widget **solo funciona en páginas servidas por HTTPS**. Si tu sitio usa HTTP, el widget
mostrará un error de seguridad y derivará a la URL canónica.

---

## 7. Opciones de configuración

El widget acepta los siguientes atributos `data-*` en el tag `<script>`:

| Atributo | Requerido | Descripción | Ejemplo |
|---|---|---|---|
| `data-clinic-slug` | Sí | Identificador único de tu clínica | `aurora-dental-ar` |
| `data-container` | Sí | ID del elemento HTML contenedor | `vitalia-booking-widget` |
| `data-offer-id` | No | UUID de la oferta a mostrar (preselecciona el tratamiento) | `b8a3f2e1-...` |
| `data-locale` | No | Idioma del widget (default: `es`) | `es` |
| `data-primary-color` | No | Color primario en hex (personalización básica) | `#0EA5E9` |
| `data-hide-header` | No | Ocultar el header del widget con logo de Vitalia | `true` |
| `data-compact` | No | Modo compacto — menos padding, diseño condensado | `true` |

**Ejemplo con todas las opciones:**

```html
<div id="vitalia-booking-widget"></div>
<script
  src="https://cdn.vitalia.health/widget/v1/vitalia-widget.js"
  data-clinic-slug="aurora-dental-ar"
  data-container="vitalia-booking-widget"
  data-offer-id="b8a3f2e1-4c7d-4e9a-b1f2-3a4c5d6e7f8a"
  data-locale="es"
  data-primary-color="#0EA5E9"
  data-hide-header="true"
  data-compact="false"
  crossorigin="anonymous"
  async
></script>
```

---

## 8. Solución de problemas frecuentes

### El widget no carga (pantalla en blanco)

1. Verifica que `data-clinic-slug` sea correcto. Lo encuentras en Configuración → Perfil.
2. Verifica que tu dominio esté registrado en la lista de dominios permitidos (sección 6.1).
3. Comprueba que tu sitio use HTTPS.
4. Abre las herramientas de desarrollador del navegador (F12) → pestaña Console → busca errores de Vitalia.

### El iframe no se ajusta en altura correctamente

Asegúrate de incluir el listener del evento `widget:resize` del snippet de la sección 2 y
que el elemento contenedor tenga `width: 100%` y un `min-height` inicial.

### El pago queda pendiente y no se confirma la reserva

MercadoPago y Stripe requieren que el dominio de retorno (return URL) esté configurado en
tu cuenta de pagos. Contacta al soporte de Vitalia (support@vitalia.health) para verificar
la configuración de tu cuenta.

### El evento `widget:booking-confirmed` no se recibe

Verifica que el listener de `message` esté registrado **antes** de que el widget se cargue.
Ubica el segundo bloque `<script>` con el listener antes del tag `<script>` del widget.

---

*Para soporte técnico: support@vitalia.health · Documentación: https://docs.vitalia.health*

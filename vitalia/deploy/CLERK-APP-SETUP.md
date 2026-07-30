# CLERK-APP-SETUP.md — Vitalia Clerk App #2 (Chris ejecuta vía dashboard)

> **Puerta Chris Q4=B:** este documento especifica los pasos para crear la
> aplicación Clerk de Vitalia. Es una app **independiente** de Nicolify —
> los usuarios de Vitalia son propietarios de clínicas (rol `clinic_owner`),
> no los usuarios de Nicolify.
>
> El backend ya tiene el adaptador de webhook implementado en
> `src/modules/vitalia/infrastructure/adapters/clerk_webhook_adapter.py`.
> Solo necesitas proveer las claves que se indican abajo.

---

## Paso 1 — Crear la aplicación en Clerk

1. Entra a [dashboard.clerk.com](https://dashboard.clerk.com).
2. Haz clic en **+ Add application**.
3. Nombre: `vitalia` (o `Vitalia Health` para el nombre visible).
4. Activa los métodos de inicio de sesión que necesites:
   - Email + contraseña (mínimo recomendado).
   - Google OAuth (opcional, mejora conversión).
5. Haz clic en **Create application**.

---

## Paso 2 — Copiar las claves de API

En el dashboard de Vitalia → **Developers** → **API Keys**:

| Clave | Variable de entorno | Dónde usar |
|---|---|---|
| Publishable Key | `VITALIA_CLERK_PUBLISHABLE_KEY` | Frontend Next.js |
| Secret Key | `VITALIA_CLERK_SECRET_KEY` | Backend FastAPI |

Copia ambas claves en `deploy/.env` (desarrollo) y en el Secret de K8s
(`deploy/k8s/secrets.template.yaml` → `kubectl apply` por Chris).

---

## Paso 3 — Configurar el webhook de Clerk

El backend necesita recibir notificaciones cuando un usuario completa el registro
(evento `user.created`) para crear automáticamente el perfil de clínica.

### 3.1 Crear el endpoint de webhook

1. En el dashboard → **Webhooks** → **+ Add Endpoint**.
2. URL del endpoint:
   ```
   https://app.vitalia.health/api/v1/vitalia/webhooks/clerk
   ```
3. Selecciona el evento: `user.created`.
4. Haz clic en **Create**.

### 3.2 Copiar el Signing Secret

Clerk genera un **Signing Secret** (`whsec_...`) para verificar la autenticidad
del webhook (algoritmo HMAC-SHA256 estándar Svix).

Copia ese valor como:

```
VITALIA_CLERK_WEBHOOK_SECRET=whsec_<tu_valor_aqui>
```

Agrega este valor en `deploy/.env` y en el Secret de K8s.

---

## Paso 4 — Configuración JWT (opcional, para uso futuro)

Por defecto, Vitalia usa su propia app Clerk, **independiente** de Nicolify.
No se requiere Single Sign-On entre Nicolify y Vitalia en la Fase 0
(03-arch.md § 5.4 — Q4=B ratificado).

Si en el futuro necesitas federación de identidades entre marcas, configura:
- **JWT Templates** → plantilla personalizada con claims adicionales
  (ej. `active_tenant_id`, `brand_slug=vitalia`).

---

## Resumen de variables de entorno necesarias

```bash
VITALIA_CLERK_PUBLISHABLE_KEY=pk_live_...
VITALIA_CLERK_SECRET_KEY=sk_live_...
VITALIA_CLERK_WEBHOOK_SECRET=whsec_...
```

Estos valores van en:
- Desarrollo local: `deploy/.env`
- K8s producción: `vitalia-secrets` Secret (vía `secrets.template.yaml` + `envsubst`)

---

## Referencia de arquitectura

- `03-arch.md § 5.4` — Clerk app #2 provisioning (Chris UI gate Q4=B)
- `src/modules/vitalia/infrastructure/adapters/clerk_webhook_adapter.py` — implementación del webhook
- `src/modules/vitalia/api/webhook_routes.py` — ruta `/api/v1/vitalia/webhooks/clerk`

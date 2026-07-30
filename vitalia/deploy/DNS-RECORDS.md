<!-- voseo-allowed: ops doc cites CLI commands verbatim — technical, not user-facing UI copy -->
# DNS-RECORDS.md — Vitalia (Chris ejecuta vía Cloudflare dashboard)

> **Puerta Chris Q4=B:** este documento especifica los registros DNS que debes crear
> manualmente en el dashboard de Cloudflare. El equipo de desarrollo preparó
> los manifests y configuraciones; los pasos de abajo los ejecutas tú.

## Prerequisitos

- Tienes acceso al dashboard de Cloudflare para la zona `vitalia.health`.
- El túnel de Cloudflare ya fue creado: `cloudflared tunnel create vitalia-tunnel`
  (el script `deploy/cloudflared/setup-tunnel.sh` guía ese proceso).
- El ID del túnel (`TUNNEL_ID`) está disponible en `~/.cloudflared/<TUNNEL_ID>.json`.

---

## Registros a crear

### 1. Dominio principal de la aplicación

| Campo | Valor |
|---|---|
| Tipo | `CNAME` |
| Nombre | `app` |
| Destino | `<TUNNEL_ID>.cfargotunnel.com` |
| Proxy | Activado (nube naranja) |
| TTL | Auto |

Resultado: `app.vitalia.health` → túnel Cloudflare → servicio K8s `vitalia-app`.

### 2. Dominio CDN (widget embebible + assets estáticos)

| Campo | Valor |
|---|---|
| Tipo | `CNAME` |
| Nombre | `cdn` |
| Destino | `<TUNNEL_ID>.cfargotunnel.com` |
| Proxy | Activado (nube naranja) |
| TTL | Auto |

Resultado: `cdn.vitalia.health` → mismo túnel → misma app (sirve widget iframe).

---

## Alternativa: crear vía CLI

Si prefieres usar la CLI de cloudflared (una vez autenticado con `cloudflared tunnel login`):

```bash
cloudflared tunnel route dns vitalia-tunnel app.vitalia.health
cloudflared tunnel route dns vitalia-tunnel cdn.vitalia.health
```

---

## Verificación post-creación

Una vez que el clúster K8s esté activo y cloudflared corriendo, verifica:

```bash
# Verifica que el túnel responde
curl -I https://app.vitalia.health/health

# Respuesta esperada:
# HTTP/2 200
# content-type: application/json
```

También puedes verificar en el dashboard de Cloudflare:
- `Zero Trust` → `Access` → `Tunnels` → `vitalia-tunnel` → estado `Healthy`.

---

## Referencia de arquitectura

- `03-arch.md § 5.3` — K8s deploy (Chris UI gate Q4=B)
- `deploy/cloudflared/config.yml` — configuración del túnel
- `deploy/cloudflared/setup-tunnel.sh` — script de setup paso a paso

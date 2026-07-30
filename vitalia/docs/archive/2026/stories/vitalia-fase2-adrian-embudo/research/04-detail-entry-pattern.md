# 04 · ¿Cuál es el mejor componente para entrar al detalle del lead?

> Juicio UX/UI + investigación + el patrón YA shipped en vitalia. Decide cómo se abre el detalle del lead desde el embudo (y reutilizable cross-surface).

## Las 3 variantes mockeadas

| | A · panel lateral | B · drawer flotante | C · página (URL propia) |
|---|---|---|---|
| Archivo | `embudo-agentico-concept.html` | `…-drawer.html` | `…-page.html` |
| Mecánica | panel fijo que **empuja** el board | overlay deslizante + scrim sobre el board | el board es el directorio; el lead abre su **página** (EntitySubNavBar) |
| URL propia | no (por default) | no (por default) | **sí** (`/adrian/embudo/{leadId}/{tab}`) |
| Board visible | sí (angosto) | atenuado detrás | no (lo reemplaza) |
| Componente vitalia | nuevo | nuevo | **`EntitySubNavBar` ya shipped** (doctores) |

## Lo que dice la investigación (master-detail, 6 variantes)

El patrón master-detail tiene presentaciones canónicas: **full page/route**, **popup/modal**, **split/side-panel**, **expand-collapse**. Trade-offs documentados:
- **Full page (route):** máximo espacio para muchos campos/tabs; **contra:** navegás ida-y-vuelta para tocar varios objetos.
- **Popup/modal/drawer:** no obscurece todo, **preserva el contexto** del item seleccionado, gesto rápido.
- **Split/side-panel:** bueno en tablet/desktop; comprime la lista.

(Oracle Alta · WebAppHuddle master-detail comparison.)

## El desempate AGÉNTICO + la directriz YA existente

Dos hechos inclinan la balanza:

1. **Vitalia YA fijó la página-con-URL como directriz UX** — `EntitySubNavBar` (ADR-vitalia-004 § D-1), shipped en `vitalia-fase2-lisa-doctores`: el doctor tiene su página `lisa/staff/[doctor-id]/{perfil,horarios,servicios}` con barra N3-dyn `[‹ Staff] | nombre | tabs-ruta`. **El lead debe seguir el mismo patrón** (consistencia + componente reusable, menos por construir). Chris lo recordaba bien: está implementado.

2. **Agentic = direccionable.** Que el lead tenga **su propia URL** es valioso para un sistema de empleados-IA: Valeria/Adrián pueden **deep-linkear** ("abrí la página de María"), la URL es **compartible**, y el detalle se **reutiliza cross-surface** (mismo `/adrian/embudo/{leadId}` se alcanza desde el Inbox, una búsqueda, o un mensaje de Valeria). Un drawer/panel transitorio no es un recurso direccionable.

## ★ Recomendación: página como canónico + intercepting route como presentación

No es A vs B vs C — es **C como arquitectura + B como presentación contextual**, gracias a un patrón de Next.js App Router (**parallel + intercepting routes**) que da lo mejor de ambos:

- El detalle es una **página real** en `/adrian/embudo/[leadId]/{datos|historial|score}` → URL propia, deep-link, refresh = página completa, reusable, agentic. (variante C)
- Cuando se navega **desde el board** (soft-nav, clic en card), la ruta se **intercepta** y se renderiza como **overlay** (drawer) sobre el board → **no perdés el Kanban** de supervisión. (sensación variante B)
- **Refresh / deep-link / llegada desde Valeria** → renderiza la **página completa** (sin interceptar). Back cierra el overlay en vez de cambiar de ruta.

> Esto es el patrón canónico de modales con URL del App Router (parallel `@modal` + intercepting `(.)`): "modal shareable por URL, contexto preservado al refrescar, back cierra el modal". Lo construís **una sola vez** (la ruta) y obtenés ambos comportamientos.

**Descarto el panel lateral (A) como primario:** comprime el board, no es direccionable por default, y se aparta del patrón shipped. (Sirve solo si quisiéramos board+detalle co-visibles permanentemente, que no es el caso de supervisión.)

### Veredicto

| Decisión | Recomendación |
|---|---|
| Canónico del detalle | **Página/ruta** `/adrian/embudo/[leadId]/{tab}` con `EntitySubNavBar` (reusa doctores) |
| Presentación desde el board | **Intercepting route** → overlay tipo drawer sobre el Kanban |
| Presentación desde Inbox / deep-link / Valeria | la **página completa** (misma ruta) |
| Tabs | rutas (`/datos`, `/historial`, `/score`) — no Shadcn Tabs internas (consistente con ADR-vitalia-004) |
| Mobile | la página completa (sin intercept) — drill-down natural |

Resultado: **un solo detalle, direccionable, reusable y agentic**, que se ve como drawer cuando trabajás en el board y como página cuando llegás directo. Variante C es la base; el intercept le agrega la comodidad de B sin perder la URL.

## Fuentes
- Oracle Alta — Master-Detail pattern · https://www.oracle.com/webfolder/ux/mobile/pattern/masterdetail.html
- WebAppHuddle — Master-Detail UI (6 design comparison) · https://webapphuddle.com/master-detail-ui-pattern-design/
- Next.js docs — Intercepting Routes · https://nextjs.org/docs/app/api-reference/file-conventions/intercepting-routes
- Next.js docs — Parallel Routes · https://nextjs.org/docs/app/api-reference/file-conventions/parallel-routes
- JavaScript Conference — Shareable Modals in Next.js (URL-synced UI) · https://javascript-conference.com/blog/shareable-modals-nextjs/
- Interno: `EntitySubNavBar.tsx` + `vitalia-fase2-lisa-doctores` (ADR-vitalia-004 § D-1) — directriz shipped

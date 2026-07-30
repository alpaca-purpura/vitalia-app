# Demo script — vitalia-bugfix-shell-nav-scroll-errors (Chris manual sign-off · DoD #37 §5)

> Ejercé los 6 bugs en el stack dev real. Esto cuenta como la verificación live (DoD #37) + tu
> `demo_signoff`. Marcá cada uno OK/FALLA. Si algo falla, anotalo y lo reabro.

## SETUP
1. Stack arriba (ya corriendo): `make dev-app-vitalia` desde `~/Proyectos/luana-vitalia` si hace falta.
2. Abrí **https://dev-app.vitalialat.com** (o `http://localhost:3002`), login `dr.demo@vitalialat.com`
   (tenant Clínica Sanaré).
3. Abrí la consola del navegador (F12 → Console) para ver errores rojos / la burbuja de Next.

## HAPPY PATH (los 6 bugs)
1. **#1 Routing:** tras login, ¿aterrizás en una pantalla válida (Agenda de Mateo), **NO** en un 404
   "no encontramos esa vista"? Recargá `/{tenantId}` (la URL pelada de la clínica) varias veces → debe
   llevarte siempre a `…/mateo/agenda`, **sin** quedar colgado en `/{tenantId}` ni mostrar la burbuja
   roja de Next "Rendered more hooks…" en la consola.
   ✅ *Resuelto esta sesión:* ese "Rendered more hooks" al aterrizar (flake ~40% en `/{tenantId}`) era
   una **soft-navigation de Next 16** y se arregló moviendo el redirect al edge (`proxy.ts`). Validado
   live 5/5 limpio. *Si lo seguís viendo* (especialmente navegando hondo DENTRO de Agenda, no al
   aterrizar), avisame: ahí quedaría el bug de framework de fondo, separado de este fix, ya trackeado.
2. **#2 Selector de tenant:** ¿se ve el selector de clínica arriba (badge + "Clínica Sanaré") aunque
   tengas una sola clínica? Recargá un par de veces → ¿sigue visible?
3. **#3 Títulos:** entrá a varias hojas (Lisa→Marca→Identidad/Voz y tono/Presencia, y algún placeholder
   como Adrián→Embudo). ¿Ya **NO** aparece el título grande arriba que repetía el nombre de la pestaña
   activa? (Los títulos de sección DENTRO de un formulario sí siguen — eso es correcto.)
4. **#4 Scroll:** en una hoja con contenido largo (ej. Presencia, o Agenda), ¿podés **scrollear** con
   la rueda y aparece la barra? Antes quedaba fijo.
5. **#5 Presencia:** en Lisa→Marca→Presencia, ¿ya **NO** está el recuadro azul "Editor de landing
   pública — próximamente"?
6. **#7 Error aislado:** (si se puede provocar un error) cuando algo falla en una hoja, ¿la barra
   lateral / ribbon / sub-tabs siguen clickeables (podés navegar a otra hoja) y ves un panel de error
   con "Reintentar", en vez de que se muera toda la app?

## EDGE / negativos
- `/{tenantId}/<agente-que-no-existe>` → debe dar el 404 contextual (con chrome), NO romper la nav.
- Hoja sin scroll necesario → no debe aparecer barra innecesaria.

## TEARDOWN
- Nada que limpiar (read/UI). Si tocaste datos en Presencia, revertí manualmente.

## Sign-off (completá)
```yaml
demo_signoff:
  signed_by: Chris
  date: 2026-06-__
  result: APPROVED | APPROVED_WITH_NOTES | REJECTED
  notes: "..."
  open_items:
    - { item: "Next 16 soft-nav 'Rendered more hooks' DENTRO de Agenda (si lo viste hondo, NO al aterrizar — el landing ya está fijo)", severity: ?, disposition: "nueva story framework / fold agenda owner — workaround edge-redirect ya aplicado para el landing" }
```

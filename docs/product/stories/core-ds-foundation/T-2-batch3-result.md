# T-2 Batch 3 — Result

## Commit

SHA: `b782905e`
Branch: `wip/vitalia`
Files: 24 nuevos archivos en `core/@luana/ui-kit/stories/`

## Stories creadas

### Atoms (13)
- `atoms.Button.stories.tsx` — Galería CVA (6 variantes × 4 tamaños + disabled + icono), Default, ConIcono, Cargando
- `atoms.Input.stories.tsx` — Default, ConValor, Deshabilitado, Email, Numero
- `atoms.Textarea.stories.tsx` — Default, ConValor (notas clínicas), Deshabilitado
- `atoms.Label.stories.tsx` — Default, ConCampo (paired con Input), Requerido
- `atoms.Select.stories.tsx` — **Abierto** (open prop para revisión directa), Default, ConValorSeleccionado, Deshabilitado
- `atoms.Checkbox.stories.tsx` — Default, Marcado, Deshabilitado, Grupo (canales)
- `atoms.Switch.stories.tsx` — Default, Activo, Deshabilitado, Grupo (preferencias de comunicación)
- `atoms.RadioGroup.stories.tsx` — Default (presencial/teleconsulta/domicilio), Urgencia, Deshabilitado
- `atoms.Badge.stories.tsx` — Galeria (4 variantes), Default, Estados (estados de turno)
- `atoms.Avatar.stories.tsx` — Default (imagen + fallback), SoloIniciales, Grupo (equipo apilado), Tamanos
- `atoms.Card.stories.tsx` — Default (métricas mensuales), Servicio (card servicio con badge + botones)
- `atoms.Separator.stories.tsx` — Horizontal, Vertical

### Overlays (8)
Todas incluyen story con overlay **abierto por default** (sin interacción requerida de Chris):

- `overlays.Dialog.stories.tsx` — **Abierto** (form agregar profesional), ConTrigger
- `overlays.Popover.stories.tsx` — **Abierto** (filtro por fecha), ConTrigger
- `overlays.DropdownMenu.stories.tsx` — **Abierto** (acciones turno), ConTrigger
- `overlays.Tooltip.stories.tsx` — **Visible** (open + TooltipProvider), EnIcono, EnBoton
- `overlays.Sheet.stories.tsx` — **Abierto** (form editar profesional, fullscreen layout), ConTrigger
- `overlays.Alert.stories.tsx` — Informativo, Destructivo, Exito
- `overlays.AlertDialog.stories.tsx` — **Abierto** (confirmar eliminar paciente, destructive), ConTrigger
- `overlays.Command.stories.tsx` — Default (inline, buscar paciente + acciones), SinResultados

### Navigation / Disclosure (4)
- `nav.Tabs.stories.tsx` — Default (detalle paciente: historial/turnos/documentos), Configuracion
- `nav.Accordion.stories.tsx` — Default (FAQ single collapsible), Multiplo (multiple defaultValue)
- `nav.Collapsible.stories.tsx` — Default (notas adicionales), Abierto (filtros avanzados open)
- `nav.ScrollArea.stories.tsx` — Default (agenda vertical), Scroll horizontal (tarjetas)

## Gates

```
smoke: 136/136 stories render clean
smoke: PASS
```

```
sb_when_to_use PASS: 44 stories carry "## Cuándo usarlo"
```

```
vitalia/frontend npx tsc --noEmit → VERDE (sin output, sin errores)
```

## Bugs de componente observados

Ninguno. (Scope: solo lectura de `src/` — no se editó código de componentes.)

## Notas de implementación

- `Select` canónico: `<Select open>` renderiza `SelectContent` inline en canvas (normalmente portal). Contenedor con `minHeight: 260` para evitar colapso visual.
- `Tooltip`: todas las stories envueltas en `<TooltipProvider>` (normalmente montado en app root). Story `Visible` usa `open` prop.
- `AlertDialogAction` destructivo: clases aplicadas manualmente (`bg-destructive text-destructive-foreground`) — el componente usa `buttonVariants()` default.
- `Command`: montado inline (no `CommandDialog`) para evitar complejidad de portal en el smoke.
- `Sheet`: story `Abierto` usa `parameters.layout: "fullscreen"` para que el panel lateral se vea completo.

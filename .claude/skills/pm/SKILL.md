---
name: pm
description: "Alias retro-compat de /pm-luana. Cuando user tipea '/pm' o usa triggers panorámicos ('estado portfolio', 'panorama', 'cross-brand', 'qué brand toca', 'priorizar entre brands', 'qué tenemos', 'cómo van las marcas'), invocar /pm-luana — ese skill cubre Modo Portfolio + Modo Core Engineering unificados. Pre-2026-05-15 existía un /pm master separado; fue fusionado a /pm-luana porque toda decisión transversal inevitablemente toca core. Esta entrada queda como pointer para no romper tipeo + descubribilidad."
allowed-tools: Read
model: opus
---

# /pm — alias de /pm-luana

> **Fusionado a `/pm-luana` (2026-05-15 post-F2 revisión).**
>
> Toda la funcionalidad master-orquestador (Modo Portfolio) + core engineering (Modo Core) vive en un solo skill: `.claude/skills/pm-luana/SKILL.md`.
>
> Razón de la fusión: en el dominio Luana, "lo transversal" ES el core. El hop master→core era artificial y agregaba latencia conversacional sin valor.

## Acción

Cuando este skill se active (por tipeo `/pm` o triggers panorámicos):

1. Leé `.claude/skills/pm-luana/SKILL.md` y seguí ESE protocolo.
2. NO ejecutés nada acá. Este file es puro pointer.

## Por qué seguir tipeando `/pm`

Convenience. `/pm-luana` y `/pm` activan el mismo skill (este pointer redirige). Para brands específicas seguís usando `/pm-nicolify`, `/pm-vitalia`, `/pm-comunify`, `/pm-lupulo` (sin cambios).

## Referencia única

- `.claude/skills/pm-luana/SKILL.md` — SSoT del PM unificado

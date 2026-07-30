# HANDOFF — vitalia-fase2-lisa-servicios (refining · /po-ux)

> Continuación del refinamiento. Sesión previa cerró por contexto (51%). Chris tiene **más comentarios** que arranca en la sesión nueva.

## Estado actual

- **Story:** `vitalia-fase2-lisa-servicios` · `state: refining` · skill activa = **`/po-ux`** (vitalia).
- **Flujo 2 rondas/2 firmas:** `input_spec_signed: true` (✍ FIRMA 1 dada por Chris) · `mockup_final_signed: false`.
- **Bloqueado en:** ✍ **FIRMA 2** (ratificación visual de los 4 mockups) — Chris iba a darla pero antes tiene **comentarios nuevos** (los trae en la sesión nueva). NO transicionar a `refined` hasta FIRMA 2.
- **Próximo tras FIRMA 2:** RONDA 2 = escribir `§ Gherkin scenarios` + `§ Matriz de cobertura` en `01-spec.md` → `refining→refined` → handoff `Skill(architect, "vitalia vitalia-fase2-lisa-servicios")`.

## SSoT de la story (leer en este orden)

1. `00-research.md` — reframe agéntico + prior-art scan + **§ 0 ratificaciones Chris** (canvas completo + data-aquí/tool-en-canal-inbound). El catálogo = **Offer Studio offers** (NO `Treatment`/`LadderSlot` nuevo · consume engine EP-2 · cero edit engine).
2. `01-spec.md` — RONDA 1 completa: `§ Modelo del servicio` · **`§ Workspace del servicio — contenido por pestaña`** (★ ~55 campos + MVP 24 must-have, agente-first) · `§ Mapa funcional` (happy + árbol + RN-1..15 + AC-1..10) · `§ Wireframes` · `§ Componentes`.
3. `checkpoint.md` — frontmatter (`module: offer`, `agentic_reframe`, firmas) + `## Prior art scan` + `## Decisión Chris`.
4. `chris-input.md` — log conversacional completo (todas las decisiones + rondas de feedback).

## Decisiones cementadas (NO re-litigar salvo que Chris lo pida)

- Servicio = **Offer Studio Offer** · catálogo **por-tenant** (scope clínica opcional) · precio **fijo o rango** · **paquetes/multi-sesión** sí.
- Escalera = **5 peldaños FIJOS** (labels médicos sobre `OfferValueLevel`: Gancho gratuito · Primera visita · Tratamiento principal · Premium · Plan/convenio) · **autoexplicativa** (vacío muestra ejemplos + "crear aquí") · SIN drawer override · SIN `ladder/[slot-id]`. Recurrente = atributo del servicio (flag), no peldaño.
- Seña/financiamiento **por servicio**. Link servicio↔doctor **opcional** (sin doctores → agente degrada). RBAC: **admin+owner** editan, resto read-only.
- **Toggle único "Activo"** — landing ELIMINADA de esta story (Chris #2, 2026-06-06).
- Workspace = patrón **staff `EntitySubNavBar`** (NO Shadcn tabs) · **5 pestañas** (Chris #4 quitó Stats): **Resumen** (#5 ex-Detalle) · **⭐ Para Adrián** (argumentario) · Doctores · Plan de pago · Prueba social.
- Catálogo con **buscador + filtros** (patrón `StaffDirectoryHeader`).

## Mockups (4 · dentro del shell-organism verbatim + `_shared.css`)

`vitalia/docs/product/stories/vitalia-fase2-lisa-servicios/mockups/`: `catalogo.html` · `escalera.html` · `servicio-workspace.html` (6 leaves cliqueables) · `nuevo-servicio.html` (Sheet con rung-picker autoexplicativo).
Servir: `cd .../mockups && python3 -m http.server 8899` → `http://127.0.0.1:8899/{archivo}.html`. (Puede haber un server viejo vivo en `:8899` de la sesión previa — `lsof -ti:8899 | xargs kill` si molesta.)
Wrapper portado verbatim de `vitalia/docs/archive/2026/stories/vitalia-fase2-lisa-marca/mockups/` (caso origen rule shell-fidelity). EntitySubNavBar shipped: `vitalia/frontend/src/components/shared/shell-organism/EntitySubNavBar.tsx`.

## Abierto para /architect (no bloquea RONDA 2)

- Schema brand-level exacto (columnas en tabla offers vitalia vs tabla aparte) + preset pack EP-2 (`vitalia/backend/.../offer/extensions.py` — hoy stub vacío).
- Persistencia del link servicio↔doctor (FK → `vitalia_doctors`).
- `FAQ` + `objeciones→respuestas` = listas de pares editables. `contraindicaciones` + `condiciones_escalada` = campos de **seguridad** (HIPAA-lite).
- Mapeo fino label médico ↔ `OfferValueLevel` + ejemplos `PROFESIONAL_SALUD` del engine como hints. Contenido de seed presets dental/estética.

## Dependencias / contexto cross-story

- **`vitalia-fase2-adrian-canal-inbound`** (`refined`) está **hard-bloqueado** en esta story (RN-16/17 match servicio→especialista necesita catálogo Offer Studio + link servicio↔doctor). El **tool agéntico** `match_service_and_specialist` vive en canal-inbound, NO acá.
- **`vitalia-fase2-adrian-propuestas`** (idea, F4) consume el catálogo (line-items + financiamiento).
- **Step 0 / WIP abierto (no tocar, pero pendientes):** `vitalia-fase2-adrian-embudo` (`developed`, pide auditor/cierre) · `vitalia-fase2-lisa-doctores` (`developing`).

## Git / seguridad

- Nada commiteado. Docs del story-folder son tracked pero sin commit (hub multi-sesión → commit por **pathspec** cuando Chris lo pida, NUNCA `git add .`).
- Skills: esta es work de `/po-ux`; NO encadenar a `/architect` hasta FIRMA 2 + RONDA 2 cerrada.

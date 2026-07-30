---
story_id: vitalia-shell-core-hardening
created_at: 2026-06-10T00:00:00-05:00
last_modified: 2026-06-10T00:00:00-05:00
notes_count: 0
refs_count: 5
conversation_count: 1
---

# chris-input.md · vitalia-shell-core-hardening

> **Qué es este archivo:** acá Chris escribe notas + referencias + Claude responde con verdicts. Cocina de la story (la conversación) — separada del spec/design/arch.
>
> Doc canónico: `docs/process/chris-input-protocol.md`.

## 💭 Notas

### 2026-06-10
Sin notas adicionales todavía · Chris escribe aquí.

## 📎 Referencias

- **📖 story-ref** · `vitalia-bugfix-shell-valeria-responsive` (refined, folded — backbone del spec: 01-spec v3 + mockup firmado + baseline build)
- **📖 story-ref** · `vitalia-fase1-shell-layout-5050-race-fix` (parked, folded — race hydration SC-3)
- **📖 story-ref** · `vitalia-ds-showcase` (demostrador R-FID, NO folded)
- **📄 doc** · `docs/architecture/luana-platform/ADR-014-design-system-homologation.md` (programa cross-brand)
- **📚 learning-ref** · `2026-06-06-n3-entity-workspace-layout-from-nicolify` + `2026-06-03-next16-softnav-redirect-rendered-more-hooks`

## 💬 Conversación

> Append-only · turn-by-turn cronológico. Verdict labels: ✓ APLICADO · ⚠️ DUDA · ❌ REFUTADO · 💡 PROPONE.

### 2026-06-10 · 👤 Chris · input de creación (consolidación shell + lift a core)
> quiero que revises todas las historias de usuario que actualmente estan en ejecución o en planificación relacionados al organism shell, incluyendo bugfixes, quiero agrupar todas en uno sola para hacer solo una revisión y luego, cuando todo esté muy bien tanto funcional como técnicamente (excelente arquitectura y estructura de archivos, etc.) lo promovemos al core de acuerdo a lo que me recomendaste (o no, aquí tu me indicas que hacer)

### 2026-06-10 · 🤖 claude · `/pm-vitalia` · 💡 PROPONE → ✓ APLICADO
Revisé todas las stories del shell. Distinguí **chrome del shell** (el wrapper que se buildea) de **features que VIVEN en el route group `(shell-organism)`** (lo consumen, no lo construyen). Hallazgos: baseline ya shipped (9 stories archived) · `core/@luana/ui-kit` v0.3.0 ya existe (lift parcial) · nicolify espejea el shell (mirror cross-brand) · proposals del lift FE/shell ya `accepted` (2026-06-06).

**Empujé contra "una sola story" literal**: una mega-story SDD cruzaría `[shell,clinics,crm]`, violaría WIP cap y mezclaría madureces. Propuse **umbrella de hardening + enchufe al programa design-system-homologation**.

Chris ratificó (AskUserQuestion):
- **Forma** → "Hardening story + programa (Rec)": umbrella `vitalia-shell-core-hardening` absorbe responsive + race-fix + 2 bugs latentes; ds-showcase = demostrador; agent-features fuera.
- **Lift timing** → "Lift-durante (Rec)": /architect buildea el hardening apuntando a `@luana/ui-kit`; brands consumen. Sequencing final lo cierra /architect en `ready`; gate brand→core es de /pm-luana.

Story creada en `state=idea`, `phase=CONSOLIDATION_INTAKE`. Folded: responsive (refined→parked) + race-fix. Linked: ds-showcase. Excluidos documentados (caps-bug, doctores keystone, agent-features).

**Próximo paso (gate antes de refinar/buildear):** cerrar las 2 stories OPEN que comparten bucket — `vitalia-fase2-adrian-embudo` (developed → /auditor o defer) + `vitalia-fase2-lisa-doctores` (developing → resolver keystone regresión o pausar) — + liberar un slot de refining. Recién ahí /po-ux reconcilia el spec único y /architect produce el ready package con el lift.

### 2026-06-10 · 👤 Chris · ratificación gate
> a, arranca el gate y commitea por pathspec

### 2026-06-10 · 🤖 claude · `/pm-vitalia` · ✓ APLICADO
Gate ejecutado: **embudo** → `defer_audit: true` (developed + dod_live_verified preservados; auditar post-hardening evita re-audit por rebase del chrome crm) · **doctores** → `parked` (⚠️ keystone regresión `/lisa/staff` queda VIVA — bug de feature Lisa, no chrome; primer trabajo post-hardening) · **lisa-servicios** → `parked` (su N3 depende del contrato `EntityWorkspaceLayout` que el hardening cambia; firma 1 preservada — al reanudar retoma RONDA 2 contra contrato nuevo). Config-cuenta queda refining (no acoplada al N3). Slot refining libre para la umbrella.

Commit por pathspec (delegado Haiku). **Siguiente:** `/po-ux vitalia vitalia-shell-core-hardening` — reconciliar spec único del chrome.

### 2026-06-10 · 🤖 claude · `/po-ux` · 💡 PROPONE
Backbone leído (01-spec v3 responsive, 19 SCs, matriz sin huecos, 2 firmas). Reconciliación acotada: race-fix se generaliza en la máquina de estados nueva (el min-width 620 muere → el caso SC-3 original se reformula como "drag inmediato seguro") · U3 ya resuelto por el default 30/70 resizable (solo trazado) · B1 entra como invariante nuevo (soft-nav confiable + revertir band-aid hard-nav). ÚNICA decisión abierta presentada a Chris: ¿dark-mode (BUG #2, out-of-scope firmado del backbone) entra al hardening? Recomendación: SÍ (evita segunda review de las mismas superficies + no liftar deuda dark al core + work-package acotado).

### 2026-06-10 · 👤 Chris · decisión dark-mode
> Si, mételo

### 2026-06-10 · 🤖 claude · `/po-ux` · ✓ APLICADO
**01-spec.md v1 unificado escrito** (`vitalia/docs/product/stories/vitalia-shell-core-hardening/01-spec.md`): backbone v3 integrado (SC-1..19 + RN-1..13 + AC-1..11 heredados verbatim, firmas heredadas) + deltas ★ UMBRELLA: **RN-14** soft-nav confiable + band-aid revertido (B1) · **RN-15** variantes dark completas (BUG #2) · **RN-16** drag inmediato seguro (ex race-fix) · **AC-12/13/14** · **SC-20/21/22** · enmienda SC-19 (dark ya no es "no tocar") · U3 trazado a SC-1/SC-4. Sin mockup nuevo (deltas = comportamiento; el dark del mockup firmado es la referencia). Matriz sin huecos.

**Pendiente Chris — firma única de reconciliación** (cubre input_spec_signed + ratifica herencia del mockup) + 2 open questions: (1) multi-tab not_applicable ¿confirmas? (2) barrido dark = sub-tabs SHIPPED + wrapper (placeholders quedan fuera) ¿confirmas?

### 2026-06-10 · 👤 Chris · pregunta fidelidad del mockup
> Quiero saber si el mockup es solo mockup o lo tomarás de forma literal y será igual? […] el comportamiento si es el que quiero pero a nivel UI me gusta como está actualmente y no quiero que retrocedamos en ese aspecto.

### 2026-06-10 · 🤖 claude · `/po-ux` · ✓ APLICADO
Confirmado: mockup = **behavior-fi, NO pixel-fi** (caveat HARD ya firmado en backbone 2026-06-06, heredado al spec § Design system constraint). Del mockup se toma SOLO comportamiento (estados A/B/C, push, tira-avatar, "+", drawer, N3); el estilo sale del design system vigente (tokens globals.css, átomos components/ui/, avatar real del catálogo, logo gradient, agent-colors — se CONSERVAN). Doble candado anti-retroceso: AC-10 + SC-19 (regresión cero ambos temas) + frontend-visual-fidelity D1 (auditor). Sin cambios al spec — la pregunta ES el caveat escrito.

### 2026-06-10 · 👤 Chris · ✍ FIRMA ÚNICA DE RECONCILIACIÓN
> Confirmo todo, firma la reconciliación

### 2026-06-10 · 🤖 claude · `/po-ux` · ✓ APLICADO — REFINED
Firma aplicada: `input_spec_signed: true` + `mockup_final_signed: true` (herencia ratificada) + `ratified_by_chris: true` → **state: refined**. Open questions resueltas: (1) multi-tab `not_applicable` ratificado · (2) barrido dark = shipped + wrapper · (3) caveat behavior-fi re-confirmado en § Open questions. Dedupe de `ratified_by_chris` duplicado en checkpoint (mismo bug de caps-last-modified — evitado acá). **Siguiente:** `/architect vitalia vitalia-shell-core-hardening` → ready package (lift-durante a @luana/ui-kit + mecanismo soft-nav RN-14 + sequencing).

### 2026-06-10/11 · 🤖 claude · `/architect` + `/dev-team` · ✓ APLICADO (cadena autónoma)
Ready package (commit 283fa5ff: decisiones A edge-redirect · B consumir N3 ya shipped en ui-kit · C dark hardcoded→token). Build T-1..T-8 completo (8/8 pushed): store máquina nueva · chrome layout · tira-avatar+cabecera · soft-nav+revert band-aid · N3 migrado a @luana/ui-kit (mirror brand-local RETIRADO; kit edit additivo único: prop opcional `activeLeaf` d3b06b11) · dark token-audit · e2e suite 52+2flaky+race 8/8 (cazó 3 bugs producto: rewrites /api→BE [bug global useTenants 404] · strip collapsedSize · drag-collapse) · SHELL-DESIGN-CONTRACT+handoff lift+demo-script (412efe4f). Live-verify #37: 13 acciones reales autenticadas + BE 0 errores → `dod_live_verified: true` + `dod_evidence` (5 entries).

### 2026-06-11 · 👤 Chris · 🔴 RONDA LIVE (probó en vivo)
> prueba el resize del chat de valeria, esta fallando y tmb mira tu mismo con playwright o chrome dev tools como se visualiza cuando se colapza el chat, queda un espacio vacío. Arreglalo
> revisa tmb como se ve cuando se expande el historial, genera todos los casos posibles mueve el resizer, en cualquier escenario siempre debe verse bien todo

### 2026-06-11 · 🤖 claude · `/dev-team` · ✓ APLICADO — 4 root causes muertos (commit ab30393a)
Reproducido + diagnosticado con Playwright autenticado (Chrome MCP cayó — server desconectado). Hallazgos: (1) react-resizable-panels v4 captura props en MOUNT → colapso runtime inerte (gap 274px + resize muerto post-ciclo); (2) collapsedSize number=PX (3.4px, no 44); (3) la persistencia del Group pisa collapse() → rAF retry; (4) **RN-7 violada: el historial robaba 260px al chat** (hasta 58px ilegible) → push real implementado. Verificación: **matriz exhaustiva 22/22** (estados × drags × ciclos × historial × persistencia × viewports · 0 errores consola) + **spec permanente `resizer-matrix.spec.ts` 7/7** (pedido "todos los casos" queda como regresión) + no-regresión 25/25. Ronda registrada en `checkpoint.chris_verify.rounds`. **Pendiente: Chris re-prueba live → signoff.**

### 2026-06-11 · 👤 Chris · 🔴 RONDA 2 (000.png + 001.png @1920)
> ya mejoró pero mira como se ve cuando el resize lo llevo hasta el minimo de valeria o cuando "descolapso", tmb se ve así. Y cuando el historial esta abierto se ve así cuando empujo el resize.

### 2026-06-11 · 🤖 claude · `/dev-team` · ✓ APLICADO — commit 1c339736
**000 (recorte al mínimo):** `grid-rows` sin cols explícitas → columna implícita `auto` trackea al CONTENIDO (604px) e ignora el contenedor → mensajes/composer recortados por overflow-hidden. Fix: `grid-cols-[minmax(0,1fr)]` + `min-w-0` → wrap real. **001 (chat desaparece con historial):** el min del panel en C no sumaba el historial (280px reales — además mi push usaba 260) → drag clampeaba al min de B. Fix: minSize efectivo dinámico (chat-min + 280) + key remount B|C (la lib captura minSize en mount) + retry rAF. **Polish:** "Valeria" completo al mínimo (era "V.") · pill modo con container query `@[24rem]` (Tailwind v4) · placeholder corto. Verificado con TUS escenarios exactos @1920: overhang 0px ×3 + **suite completa 68/68 (0 flaky)** + asserts permanentes anti-recorte + min-C en resizer-matrix. **Re-probá: drag al mínimo · descolapsar · historial + drag.**

### 2026-06-11 · 👤 Chris · ✍ SIGNOFF
> ya quedó bien, continúa con el cierre hasta el done

### 2026-06-11 · 🤖 claude · `/auditor` + `/pm-vitalia` · ✓ APLICADO — **DONE**
Cierre completo: signoff SATISFIED registrado → ledger matriz ✅ + reconcile RN-7 280px → `developed` → `/auditor` (gate-runner destapó 4 arch fails PRE-EXISTENTES: allowlists stale post-rename inbox→adrian + 2 tests stale [ribbon 23 con `recuperar` · audited-section dual-filter] — Carril R, alineados a conducta shipped; suite FULL 2664 tests 0 fail) → **APPROVED** (auditor independiente re-corrió gates + gherkin-matrix 22/22 + C1-C5 PASS) → 07-merge.md → **archive R2** (`vitalia/docs/archive/2026/stories/vitalia-shell-core-hardening/`) → `state: done` (a9e28952). Folded stories marcadas DELIVERED. cap-doctor SANO 0 deriva. **Post-merge:** handoff lift chrome→`@luana/ui-kit` queda en proposal `2026-06-01-lift-shell-organism` para `/pm-luana` · embudo (defer_audit) listo para su auditoría · CIL: stale-gate freshness (L1) + SC-19 flaky theme-hydration (L3) + symlink-war pnpm host↔container (L1).

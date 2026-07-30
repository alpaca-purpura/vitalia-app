# T-6 Impl Log — Dark token-audit (Decisión C)

**Story:** vitalia-shell-core-hardening  
**Ticket:** T-6 — "Dark token-audit: hardcoded→token en sub-tabs shipped + variantes dark faltantes"  
**Date:** 2026-06-10  
**Branch:** wip/vitalia  
**Base:** c23b88d9 (T-1..T-5 pushed, tree clean)

---

## § Skills Consulted

| Skill | Por qué invocada | Decisión tomada |
|---|---|---|
| `frontend-expert` | FSD-Lite boundaries, React patterns baseline, Tailwind conventions | `bg-background` (Shadcn semantic token) para toggle thumb; `dark:` variant prefix para CTA amber button |
| `frontend-visual-fidelity` | D1 design-system-first, no reinventar tokens | Preferir tokens existentes (`bg-background`) sobre crear nuevo vt-* utility |
| `chrome-devtools-verify` | Live verification gate | Stack dev no levantado por instrucción explícita del caller — live-verify dark delegado a T-8 gate #37. Documentado en T-6-result.md |

---

## § Plan

### Step 1 — Grep inventory (AC-12)

Superficies shipped escaneadas:
- `features/adrian/components/inbox/` ✓
- `features/adrian/components/embudo/` ✓
- `features/lisa/components/staff/` ✓
- `features/lisa/components/marca/` ✓
- `features/mateo/` ✓
- `components/shared/shell-organism/` ✓

Patterns buscados: `bg-white`, `bg-[#...]`, `text-[#...]`, `border-[#...]`, `rgb()`, `rgba()`, explicit `#hex`.

### Step 2 — Análisis BUG#2 canónico (ContactSidebar)

`ContactSidebar.tsx:127` YA usa `vt-bg-surface` — dark-aware. El `rgb(255,255,255)` reportado en el bug observado fue corregido durante T-2/T-3. No requiere acción en T-6.

### Step 3 — Hardcoded color inventory (completo)

**`text-white` en backgrounds de color de agente/gradientes — INTENCIONAL, no es bug:**
- `VoiceMessagePlayer.tsx` → `hover:vt-bg-cian hover:vt-text-white` (hover sobre bg de agente)
- `ProposalCardBanner.tsx` → `text-white vt-bg-gradient-agent` (sobre gradiente agente)
- `SendButton.tsx` → `text-white transition-opacity` (botón de envío sobre bg coloreado)
- `ModeToggle.tsx` → `vt-bg-success text-white` (toggle activo sobre bg success)
- `MessageBubble.tsx` → `bg-agent-valeria text-white` (burbuja usuario sobre color agente)
- `ChatHeader.tsx`, `ValeriaSidebar.tsx`, `ChatComposer.tsx`, `ValeriaCollapsedStrip.tsx`, `DelegateMarker.tsx` → todos `text-white` sobre gradientes/colores de agente
- `SocialMediaLinksEditor.tsx` (×5 SVG icons) → `text-white` sobre colored platform buttons
- `StaffEmptyState.tsx` → `bg-[color:var(--vitalia-azul-marino-color)] text-white dark:...` (ya tiene dark:)
- `NuevoIntegranteModal.tsx` → `vt-bg-gradient-app-cta text-white dark:text-white` (ya tiene dark:)
- `AvatarUploader.tsx:118` → `text-white` overlay sobre imagen
- `GeneratedBioSections.tsx:116` → `bg-[var(--agent-lisa)] text-white` (sobre color agente)
- `CrearCitaButton.tsx` → `bg-agent-valeria text-white` (sobre color agente)
- `AgendaToolbar.tsx` → `hover:bg-agent-valeria hover:text-white` (hover sobre agente)

**REAL ISSUES (necesitan fix):**

1. **`DoctorPerfilView.tsx:348`** — `bg-white` en thumb de toggle custom  
   - Contexto: thumb pequeño de un toggle ON/OFF custom (no Shadcn Switch)
   - Fix: `bg-background` (Shadcn semantic — blanco en light, near-black en dark)
   - Razón: thumb debe contrastar con el track (`bg-agent-lisa` verde / `bg-muted` gris) en AMBOS modos

2. **`TakeoverBanner.tsx:91`** — `bg-amber-500 text-white` en botón CTA sin variante dark  
   - Contexto: botón "Devolver a Adrián" en banner de takeover. Banner container YA tiene `dark:from-amber-900/20 dark:to-amber-900/10`
   - Fix: agregar `dark:bg-amber-600 dark:border-amber-600` para slightly darker en dark mode
   - Razón: Decisión C = preferir dark: variant sobre crear token nuevo; `amber-600` es oscurecimiento estándar del `amber-500`

### Step 4 — globals.css dark token gap analysis

Existente (correcto):
- `--vitalia-success-soft-bg` → dark variant ✓ (`hsl(142 40% 13%)`)
- `--vitalia-danger-soft-bg` → dark variant ✓ (`hsl(0 45% 15%)`)
- `--vitalia-danger-soft-border` → dark variant ✓ (`hsl(0 45% 28%)`)

Ausente pero NO requerido:
- `--vitalia-warning-soft-bg` — NO existe utility `vt-bg-warning-soft`, NO usada en ningún componente shipped. No requiere acción T-6.
- `--vitalia-info-soft-bg` — NO existe utility `vt-bg-info-soft`, NO usada. No requiere acción T-6.

Los `vt-bg-warning-12` (opacity 12%) y `vt-text-warning` consumen `--vitalia-warning` (hue amber) que permanece igual en dark — contraste aceptable por ser opacity-based (12% sobre dark background aún legible).

**Conclusión globals.css:** No se requieren cambios para T-6.

### Step 5 — Pre-existing arch test failures (no introducidas por T-6)

Los 4 failures en arch suite (test_fsd_boundaries + test_no_cross_feature_imports) son pre-existentes:
- `crm-shared` cross-feature imports en adrian/ (pre-T-6)
- Stale allowlist entry `src/features/inbox/types/conversation-detail.ts` (archivo renombrado en T-5/refactor previo)
- NO introducidas por T-6 (estas estaban en baseline c23b88d9)

---

## § Implementation

### Files changed

| Archivo | Cambio | Patrón |
|---|---|---|
| `features/lisa/components/staff/workspace/perfil/DoctorPerfilView.tsx:348` | `bg-white` → `bg-background` | Hardcoded → semantic token dark-aware |
| `features/adrian/components/inbox/TakeoverBanner.tsx:91` | añadir `dark:bg-amber-600 dark:border-amber-600` | Añadir dark: variant |

### globals.css

Sin cambios — todos los tokens --vitalia-* necesarios ya tienen dark override. Las utilidades `vt-bg-warning-12` / `vt-text-warning` son opacity-based y self-adapting.

---

## § Gates

- tsc --noEmit: PASS (0 errores)
- eslint <changed files>: PASS (0 warnings nuevos)
- vitest test_no_hardcoded_colors: PASS (2/2)
- vitest arch suite: 28/30 PASS — 4 failures PRE-EXISTENTES (no introducidas por T-6)
- Live verify dark: PENDIENTE — stack dev no levantado por instrucción caller. Delegado a T-8 gate #37 (dod_evidence).

# T-6 Result — Dark token-audit (Decisión C)

**Story:** vitalia-shell-core-hardening  
**Ticket:** T-6  
**State:** pushed  
**Date:** 2026-06-10  

---

## Inventory barrido — Superficies shipped

Superficies escaneadas: `features/adrian/inbox/`, `features/adrian/embudo/`, `features/lisa/staff/`, `features/lisa/marca/`, `features/mateo/`, `components/shared/shell-organism/`

### Hardcoded colors migradas (2 ocurrencias reales)

| Archivo | Línea | De | A | Patrón |
|---|---|---|---|---|
| `features/lisa/components/staff/workspace/perfil/DoctorPerfilView.tsx` | 348 | `bg-white` | `bg-background` | hardcoded → semantic Shadcn token (dark-aware: `0 0% 100%` light / `240 10% 4%` dark) |
| `features/adrian/components/inbox/TakeoverBanner.tsx` | 91 | `bg-amber-500 border-amber-500` | `bg-amber-500 dark:bg-amber-600 border-amber-500 dark:border-amber-600` | añadir dark: variant al CTA button del banner |

### text-white — INTENCIONAL (no requieren migración)

Todos los casos de `text-white` en shipped surfaces están sobre backgrounds de color de agente, gradientes, o superficies de color explícito:
- `vt-bg-success text-white` (ModeToggle toggle activo)
- `bg-agent-valeria text-white` (MessageBubble, ChatComposer, CrearCitaButton)
- `vt-bg-gradient-agent text-white` (ProposalCardBanner)
- SVG icons `text-white` sobre botones colored (SocialMediaLinksEditor ×5)
- `text-white` en overlays/labels de imagen (AvatarUploader)
- Shell-organism: ChatHeader, ValeriaSidebar, ValeriaCollapsedStrip, DelegateMarker — todos sobre gradientes del agente

Patrón correcto: `text-white` sobre colored background = contraste intencional. Dark mode no cambia los agent colors, por lo que `text-white` sobre esos colores sigue siendo correcto.

### BUG#2 canónico (ContactSidebar `rgb(255,255,255)`)

`ContactSidebar.tsx:127` YA usa `vt-bg-surface` (dark-aware). El bug reportado fue resuelto durante T-2/T-3. Verificado limpio.

---

## Variantes dark agregadas a globals.css

**Ninguna** — todas las variantes necesarias ya existen:
- `--vitalia-success-soft-bg` dark ✓
- `--vitalia-danger-soft-bg` dark ✓
- `--vitalia-danger-soft-border` dark ✓
- `vt-bg-warning-12` (opacity-based, self-adapting en dark) ✓
- Agent soft tokens (`--agent-*-soft`) dark ✓

`--vitalia-warning-soft-bg` no está definida NI usada en shipped surfaces — no requiere acción T-6.

---

## Skills consulted

| Skill | Decisión |
|---|---|
| `frontend-expert` | `bg-background` (Shadcn semantic, dark-aware) para toggle thumb; `dark:bg-amber-600` dark variant CTA |
| `frontend-visual-fidelity` (D1) | Preferir tokens existentes sobre nuevas utilidades — reduce deuda (Decisión C) |
| `chrome-devtools-verify` | Stack dev no levantado (instrucción caller: "si NO está levantado, NO lo levantes"). Live-verify dark delegado a T-8 gate #37 dod_evidence. |

---

## Quality gates

| Gate | Resultado |
|---|---|
| `tsc --noEmit` | PASS — 0 errores |
| `eslint <changed files>` | PASS — 0 warnings nuevos |
| `vitest test_no_hardcoded_colors` | PASS — 2/2 |
| `vitest arch/ suite` | 28/30 PASS — 4 failures PRE-EXISTENTES (crm-shared boundary + stale allowlist, pre-T-6) |
| Live verify dark (SC-20) | PENDIENTE — T-8 gate #37 |

---

## AC-12 status

Grep de `#[0-9a-fA-F]`, `rgb(`, `bg-white`, `bg-[#` en shipped surfaces post-fix:
- **0 nuevas ocurrencias** hardcoded no-intencionales restantes
- `bg-white` en DoctorPerfilView ELIMINADO → `bg-background`
- `text-white` restantes = INTENCIONAL (sobre colored backgrounds) — exentos per AC-12 spec

Gate arch: `test_no_hardcoded_colors.test.ts` PASS (escanea hex/rgb literals, no Tailwind named colors).

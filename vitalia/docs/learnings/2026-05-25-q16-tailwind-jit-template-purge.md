---
brand: vitalia
date: 2026-05-25
slug: q16-tailwind-jit-template-purge
promotable: candidate
applies_to_other_brands_potentially: [nicolify, comunify, lupulo, saasora, inmoflow, retailly, fixia, guestly, fitflow]
target_core_package: core/luana-core-ui-helpers/ (tailwind-helpers — si emerge cross-brand)
origin_story: vitalia-fase1-ribbon-6-tabs (F1-S7)
---

# Tailwind JIT template literal purge gotcha — Q16 active:hover mechanism

**Qué aprendimos:** las clases Tailwind generadas con template literals dinámicos (`` `hover:${agentBgSoftClass(slug)}` ``) son **purged por JIT** y NO incluidas en el CSS bundle. En la práctica, el código RibbonTab.tsx tiene la intención documentada de "preservar tint del agente en active:hover via CSS specificity", pero el mecanismo funciona accidentalmente: el active branch no tiene `hover:bg-muted` competing → no hay nada que degrade el tint → visual outcome correcto pero **mechanism documentado ≠ mechanism real**.

**Origen:** story `vitalia-fase1-ribbon-6-tabs` (F1-S7) 2026-05-25, auditor-frontend WARN-1. Q16 cementado spec v2 post-Playwright audit como "active:hover PRESERVA tint del agente — CSS specificity HARD via `[data-active=true].bg-agent-X-soft:hover` selector". Auditor encontró que el código real usa template literal dinámico, que Tailwind JIT NO captura como static class.

**Mecanismo observado (forensic):**

```tsx
// vitalia/frontend/src/components/shared/shell-organism/RibbonTab.tsx
className={cn(
  "flex shrink-0 items-center gap-2 rounded-md px-4 text-sm transition-colors",
  active
    ? cn(
        agentBgSoftClass(slug),        // ✅ static class via switch helper — JIT incluido
        "font-semibold text-foreground",
        `hover:${agentBgSoftClass(slug)}`,  // ❌ template literal — JIT purge silencioso
      )
    : "font-medium text-muted-foreground hover:bg-muted hover:text-foreground",
)}
```

`agentBgSoftClass(slug)` retorna `'bg-agent-lisa-soft'` (string literal por switch — Tailwind JIT detecta). Pero `` `hover:${agentBgSoftClass(slug)}` `` produce `'hover:bg-agent-lisa-soft'` que NO existe como static string en el codebase — Tailwind purge lo elimina del bundle final.

**Por qué Q16 "funciona" accidentalmente:**

El branch active solo aplica `agentBgSoftClass(slug)` + `font-semibold` + `text-foreground`. No hay `hover:bg-muted` competing (que sí está en el inactive branch). Cuando user hovers sobre active tab:
- Tailwind generated `bg-agent-lisa-soft` persiste (background-color: rgba(0,208,132,0.12))
- No hay regla `hover:*` matching → no override
- Visual outcome: tint preservado ✓ (pero NO por specificity hack — por ausencia de competing rule)

**Por qué el bug NO causa visual regression hoy:**

Active branch no comparte hover overrides con inactive branch (clases separadas via ternary). Si futuro refactor agrega `hover:bg-muted` shared o `:hover` rule global, el tint sí se degradará.

**How to apply (defensive pattern para futuras stories Tailwind v4):**

1. **NUNCA template literals en class strings** que ejecuten Tailwind JIT — preferí static helpers:
   ```ts
   // ❌ EVITAR
   `hover:${agentBgSoftClass(slug)}`
   `bg-${color}-500`

   // ✅ HACER
   agentHoverBgSoftClass(slug)  // helper switch case retorna 'hover:bg-agent-lisa-soft' static
   getColorClass(color)          // helper map retorna static class
   ```

2. **Allowlist explícito en `_agent-tw-classes.ts`** (o equivalente brand):
   ```ts
   // Esta constante TIENE QUE existir verbatim — Tailwind grep la encuentra
   const _AGENT_TW_ALLOWLIST = [
     'bg-agent-lisa-soft',    'hover:bg-agent-lisa-soft',
     'bg-agent-lucas-soft',   'hover:bg-agent-lucas-soft',
     'bg-agent-adrian-soft',  'hover:bg-agent-adrian-soft',
     'bg-agent-valeria-soft', 'hover:bg-agent-valeria-soft',
     'bg-agent-camila-soft',  'hover:bg-agent-camila-soft',
   ] as const;
   ```

3. **Arch fitness test verificando hover class presence** post-render:
   ```ts
   // RibbonTab.test.tsx — assertion explícita
   const tab = render(<RibbonTab slug="lisa" active={true} ... />);
   const className = tab.querySelector('[role=tab]').className;
   expect(className).toContain('bg-agent-lisa-soft');
   expect(className).toContain('hover:bg-agent-lisa-soft');  // ★ asegurar present
   ```

4. **Visual golden `ribbon-hover-active.png`** capturando hover sobre active tab — Playwright `.hover()` + `.toHaveScreenshot()`.

**Follow-up ticket sugerido:**

- F1-S8 (sub-tabs-line2) o standalone "vitalia-shell-organism-q16-jit-static-classes"
- Scope: agregar `agentHoverBgSoftClass(slug)` helper en `_agent-tw-classes.ts` + EXTEND `_AGENT_TW_ALLOWLIST` constante + unit test asserting hover class present + visual golden hover-active
- Severity: LOW (functional behavior correct, hardening defensive intent)

**Cross-brand applicability:**

Pattern aplicable a TODA brand activa que use Tailwind tokens per-tenant/per-agent/per-color dinámicos (nicolify Lisa, comunify cohort, futuros brands). Anti-pattern es universal cross-Tailwind-v4-projects.

**Promotion candidate:**

Si nicolify/comunify/lupulo adoptan multi-tenant color tokens similares y cae el mismo gotcha → lift `getColorClass()` + `_AGENT_TW_ALLOWLIST` helper a `core/luana-core-ui-helpers/` futuro. Promotable: candidate — depende de 2+ brand adoption.

**References:**

- Tailwind v4 JIT purge: https://tailwindcss.com/docs/content-configuration#dynamic-class-names
- Q16 spec anchor: `01-spec.md` § Q-table Q16 + § Estados visuales active:hover row (po_ux_version 2)
- Q16 arch anchor: `03-arch.md` § D17.2 cement (iter 1-A amendment)
- Audit finding: `REVIEW.md` § WARN-1

---
ticket: T-2
story_id: vitalia-fase1-stack-stability
brand: vitalia
state: pushed
validator_ids: [val-t2-css-vars-present, val-t2-dark-vars-present, val-t2-agent-tokens-tailwind, val-t2-vt-preserved, val-t2-tsc-clean]
---

# T-2 — globals.css agent tokens + tailwind extend — Result

## Deliverables

### globals.css
- Added `@layer base` block per Design Contract § 5.1 verbatim
- `:root` block: --background, --foreground, --card, --card-foreground, --popover, --popover-foreground, --primary, --primary-foreground, --secondary, --secondary-foreground, --muted, --muted-foreground, --accent, --accent-foreground, --destructive, --destructive-foreground, --border, --input, --ring, --radius, --agent-lisa, --agent-lisa-soft, --agent-lucas, --agent-lucas-soft, --agent-adrian, --agent-adrian-soft, --agent-valeria, --agent-valeria-soft, --agent-camila, --agent-camila-soft, --agent-mateo, --agent-config
- `.dark` block: all surface tokens overridden for dark mode + 5 agent-soft dark variants
- Legacy `:root { --vitalia-* }` PRESERVED
- Legacy `.vt-*` classes (150+) PRESERVED

### tailwind.config.ts
- Shadcn semantic tokens added: background, foreground, primary.{DEFAULT,foreground}, secondary.{DEFAULT,foreground}, muted.{DEFAULT,foreground}, accent.{DEFAULT,foreground}, destructive.{DEFAULT,foreground}, card.{DEFAULT,foreground}, popover.{DEFAULT,foreground}, border, input, ring
- Agent tokens added: agent.{lisa,lisa-soft,lucas,lucas-soft,adrian,adrian-soft,valeria,valeria-soft,camila,camila-soft,mateo,config}
- borderRadius: added md + sm tokens (Shadcn requirement)
- All existing vitalia-* colors preserved

## Validators

| Validator | Status |
|---|---|
| val-t2-css-vars-present | PASS — @layer base :root has all Shadcn standard + agent tokens |
| val-t2-dark-vars-present | PASS — .dark block has surface + agent-soft dark variants |
| val-t2-agent-tokens-tailwind | PASS — tailwind.config.ts has agent.{lisa..config} tokens |
| val-t2-vt-preserved | PASS — legacy .vt-* block intact, 0 deletions to existing classes |
| val-t2-tsc-clean | PASS — `npx tsc --noEmit` 0 errors |

## Gherkin coverage
- SC-04 "Agent token lisa renders green" → colors.agent.lisa = hsl(var(--agent-lisa)) configured
- SC-05 "Dark mode vars present" → .dark block with overrides present

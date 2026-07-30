# @luana/extension-sdk v0.0.8-alpha

Luana extension SDK — TypeScript type mirror v0.0.8-alpha.

FE-mirror partial scope: EP-6 `SidebarRouteDef` + EP-10 `LandingTemplateDef` + EP-18 `WizardStepDef`.

**NO runtime registry FE-side** — registration always BE at FastAPI startup.
TS types are TYPE-ONLY exports — compile-time validation in Stories 11-13 brand FE apps.

## Exported types

- `BrandContext` — per-tenant context (9 fields, mirrors Python frozen dataclass)
- `SidebarRouteDef` — EP-6 sidebar route definition
- `LandingTemplateDef` — EP-10 landing template definition
- `WizardStepDef` — EP-18 onboarding wizard step definition

## Usage

```typescript
import type { BrandContext, SidebarRouteDef, WizardStepDef, LandingTemplateDef } from '@luana/extension-sdk';
```

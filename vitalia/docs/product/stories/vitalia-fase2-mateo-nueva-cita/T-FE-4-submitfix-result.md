---
ticket: T-FE-4-submitfix
story_id: vitalia-fase2-mateo-nueva-cita
brand: vitalia
type: bugfix
state: done
resolved_at: 2026-06-22
---

# T-FE-4 — Inline Create Patient Submit Fix (Bug #5)

## Summary

After the nested-`<form>` fix (Bug #4, applied by Chris), clicking "Crear paciente" with a valid name and blank phone still did nothing: no POST fired, no validation error rendered, no pending state.

## Root Cause (2-part)

### Part 1 — Zod schema (primary)

```typescript
// BUGGY (before)
phone: z.string().min(6, "Ingresa un teléfono válido").max(20).nullable().optional()
//                    ^^ fails for "" — RHF blocks handleSubmit silently
```

`defaultValues: { phone: "" }` means when the phone field is left blank, `""` (empty string) is NOT `null` or `undefined`. The `z.string().min(6)` validator fails on `""`, so `zodResolver` returns a validation error, `form.handleSubmit` never invokes its callback, and the mutation is never called — all silently (no error rendered because RHF `mode: "onSubmit"` with `""` on an optional field treats it as a "not dirty" no-op in the UI).

### Part 2 — onClick invocation (secondary)

```typescript
// BUGGY (before)
onClick={form.handleSubmit(handleInlineSubmit)}
// form.handleSubmit(cb) returns a function — passing it as onClick means
// React calls it with the SyntheticEvent arg, which is fine, BUT the async
// promise is unvoided. Changed to explicit invocation for clarity.

// FIXED
onClick={() => void form.handleSubmit(handleInlineSubmit)()}
```

## Fix Applied

**File:** `vitalia/frontend/src/features/mateo/components/nueva-cita/PatientPickerWithCreate.tsx`

### Schema fix

```typescript
// FIXED — empty string → null via union + transform
const InlineCreateSchema = z.object({
  name: z.string().min(2, "El nombre debe tener al menos 2 caracteres").max(120),
  phone: z
    .union([
      z.string().min(6, "Ingresa un teléfono válido").max(20),
      z.literal(""),
    ])
    .nullable()
    .optional()
    .transform((v): string | null => (v === "" || v == null ? null : v)),
});

// RHF 3-arg generic: separates input type (form fields) from output type (post-transform)
// This is required when using .transform() with zodResolver + TypeScript strict
type InlineCreateFormInput = z.input<typeof InlineCreateSchema>;   // phone?: string|""|null|undefined
type InlineCreateFormOutput = z.output<typeof InlineCreateSchema>; // phone: string|null

const form = useForm<InlineCreateFormInput, unknown, InlineCreateFormOutput>({
  resolver: zodResolver(InlineCreateSchema),
  defaultValues: { name: "", phone: "" },
  mode: "onSubmit",
});

const handleInlineSubmit = async (data: InlineCreateFormOutput) => { ... }
```

### onClick fix

```typescript
onClick={() => void form.handleSubmit(handleInlineSubmit)()}
```

## Main Submit Analysis (NuevaCitaView)

Checked `NuevaCitaView` submit path: `<form onSubmit={handleSubmit(onSubmit)}>` + `NuevaCitaActions onSubmit={handleSubmit(onSubmit)}` → `FormActionBar` submit button is `type="button"` calling `onClick={onSubmit}`. `handleSubmit(onSubmit)` is a function; `FormActionBar` calls `onSubmit?.()` which correctly invokes it. **NOT affected by the same bug class.**

## TDD Evidence

**RED first (regression guard):**
```
SC-crear-paciente-sin-telefono: name-only (phone blank) MUST call mutation [regression guard bug#5]
FAIL — mockCreatePatient not called (line 281)
```
Confirmed the bug: `handleSubmit` was blocked by Zod validation failing on `""`.

**GREEN after fix:**
```
✓ src/features/mateo/components/nueva-cita/__tests__/PatientPickerWithCreate.test.tsx (5 tests) 292ms
5 passed (5)
```

## G5 Gate Results

| Gate | Result |
|---|---|
| `tsc --noEmit` | 0 errors |
| `eslint src/` | 0 errors |
| `vitest run src/features/mateo/` | 371/371 PASS (30 test files) |

## Files Changed

| File | Change |
|---|---|
| `vitalia/frontend/src/features/mateo/components/nueva-cita/PatientPickerWithCreate.tsx` | Schema fix (union+transform) + `InlineCreateFormInput`/`Output` types + `useForm<Input,_,Output>` + onClick explicit invocation |
| `vitalia/frontend/src/features/mateo/components/nueva-cita/__tests__/PatientPickerWithCreate.test.tsx` | Added `SC-crear-paciente-sin-telefono` regression guard test (RED-first → GREEN) |

## Regression Guard

Test `SC-crear-paciente-sin-telefono` in `PatientPickerWithCreate.test.tsx` ensures this bug class cannot regress: any future schema change that breaks empty-phone submit will fail this test before reaching CI.

# T-9 Implementation Log — FE Vitest unit tests (hooks + store + schemas + utils + integration)

**Story:** vitalia-fase2-lisa-marca
**Ticket:** T-9
**Surface:** FE tests (non-production code)
**Date:** 2026-05-27
**Builder:** claude-sonnet-f2-s7-t9

---

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| `tessl__vitest` | Setting up Vitest patterns for React Query hooks, fake timers, vi.hoisted | Used `vi.hoisted()` for mock variables that need to be available when `vi.mock` factory is hoisted. Used `vi.advanceTimersByTimeAsync()` instead of `vi.advanceTimersByTime() + waitFor` — async version processes microtasks/promises in the same call. |
| `tessl__react-patterns` | Hook test isolation, QueryClientProvider wrapper pattern | Each test creates its own `QueryClient` via `makeWrapper()` factory to avoid cache pollution between tests. |
| `frontend-expert` | FSD-Lite boundaries, test file locations | Tests in `__tests__/` subdirectories per FSD-Lite. No production code edits per T-9 scope. |

---

## Gap Analysis

Running `npx vitest run src/features/lisa/` pre-T-9 showed **141 tests in 15 files**.

Files with NO tests (T-9 targets):
- `hooks/__tests__/` — empty (useIdentityAutosave, useVisualsAutosave, usePersonalityAutosave, useContactAutosave, useVoicePreview, useVoiceBlocklist)
- `store/__tests__/` — empty (useMarcaIdentidadStore)
- `api/__tests__/` — empty (marcaKeys factory)
- `utils/marca/__tests__/` — empty (detectProhibitedPhrases, hashVoiceBlocks)
- `components/marca/identidad/__tests__/` — partial (ClinicVerticalReadOnly missing)

---

## Files Created

### Utils
- `vitalia/frontend/src/features/lisa/utils/marca/__tests__/prohibitedPhraseDetector.test.ts`
  - 19 tests covering `detectProhibitedPhrases` and `hashVoiceBlocks`
  - Cases: empty inputs, exact match, case-insensitive, multiple matches, false positives, result payload, hash determinism, key-order independence

### Zustand Store
- `vitalia/frontend/src/features/lisa/store/__tests__/marca-store.test.ts`
  - 16 tests covering `useMarcaIdentidadStore`
  - Cases: initial state, setDropzoneActive, setColorPickerOpen (all slots), setLogoUploading, resetUiState (individual + combined)
  - Pattern: `renderHook` + `act` + `beforeEach(() => useMarcaIdentidadStore.setState(...))` reset

### API Key Factory
- `vitalia/frontend/src/features/lisa/api/__tests__/marca.test.ts`
  - 24 tests covering all 11 `marcaKeys` entries
  - Cases: correct tuple structure, tenant isolation, no-collision between sub-resources, voicePreview 2D key (tenant+hash)

### Hooks — Autosave (4 files)
- `vitalia/frontend/src/features/lisa/hooks/__tests__/useIdentityAutosave.test.ts` (11 tests)
- `vitalia/frontend/src/features/lisa/hooks/__tests__/useVisualsAutosave.test.ts` (10 tests)
- `vitalia/frontend/src/features/lisa/hooks/__tests__/usePersonalityAutosave.test.ts` (11 tests)
- `vitalia/frontend/src/features/lisa/hooks/__tests__/useContactAutosave.test.ts` (10 tests)
  - Shared pattern: `vi.useFakeTimers()` + `vi.hoisted()` for mock variables
  - Key fix: `vi.advanceTimersByTimeAsync(600)` inside `await act(async () => {...})` to process fake timer ticks AND flush React Query mutation microtasks in one step
  - Cases: initial state, dirty transition, debounce (NO fire at 300ms), debounce (fire at 600ms), rapid edits (1 mutation only), saved/error transitions, cancelAutosave

### Hooks — Query (2 files)
- `vitalia/frontend/src/features/lisa/hooks/__tests__/useVoicePreview.test.ts` (9 tests)
  - Cases: disabled when `enabled=false`, disabled when `personalityProfileId=""`, fetch success returns preview, isError on failure, correct blocksHash passed, tenant isolation (2 tenants = 2 fetches)
- `vitalia/frontend/src/features/lisa/hooks/__tests__/useVoiceBlocklist.test.ts` (7 tests)
  - Cases: returns phrases array, isLoading transitions, fallback `[]` when `items=undefined`, empty list, correct tenantId passed

### Component
- `vitalia/frontend/src/features/lisa/components/marca/identidad/__tests__/ClinicVerticalReadOnly.test.tsx` (14 tests)
  - Cases: vertical pill text, "Sin especialidad registrada" fallback, specialty pills (up to 5), "+N más" badge (6, 8 specialties), no badge when exactly 5, 6th item hidden, edit link href, "Editar" text, ARIA section label, ARIA specialties label

---

## Technical Decisions

### `vi.hoisted()` pattern
```typescript
const { mockUpdateIdentity } = vi.hoisted(() => ({
  mockUpdateIdentity: vi.fn(),
}));
vi.mock("../../api/marca", async (importOriginal) => {
  const actual = await importOriginal<...>();
  return { ...actual, updateIdentity: mockUpdateIdentity };
});
```
Using `vi.mock` factory with a reference to an outer variable causes "Cannot access 'mockX' before initialization" because `vi.mock` is hoisted to the top of the file. `vi.hoisted()` creates variables in the hoisting zone.

### `vi.advanceTimersByTimeAsync()` for debounce tests
```typescript
await act(async () => {
  await vi.advanceTimersByTimeAsync(600);
});
expect(mockUpdateIdentity).toHaveBeenCalledTimes(1);
```
The sync `vi.advanceTimersByTime()` does not flush React Query's async mutation microtasks. `vi.advanceTimersByTimeAsync()` advances fake timers AND processes the promise queue. No `waitFor` needed.

### Fixture types aligned to actual API contracts
- `CONTACT_VALUES` uses `BrandContactPatchPayload` fields (camelCase): `websiteUrl`, `instagramHandle`, `facebookPage`, `googleBusinessUrl`, `whatsappBusiness` — not legacy snake_case address fields.

---

## Quality Gate Results

- `tsc --noEmit`: 0 errors
- `eslint src/features/lisa/ --cache`: 0 errors, 0 warnings
- `vitest run src/features/lisa/`: 267 tests, 25 files, all PASS
- No production code modified (T-9 scope: tests only)
- No existing tests removed or duplicated

### Test count delta
| State | Files | Tests |
|---|---|---|
| Pre-T-9 | 15 | 141 |
| Post-T-9 | 25 | 267 |
| **Delta** | **+10** | **+126** |

---

## Constraint Compliance

- HIPAA-lite: No PHI in test fixtures. Patient data used: synthetic clinic names, no real medical records.
- Spanish neutro: Test descriptions use Spanish neutro (no voseo). All `describe`/`it` strings reviewed.
- Tenant isolation tested: marcaKeys tests verify different tenantId produces different cache keys; useVoicePreview tenant isolation test confirms 2 separate fetches for 2 tenants.
- Anti-creep: `detectProhibitedPhrases` tested as substring scan only — NO LLM call mocked. `useVoiceBlocklist` tested as simple GET — NO voice compiler invoked.

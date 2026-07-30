# T-FE-4 — Stale Clerk JWT Token Fix · Result

**Story:** vitalia-fase2-mateo-nueva-cita  
**Ticket:** T-FE-4  
**Type:** Regression bugfix (integration)  
**Date:** 2026-06-22

---

## Root cause (confirmed by live DevTools)

`NuevaCitaView.tsx` cached the Clerk JWT in React state via `useState + useEffect`:

```typescript
// DELETED — the bug
const [token, setToken] = React.useState<string>("");
React.useEffect(() => {
  if (!isLoaded || !isSignedIn) return;
  void getToken().then((t) => setToken(t ?? "")).catch(() => setToken(""));
}, [isLoaded, isSignedIn, getToken]);
```

Clerk JWTs expire in ~60 seconds. The effect only re-ran when auth state changed (not on expiry). Every POST/PATCH/DELETE issued after 60 seconds used the expired cached token → Clerk returned 307 → /sign-in.

DevTools evidence: `x-clerk-auth-reason: session-token-expired-refresh-non-eligible-non-get`

---

## Fix applied

`getToken()` (the function returned by `useAuth()`) transparently returns a cached-valid token or refreshes an expired one. It must be called INSIDE each `queryFn`/`mutationFn`, not cached in state.

### Files modified

| File | Change |
|---|---|
| `features/mateo/hooks/use-nueva-cita.ts` | 6 hooks: removed `token` from `BaseParams`; added `const { getToken, isLoaded, isSignedIn } = useAuth()` at hook body; resolve `const token = await getToken()` inside each `queryFn`/`mutationFn`; changed `enabled` gate to `isLoaded && Boolean(isSignedIn)` |
| `features/mateo/hooks/use-patients.ts` | 2 hooks (useSearchPatients, useCreatePatientInline): same pattern |
| `features/mateo/hooks/use-availability.ts` | 2 hooks (useAvailabilityCheck, useDayStrip): same pattern |
| `features/mateo/components/nueva-cita/NuevaCitaView.tsx` | Deleted entire token state+useEffect block; removed `token=` prop from all sub-components |
| `features/mateo/components/nueva-cita/AvailabilityChip.tsx` | Removed `token: string` from props interface + call sites |
| `features/mateo/components/nueva-cita/DayAvailabilityStrip.tsx` | Removed `token: string` from props interface + call sites |
| `features/mateo/components/nueva-cita/FreeDoctorsList.tsx` | Removed `token: string` from props interface (was unused in component body) |
| `features/mateo/components/nueva-cita/PatientPickerWithCreate.tsx` | Removed `token: string` from props; updated hook calls to omit token |

### Tests modified

| File | Change |
|---|---|
| `hooks/__tests__/use-nueva-cita.test.ts` | Added `vi.hoisted` + Clerk mock with `mockGetToken`; removed `token` from all hook calls; added T-FE-4 regression describe block |
| `hooks/__tests__/use-patients.test.ts` | Added Clerk mock; removed `token` from all hook calls |
| `hooks/__tests__/use-availability.test.ts` | Added Clerk mock; removed `token` from all hook calls |
| `components/nueva-cita/__tests__/AvailabilityChip.test.tsx` | Removed `token` from `BASE_PROPS` |
| `components/nueva-cita/__tests__/DayAvailabilityStrip.test.tsx` | Removed `token` from `BASE_PROPS` |
| `components/nueva-cita/__tests__/FreeDoctorsList.test.tsx` | Removed `token` from `BASE_PROPS` |
| `components/nueva-cita/__tests__/PatientPickerWithCreate.test.tsx` | Removed `token="tok"` from all render calls |

---

## TDD regression test (RED before refactor, GREEN after)

Added in `use-nueva-cita.test.ts`:

```typescript
describe("T-FE-4 regression: getToken() called per-request inside queryFn", () => {
  it("useNuevaCitaServices calls getToken() inside queryFn (not cached at mount)", async () => {
    mockGetToken.mockClear();
    const { result } = renderHook(() => useNuevaCitaServices({ tenantId: "t1" }), ...);
    await waitFor(() => !result.current.isPending);
    expect(mockGetToken).toHaveBeenCalled(); // fails with old pattern (0 calls in queryFn)
  });
  // + useNuevaCitaFreeDoctors equivalent
});
```

---

## G5 Gate results

```
tsc --noEmit    → 0 errors
eslint          → 0 errors
vitest run      → 30 files, 370 tests PASS
```

---

## What was NOT touched (per FORBIDDEN_TO_TOUCH)

- `core/@luana/ui-kit/src/` — untouched
- `core/luana-core-*/src/` — untouched
- Backend — untouched
- Other features — untouched
- Other brands — untouched
- `useActorHeaders()` / `useClinicId()` — unchanged (those headers don't expire)

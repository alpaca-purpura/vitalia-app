// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * staff-picker-adapter.test.ts — Vitest unit tests for the doctor picker
 * page↔cursor adapter (D3-A switcher · T-FE-switcher-wire).
 *
 * The EntityPicker (@luana/ui-kit, canon §2.4) speaks cursor pagination;
 * the doctors list endpoint speaks page/page_size. These tests pin the
 * pure adapter + the searchFn request contract:
 *   - pickerCursorToPage: cursor = stringified page (null/garbage → 1)
 *   - mapDoctorsPageToPickerResult: nextCursor only while pages remain,
 *     total passthrough, displayName fallback to "firstName lastName"
 *   - useDoctorPickerSearchFn: ALWAYS sends active=true (RN-D3A-2) +
 *     server-side q (RN-D3A-1) + page_size=limit (never full collection)
 *
 * TDD: written BEFORE the adapter (RED-first).
 *
 * T-FE-switcher-wire vitalia-fase2-lisa-doctores
 * spec_anchor: 03-arch-delta.md § 2.2 + 04-validators.yaml V-D3A-2/V-D3A-3
 * downstream-regression-na: brand-local vitalia FE test; no cross-brand consumers
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook } from "@testing-library/react";
import {
  pickerCursorToPage,
  mapDoctorsPageToPickerResult,
  useDoctorPickerSearchFn,
} from "../staff";
import type { PaginatedDoctors, DoctorListItem } from "../../types/staff.types";

// ── Module mocks (hook-level test only) ────────────────────────────────────────

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: async () => "test-token",
    isLoaded: true,
    isSignedIn: true,
  }),
}));

vi.mock("@/hooks/useTenantId", () => ({
  useTenantId: () => "tenant-uuid-1",
}));

vi.mock("@/hooks/useClinicId", () => ({
  useClinicId: () => "clinic-uuid-1",
}));

const fetchClientMock = vi.fn();
vi.mock("@/lib/api/fetchClient", () => ({
  fetchClient: (...args: unknown[]) => fetchClientMock(...args),
}));

// ── Fixtures ───────────────────────────────────────────────────────────────────

function makeDoctor(overrides: Partial<DoctorListItem> = {}): DoctorListItem {
  return {
    id: "doc-1",
    firstName: "Ana",
    lastName: "García Mendoza",
    specialty: "Odontología Cosmética",
    active: true,
    ...overrides,
  };
}

function makePage(overrides: Partial<PaginatedDoctors> = {}): PaginatedDoctors {
  return {
    items: [makeDoctor()],
    total: 1,
    page: 1,
    pageSize: 20,
    ...overrides,
  };
}

// ── pickerCursorToPage ─────────────────────────────────────────────────────────

describe("pickerCursorToPage", () => {
  it("null/undefined cursor → first page", () => {
    expect(pickerCursorToPage(null)).toBe(1);
    expect(pickerCursorToPage(undefined)).toBe(1);
  });

  it("stringified page passes through", () => {
    expect(pickerCursorToPage("3")).toBe(3);
  });

  it("garbage cursor → first page (no NaN fetch)", () => {
    expect(pickerCursorToPage("abc")).toBe(1);
  });

  it("zero/negative cursor → first page", () => {
    expect(pickerCursorToPage("0")).toBe(1);
    expect(pickerCursorToPage("-2")).toBe(1);
  });
});

// ── mapDoctorsPageToPickerResult ───────────────────────────────────────────────

describe("mapDoctorsPageToPickerResult", () => {
  it("intermediate page → nextCursor = String(page + 1)", () => {
    const res = makePage({ total: 45, page: 1, pageSize: 20 });
    expect(mapDoctorsPageToPickerResult(res, 1).nextCursor).toBe("2");
  });

  it("last page → nextCursor null (no more pages)", () => {
    const res = makePage({ total: 45, page: 3, pageSize: 20 });
    expect(mapDoctorsPageToPickerResult(res, 3).nextCursor).toBeNull();
  });

  it("single page → nextCursor null", () => {
    const res = makePage({ total: 2, page: 1, pageSize: 20 });
    expect(mapDoctorsPageToPickerResult(res, 1).nextCursor).toBeNull();
  });

  it("total passes through (picker footer 'Mostrando N de M')", () => {
    const res = makePage({ total: 45 });
    expect(mapDoctorsPageToPickerResult(res, 1).total).toBe(45);
  });

  it("maps name from displayName when present", () => {
    const res = makePage({
      items: [makeDoctor({ displayName: "Dra. Ana García" })],
    });
    expect(mapDoctorsPageToPickerResult(res, 1).items[0]?.name).toBe(
      "Dra. Ana García",
    );
  });

  it("falls back to 'firstName lastName' when displayName absent", () => {
    const res = makePage({ items: [makeDoctor({ displayName: null })] });
    expect(mapDoctorsPageToPickerResult(res, 1).items[0]?.name).toBe(
      "Ana García Mendoza",
    );
  });

  it("guards pageSize 0 (no division blow-up)", () => {
    const res = makePage({ total: 10, pageSize: 0 });
    expect(() => mapDoctorsPageToPickerResult(res, 1)).not.toThrow();
  });

  it("item id passes through (navigation target)", () => {
    const res = makePage({ items: [makeDoctor({ id: "doc-carlos-9" })] });
    expect(mapDoctorsPageToPickerResult(res, 1).items[0]?.id).toBe(
      "doc-carlos-9",
    );
  });
});

// ── useDoctorPickerSearchFn (request contract) ─────────────────────────────────

describe("useDoctorPickerSearchFn", () => {
  beforeEach(() => {
    fetchClientMock.mockReset();
    fetchClientMock.mockResolvedValue(makePage({ total: 1 }));
  });

  it("sends active=true ALWAYS (RN-D3A-2: inactive hidden)", async () => {
    const { result } = renderHook(() => useDoctorPickerSearchFn());
    await result.current({ q: "", cursor: null, limit: 20 });
    const url = fetchClientMock.mock.calls[0]?.[0] as string;
    expect(url).toContain("active=true");
  });

  it("sends q server-side when non-empty (RN-D3A-1: never client-side filter)", async () => {
    const { result } = renderHook(() => useDoctorPickerSearchFn());
    await result.current({ q: "ana", cursor: null, limit: 20 });
    const url = fetchClientMock.mock.calls[0]?.[0] as string;
    expect(url).toContain("q=ana");
  });

  it("omits q param when empty (initial page)", async () => {
    const { result } = renderHook(() => useDoctorPickerSearchFn());
    await result.current({ q: "", cursor: null, limit: 20 });
    const url = fetchClientMock.mock.calls[0]?.[0] as string;
    expect(url).not.toContain("q=");
  });

  it("sends page_size=limit (hard page size — never full collection)", async () => {
    const { result } = renderHook(() => useDoctorPickerSearchFn());
    await result.current({ q: "", cursor: null, limit: 20 });
    const url = fetchClientMock.mock.calls[0]?.[0] as string;
    expect(url).toContain("page_size=20");
    expect(url).toContain("page=1");
  });

  it("maps cursor → page param (cursor '2' → page=2)", async () => {
    const { result } = renderHook(() => useDoctorPickerSearchFn());
    await result.current({ q: "", cursor: "2", limit: 20 });
    const url = fetchClientMock.mock.calls[0]?.[0] as string;
    expect(url).toContain("page=2");
  });

  it("returns a STABLE function identity across re-renders (EntityPicker fetch effect dep)", () => {
    const { result, rerender } = renderHook(() => useDoctorPickerSearchFn());
    const first = result.current;
    rerender();
    expect(result.current).toBe(first);
  });

  it("passes tenant + clinic context to fetchClient (tenant isolation)", async () => {
    const { result } = renderHook(() => useDoctorPickerSearchFn());
    await result.current({ q: "", cursor: null, limit: 20 });
    const opts = fetchClientMock.mock.calls[0]?.[1] as Record<string, unknown>;
    expect(opts["tenantId"]).toBe("tenant-uuid-1");
    expect(opts["clinicId"]).toBe("clinic-uuid-1");
  });
});

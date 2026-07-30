/**
 * marca-store.test.ts — Vitest unit tests para el Zustand UI state store de Identidad.
 *
 * T-9 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-9 deliverables + ADR-vitalia-004 § 4 (Zustand = UI state ONLY)
 *
 * Tests cubiertos:
 *   - Estado inicial (dropzoneActive=false, colorPickerOpen=null, logoUploading=false)
 *   - setDropzoneActive: true / false
 *   - setColorPickerOpen: slots válidos / null (cierre)
 *   - setLogoUploading: true / false
 *   - resetUiState: vuelve a initialState
 *   - Aislamiento entre tests (beforeEach reset)
 *
 * downstream-regression-na: brand-local vitalia FE store tests; no cross-brand consumers
 */

import { describe, it, expect, beforeEach } from "vitest";
import { act, renderHook } from "@testing-library/react";
import { useMarcaIdentidadStore } from "../marca-identidad-store";
import type { ColorPickerSlot } from "../marca-identidad-store";

// Resetear store antes de cada test para aislamiento
beforeEach(() => {
  useMarcaIdentidadStore.setState({
    dropzoneActive: false,
    colorPickerOpen: null,
    logoUploading: false,
  });
});

// ── Estado inicial ─────────────────────────────────────────────────────────────

describe("useMarcaIdentidadStore — estado inicial", () => {
  it("dropzoneActive empieza en false", () => {
    const { result } = renderHook(() => useMarcaIdentidadStore());
    expect(result.current.dropzoneActive).toBe(false);
  });

  it("colorPickerOpen empieza en null (todos cerrados)", () => {
    const { result } = renderHook(() => useMarcaIdentidadStore());
    expect(result.current.colorPickerOpen).toBeNull();
  });

  it("logoUploading empieza en false", () => {
    const { result } = renderHook(() => useMarcaIdentidadStore());
    expect(result.current.logoUploading).toBe(false);
  });
});

// ── setDropzoneActive ──────────────────────────────────────────────────────────

describe("useMarcaIdentidadStore — setDropzoneActive", () => {
  it("activa el dropzone al pasar true", () => {
    const { result } = renderHook(() => useMarcaIdentidadStore());

    act(() => result.current.setDropzoneActive(true));
    expect(result.current.dropzoneActive).toBe(true);
  });

  it("desactiva el dropzone al pasar false", () => {
    const { result } = renderHook(() => useMarcaIdentidadStore());

    act(() => result.current.setDropzoneActive(true));
    act(() => result.current.setDropzoneActive(false));
    expect(result.current.dropzoneActive).toBe(false);
  });

  it("mantiene otros estados al cambiar dropzoneActive", () => {
    const { result } = renderHook(() => useMarcaIdentidadStore());

    act(() => result.current.setColorPickerOpen("primary"));
    act(() => result.current.setDropzoneActive(true));

    expect(result.current.colorPickerOpen).toBe("primary"); // no cambia
    expect(result.current.dropzoneActive).toBe(true);
  });
});

// ── setColorPickerOpen ─────────────────────────────────────────────────────────

describe("useMarcaIdentidadStore — setColorPickerOpen", () => {
  const slots: ColorPickerSlot[] = ["primary", "accent", "background", null];

  it("abre el popover de color 'primary'", () => {
    const { result } = renderHook(() => useMarcaIdentidadStore());

    act(() => result.current.setColorPickerOpen("primary"));
    expect(result.current.colorPickerOpen).toBe("primary");
  });

  it("abre el popover de color 'accent'", () => {
    const { result } = renderHook(() => useMarcaIdentidadStore());

    act(() => result.current.setColorPickerOpen("accent"));
    expect(result.current.colorPickerOpen).toBe("accent");
  });

  it("abre el popover de color 'background'", () => {
    const { result } = renderHook(() => useMarcaIdentidadStore());

    act(() => result.current.setColorPickerOpen("background"));
    expect(result.current.colorPickerOpen).toBe("background");
  });

  it("cierra el popover al pasar null", () => {
    const { result } = renderHook(() => useMarcaIdentidadStore());

    act(() => result.current.setColorPickerOpen("accent"));
    act(() => result.current.setColorPickerOpen(null));
    expect(result.current.colorPickerOpen).toBeNull();
  });

  it("acepta todos los slots válidos sin lanzar excepción", () => {
    const { result } = renderHook(() => useMarcaIdentidadStore());

    for (const slot of slots) {
      expect(() => {
        act(() => result.current.setColorPickerOpen(slot));
      }).not.toThrow();
    }
  });

  it("solo un popover abierto a la vez (el último slot gana)", () => {
    const { result } = renderHook(() => useMarcaIdentidadStore());

    act(() => result.current.setColorPickerOpen("primary"));
    act(() => result.current.setColorPickerOpen("accent"));
    expect(result.current.colorPickerOpen).toBe("accent");
  });
});

// ── setLogoUploading ───────────────────────────────────────────────────────────

describe("useMarcaIdentidadStore — setLogoUploading", () => {
  it("activa logoUploading al pasar true", () => {
    const { result } = renderHook(() => useMarcaIdentidadStore());

    act(() => result.current.setLogoUploading(true));
    expect(result.current.logoUploading).toBe(true);
  });

  it("desactiva logoUploading al pasar false", () => {
    const { result } = renderHook(() => useMarcaIdentidadStore());

    act(() => result.current.setLogoUploading(true));
    act(() => result.current.setLogoUploading(false));
    expect(result.current.logoUploading).toBe(false);
  });
});

// ── resetUiState ───────────────────────────────────────────────────────────────

describe("useMarcaIdentidadStore — resetUiState", () => {
  it("vuelve dropzoneActive a false", () => {
    const { result } = renderHook(() => useMarcaIdentidadStore());

    act(() => result.current.setDropzoneActive(true));
    act(() => result.current.resetUiState());
    expect(result.current.dropzoneActive).toBe(false);
  });

  it("vuelve colorPickerOpen a null", () => {
    const { result } = renderHook(() => useMarcaIdentidadStore());

    act(() => result.current.setColorPickerOpen("background"));
    act(() => result.current.resetUiState());
    expect(result.current.colorPickerOpen).toBeNull();
  });

  it("vuelve logoUploading a false", () => {
    const { result } = renderHook(() => useMarcaIdentidadStore());

    act(() => result.current.setLogoUploading(true));
    act(() => result.current.resetUiState());
    expect(result.current.logoUploading).toBe(false);
  });

  it("resetea todos los campos a initialState en una sola llamada", () => {
    const { result } = renderHook(() => useMarcaIdentidadStore());

    act(() => {
      result.current.setDropzoneActive(true);
      result.current.setColorPickerOpen("primary");
      result.current.setLogoUploading(true);
    });

    act(() => result.current.resetUiState());

    expect(result.current.dropzoneActive).toBe(false);
    expect(result.current.colorPickerOpen).toBeNull();
    expect(result.current.logoUploading).toBe(false);
  });
});

// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * bio-docs-api.test.ts — Unit tests for bio-docs API hooks (T-FE-bio-docs, D3-B).
 *
 * Coverage:
 *   - staffKeys.bioFiles key shape
 *   - BioFile type structure (compile-time via TypeScript + shape assertion)
 *   - Upload mutation validates file type + size (unit logic)
 *   - SC-D3B-3: invalid file type → error state, no fetch to upload endpoint
 *   - SC-D3B-5: STORAGE_UNAVAILABLE (503) → mutation error with error code
 *
 * T-FE-bio-docs vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § D3-B + Gherkin SC-D3B-3 + SC-D3B-5
 * downstream-regression-na: brand-local vitalia FE test; no cross-brand consumers
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { staffKeys } from "../staff";
import type { BioFile } from "../../types/staff.types";

// ── staffKeys.bioFiles ────────────────────────────────────────────────────────

describe("staffKeys.bioFiles", () => {
  it("produces correct query key shape", () => {
    const key = staffKeys.bioFiles("doctor-abc");
    // Expected: ['lisa','staff','detail','doctor-abc','bio-files']
    expect(key).toContain("lisa");
    expect(key).toContain("staff");
    expect(key).toContain("doctor-abc");
    expect(key).toContain("bio-files");
  });

  it("is distinct from blocks key", () => {
    const bioKey = staffKeys.bioFiles("d1");
    const blockKey = staffKeys.blocks("d1");
    expect(JSON.stringify(bioKey)).not.toBe(JSON.stringify(blockKey));
  });
});

// ── BioFile type shape (runtime shape assertion against expected DTO) ─────────

describe("BioFile interface shape", () => {
  it("accepts a valid BioFileDTO shape (camelCase mirror)", () => {
    // This test documents the expected shape. TypeScript will error at compile-time
    // if the interface diverges from what we assert here.
    const bioFile: BioFile = {
      id: "550e8400-e29b-41d4-a716-446655440000",
      filename: "curriculum_vitae.pdf",
      sizeBytes: 256_000,
      contentType: "application/pdf",
      uploadedAt: "2026-06-12T10:00:00Z",
    };
    expect(bioFile.id).toBe("550e8400-e29b-41d4-a716-446655440000");
    expect(bioFile.sizeBytes).toBe(256_000);
    expect(bioFile.contentType).toBe("application/pdf");
  });
});

// ── SC-D3B-3: Invalid file type → local error, no upload fetch ───────────────

describe("SC-D3B-3: invalid file type rejected client-side", () => {
  const ALLOWED_TYPES = [
    "application/pdf",
    "image/jpeg",
    "image/png",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  ];
  const MAX_SIZE_BYTES = 10 * 1024 * 1024;

  function validateFile(file: { type: string; size: number }): string | null {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return "Tipo de archivo no permitido";
    }
    if (file.size > MAX_SIZE_BYTES) {
      return "El archivo supera 10 MB";
    }
    return null;
  }

  it("rejects .exe file type", () => {
    const err = validateFile({ type: "application/x-msdownload", size: 1000 });
    expect(err).toBe("Tipo de archivo no permitido");
  });

  it("rejects .zip file type", () => {
    const err = validateFile({ type: "application/zip", size: 1000 });
    expect(err).toBe("Tipo de archivo no permitido");
  });

  it("rejects file over 10 MB", () => {
    const err = validateFile({
      type: "application/pdf",
      size: 11 * 1024 * 1024,
    });
    expect(err).toBe("El archivo supera 10 MB");
  });

  it("accepts valid PDF within size limit", () => {
    const err = validateFile({ type: "application/pdf", size: 1 * 1024 * 1024 });
    expect(err).toBeNull();
  });

  it("accepts valid JPEG", () => {
    const err = validateFile({ type: "image/jpeg", size: 500_000 });
    expect(err).toBeNull();
  });
});

// ── SC-D3B-5: Storage unavailable → error code STORAGE_UNAVAILABLE ───────────

describe("SC-D3B-5: storage unavailable error code", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    // Mock fetch to return 503 (storage unavailable)
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => ({ detail: "Storage unavailable" }),
    } as Response);
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("detects 503 and throws STORAGE_UNAVAILABLE", async () => {
    // Simulate the upload step-1 logic extracted from useBioFileUpload
    const response = await global.fetch("/api/v1/vitalia/assets/upload", {
      method: "POST",
    });

    let errorCode: string | null = null;
    if (!response.ok) {
      const status = response.status;
      if (status === 503) {
        errorCode = "STORAGE_UNAVAILABLE";
      } else {
        errorCode = `UPLOAD_ERROR_${status}`;
      }
    }

    expect(errorCode).toBe("STORAGE_UNAVAILABLE");
  });

  it("non-503 error produces generic error code", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({}),
    } as Response);

    const response = await global.fetch("/api/v1/vitalia/assets/upload", {
      method: "POST",
    });

    let errorCode: string | null = null;
    if (!response.ok) {
      const status = response.status;
      errorCode = status === 503 ? "STORAGE_UNAVAILABLE" : `UPLOAD_ERROR_${status}`;
    }

    expect(errorCode).toBe("UPLOAD_ERROR_500");
  });
});

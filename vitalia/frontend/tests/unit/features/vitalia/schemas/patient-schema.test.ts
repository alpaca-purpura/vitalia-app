import { describe, it, expect } from "vitest";
import { medicalPdfUploadSchema } from "@/features/vitalia/schemas/patient-schema";

describe("medicalPdfUploadSchema", () => {
  it("accepts valid PDF upload data", () => {
    const result = medicalPdfUploadSchema.safeParse({
      file_name: "historial_clinico.pdf",
      content_type: "application/pdf",
      base64_content: "JVBERi0xLjQK...",
    });
    expect(result.success).toBe(true);
  });

  it("rejects non-pdf content_type", () => {
    const result = medicalPdfUploadSchema.safeParse({
      file_name: "historial.docx",
      content_type: "application/msword",
      base64_content: "base64content",
    });
    expect(result.success).toBe(false);
  });

  it("rejects empty file_name", () => {
    const result = medicalPdfUploadSchema.safeParse({
      file_name: "",
      content_type: "application/pdf",
      base64_content: "base64content",
    });
    expect(result.success).toBe(false);
  });

  it("rejects missing base64_content", () => {
    const result = medicalPdfUploadSchema.safeParse({
      file_name: "file.pdf",
      content_type: "application/pdf",
    });
    expect(result.success).toBe(false);
  });
});

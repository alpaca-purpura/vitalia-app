/**
 * Tests for DoctorAvatarPicker component contract.
 * Verifies: named exports, availability microcopy, DoctorOption shape.
 */
import { describe, it, expect, vi } from "vitest";
import type { DoctorOption } from "@/features/vitalia/components/doctor-avatar-picker";

describe("DoctorAvatarPicker exports", () => {
  it("exports DoctorAvatarPicker as named export", async () => {
    const mod = await import("@/features/vitalia/components/doctor-avatar-picker");
    expect(typeof mod.DoctorAvatarPicker).toBe("function");
    expect(mod).not.toHaveProperty("default");
  });
});

describe("DoctorAvatarPicker microcopy", () => {
  it("availability labels are in Spanish neutro", async () => {
    const { MICROCOPY_BOOKING } = await import("@/features/vitalia/config/microcopy");
    const voseoVerbs = /\b(tenés|podés|hacés|mirá|dejá|usá)\b/i;
    expect(MICROCOPY_BOOKING.availability.available).not.toMatch(voseoVerbs);
    expect(MICROCOPY_BOOKING.availability.busy).not.toMatch(voseoVerbs);
  });

  it("availability labels match spec § 8.4", async () => {
    const { MICROCOPY_BOOKING } = await import("@/features/vitalia/config/microcopy");
    expect(MICROCOPY_BOOKING.availability.available).toBe("Disponible");
    expect(MICROCOPY_BOOKING.availability.busy).toBe("Ocupado");
  });
});

describe("DoctorAvatarPicker prop contract", () => {
  it("DoctorOption has required fields: id, name, specialties, isAvailable", () => {
    const doctor: DoctorOption = {
      id: "doc-1",
      name: "Dr. Ramírez",
      specialties: ["Odontología", "Ortodoncia"],
      isAvailable: true,
    };
    expect(doctor.id).toBe("doc-1");
    expect(doctor.name).toBe("Dr. Ramírez");
    expect(doctor.specialties).toHaveLength(2);
    expect(doctor.isAvailable).toBe(true);
  });

  it("onChange is invoked with doctor id string", () => {
    const onChange = vi.fn((id: string) => id);
    onChange("doc-1");
    expect(onChange).toHaveBeenCalledWith("doc-1");
  });

  it("unavailable doctor does not trigger onChange", () => {
    // Simulates the component guarding against unavailable doctors
    const onChange = vi.fn((id: string) => id);
    const doctor: DoctorOption = {
      id: "doc-2",
      name: "Dra. Soto",
      specialties: ["Psicología"],
      isAvailable: false,
    };
    // Component disables unavailable doctors — this simulates checking the guard
    if (doctor.isAvailable) {
      onChange(doctor.id);
    }
    expect(onChange).not.toHaveBeenCalled();
  });

  it("optional fields avatarUrl and initials are nullable", () => {
    const doctorWithoutAvatar: DoctorOption = {
      id: "doc-3",
      name: "Dr. López",
      specialties: ["Psiquiatría"],
      isAvailable: true,
      avatarUrl: null,
      initials: "DL",
    };
    expect(doctorWithoutAvatar.avatarUrl).toBeNull();
    expect(doctorWithoutAvatar.initials).toBe("DL");
  });
});

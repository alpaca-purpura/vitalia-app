// cap: brand_studio.lisa-marca
import { describe, expect, it } from "vitest";
import { aggregateAutosaveStatus } from "../aggregateAutosave";

describe("aggregateAutosaveStatus", () => {
  it("returns idle for empty or all-idle sections", () => {
    expect(aggregateAutosaveStatus([])).toEqual({ status: "idle", savedAt: null });
    expect(
      aggregateAutosaveStatus([
        { status: "idle", savedAt: null },
        { status: "idle", savedAt: null },
      ]),
    ).toEqual({ status: "idle", savedAt: null });
  });

  it("prioritizes saving over everything", () => {
    const r = aggregateAutosaveStatus([
      { status: "saved", savedAt: new Date() },
      { status: "saving", savedAt: null },
      { status: "error", savedAt: null },
    ]);
    expect(r.status).toBe("saving");
  });

  it("prioritizes error over dirty and saved", () => {
    const r = aggregateAutosaveStatus([
      { status: "saved", savedAt: new Date() },
      { status: "dirty", savedAt: null },
      { status: "error", savedAt: null },
    ]);
    expect(r.status).toBe("error");
  });

  it("prioritizes dirty over saved", () => {
    const r = aggregateAutosaveStatus([
      { status: "saved", savedAt: new Date() },
      { status: "dirty", savedAt: null },
    ]);
    expect(r.status).toBe("dirty");
  });

  it("returns saved with the MOST RECENT savedAt when all sections saved", () => {
    const older = new Date("2026-06-03T18:00:00Z");
    const newer = new Date("2026-06-03T18:05:00Z");
    const r = aggregateAutosaveStatus([
      { status: "saved", savedAt: older },
      { status: "saved", savedAt: newer },
    ]);
    expect(r.status).toBe("saved");
    expect(r.savedAt).toEqual(newer);
  });

  it("ignores idle sections when others are saved", () => {
    const at = new Date("2026-06-03T18:05:00Z");
    const r = aggregateAutosaveStatus([
      { status: "idle", savedAt: null },
      { status: "saved", savedAt: at },
    ]);
    expect(r).toEqual({ status: "saved", savedAt: at });
  });
});

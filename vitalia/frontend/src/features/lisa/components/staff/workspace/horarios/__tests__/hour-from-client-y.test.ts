// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * hour-from-client-y.test.ts — regression unit for bug7 r3 D-2.
 *
 * El drag-create pasó de mouseenter-por-celda (roto: los bloques existentes
 * con pointer-events-auto tapaban las celdas) a coordenadas contra el rect
 * de la columna. hourFromClientY es la función pura de ese mapeo.
 */

import { describe, it, expect } from "vitest";
import { hourFromClientY } from "../AvailabilityCalendar";

const HOUR_HEIGHT = 48;

describe("hourFromClientY (bug7 r3 D-2)", () => {
  // Vista base: 07:00–21:00 → startHour=7, hourCount=14
  const COLUMN_TOP = 100;

  it("mapea el centro de la primera celda al startHour", () => {
    expect(hourFromClientY(COLUMN_TOP + 24, COLUMN_TOP, 7, 14, HOUR_HEIGHT)).toBe(7);
  });

  it("mapea celdas intermedias por offset vertical", () => {
    // celda 2 (09:00): offset [96, 144)
    expect(hourFromClientY(COLUMN_TOP + 96, COLUMN_TOP, 7, 14, HOUR_HEIGHT)).toBe(9);
    expect(hourFromClientY(COLUMN_TOP + 143, COLUMN_TOP, 7, 14, HOUR_HEIGHT)).toBe(9);
    expect(hourFromClientY(COLUMN_TOP + 144, COLUMN_TOP, 7, 14, HOUR_HEIGHT)).toBe(10);
  });

  it("clampa por arriba: puntero sobre el header no baja del startHour", () => {
    expect(hourFromClientY(COLUMN_TOP - 200, COLUMN_TOP, 7, 14, HOUR_HEIGHT)).toBe(7);
  });

  it("clampa por abajo: puntero más allá de la última celda devuelve la última hora", () => {
    // última celda = 20:00 (hourCount 14 → idx 13)
    expect(hourFromClientY(COLUMN_TOP + 5000, COLUMN_TOP, 7, 14, HOUR_HEIGHT)).toBe(20);
  });

  it("vista 24h: startHour=0, hourCount=24", () => {
    expect(hourFromClientY(COLUMN_TOP + 23 * 48 + 10, COLUMN_TOP, 0, 24, HOUR_HEIGHT)).toBe(23);
    expect(hourFromClientY(COLUMN_TOP - 1, COLUMN_TOP, 0, 24, HOUR_HEIGHT)).toBe(0);
  });
});

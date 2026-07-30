// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-R (G2-F2a)
/**
 * ServiceStatusBar.test.tsx — confirm-before-activate behavior (G2-F2a).
 *
 * Covers:
 *   - Deactivating (is_active=true → switch off) fires onToggleActive(false) directly.
 *   - Activating (is_active=false → switch on) does NOT fire immediately — it opens
 *     a confirm dialog first (the actual confirm click renders in a Radix portal and
 *     is exercised by live-verify, same pattern as ServiceCard's kebab).
 *
 * downstream-regression-na: brand-local vitalia FE test; no cross-brand consumers
 * spec_anchor: chris_verify.rounds[2] G2-F2a + 01-spec.md RN-10/AC-19
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import type { ServiceDetail } from "../../../types/servicios.types";
import { ServiceStatusBar } from "../ServiceStatusBar";

function makeDetail(over: Partial<ServiceDetail> = {}): ServiceDetail {
  return {
    offer_id: "off-1",
    public_name: "Diseño de sonrisa",
    is_active: true,
    canonical_service_ref: null,
    ...over,
  } as ServiceDetail;
}

describe("ServiceStatusBar — activate confirm (G2-F2a)", () => {
  const onToggleActive = vi.fn();
  beforeEach(() => vi.clearAllMocks());

  it("deactivating fires onToggleActive(false) directly (no confirm)", () => {
    render(
      <ServiceStatusBar servicio={makeDetail({ is_active: true })} onToggleActive={onToggleActive} />,
    );
    fireEvent.click(screen.getByRole("switch"));
    expect(onToggleActive).toHaveBeenCalledWith(false);
  });

  it("activating does NOT fire immediately — opens the confirm dialog first", () => {
    render(
      <ServiceStatusBar servicio={makeDetail({ is_active: false })} onToggleActive={onToggleActive} />,
    );
    fireEvent.click(screen.getByRole("switch"));
    // Confirm pending → the real toggle has NOT fired yet.
    expect(onToggleActive).not.toHaveBeenCalled();
  });
});

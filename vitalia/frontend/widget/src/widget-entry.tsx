/**
 * widget-entry.tsx — UMD bundle entry point for the Vitalia booking widget.
 *
 * Builds via Vite UMD as `VitaliaBookingWidget` global.
 * Embed snippet: see vitalia/docs/booking-widget-embed.md
 *
 * Usage (auto-init from data-clinic-slug attribute):
 *   <div id="vitalia-booking-widget" data-clinic-slug="aurora-dental" data-offer-id="off_abc"></div>
 *   <script src="https://cdn.vitalia.health/widget/widget.umd.js"></script>
 *
 * The widget mounts itself into the #vitalia-booking-widget container.
 */

import React from "react";
import ReactDOM from "react-dom/client";
import { BookingWidgetRoot } from "./components/BookingWidgetRoot";
import "./styles.css";

export { BookingWidgetRoot };
export { CalendarSlotPicker } from "./components/CalendarSlotPicker";
export { ConsentStep } from "./components/ConsentStep";
export { PaymentStep } from "./components/PaymentStep";
export { SuccessStep } from "./components/SuccessStep";
export {
  postMessageToParent,
  createOriginValidator,
  isWidgetMessage,
} from "./postmessage-protocol";
export type { WidgetMessage } from "./postmessage-protocol";

/**
 * Auto-mount the widget into the #vitalia-booking-widget container.
 * Called automatically when the script loads (UMD IIFE wrapper).
 */
function autoMount(): void {
  const mountEl = document.getElementById("vitalia-booking-widget");
  if (!mountEl) return;

  // Prevent double-mount in React 19 strict mode
  if (mountEl.dataset["vitaliaWidgetMounted"] === "true") return;
  mountEl.dataset["vitaliaWidgetMounted"] = "true";

  const root = ReactDOM.createRoot(mountEl);
  root.render(
    <React.StrictMode>
      <BookingWidgetRoot />
    </React.StrictMode>
  );
}

// Auto-mount on DOM ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", autoMount);
} else {
  autoMount();
}

/**
 * VitaliaBookingWidget namespace exposed as UMD global.
 * Clinic developers can also call `window.VitaliaBookingWidget.mount(...)` manually.
 */
const VitaliaBookingWidget = {
  /**
   * Manually mount the booking widget into a container element.
   *
   * @param containerId - ID of the DOM element to mount into
   */
  mount(containerId: string): void {
    const el = document.getElementById(containerId);
    if (!el) {
      console.error(`[VitaliaBookingWidget] Container #${containerId} not found.`);
      return;
    }

    const root = ReactDOM.createRoot(el);
    root.render(
      <React.StrictMode>
        <BookingWidgetRoot />
      </React.StrictMode>
    );
  },
};

export { VitaliaBookingWidget };

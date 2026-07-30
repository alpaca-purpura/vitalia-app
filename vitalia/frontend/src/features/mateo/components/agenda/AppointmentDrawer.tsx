// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * AppointmentDrawer.tsx — Appointment detail Sheet with 5 accordion sections.
 * T-14 vitalia-fase2-valeria-agenda
 *
 * Features:
 *   - Shadcn Sheet side="bottom" (h-[95vh]) on mobile <md + side="right" on desktop (AC-12)
 *   - Drag resize handle (left edge) 440-640px — persisted via useDrawerWidth
 *   - 5 Shadcn Accordion sections (turno + pago expanded by default)
 *   - Stale data banner when concurrent edit detected (staleDetected via Zustand)
 *   - Loading skeleton while useAppointmentDetail fetches
 *   - Error fallback for fetch failures
 *   - telemetry: slot_drawer_opened fires on mount via data-testid marker
 *   - ARIA: role="dialog" + aria-modal + aria-labelledby="drawer-title" (Sheet handles)
 *   - Esc closes + focus returns to triggering slot (Sheet handles internally)
 *
 * Tenant data: AppointmentDrawerPagoSection receives tenantCurrency + tenantLocale
 * from useTenantLocale() — NEVER hardcoded.
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 03-arch.md § 6.6 + § 6.11 + 06-tickets.yaml T-14
 */

import { useEffect, useRef, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import { useDrawerStore } from "../../store/agenda-store";
import { useDrawerWidth } from "../../hooks/useDrawerWidth";
import { useAppointmentDetail } from "../../api/agenda";
import { usePatchAppointmentStatus } from "../../api/agenda";
import { AppointmentDrawerHeader } from "./AppointmentDrawerHeader";
import { AppointmentDrawerSkeleton } from "./AppointmentDrawerSkeleton";
import { AppointmentDrawerStaleBanner } from "./AppointmentDrawerStaleBanner";
import { AppointmentDrawerTurnoSection } from "./AppointmentDrawerTurnoSection";
import { AppointmentDrawerPagoSection } from "./AppointmentDrawerPagoSection";
import { AppointmentDrawerNotasSection } from "./AppointmentDrawerNotasSection";
import { AppointmentDrawerAccionesAvanzadasSection } from "./AppointmentDrawerAccionesAvanzadasSection";
import { useQueryClient } from "@tanstack/react-query";
import { agendaKeys } from "../../api/agenda";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AppointmentDrawerProps {
  /** Tenant ID from Clerk session (required for API calls). */
  tenantId: string;
  /**
   * Tenant currency fallback (ISO 4217) from useTenantLocale().
   * NEVER hardcode — pass from parent which reads useTenantLocale().
   */
  tenantCurrency: string;
  /**
   * Tenant locale string for Intl formatting (e.g., "es-PE", "es-AR").
   * NEVER hardcode — pass from parent which reads useTenantLocale().
   */
  tenantLocale: string;
  /**
   * Tenant timezone (e.g., "America/Lima") from useTenantLocale().
   * NEVER hardcode — forwarded to PagoSection for payment date formatting.
   */
  tenantTimezone: string;
}

// ── Constants ─────────────────────────────────────────────────────────────────

/** Resize handle dimensions */
const RESIZE_HANDLE_WIDTH = 8; // px

// ── Resize hook (pointer events) ──────────────────────────────────────────────

/**
 * Returns props to attach to the resize handle div.
 * Pointer events provide smooth resize across devices.
 * Width debounced 100ms to localStorage via useDrawerWidth.
 */
function useResizeHandle(
  setDrawerWidth: (width: number) => void,
  drawerWidth: number,
) {
  const isDragging = useRef(false);
  const startX = useRef(0);
  const startWidth = useRef(0);
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const onPointerDown = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      isDragging.current = true;
      startX.current = e.clientX;
      startWidth.current = drawerWidth;
      e.currentTarget.setPointerCapture(e.pointerId);
      e.preventDefault();
    },
    [drawerWidth],
  );

  const onPointerMove = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      if (!isDragging.current) return;
      // Drawer is on the right side — moving left increases width
      const delta = startX.current - e.clientX;
      const newWidth = startWidth.current + delta;

      // Debounce state write (100ms) — single write path (F5 fix: removed immediate dupe).
      // React state update drives both visual and localStorage (via useDrawerWidth).
      if (debounceTimer.current) clearTimeout(debounceTimer.current);
      debounceTimer.current = setTimeout(() => {
        setDrawerWidth(newWidth);
      }, 100);
    },
    [setDrawerWidth],
  );

  const onPointerUp = useCallback(() => {
    isDragging.current = false;
  }, []);

  return { onPointerDown, onPointerMove, onPointerUp };
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * AppointmentDrawer — full appointment detail side panel.
 *
 * Consumes useDrawerStore for open/close state + selectedSlotId.
 * Fetches appointment detail via useAppointmentDetail when drawer opens.
 */
export function AppointmentDrawer({
  tenantId,
  tenantCurrency,
  tenantLocale,
  tenantTimezone,
}: AppointmentDrawerProps) {
  useAuth(); // Confirm auth context is available (Clerk)
  const queryClient = useQueryClient();

  // Responsive side: bottom (full-screen 95vh) on mobile, right on desktop
  // Breakpoint matches Tailwind `md` (768px) — AC-12
  const isMobile = useMediaQuery("(max-width: 767px)");

  // Drawer state from Zustand
  const { drawerOpen, selectedSlotId, staleDetected, closeDrawer, setStaleDetected } =
    useDrawerStore();

  // Drawer width + resize
  const { drawerStyle, drawerWidth, setDrawerWidth } = useDrawerWidth();
  const resizeHandleProps = useResizeHandle(setDrawerWidth, drawerWidth);

  // Appointment detail fetch
  const {
    data: appointment,
    isLoading,
    isError,
    error,
    refetch,
  } = useAppointmentDetail({
    tenantId,
    appointmentId: selectedSlotId,
    enabled: drawerOpen && !!selectedSlotId,
  });

  // Status change mutation
  const patchStatus = usePatchAppointmentStatus(tenantId);

  // Telemetry on drawer open — fire slot_drawer_opened event
  useEffect(() => {
    if (drawerOpen && selectedSlotId) {
      // Emit telemetry event (non-blocking, best-effort)
      // The actual implementation will be in the telemetry service
      // For now we mark it as opened via data attribute on mount
      const el = document.querySelector("[data-drawer-opened-telemetry]");
      if (el) {
        el.setAttribute("data-slot-id", selectedSlotId);
        el.setAttribute("data-opened-at", new Date().toISOString());
      }
    }
  }, [drawerOpen, selectedSlotId]);

  // Invalidate detail cache on stale reload trigger
  const handleReload = useCallback(() => {
    if (!selectedSlotId) return;
    setStaleDetected(false);
    void queryClient.invalidateQueries({
      queryKey: agendaKeys.detail(tenantId, selectedSlotId),
    });
  }, [selectedSlotId, setStaleDetected, queryClient, tenantId]);

  // Status change handler
  const handleStatusChange = useCallback(
    (newStatus: "CANCELLED" | "COMPLETED" | "NO_SHOW", reason?: string) => {
      if (!selectedSlotId) return;
      patchStatus.mutate({
        appointmentId: selectedSlotId,
        payload: { newStatus, reason: reason ?? undefined },
      });
    },
    [selectedSlotId, patchStatus],
  );

  return (
    <Sheet
      open={drawerOpen}
      onOpenChange={(open) => {
        if (!open) closeDrawer();
      }}
    >
      <SheetContent
        side={isMobile ? "bottom" : "right"}
        className={cn(
          "flex flex-col p-0 gap-0",
          // Mobile: full-screen bottom drawer (AC-12)
          isMobile
            ? "h-[95vh] max-h-[95vh] rounded-t-2xl !w-full"
            : // Desktop: resizable right-side panel
              "!w-auto",
        )}
        style={isMobile ? undefined : drawerStyle}
        aria-labelledby="drawer-title"
        data-testid="appointment-drawer"
        data-drawer-opened-telemetry=""
      >
        {/* Screen-reader accessible title (visually hidden — header provides visible title) */}
        <SheetTitle className="sr-only">
          {appointment
            ? `Detalle del turno de ${appointment.patientNameMasked}`
            : "Detalle del turno"}
        </SheetTitle>
        <SheetDescription className="sr-only">
          Panel lateral con el detalle del turno médico seleccionado.
        </SheetDescription>

        {/* Resize handle — left edge for right-side drawer */}
        <div
          role="separator"
          aria-label="Ajustar ancho del panel"
          aria-orientation="vertical"
          className={cn(
            "absolute left-0 top-0 bottom-0 cursor-col-resize z-10",
            "hover:bg-primary/20 active:bg-primary/30 transition-colors",
            "touch-none select-none",
          )}
          style={{ width: `${RESIZE_HANDLE_WIDTH}px` }}
          {...resizeHandleProps}
          data-testid="resize-handle"
        />

        {/* Content container (padded left for resize handle) */}
        <div
          className="flex flex-col flex-1 overflow-hidden"
          style={{ paddingLeft: `${RESIZE_HANDLE_WIDTH}px` }}
        >
          {/* Loading skeleton */}
          {isLoading && <AppointmentDrawerSkeleton />}

          {/* Error state */}
          {isError && !isLoading && (
            <div
              className="flex flex-col gap-4 p-6"
              role="alert"
              aria-live="assertive"
            >
              <Alert variant="destructive">
                <AlertTriangle
                  className="h-4 w-4"
                  aria-hidden="true"
                />
                <AlertDescription>
                  {error?.message ?? "No se pudo cargar el detalle del turno."}
                </AlertDescription>
              </Alert>
              <Button
                variant="outline"
                size="sm"
                onClick={() => void refetch()}
                className="w-fit"
              >
                Reintentar
              </Button>
            </div>
          )}

          {/* Drawer content (appointment loaded) */}
          {appointment && !isLoading && (
            <div className="flex flex-col flex-1 overflow-hidden">
              {/* Header — PHI-masked patient identity */}
              <AppointmentDrawerHeader
                patientNameMasked={appointment.patientNameMasked}
                patientDniMasked={appointment.patientDniMasked}
              />

              <Separator />

              {/* Stale banner — shown when concurrent edit detected */}
              {staleDetected && (
                <div className="px-4 pt-3">
                  <AppointmentDrawerStaleBanner onReload={handleReload} />
                </div>
              )}

              {/* 5-section Accordion — scrollable body */}
              <div className="flex-1 overflow-y-auto">
                <Accordion
                  type="multiple"
                  defaultValue={["turno", "pago"]}
                  className="w-full"
                >
                  {/* 1. Turno — expanded by default */}
                  <AccordionItem value="turno" className="px-4">
                    <AccordionTrigger className="text-sm font-medium py-3">
                      Turno
                    </AccordionTrigger>
                    <AccordionContent>
                      <AppointmentDrawerTurnoSection
                        appointment={appointment}
                        onStatusChange={handleStatusChange}
                        isUpdating={patchStatus.isPending}
                      />
                    </AccordionContent>
                  </AccordionItem>

                  {/* 2. Pago — expanded by default */}
                  <AccordionItem value="pago" className="px-4">
                    <AccordionTrigger className="text-sm font-medium py-3">
                      Pago
                    </AccordionTrigger>
                    <AccordionContent>
                      <AppointmentDrawerPagoSection
                        appointment={appointment}
                        tenantId={tenantId}
                        tenantCurrency={tenantCurrency}
                        tenantLocale={tenantLocale}
                        tenantTimezone={tenantTimezone}
                      />
                    </AccordionContent>
                  </AccordionItem>

                  {/* 3. Histórico de pagos — collapsed by default */}
                  <AccordionItem value="historico" className="px-4">
                    <AccordionTrigger className="text-sm font-medium py-3">
                      Histórico
                    </AccordionTrigger>
                    <AccordionContent>
                      <div className="flex flex-col gap-2 text-sm text-muted-foreground">
                        {appointment.payments.length > 0 ? (
                          <p>
                            {appointment.payments.length} pago
                            {appointment.payments.length !== 1 ? "s" : ""} registrado
                            {appointment.payments.length !== 1 ? "s" : ""}.
                          </p>
                        ) : (
                          <p>Sin historial de pagos.</p>
                        )}
                      </div>
                    </AccordionContent>
                  </AccordionItem>

                  {/* 4. Notas — collapsed by default */}
                  <AccordionItem value="notas" className="px-4">
                    <AccordionTrigger className="text-sm font-medium py-3">
                      Notas internas
                    </AccordionTrigger>
                    <AccordionContent>
                      <AppointmentDrawerNotasSection appointment={appointment} />
                    </AccordionContent>
                  </AccordionItem>

                  {/* 5. Acciones avanzadas — collapsed by default */}
                  <AccordionItem value="acciones-avanzadas" className="px-4 border-b-0">
                    <AccordionTrigger className="text-sm font-medium py-3">
                      Acciones avanzadas
                    </AccordionTrigger>
                    <AccordionContent>
                      <AppointmentDrawerAccionesAvanzadasSection
                        appointment={appointment}
                        tenantId={tenantId}
                      />
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>
              </div>
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

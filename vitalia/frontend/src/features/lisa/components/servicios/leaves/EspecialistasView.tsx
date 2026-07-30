// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-7
"use client";
/**
 * EspecialistasView.tsx — Leaf 3: Especialistas vinculados al servicio.
 *
 * Route segment: "doctores" (label: "Especialistas"). See ServicioWorkspaceShell
 * SERVICIO_LEAVES and T-7-impl-log.md § Upstream deficiency for segment≠label note.
 *
 * Displays linked specialists (from ServiceDetail.specialists) + unlink action.
 * Linking uses EspecialistaLinkPicker (staff roster checklist).
 *
 * spec §Workspace Pestaña 3 · 01-spec.md §Workspace Pestaña 3
 * NOT PHI: specialist link is NOT PHI (doctor_id != patient data).
 * Link POST carries X-Clinic-ID (clinic-scoped write).
 */

import { useState } from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { useServicioDetail, useUnlinkSpecialist } from "../../../api/servicios";
import Link from "next/link";
import { useTenantId } from "@/hooks/useTenantId";
import { EspecialistaLinkPicker } from "../EspecialistaLinkPicker";

interface EspecialistasViewProps {
  offerId: string;
}

export function EspecialistasView({ offerId }: EspecialistasViewProps) {
  const { data: servicio } = useServicioDetail({ offerId });
  const tenantId = useTenantId();
  const { mutate: unlink, isPending: isUnlinking } = useUnlinkSpecialist(offerId);
  const [showPicker, setShowPicker] = useState(false);

  if (!servicio) {
    return (
      <div className="p-6 space-y-3">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-14 bg-muted rounded-md animate-pulse" />
        ))}
      </div>
    );
  }

  const specialists = servicio.specialists;

  return (
    <div className="p-5 md:p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold">Especialistas habilitados</h2>
          <p className="text-sm text-muted-foreground">
            Los especialistas que realizan este servicio en tu clínica.
          </p>
        </div>
        <Button size="sm" onClick={() => setShowPicker(true)}>
          Vincular especialista
        </Button>
      </div>

      {/* Linked specialists list */}
      {specialists.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border p-8 text-center">
          <p className="text-sm text-muted-foreground">
            No hay especialistas vinculados todavía.
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Vincúlalos para que Adrián pueda asignar el especialista correcto al vender.
          </p>
          {tenantId && (
            <Link
              href={`/${tenantId}/lisa/staff`}
              className="text-xs text-primary underline-offset-2 hover:underline mt-2 inline-block"
            >
              Agrega especialistas en Lisa → Especialistas ↗
            </Link>
          )}
        </div>
      ) : (
        <ul className="space-y-2">
          {specialists.map((s) => {
            const name = s.display_name ?? null;
            const initials = name
              ? name
                  .trim()
                  .split(/\s+/)
                  .slice(0, 2)
                  .map((w) => w[0]?.toUpperCase() ?? "")
                  .join("")
              : "E";
            const shortId = s.doctor_id.slice(0, 8);
            return (
            <li
              key={s.id}
              className="flex items-center justify-between rounded-lg border border-border p-3"
            >
              <div className="flex items-center gap-3">
                <Avatar className="h-9 w-9">
                  <AvatarFallback className="text-xs">{initials}</AvatarFallback>
                </Avatar>
                <div>
                  <p className="text-sm font-medium">
                    {name ?? "Especialista"}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {s.specialty ?? shortId}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {tenantId && (
                  <Link
                    href={`/${tenantId}/lisa/staff/${s.doctor_id}`}
                    className="text-xs text-muted-foreground hover:text-foreground"
                  >
                    Ver detalle ↗
                  </Link>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={isUnlinking}
                  onClick={() => unlink(s.doctor_id)}
                  className="text-destructive hover:text-destructive"
                >
                  Desvincular
                </Button>
              </div>
            </li>
            );
          })}
        </ul>
      )}

      {/* Specialist link picker */}
      {showPicker && (
        <EspecialistaLinkPicker
          offerId={offerId}
          linkedDoctorIds={specialists.map((s) => s.doctor_id)}
          onClose={() => setShowPicker(false)}
        />
      )}
    </div>
  );
}

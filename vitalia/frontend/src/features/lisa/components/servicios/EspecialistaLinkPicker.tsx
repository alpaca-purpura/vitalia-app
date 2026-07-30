// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-7
"use client";
/**
 * EspecialistaLinkPicker.tsx — Inline checklist to link specialists to a servicio.
 *
 * Renders a staff roster (from useStaffList) filtered by what's already linked.
 * Checking a doctor → POST /servicios/{id}/specialists (useLinkSpecialist).
 * On close, dirty state is flushed (no "Guardar" — autosave on-check, RN-20).
 *
 * Appears inline below the EspecialistasView header when "Vincular especialista" clicked.
 * spec §Workspace Pestaña 3 · 03-arch-fe.md §5 EspecialistaLinkPicker
 */

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Checkbox } from "@luana/ui-kit";
import { Label } from "@/components/ui/label";
import { useStaffList } from "../../api/staff";
import { useLinkSpecialist } from "../../api/servicios";

interface EspecialistaLinkPickerProps {
  offerId: string;
  linkedDoctorIds: string[];
  onClose: () => void;
}

export function EspecialistaLinkPicker({
  offerId,
  linkedDoctorIds,
  onClose,
}: EspecialistaLinkPickerProps) {
  const [search, setSearch] = useState("");
  const { data, isLoading } = useStaffList({ filters: { q: search } });
  const { mutate: link, isPending } = useLinkSpecialist(offerId);

  const doctors = data?.items ?? [];

  // Only show doctors that are NOT already linked
  const available = doctors.filter((d) => !linkedDoctorIds.includes(d.id));

  const handleCheck = (doctorId: string, checked: boolean) => {
    if (!checked) return; // Un-check not supported from this picker (use Desvincular)
    link(doctorId);
  };

  return (
    <div className="rounded-lg border border-border bg-card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium">Vincular especialista</p>
        <Button variant="ghost" size="sm" onClick={onClose}>
          Cerrar
        </Button>
      </div>

      {/* Search input */}
      <Input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Buscar por nombre o especialidad…"
        className="h-8 text-sm"
      />

      {/* Roster list */}
      {isLoading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-10 bg-muted rounded animate-pulse" />
          ))}
        </div>
      ) : available.length === 0 ? (
        <p className="text-sm text-muted-foreground py-2 text-center">
          {doctors.length === 0
            ? "No hay especialistas registrados aún."
            : "Todos los especialistas ya están vinculados."}
        </p>
      ) : (
        <ul className="space-y-1 max-h-56 overflow-y-auto pr-1">
          {available.map((doc) => {
            const initials = `${doc.firstName[0] ?? ""}${doc.lastName[0] ?? ""}`.toUpperCase();
            const fullName = `${doc.firstName} ${doc.lastName}`;
            return (
              <li
                key={doc.id}
                className="flex items-center gap-3 rounded-md px-2 py-1.5 hover:bg-muted/50 transition-colors"
              >
                <Checkbox
                  id={`link-${doc.id}`}
                  disabled={isPending}
                  onCheckedChange={(checked) =>
                    handleCheck(doc.id, checked === true)
                  }
                />
                <Avatar className="h-7 w-7">
                  <AvatarFallback className="text-xs">{initials}</AvatarFallback>
                </Avatar>
                <Label
                  htmlFor={`link-${doc.id}`}
                  className="cursor-pointer flex-1 text-sm"
                >
                  {fullName}
                  {doc.specialty && (
                    <span className="ml-1 text-xs text-muted-foreground">
                      · {doc.specialty}
                    </span>
                  )}
                </Label>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

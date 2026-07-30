// canon: design-system-canon.md §5 · story-origin: core-ds-foundation
"use client";

/**
 * AutosaveGroupSection — autoguardado + grupos de campos del canon §2.6 (@luana/ui-kit).
 * FloatingAutosaveIndicator (todos los estados), AutosaveBadge, Group + GroupHeader
 * con barrita de color por agente y error semántico.
 */

import { useState } from "react";

import {
  PageSection,
  PageContentStack,
  FloatingAutosaveIndicator,
  AutosaveBadge,
  Group,
  GroupHeader,
  Input,
  Button,
} from "@luana/ui-kit";
import type { AutosaveStatus } from "@luana/hooks";

const ESTADOS: AutosaveStatus[] = ["idle", "dirty", "saving", "saved", "error"];

export function AutosaveGroupSection() {
  const [estado, setEstado] = useState<AutosaveStatus>("saved");

  return (
    <PageSection title="Autoguardado y grupos" data-testid="showcase-section-autosave">
      <PageContentStack>
        <div className="space-y-3">
          <span className="text-sm font-medium text-muted-foreground">
            FloatingAutosaveIndicator (cambia el estado)
          </span>
          <div className="flex flex-wrap gap-2">
            {ESTADOS.map((e) => (
              <Button
                key={e}
                size="sm"
                variant={e === estado ? "default" : "outline"}
                onClick={() => setEstado(e)}
              >
                {e}
              </Button>
            ))}
          </div>
          <div className="relative h-20 rounded-lg border border-border">
            <FloatingAutosaveIndicator status={estado} savedAt={new Date()} />
          </div>
        </div>

        <div className="space-y-2">
          <span className="text-sm font-medium text-muted-foreground">
            AutosaveBadge (inline)
          </span>
          <div className="flex flex-wrap items-center gap-4">
            <AutosaveBadge status="saving" />
            <AutosaveBadge status="saved" savedAt={new Date()} />
            <AutosaveBadge status="error" />
          </div>
        </div>

        <div className="space-y-2">
          <span className="text-sm font-medium text-muted-foreground">
            Group + GroupHeader (barrita de agente · error semántico)
          </span>
          <Group accentClass="border-l-agent-lisa">
            <GroupHeader
              title="Identidad del paciente"
              whatFor="Para Lisa"
              whatForTooltip="Lisa usa estos datos para personalizar el seguimiento clínico."
            />
            <div className="space-y-3 pt-2">
              <Input placeholder="Nombre completo" defaultValue="María Fernanda Quiroga" />
              <Input placeholder="Documento" defaultValue="CURP QURM920514…" />
            </div>
          </Group>

          <Group accentClass="border-l-agent-mateo" hasError>
            <GroupHeader
              title="Datos de contacto"
              whatFor="Para Mateo"
              missingFields={["Teléfono", "Correo"]}
            />
            <div className="space-y-3 pt-2">
              <Input placeholder="Teléfono" />
              <Input placeholder="Correo" />
            </div>
          </Group>
        </div>
      </PageContentStack>
    </PageSection>
  );
}

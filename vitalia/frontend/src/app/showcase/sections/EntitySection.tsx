// canon: design-system-canon.md §5 · story-origin: core-ds-foundation
"use client";

/**
 * EntitySection — componentes de entidad del canon N3 (@luana/ui-kit).
 * EntityInfoCard (grilla Opción B), EntityPicker (selector debounced + paginado
 * con searchFn stub en memoria), EntityWorkspaceLayout en modo master y detalle.
 */

import { useState } from "react";

import {
  PageSection,
  PageContentStack,
  EntityInfoCard,
  EntityInfoCardSkeleton,
  EntityInfoCardEmpty,
  EntityPicker,
  EntityWorkspaceLayout,
  type EntityPickerItem,
  type EntitySearchArgs,
  type EntitySearchResult,
  type EntitySubNavLeaf,
  type EntitySubNavEntity,
} from "@luana/ui-kit";

// ── Datos de ejemplo (LatAm, español neutro) ───────────────────────────────────

interface ClinicaItem extends EntityPickerItem {
  ciudad: string;
}

const NOMBRES_CLINICAS = [
  "Clínica Sanaré",
  "Centro Dental Aurora",
  "Estética Mindful",
  "Visión Clara Oftalmología",
  "Dermatología Renacer",
  "Nutrición Vital",
  "Sonríe Cosmético",
  "Piel Sana Estética",
  "Odonto Premium",
  "Bienestar Integral",
];

const CIUDADES = ["CDMX", "Buenos Aires", "Bogotá", "Lima", "Santiago", "Guadalajara"];

const CLINICAS: ClinicaItem[] = Array.from({ length: 30 }, (_, i) => ({
  id: `clinica-${i + 1}`,
  name: `${NOMBRES_CLINICAS[i % NOMBRES_CLINICAS.length]} ${Math.floor(i / NOMBRES_CLINICAS.length) + 1}`,
  ciudad: CIUDADES[i % CIUDADES.length]!,
}));

// searchFn STUB — pagina en memoria (cursor = offset). NO toca el backend.
async function searchClinicas({ q, cursor, limit }: EntitySearchArgs): Promise<EntitySearchResult<ClinicaItem>> {
  const filtradas = q
    ? CLINICAS.filter((c) => c.name.toLowerCase().includes(q.toLowerCase()))
    : CLINICAS;
  const offset = cursor ? Number.parseInt(cursor, 10) : 0;
  const slice = filtradas.slice(offset, offset + limit);
  const next = offset + limit;
  return {
    items: slice,
    nextCursor: next < filtradas.length ? String(next) : null,
    total: filtradas.length,
  };
}

// ── Workspace de ejemplo ────────────────────────────────────────────────────────

const PACIENTE: EntitySubNavEntity = {
  id: "pac-1",
  name: "María Fernanda Quiroga",
  icon: "🦷",
};

const LEAVES: EntitySubNavLeaf[] = [
  { id: "datos", label: "Datos", href: "/showcase#datos", avatarBgClass: "bg-agent-lisa-soft" },
  { id: "tratamiento", label: "Tratamiento", href: "/showcase#tratamiento", isPrimary: true, avatarBgClass: "bg-agent-lisa-soft" },
  { id: "historial", label: "Historial", href: "/showcase#historial", avatarBgClass: "bg-agent-lisa-soft" },
  { id: "agregar", label: "Agregar nota", href: "/showcase#agregar", isAddAffordance: true },
];

export function EntitySection() {
  const [seleccion, setSeleccion] = useState<ClinicaItem | null>(CLINICAS[0] ?? null);

  return (
    <PageSection title="Componentes de entidad" data-testid="showcase-section-entity">
      <PageContentStack>
        <div className="space-y-2">
          <span className="text-sm font-medium text-muted-foreground">
            EntityPicker (búsqueda debounced + paginación cursor · 30 clínicas en memoria)
          </span>
          <EntityPicker<ClinicaItem>
            value={seleccion}
            onChange={setSeleccion}
            searchFn={searchClinicas}
            placeholder="Selecciona una clínica"
            searchPlaceholder="Buscar clínica…"
          />
        </div>

        <div className="space-y-2">
          <span className="text-sm font-medium text-muted-foreground">
            EntityInfoCard (grilla Opción B · auto-fill)
          </span>
          <div className="grid gap-4 [grid-template-columns:repeat(auto-fill,minmax(250px,1fr))]">
            <EntityInfoCard
              title="Clínica Sanaré"
              subtitle="Odontología"
              initials="CS"
              accentClass="border-t-agent-lisa"
              mediaClass="bg-agent-lisa-soft"
              metrics={[
                { label: "Pacientes", value: 128 },
                { label: "Turnos hoy", value: 14 },
              ]}
              status={{ label: "Activa", variant: "default" }}
              onClick={() => undefined}
            />
            <EntityInfoCard
              title="Centro Dental Aurora"
              subtitle="Estética"
              initials="CA"
              accentClass="border-t-agent-adrian"
              mediaClass="bg-agent-adrian-soft"
              metrics={[
                { label: "Pacientes", value: 86 },
                { label: "Turnos hoy", value: 9 },
              ]}
              status={{ label: "Activa", variant: "default" }}
              onClick={() => undefined}
            />
            <EntityInfoCard
              title="Estética Mindful"
              subtitle="Dermatología"
              initials="EM"
              accentClass="border-t-agent-valeria"
              mediaClass="bg-agent-valeria-soft"
              metrics={[
                { label: "Pacientes", value: 47 },
                { label: "Turnos hoy", value: 0 },
              ]}
              status={{ label: "Borrador", variant: "secondary" }}
              inactive
              onClick={() => undefined}
            />
            <EntityInfoCardSkeleton />
            <EntityInfoCardEmpty />
          </div>
        </div>

        <div className="space-y-2">
          <span className="text-sm font-medium text-muted-foreground">
            EntityWorkspaceLayout · modo master (entity=null)
          </span>
          <div className="h-48 rounded-lg border border-border">
            <EntityWorkspaceLayout
              entity={null}
              leaves={[]}
              rootHref="/showcase#pacientes"
              rootLabel="Pacientes"
              placeholder="Selecciona un paciente del directorio"
            >
              <div className="p-6 text-sm text-muted-foreground">
                Vista de directorio: aquí iría la grilla de pacientes.
              </div>
            </EntityWorkspaceLayout>
          </div>
        </div>

        <div className="space-y-2">
          <span className="text-sm font-medium text-muted-foreground">
            EntityWorkspaceLayout · modo detalle (entity set + hojas N3)
          </span>
          <div className="h-56 rounded-lg border border-border">
            <EntityWorkspaceLayout
              entity={PACIENTE}
              leaves={LEAVES}
              rootHref="/showcase#pacientes"
              rootLabel="Pacientes"
            >
              <div className="p-6 text-sm text-muted-foreground">
                Hoja activa: tratamiento de blanqueamiento dental · próximo control 18 de junio.
              </div>
            </EntityWorkspaceLayout>
          </div>
        </div>
      </PageContentStack>
    </PageSection>
  );
}

// canon: design-system-canon.md §5 · story-origin: core-ds-foundation
"use client";

/**
 * LayoutPrimitivesSection — primitivas de layout del canon §2.7 (@luana/ui-kit).
 * Toolbar, FilterBar, EmptyState, ErrorState, skeletons, Pagination, DetailLayout,
 * FormLayout. Toda hoja se ARMA de estas, no con <div> de layout sueltos.
 */

import { useState } from "react";

import {
  PageSection,
  Toolbar,
  FilterBar,
  EmptyState,
  ErrorState,
  ListPageSkeleton,
  FormPageSkeleton,
  Pagination,
  DetailLayout,
  FormLayout,
  Button,
  Input,
  Badge,
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  PageContentStack,
} from "@luana/ui-kit";

function Block({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <span className="text-sm font-medium text-muted-foreground">{label}</span>
      <div className="rounded-lg border border-border p-4">{children}</div>
    </div>
  );
}

export function LayoutPrimitivesSection() {
  const [page, setPage] = useState(2);

  return (
    <PageSection title="Primitivas de layout" data-testid="showcase-section-layout">
      <PageContentStack>
        <Block label="Toolbar">
          <Toolbar>
            <h3 className="text-base font-semibold">Pacientes</h3>
            <div className="ml-auto flex gap-2">
              <Button variant="outline" size="sm">
                Exportar
              </Button>
              <Button size="sm">Nuevo paciente</Button>
            </div>
          </Toolbar>
        </Block>

        <Block label="FilterBar">
          <FilterBar
            search={<Input placeholder="Buscar paciente o tratamiento" className="w-72" />}
            sort={
              <Button variant="outline" size="sm">
                Ordenar: más recientes
              </Button>
            }
          />
        </Block>

        <Block label="EmptyState">
          <EmptyState
            title="Sin turnos para hoy"
            description="Cuando se agende una consulta aparecerá aquí. Compártele el enlace de reserva a tus pacientes."
            action={<Button size="sm">Crear turno</Button>}
          />
        </Block>

        <Block label="ErrorState">
          <ErrorState
            title="No se pudo cargar la agenda"
            message="Revisa tu conexión e inténtalo de nuevo."
            onRetry={() => undefined}
            retryLabel="Reintentar"
          />
        </Block>

        <Block label="ListPageSkeleton">
          <ListPageSkeleton rows={4} />
        </Block>

        <Block label="FormPageSkeleton">
          <FormPageSkeleton sections={2} />
        </Block>

        <Block label="Pagination">
          <Pagination
            page={page}
            pageCount={8}
            onPrev={() => setPage((p) => Math.max(1, p - 1))}
            onNext={() => setPage((p) => Math.min(8, p + 1))}
          />
        </Block>

        <Block label="DetailLayout (contenido + aside)">
          <DetailLayout>
            <Card>
              <CardHeader>
                <CardTitle>María Fernanda Quiroga</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">
                Tratamiento de blanqueamiento dental · Próximo control el 18 de junio.
              </CardContent>
            </Card>
            <aside className="flex flex-col gap-2">
              <Badge>Plan activo</Badge>
              <span className="text-sm text-muted-foreground">Clínica Sanaré · CDMX</span>
            </aside>
          </DetailLayout>
        </Block>

        <Block label="FormLayout (paired)">
          <FormLayout paired>
            <Input placeholder="Nombre" defaultValue="Sofía Robles" />
            <Input placeholder="Teléfono" defaultValue="+52 55 1234 5678" />
            <Input placeholder="Tratamiento" defaultValue="Limpieza profunda" />
            <Input placeholder="Profesional" defaultValue="Dr. Luis Méndez" />
          </FormLayout>
        </Block>
      </PageContentStack>
    </PageSection>
  );
}

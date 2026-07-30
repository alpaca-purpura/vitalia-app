// canon: design-system-canon.md §5 · story-origin: core-ds-foundation
"use client";

/**
 * ArchetypesSection — scaffolds de página del canon §6.2 (@luana/ui-kit).
 * ListPageScaffold, DetailPageScaffold, FormPageScaffold, DashboardPageScaffold:
 * el consumidor RELLENA slots, no maqueta layout bespoke.
 */

import {
  PageSection,
  PageContentStack,
  PageHeader,
  ListPageScaffold,
  DetailPageScaffold,
  FormPageScaffold,
  DashboardPageScaffold,
  EntityInfoCard,
  FloatingAutosaveIndicator,
  Toolbar,
  Pagination,
  Button,
  Input,
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@luana/ui-kit";

function Frame({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <span className="text-sm font-medium text-muted-foreground">{label}</span>
      <div className="rounded-lg border border-border p-4">{children}</div>
    </div>
  );
}

export function ArchetypesSection() {
  return (
    <PageSection title="Arquetipos de página" data-testid="showcase-section-archetypes">
      <PageContentStack>
        <Frame label="ListPageScaffold">
          <ListPageScaffold
            header={<PageHeader title="Pacientes" subtitle="Directorio de la clínica" />}
            toolbar={
              <Toolbar>
                <Button size="sm">Nuevo paciente</Button>
              </Toolbar>
            }
            pagination={
              <Pagination page={1} pageCount={3} onPrev={() => undefined} onNext={() => undefined} />
            }
          >
            <div className="grid gap-4 [grid-template-columns:repeat(auto-fill,minmax(250px,1fr))]">
              <EntityInfoCard
                title="María Fernanda Quiroga"
                subtitle="Blanqueamiento"
                initials="MQ"
                accentClass="border-t-agent-lisa"
                metrics={[{ label: "Sesiones", value: 3 }]}
                onClick={() => undefined}
              />
              <EntityInfoCard
                title="Sofía Robles"
                subtitle="Limpieza"
                initials="SR"
                accentClass="border-t-agent-adrian"
                metrics={[{ label: "Sesiones", value: 1 }]}
                onClick={() => undefined}
              />
            </div>
          </ListPageScaffold>
        </Frame>

        <Frame label="DetailPageScaffold">
          <DetailPageScaffold
            header={<PageHeader title="María Fernanda Quiroga" subtitle="Paciente activa" />}
          >
            <Card>
              <CardHeader>
                <CardTitle>Tratamiento en curso</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">
                Blanqueamiento dental · próximo control el 18 de junio · Dr. Luis Méndez.
              </CardContent>
            </Card>
          </DetailPageScaffold>
        </Frame>

        <Frame label="FormPageScaffold">
          <FormPageScaffold
            header={<PageHeader title="Nuevo paciente" subtitle="Completa los datos básicos" />}
            paired
            autosaveIndicator={<FloatingAutosaveIndicator status="saved" savedAt={new Date()} />}
          >
            <Input placeholder="Nombre" defaultValue="Camila Vásquez" />
            <Input placeholder="Teléfono" defaultValue="+57 300 123 4567" />
            <Input placeholder="Tratamiento" defaultValue="Ortodoncia" />
            <Input placeholder="Profesional" defaultValue="Dra. Ana Torres" />
          </FormPageScaffold>
        </Frame>

        <Frame label="DashboardPageScaffold">
          <DashboardPageScaffold
            header={<PageHeader title="Panel de la clínica" subtitle="Resumen de hoy" />}
          >
            <div className="grid gap-4 [grid-template-columns:repeat(auto-fill,minmax(200px,1fr))]">
              <Card>
                <CardHeader>
                  <CardTitle>Turnos hoy</CardTitle>
                </CardHeader>
                <CardContent className="text-2xl font-semibold">14</CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Pacientes activos</CardTitle>
                </CardHeader>
                <CardContent className="text-2xl font-semibold">128</CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Ingresos del mes</CardTitle>
                </CardHeader>
                <CardContent className="text-2xl font-semibold">$248,500 MXN</CardContent>
              </Card>
            </div>
          </DashboardPageScaffold>
        </Frame>
      </PageContentStack>
    </PageSection>
  );
}

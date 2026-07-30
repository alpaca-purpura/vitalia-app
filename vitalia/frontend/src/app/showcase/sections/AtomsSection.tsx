// canon: design-system-canon.md §5 · story-origin: core-ds-foundation
"use client";

/**
 * AtomsSection — átomos Shadcn-style del canon (@luana/ui-kit).
 * Botones, inputs, badges, avatar, card, skeleton, select, tooltip, switch,
 * checkbox, separator — con datos LatAm realistas.
 */

import { useState } from "react";

import {
  Button,
  Input,
  Badge,
  Avatar,
  AvatarFallback,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Skeleton,
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
  Tooltip,
  TooltipProvider,
  TooltipTrigger,
  TooltipContent,
  Switch,
  Checkbox,
  Separator,
  PageSection,
  PageContentStack,
} from "@luana/ui-kit";

function SwatchRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <span className="text-sm font-medium text-muted-foreground">{label}</span>
      <div className="flex flex-wrap items-center gap-3">{children}</div>
    </div>
  );
}

export function AtomsSection() {
  const [pais, setPais] = useState<string>("");
  const [recordatorios, setRecordatorios] = useState(true);
  const [acepta, setAcepta] = useState(false);

  return (
    <PageSection title="Átomos" data-testid="showcase-section-atoms">
      <PageContentStack>
        <SwatchRow label="Botones">
          <Button>Agendar consulta</Button>
          <Button variant="secondary">Ver pacientes</Button>
          <Button variant="outline">Exportar</Button>
          <Button variant="ghost">Cancelar</Button>
          <Button variant="destructive">Eliminar</Button>
          <Button variant="link">Más información</Button>
          <Button size="sm">Chico</Button>
          <Button size="lg">Grande</Button>
        </SwatchRow>

        <SwatchRow label="Badges">
          <Badge>Activo</Badge>
          <Badge variant="secondary">Borrador</Badge>
          <Badge variant="outline">Pendiente</Badge>
          <Badge variant="destructive">Vencido</Badge>
        </SwatchRow>

        <SwatchRow label="Input">
          <Input placeholder="Nombre del paciente" defaultValue="María Fernanda Quiroga" />
          <Input placeholder="Correo" defaultValue="contacto@clinicasanare.mx" />
        </SwatchRow>

        <SwatchRow label="Select">
          <Select value={pais} onValueChange={setPais}>
            <SelectTrigger className="w-64">
              <SelectValue placeholder="Selecciona el país" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="mx">México</SelectItem>
              <SelectItem value="ar">Argentina</SelectItem>
              <SelectItem value="co">Colombia</SelectItem>
              <SelectItem value="pe">Perú</SelectItem>
              <SelectItem value="cl">Chile</SelectItem>
            </SelectContent>
          </Select>
        </SwatchRow>

        <SwatchRow label="Avatar">
          <Avatar>
            <AvatarFallback>MQ</AvatarFallback>
          </Avatar>
          <Avatar>
            <AvatarFallback>JL</AvatarFallback>
          </Avatar>
          <Avatar>
            <AvatarFallback>SR</AvatarFallback>
          </Avatar>
        </SwatchRow>

        <SwatchRow label="Tooltip">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline">Pasa el cursor</Button>
              </TooltipTrigger>
              <TooltipContent>Muestra los turnos de hoy en la agenda</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </SwatchRow>

        <SwatchRow label="Switch · Checkbox">
          <label className="flex items-center gap-2 text-sm">
            <Switch checked={recordatorios} onCheckedChange={setRecordatorios} />
            Recordatorios automáticos
          </label>
          <label className="flex items-center gap-2 text-sm">
            <Checkbox checked={acepta} onCheckedChange={(v) => setAcepta(v === true)} />
            Acepto el consentimiento informado
          </label>
        </SwatchRow>

        <SwatchRow label="Card">
          <Card className="w-80">
            <CardHeader>
              <CardTitle>Clínica Sanaré</CardTitle>
              <CardDescription>Odontología cosmética · Ciudad de México</CardDescription>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              128 pacientes activos · 14 turnos hoy
            </CardContent>
          </Card>
        </SwatchRow>

        <Separator />

        <SwatchRow label="Skeleton (estado de carga)">
          <div className="space-y-2">
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-4 w-64" />
            <Skeleton className="h-4 w-40" />
          </div>
        </SwatchRow>
      </PageContentStack>
    </PageSection>
  );
}

import type { Meta, StoryObj } from "@storybook/nextjs";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "../src/form";
import { Input } from "../src/input";
import { Button } from "../src/button";
import { Textarea } from "../src/textarea";

const meta = {
  title: "Organisms/Form",
  component: Form,
  tags: ["autodocs"],
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: [
          "## Cuándo usarlo",
          "",
          "El sistema de `Form` (React Hook Form + Zod + Shadcn) es el patrón canónico para todo formulario del design system. Compone `FormField`, `FormItem`, `FormLabel`, `FormControl`, `FormDescription` y `FormMessage` sobre cualquier input. Accesibilidad automática: ARIA ids, `aria-invalid`, `aria-describedby` se inyectan via contexto sin código manual.",
          "",
          "## Cuándo NO / alternativa",
          "",
          "- **Campo único sin validación** → un `Input` + `Label` sueltos están bien.",
          "- **Autosave sin botón** → el sistema de autosave de Luana usa `form.watch()` + debounce; no requiere botón de guardado (`form-runtime-array.md` — autosave non-negotiable).",
          "- **Formulario de búsqueda** → `Input` libre + estado local, sin `zodResolver`.",
        ].join("\n"),
      },
    },
  },
} satisfies Meta<typeof Form>;

export default meta;
type Story = StoryObj<typeof meta>;

// ── Esquema de ejemplo: registro de paciente ─────────────────────────────────

const pacienteSchema = z.object({
  nombre: z.string().min(2, "El nombre debe tener al menos 2 caracteres"),
  apellido: z.string().min(2, "El apellido debe tener al menos 2 caracteres"),
  email: z.string().email("Ingresa un correo electrónico válido"),
  motivo: z.string().min(10, "Describe el motivo de consulta (mín. 10 caracteres)"),
});

type PacienteForm = z.infer<typeof pacienteSchema>;

export const Default: Story = {
  name: "Registro de paciente",
  render: () => {
    const form = useForm<PacienteForm>({
      resolver: zodResolver(pacienteSchema),
      defaultValues: { nombre: "", apellido: "", email: "", motivo: "" },
    });

    const onSubmit = (data: PacienteForm) => {
      window.alert(JSON.stringify(data, null, 2));
    };

    return (
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5 w-[480px]">
          <div className="grid grid-cols-2 gap-4">
            <FormField
              control={form.control}
              name="nombre"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nombre</FormLabel>
                  <FormControl>
                    <Input placeholder="Lucía" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="apellido"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Apellido</FormLabel>
                  <FormControl>
                    <Input placeholder="Méndez" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Correo electrónico</FormLabel>
                <FormControl>
                  <Input type="email" placeholder="lucia@ejemplo.com" {...field} />
                </FormControl>
                <FormDescription>
                  Se usa para enviar recordatorios de cita.
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="motivo"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Motivo de consulta</FormLabel>
                <FormControl>
                  <Textarea
                    placeholder="Describe brevemente el motivo de tu consulta..."
                    className="resize-none"
                    rows={3}
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <Button type="submit" className="w-full">
            Registrar paciente
          </Button>
        </form>
      </Form>
    );
  },
};

export const ConErrores: Story = {
  name: "Con errores de validación",
  render: () => {
    const form = useForm<PacienteForm>({
      resolver: zodResolver(pacienteSchema),
      defaultValues: { nombre: "L", apellido: "", email: "no-es-email", motivo: "corto" },
      mode: "onChange",
    });

    // Trigger validation immediately to show errors
    const { trigger } = form;
    void trigger();

    return (
      <Form {...form}>
        <form className="space-y-5 w-[480px]">
          <FormField
            control={form.control}
            name="nombre"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Nombre</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Correo electrónico</FormLabel>
                <FormControl>
                  <Input type="email" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="motivo"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Motivo de consulta</FormLabel>
                <FormControl>
                  <Textarea className="resize-none" rows={3} {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </form>
      </Form>
    );
  },
};

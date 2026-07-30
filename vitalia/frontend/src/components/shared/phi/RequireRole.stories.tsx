// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { RequireRole } from "./RequireRole";

/**
 * RequireRole — role-gated PHI content wrapper.
 * HIPAA-lite: shows children only if userRole is in the allowed list.
 */
const meta: Meta<typeof RequireRole> = {
  title: "Shared/PHI/RequireRole",
  component: RequireRole,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-surface" },
    layout: "padded",
    docs: {
      description: {
        component:
          "Renders children only when the current user's role is in the allowed list. Shows `fallback` or nothing when access is denied.",
      },
    },
  },
  argTypes: {
    userRole: {
      control: "select",
      options: [
        "doctor",
        "nurse",
        "admin_clinic",
        "patient",
        "marketing",
        "sales",
        "superadmin",
      ],
    },
  },
};
export default meta;

type Story = StoryObj<typeof RequireRole>;

/** Doctor role — access granted */
export const DoctorAllowed: Story = {
  name: "Doctor — acceso permitido",
  args: {
    roles: ["doctor", "nurse", "admin_clinic"],
    userRole: "doctor",
    children: (
      <div className="p-3 rounded border vt-border-verde-lima vt-bg-success-soft">
        <span className="text-sm vt-text-success">
          Contenido PHI visible para doctor
        </span>
      </div>
    ),
    fallback: (
      <div className="p-3 rounded border vt-border-danger-soft vt-bg-danger-soft">
        <span className="text-sm vt-text-danger">Acceso denegado</span>
      </div>
    ),
  },
};

/** Nurse role — access granted */
export const NurseAllowed: Story = {
  name: "Enfermería — acceso permitido",
  args: {
    roles: ["doctor", "nurse", "admin_clinic"],
    userRole: "nurse",
    children: (
      <div className="p-3 rounded border vt-border-verde-lima vt-bg-success-soft">
        <span className="text-sm vt-text-success">
          Contenido PHI visible para enfermería
        </span>
      </div>
    ),
    fallback: (
      <div className="p-3 rounded border vt-border-danger-soft vt-bg-danger-soft">
        <span className="text-sm vt-text-danger">Acceso denegado</span>
      </div>
    ),
  },
};

/** Marketing role — access denied */
export const MarketingDenied: Story = {
  name: "Marketing — acceso denegado",
  args: {
    roles: ["doctor", "nurse", "admin_clinic"],
    userRole: "marketing",
    children: (
      <div className="p-3 rounded border vt-border-verde-lima vt-bg-success-soft">
        <span className="text-sm vt-text-success">
          Contenido PHI — no debería verse
        </span>
      </div>
    ),
    fallback: (
      <div className="p-3 rounded border vt-border-danger-soft vt-bg-danger-soft">
        <span className="text-sm vt-text-danger">
          Acceso denegado — rol insuficiente
        </span>
      </div>
    ),
  },
};

/** Patient role — sees only own data fallback */
export const PatientRestricted: Story = {
  name: "Paciente — vista restringida",
  args: {
    roles: ["doctor", "nurse", "admin_clinic"],
    userRole: "patient",
    children: (
      <span className="text-sm vt-text-success">Datos clínicos completos</span>
    ),
    fallback: (
      <span className="text-sm vt-text-muted">
        Solo puedes ver tu propio historial desde el portal del paciente.
      </span>
    ),
  },
};

/** No role / null — always denied */
export const NullRole: Story = {
  name: "Rol nulo — siempre denegado",
  args: {
    roles: ["doctor", "nurse"],
    userRole: null,
    children: <span className="vt-text-success">Datos seguros</span>,
    fallback: <span className="vt-text-danger">Sin sesión activa</span>,
  },
};

/** Without fallback — renders nothing when denied */
export const NullFallback: Story = {
  name: "Sin fallback — acceso denegado = vacío",
  args: {
    roles: ["doctor"],
    userRole: "sales",
    children: <span className="vt-text-success">Diagnóstico clínico</span>,
  },
};

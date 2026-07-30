// cap: sales_agent.inbox-handler-mode-occ
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { ContactSidebar } from "./ContactSidebar";

/**
 * ContactSidebar — patient contact details panel.
 * PHI fields are masked via PiiMaskedSpan per HIPAA-lite.
 * All story args use FAKE data — no real patient PHI.
 */
const meta: Meta<typeof ContactSidebar> = {
  title: "Shared/ContactSidebar",
  component: ContactSidebar,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
    layout: "padded",
  },
};
export default meta;

type Story = StoryObj<typeof ContactSidebar>;

/** Patient context — full contact info (masked) */
export const PatientContext: Story = {
  name: "Paciente — todos los campos",
  args: {
    contact: {
      patientId: "pat-abc-fake-001",
      name: "María López", // fake
      phone: "+54 11 5555-1234", // fake
      email: "m.lopez@example.com", // fake
      statusTag: "Activo",
      npsScore: 9,
    },
  },
};

/** Lead context — only email */
export const LeadContext: Story = {
  name: "Lead — solo correo",
  args: {
    contact: {
      patientId: "lead-fake-002",
      email: "lead.fake@example.com", // fake
      statusTag: "Prospecto",
    },
  },
};

/** Empty state — only required patientId */
export const EmptyState: Story = {
  name: "Estado vacío",
  args: {
    contact: {
      patientId: "pat-empty-003",
    },
  },
};

/** With action buttons in children slot */
export const WithActions: Story = {
  name: "Con acciones adicionales",
  args: {
    contact: {
      patientId: "pat-fake-004",
      name: "Carlos Díaz", // fake
      phone: "+52 55 5555-6789", // fake
      statusTag: "En seguimiento",
    },
    children: (
      <div className="flex gap-2">
        <button
          className="flex-1 text-xs font-medium py-1.5 px-3 rounded border vt-border-cian vt-text-cian"
          type="button"
        >
          Ver expediente
        </button>
        <button
          className="flex-1 text-xs font-medium py-1.5 px-3 rounded text-white vt-bg-cian"
          type="button"
        >
          Contactar
        </button>
      </div>
    ),
  },
};

/** Phone + email only (no name) */
export const PhoneAndEmailOnly: Story = {
  name: "Teléfono y correo — sin nombre",
  args: {
    contact: {
      patientId: "pat-fake-005",
      phone: "+56 9 5555-8901", // fake
      email: "otro.fake@example.com", // fake
    },
  },
};

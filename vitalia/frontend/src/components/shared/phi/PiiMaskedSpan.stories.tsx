// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { PiiMaskedSpan } from "./PiiMaskedSpan";
import { RequireRole } from "./RequireRole";

/**
 * PiiMaskedSpan — masked PHI field display.
 *
 * HIPAA-lite: all PHI is shown masked.
 * Story args use FAKE/REDACTED data — no real PHI in story fixtures.
 */
const meta: Meta<typeof PiiMaskedSpan> = {
  title: "Shared/PHI/PiiMaskedSpan",
  component: PiiMaskedSpan,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-surface" },
    layout: "padded",
    docs: {
      description: {
        component:
          "Renders masked PHI values per HIPAA-lite rules. Uses FAKE data in stories — never real patient data.",
      },
    },
  },
  argTypes: {
    fieldType: {
      control: "select",
      options: [
        "name",
        "dni",
        "cuit",
        "phone",
        "email",
        "address",
        "date_of_birth",
        "generic",
      ],
    },
  },
};
export default meta;

type Story = StoryObj<typeof PiiMaskedSpan>;

/** Masked patient name (fake data) */
export const NameMasked: Story = {
  name: "Nombre — enmascarado",
  args: {
    value: "Ana García", // fake name for demo
    fieldType: "name",
  },
};

/** Masked DNI (fake) */
export const DniMasked: Story = {
  name: "DNI — enmascarado",
  args: {
    value: "12345678", // fake DNI
    fieldType: "dni",
  },
};

/** Masked CUIT (fake) */
export const CuitMasked: Story = {
  name: "CUIT — enmascarado",
  args: {
    value: "20123456789", // fake CUIT
    fieldType: "cuit",
  },
};

/** Masked phone (fake) */
export const PhoneMasked: Story = {
  name: "Teléfono — enmascarado",
  args: {
    value: "+54 11 5555-4567", // fake phone
    fieldType: "phone",
  },
};

/** Masked email (fake) */
export const EmailMasked: Story = {
  name: "Correo — enmascarado",
  args: {
    value: "ana.garcia@example.com", // fake email
    fieldType: "email",
  },
};

/** Masked date of birth (fake) */
export const DateOfBirthMasked: Story = {
  name: "Fecha de nacimiento — enmascarada",
  args: {
    value: "15/03/1985", // fake date
    fieldType: "date_of_birth",
  },
};

/** Null value — shows dash */
export const NullValue: Story = {
  name: "Valor nulo",
  args: {
    value: null,
    fieldType: "name",
  },
};

/** Doctor role — can see unmasked via RequireRole wrapper demo */
export const DoctorRoleReveal: Story = {
  name: "Doctor — puede ver (RequireRole demo)",
  render: () => (
    <div className="flex flex-col gap-3">
      <div>
        <p className="text-xs vt-text-muted" style={{ marginBottom: 4 }}>
          Rol: doctor (puede ver)
        </p>
        <RequireRole roles={["doctor"]} userRole="doctor">
          <span style={{ fontFamily: "monospace" }}>Ana García</span>
        </RequireRole>
      </div>
      <div>
        <p className="text-xs vt-text-muted" style={{ marginBottom: 4 }}>
          Rol: marketing (bloqueado — muestra enmascarado)
        </p>
        <RequireRole
          roles={["doctor", "nurse", "admin_clinic"]}
          userRole="marketing"
          fallback={<PiiMaskedSpan value="Ana García" fieldType="name" />}
        >
          <span style={{ fontFamily: "monospace" }}>Ana García</span>
        </RequireRole>
      </div>
    </div>
  ),
};

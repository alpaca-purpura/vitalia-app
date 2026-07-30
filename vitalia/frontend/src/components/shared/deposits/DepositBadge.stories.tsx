// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { DepositBadge } from "./DepositBadge";

/**
 * DepositBadge — prepaid booking deposit status badge.
 * Full payment integration arrives in scheduling-prepaid (Slice 2+).
 * Currency comes from useTenantLocale — NEVER hardcoded 'USD'.
 */
const meta: Meta<typeof DepositBadge> = {
  title: "Shared/Deposits/DepositBadge",
  component: DepositBadge,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-surface" },
    layout: "padded",
  },
  argTypes: {
    status: {
      control: "select",
      options: ["pending", "paid", "partial", "refunded", "expired"],
    },
    size: {
      control: "radio",
      options: ["sm", "md"],
    },
  },
};
export default meta;

type Story = StoryObj<typeof DepositBadge>;

/** Pending deposit */
export const Pending: Story = {
  name: "Pendiente",
  args: { status: "pending", amount: 1500, currency: "ARS", size: "md" },
};

/** Paid deposit */
export const Paid: Story = {
  name: "Pagado",
  args: { status: "paid", amount: 1500, currency: "ARS", size: "md" },
};

/** Partial payment */
export const Partial: Story = {
  name: "Pago parcial",
  args: { status: "partial", amount: 750, currency: "ARS", size: "md" },
};

/** Refunded */
export const Refunded: Story = {
  name: "Reembolsado",
  args: { status: "refunded", amount: 1500, currency: "ARS", size: "md" },
};

/** Expired */
export const Expired: Story = {
  name: "Vencido",
  args: { status: "expired", size: "md" },
};

/** Small size */
export const SmallSize: Story = {
  name: "Tamaño pequeño",
  args: { status: "paid", amount: 200, currency: "USD", size: "sm" },
};

/** All statuses */
export const AllStatuses: Story = {
  name: "Todos los estados",
  render: () => (
    <div className="flex flex-wrap gap-2">
      <DepositBadge status="pending" amount={1500} currency="ARS" />
      <DepositBadge status="paid" amount={1500} currency="ARS" />
      <DepositBadge status="partial" amount={750} currency="ARS" />
      <DepositBadge status="refunded" amount={1500} currency="ARS" />
      <DepositBadge status="expired" />
    </div>
  ),
};

/** MXN currency */
export const MexicoPeso: Story = {
  name: "Peso mexicano",
  args: { status: "paid", amount: 800, currency: "MXN", size: "md" },
};

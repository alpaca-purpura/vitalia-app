// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: TBD
import type { Meta, StoryObj } from "@storybook/nextjs";
import { AgentAvatar } from "./AgentAvatar";

/**
 * AgentAvatar — circular avatar for Vitalia AI agents (Valeria, Adrián, Lucas).
 * Gradient backgrounds from design-system.md globals.css.
 */
const meta: Meta<typeof AgentAvatar> = {
  title: "Shared/Agents/AgentAvatar",
  component: AgentAvatar,
  tags: ["autodocs"],
  parameters: {
    backgrounds: { default: "vitalia-bg" },
  },
  argTypes: {
    role: {
      control: "select",
      options: ["valeria", "adrian", "lucas", "unknown_role"],
      description: "Agent role — maps to display name + gradient",
    },
    size: {
      control: "radio",
      options: ["sm", "md", "lg"],
      description: "Avatar size: sm (24px) | md (32px) | lg (48px)",
    },
  },
};
export default meta;

type Story = StoryObj<typeof AgentAvatar>;

/** Valeria — cian-to-purple gradient (primary agent) */
export const Valeria: Story = {
  args: { role: "valeria", size: "md" },
};

/** Adrián — purple-to-navy gradient */
export const Adrian: Story = {
  args: { role: "adrian", size: "md" },
};

/** Lucas — lime-to-cian gradient */
export const Lucas: Story = {
  args: { role: "lucas", size: "md" },
};

/** Unknown role — fallback gradient + 2-char initials */
export const UnknownRole: Story = {
  args: { role: "copilot_agent", size: "md" },
  name: "Unknown role (fallback)",
};

/** All three agents at medium size */
export const AllAgentsMd: Story = {
  name: "All agents — md",
  render: () => (
    <div className="flex items-center gap-4">
      <AgentAvatar role="valeria" size="md" />
      <AgentAvatar role="adrian" size="md" />
      <AgentAvatar role="lucas" size="md" />
    </div>
  ),
};

/** Size comparison: sm | md | lg */
export const SizeVariants: Story = {
  name: "Size variants — Valeria",
  render: () => (
    <div className="flex items-end gap-4">
      <div className="flex flex-col items-center gap-1">
        <AgentAvatar role="valeria" size="sm" />
        <span className="text-[10px] vt-text-muted">sm</span>
      </div>
      <div className="flex flex-col items-center gap-1">
        <AgentAvatar role="valeria" size="md" />
        <span className="text-[10px] vt-text-muted">md</span>
      </div>
      <div className="flex flex-col items-center gap-1">
        <AgentAvatar role="valeria" size="lg" />
        <span className="text-[10px] vt-text-muted">lg</span>
      </div>
    </div>
  ),
};

/** With status indicator overlay (CSS positioning demo) */
export const WithStatusIndicator: Story = {
  name: "With status indicator",
  render: () => (
    <div className="relative inline-flex">
      <AgentAvatar role="valeria" size="md" />
      <span
        className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-white vt-bg-success"
        aria-label="En línea"
      />
    </div>
  ),
};

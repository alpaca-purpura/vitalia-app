// cap: platform.topbar-global
// story-origin: TBD
/**
 * agents — barrel exports
 * No default exports per FSD-Lite + arch fitness gate.
 */

export { AgentAvatar } from "./AgentAvatar";
export type { AgentAvatarProps } from "./AgentAvatar";

export { AgentAttribution } from "./AgentAttribution";
export type { AgentAttributionProps } from "./AgentAttribution";

export {
  agentNameByRole,
  AGENT_ROLES,
  AGENT_GRADIENT_CLASS,
  AGENT_INITIALS,
} from "./agent-names";
export type { AgentRole } from "./agent-names";

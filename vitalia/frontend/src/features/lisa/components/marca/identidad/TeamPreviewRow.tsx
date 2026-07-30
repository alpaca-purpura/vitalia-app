// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
"use client";

/**
 * TeamPreviewRow.tsx — Compact avatar row showing team members.
 *
 * Renders up to 3 avatars from lisa-doctores feature (F2-S8).
 * If the lisa-doctores API is not yet ready, renders graceful fallback.
 * Shows +N counter when team has more than 3 members.
 * "Gestionar equipo" link to /lisa/doctores (disabled tooltip if story not done).
 *
 * Spanish neutro LatAm — no voseo.
 *
 * T-5 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-5 deliverables
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */


import Link from "next/link";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

const MAX_VISIBLE = 3;

export interface TeamMember {
  id: string;
  name: string;
  role?: string;
  avatarUrl?: string | null;
}

export interface TeamPreviewRowProps {
  members: TeamMember[];
  tenantId: string;
  /** Whether the doctores feature story (F2-S8) is complete. */
  doctoresStoryDone?: boolean;
  isLoading?: boolean;
  className?: string;
}

function getInitials(name: string): string {
  return name
    .trim()
    .split(/\s+/)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .slice(0, 2)
    .join("");
}

/**
 * TeamPreviewRow — compact avatar stack with count and manage link.
 * Gracefully degrades if doctores API not ready.
 */
export function TeamPreviewRow({
  members,
  tenantId,
  doctoresStoryDone = false,
  isLoading = false,
  className,
}: TeamPreviewRowProps) {
  const visible = members.slice(0, MAX_VISIBLE);
  const hiddenCount = members.length - visible.length;
  const managePath = `/${tenantId}/lisa/doctores`;

  return (
    <section
      aria-label="Equipo médico"
      className={cn(
        "rounded-lg border border-border bg-card p-4 flex flex-col gap-3",
        className,
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-foreground">Equipo</h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Integrantes del equipo médico de la clínica.
          </p>
        </div>

        {doctoresStoryDone ? (
          <Link
            href={managePath}
            className="shrink-0 text-xs text-primary hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded"
            aria-label="Gestionar integrantes del equipo"
          >
            Gestionar equipo
          </Link>
        ) : (
          <Tooltip>
            <TooltipTrigger asChild>
              <span
                className="shrink-0 cursor-not-allowed text-xs text-muted-foreground"
                aria-disabled="true"
              >
                Gestionar equipo
              </span>
            </TooltipTrigger>
            <TooltipContent side="bottom">
              <p className="text-xs">Disponible próximamente</p>
            </TooltipContent>
          </Tooltip>
        )}
      </div>

      {/* Avatar stack */}
      {isLoading ? (
        <div
          aria-busy="true"
          aria-label="Cargando equipo"
          className="flex gap-1"
        >
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="h-8 w-8 rounded-full bg-muted/60 animate-pulse"
            />
          ))}
        </div>
      ) : members.length === 0 ? (
        <p className="text-xs text-muted-foreground italic">
          Sin integrantes registrados aún.
        </p>
      ) : (
        <div className="flex items-center gap-1" aria-label={`${members.length} integrantes`}>
          {/* Stacked avatars */}
          <div className="flex">
            {visible.map((member, idx) => (
              <Avatar
                key={member.id}
                className={cn(
                  "h-8 w-8 border-2 border-card",
                  idx > 0 && "-ml-2",
                )}
              >
                {member.avatarUrl ? (
                  <AvatarImage src={member.avatarUrl} alt={member.name} />
                ) : null}
                <AvatarFallback className="bg-primary/10 text-xs font-medium text-primary">
                  {getInitials(member.name)}
                </AvatarFallback>
              </Avatar>
            ))}
            {/* +N overflow */}
            {hiddenCount > 0 && (
              <Avatar className="h-8 w-8 -ml-2 border-2 border-card">
                <AvatarFallback className="bg-muted text-xs font-medium text-muted-foreground">
                  +{hiddenCount}
                </AvatarFallback>
              </Avatar>
            )}
          </div>

          <span className="ml-2 text-xs text-muted-foreground">
            {members.length === 1
              ? "1 integrante"
              : `${members.length} integrantes`}
          </span>
        </div>
      )}
    </section>
  );
}

TeamPreviewRow.displayName = "TeamPreviewRow";

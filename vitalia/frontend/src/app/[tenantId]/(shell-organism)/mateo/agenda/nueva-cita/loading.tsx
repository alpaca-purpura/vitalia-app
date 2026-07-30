// cap: scheduling.mateo-agenda
/**
 * NuevaCitaLoading — Loading UI for the nueva-cita route.
 * T-FE-1 vitalia-fase2-mateo-nueva-cita
 *
 * Shown by Next.js streaming while the page renders server-side.
 * Mimics FormPageScaffold skeleton to prevent layout shift.
 */

import { Skeleton } from "@luana/ui-kit";

export default function NuevaCitaLoading() {
  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Header skeleton */}
      <div className="flex items-center gap-3">
        <Skeleton className="h-8 w-20" />
        <Skeleton className="h-6 w-48" />
      </div>

      {/* Form fields skeleton */}
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-10 w-full" />
        </div>
      ))}

      {/* Action bar skeleton */}
      <div className="flex justify-end gap-3">
        <Skeleton className="h-10 w-24" />
        <Skeleton className="h-10 w-32" />
      </div>
    </div>
  );
}

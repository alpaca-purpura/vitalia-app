// cap: configuracion.cuenta
// story-origin: vitalia-fase2-config-cuenta
/**
 * use-account-query.ts — client GET /api/v1/clinics/account/ (React Query).
 *
 * Fix live-verify 2026-06-11: los pages SSR pasan initialData={null} y el view
 * dependía 100% de eso → el form nacía vacío y NUNCA cargaba los datos reales
 * del tenant (SC-11 roto). Este hook es la fuente client-side canónica; los
 * views usan `data ?? initialData`.
 *
 * X-User-ID: el account_router exige el header en TODAS las routes (422 si falta).
 */

"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { cuentaKeys, getAccount } from "../api/get-account";
import type { ClinicAccountDTO } from "../types/cuenta.types";

export function useAccountQuery(tenantId: string) {
  const { getToken, isLoaded, isSignedIn, userId } = useAuth();

  return useQuery<ClinicAccountDTO>({
    queryKey: cuentaKeys.account(tenantId),
    queryFn: async () => {
      const token = await getToken();
      if (!token || !userId) throw new Error("No autenticado");
      return getAccount({ token, tenantId, userId });
    },
    enabled: isLoaded && !!isSignedIn && !!userId,
  });
}

// cap: configuracion.cuenta
// story-origin: vitalia-fase2-config-cuenta
/**
 * patch-account.ts — PATCH /api/v1/clinics/account/ (trailing slash mandatory).
 *
 * Sends camelCase payload. Camelize boundary: snake_case BE response → ClinicAccountDTO.
 *
 * T-1 vitalia-fase2-config-cuenta
 * spec_anchor: 03-arch.md § 4 (PATCH route)
 * downstream-regression-na: brand-local vitalia FE API; no cross-brand consumers
 */

import { fetchClient } from "@/lib/api/fetchClient";
import { keysToCamel, keysToSnake } from "@/lib/api/keys-to-camel";
import type { ClinicAccountDTO, ClinicAccountPatchDTO } from "../types/cuenta.types";

export interface PatchAccountOptions {
  token: string;
  tenantId: string;
  clinicId?: string | null;
  /** Clerk userId real — X-User-ID (actor de audit, requerido por el router). */
  userId: string;
  /** Rol vitalia (de useCurrentUser /me) — X-User-Role (RBAC: owner | admin_clinic). */
  userRole?: string | null;
  payload: ClinicAccountPatchDTO;
}

/**
 * PATCHes the tenant's clinic account data.
 * Payload: decamelize boundary (keysToSnake) — el BE Pydantic es snake_case SIN
 * alias camelCase: un body camelCase se ignora silencioso (200 sin persistir).
 * Response: camelize boundary applied → ClinicAccountDTO.
 *
 * RBAC: roles {owner, admin_clinic} pueden PATCH (BE enforces → 403 resto).
 * READ-ONLY fields (country/language/clinicType) MUST NOT be in payload.
 */
export async function patchAccount(opts: PatchAccountOptions): Promise<ClinicAccountDTO> {
  const raw = await fetchClient<unknown>("/api/v1/clinics/account/", {
    method: "PATCH",
    token: opts.token,
    tenantId: opts.tenantId,
    clinicId: opts.clinicId,
    headers: {
      "X-User-ID": opts.userId,
      "X-User-Role": opts.userRole ?? "owner",
    },
    body: JSON.stringify(keysToSnake(opts.payload)),
  });
  return keysToCamel<ClinicAccountDTO>(raw);
}

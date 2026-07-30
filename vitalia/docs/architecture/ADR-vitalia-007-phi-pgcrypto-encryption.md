# ADR-vitalia-007 — PHI encryption at-rest con pgcrypto (symmetric KEK env-based dev, KMS path prod)

- **Status:** accepted
- **Date:** 2026-05-30
- **Brand:** vitalia
- **Story origin:** `vitalia-crm-phi-base-tables-migration`
- **Supersedes/extends:** consume el patrón ya existente `vitalia/backend/src/modules/vitalia/_shared/encryption/kek_client.py::KEKClient` (migración 025 nps comment) — NO crea capa nueva.
- **Refuerza:** `vitalia/.claude/rules/hipaa-lite.md § Encryption at rest`.

## Contexto

La verificación live god-matrix de `vitalia-iam-slice2-phi-real-auth` (done 2026-05-30) expuso que `vitalia_patients` y `vitalia_leads` no existen en dev (HTTP 500). Al crear estas tablas base PHI, Chris ratificó (2026-05-30) cifrar las columnas PHI identitarias **at-rest** vía `pgcrypto` (hipaa-lite full), greenfield (sin prod ni datos plaintext → se crea cifrado desde el inicio, sin data-migration).

Ya existe en vitalia un patrón pgcrypto para `nps_responses.comment` (migración 025) + un `KEKClient` env-based (`_shared/encryption/kek_client.py`). Sin embargo: (1) el patrón 025 usa **trigger BEFORE INSERT/UPDATE + GUC de sesión `app.encryption_key`** que **nunca se inyecta en ninguna sesión del código** (gap latente: la KEK GUC no se setea → el trigger almacenaría NULL); (2) `VITALIA_PHI_KEK` **no está declarada en `.env.dev.template` ni docker-compose** → ni siquiera el env var existe en dev. Para que la verificación live de esta story funcione (anti-teatro), hay que cerrar ambos gaps.

## Decisión

### D1 — Cifrado inline `pgp_sym_encrypt/decrypt` con KEK como bound param (NO trigger+GUC para patients/leads)

Las columnas PHI identitarias se almacenan **`BYTEA` cifradas** con `pgp_sym_encrypt(:val, :kek)` al escribir y se descifran con `pgp_sym_decrypt(col, :kek)::text` al leer, **directamente en el SQL crudo** de `patient_repository.py` + `lead_repository.py`. La KEK se pasa como **bound parameter `:kek`** obtenido de `KEKClient.get_key()`, NO vía GUC de sesión.

**Por qué inline-param y NO el trigger+GUC del patrón 025:**
- Los repos patient/lead ya usan SQL crudo con `text()` + bound params → el cifrado inline es coherente con su estilo (cero nueva infra).
- El trigger+GUC de 025 depende de `current_setting('app.encryption_key')` que **nadie inyecta** en el connection pool actual → patrón roto en runtime. Adoptarlo replicaría el bug. (Documentar el gap de 025 como follow-up — NO arreglar inline aquí.)
- Bound param es explícito, testeable (round-trip en integration), y la KEK nunca toca logs.

### D2 — KEK source: env `VITALIA_PHI_KEK` (dev/staging) vía `KEKClient`, slot KMS para prod

- **Dev/staging:** `KEKClient.from_env()` lee `VITALIA_PHI_KEK` (hex ≥32 bytes = AES-256). Esta story **agrega** `VITALIA_PHI_KEK` a `vitalia/.env.dev.template` (con un valor dev fijo documentado como NO-secreto-prod) + `vitalia/docker-compose.dev.yml` (env passthrough), cerrando el gap que dejó 025 sin KEK.
- **Prod (deferred):** subclasear `KEKClient` con adapter Vault/AWS KMS/GCP KMS (`get_key()` override) + DI en `main.py`. hipaa-lite.md exige **KEK rotada anualmente + backup key separada (no la misma KEK runtime)**. El path está documentado en el docstring de `KEKClient` (ya existe) — esta story NO implementa KMS (no hay prod).
- **NUNCA** hardcodear la KEK en código. **NUNCA** loguear la KEK (ni en `structlog`, ni en traces, ni en el transcript de verificación live — solo status codes + logs sanitizados).

### D3 — Columnas cifradas vs plaintext (qué se cifra)

| Tabla | Cifradas (BYTEA, PHI/PII) | Plaintext (claves/flags/metadata — se filtran/indexan) |
|---|---|---|
| `vitalia_patients` | `name`, `date_of_birth`, `dni`, `phone`, `email`, `address` | `id`, `tenant_id`, `clinic_id`, `marketing_opt_in`, `opt_out`, `opt_out_reason`, `opt_out_at`, `marketing_opt_out_at`, `deleted_at`, `created_at`, `updated_at` |
| `vitalia_leads` | `name`, `email`, `phone`, `notes` | `id`, `tenant_id`, `source`, `status`, `deleted_at`, `created_at`, `updated_at` |

- `date_of_birth` (hoy `TIMESTAMPTZ` en el dominio) se cifra → su columna física es `BYTEA`; al descifrar se castea de vuelta a timestamp en la capa repo. Es PHI identitario (hipaa-lite § PHI fields canónicos lista `patient.date_of_birth`).
- `opt_out_reason` se mantiene **plaintext**: es metadata administrativa (motivo de baja de marketing), NO PHI clínico identitario, y el repo no lo trata como sensible (el audit ya lo redacta en su payload).
- `notes` (leads) se cifra por defecto: puede contener PII de contacto/contexto del prospecto.

### D4 — NO indexar columnas cifradas

Las columnas `BYTEA` cifradas **NO se indexan** (un índice sobre ciphertext no soporta lookup por valor plaintext — `WHERE dni = X` sería imposible sin descifrar toda la tabla). Lookup por `dni`/`email` cifrado = **fuera de scope** → si se necesita en el futuro, **blind index** (HMAC determinístico de la columna en una col separada indexable) = follow-up story. Los índices de esta migración van solo sobre claves/flags plaintext: `(tenant_id, clinic_id)`, partial opt_out/marketing, `(tenant_id)`, `(tenant_id, status)`.

### D5 — Downgrade strategy: 035 NO dropea la tabla (016 la owna)

`016_vitalia` creó `vitalia_patients` (esqueleto) con `CREATE TABLE IF NOT EXISTS` y está aplicada en la cadena 015→016→…→034. La migración 035 **reconcile** (agrega las columnas PHI faltantes con `ADD COLUMN IF NOT EXISTS`) + crea `vitalia_leads` net-new. Por lo tanto el `downgrade()` de 035 **solo**:
- `DROP TABLE IF EXISTS vitalia_leads` (035 la creó → la puede dropear).
- `ALTER TABLE vitalia_patients DROP COLUMN IF EXISTS {name,date_of_birth,dni,phone,email,address}` (las columnas que 035 agregó).
- **NO** `DROP TABLE vitalia_patients` (la owna 016 — dropearla rompería la cadena al hacer downgrade más allá de 035).
- **NO** `DROP EXTENSION pgcrypto` (compartida por 013/005/025 + futuras).

### D6 — Greenfield (sin data-migration)

No hay prod ni filas plaintext existentes en dev → las tablas se crean cifradas desde el inicio. Si en el futuro prod tuviera filas plaintext de "Story 11", el cifrado de datos existentes sería una story aparte (NO esta).

## Consecuencias

- **Positivas:** PHI cifrado at-rest cumpliendo hipaa-lite; reusa `KEKClient` existente (cero capa nueva); cierra el gap `VITALIA_PHI_KEK` que dejó 025; verificación live real posible (SC-1/SC-5).
- **Negativas / tradeoffs:** no hay lookup por columna cifrada (aceptado — blind index es follow-up); el patrón inline-param diverge del trigger+GUC de 025 (justificado: 025 está roto en runtime); la KEK dev vive en env var (aceptado para dev; prod = KMS slot documentado).
- **Deuda registrada (follow-up, NO en esta story):** (1) wirear o deprecar el trigger+GUC de 025 (KEK nunca inyectada); (2) blind index si se necesita búsqueda por dni/email; (3) adapter KMS prod + rotación anual; (4) decisión sobre las 5 migraciones legacy huérfanas en `src/modules/vitalia/persistence/migrations/`.

## Validación legacy-mining (2026-05-30 · pre-build, prompt-directed)

Antes de construir se minó el monolito original (`~/Proyectos/luana-nicolify-legacy`, branch `legacy/nicolify-original`) buscando una solución canónica previa para PHI patients/leads que se pudiera traer en vez de inventar (`grep pgp_sym|encrypt|decrypt|CREATE TABLE.*patients|leads`). Resultado:

- **El legacy NO resolvió esto.** `crm/infrastructure/persistence/{patient,lead}_repository.py` del legacy son SQL plaintext **sin** cifrado; `vitalia_leads` **nunca** se creó en ningún árbol legacy (mismo gap); `vitalia_patients` solo en `016` (idéntico esqueleto al actual).
- El único cifrado pgcrypto del legacy es el de NPS/fidelización (`025` trigger+GUC) — el **mismo patrón roto** (GUC `app.encryption_key` nunca inyectada).
- `KEKClient` actual = el transplantado del legacy verbatim → **reuse** (API `from_env()`/`get_key()` confirmada), no recrear.

**Conclusión:** no existe solución canónica mejor para importar. La decisión D1 (pgp_sym inline + bound param `:kek`, evitando el trigger+GUC roto) se ratifica como la coherente con el módulo. Sin cambios al ADR ni al `03-arch` tras la minería.

## Referencias

- `vitalia/.claude/rules/hipaa-lite.md § Encryption at rest`
- `vitalia/backend/src/modules/vitalia/_shared/encryption/kek_client.py` (KEKClient — EXTEND)
- `vitalia/backend/alembic/versions/025_vitalia_pgcrypto_nps_comment.py` (patrón pgcrypto previo — referencia)
- `vitalia/backend/tests/architecture/test_pgcrypto_phi_columns.py` (gate BYTEA — extender con patients/leads)
- `.claude/rules/backend-migrations.md` (idempotencia forward-only)

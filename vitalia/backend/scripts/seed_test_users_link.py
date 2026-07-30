"""Seed test users + tenants + user_tenants + clinic branch + PHI patient (RBAC test matrix · SSoT).

Origin: pre-flight gate Slice 1 vitalia (Chris ratificó 2026-05-20 NO Clerk Organizations).
Multi-tenancy via tenants + users + user_tenants en engine luana-core-iam.
Extended 2026-05-29 (P2 god-user): full per-role test matrix over the demo tenant (Sanaré)
so every VitaliaRole can be exercised via REAL RBAC (never bypass).
Extended 2026-05-30 (T-3 PHI base tables): add 1 encrypted patient + 1 encrypted lead
so SC-1/SC-5 integration tests can exercise tablas reales (035 migration).

What this seed does (idempotent — ON CONFLICT DO NOTHING/UPDATE everywhere):
  1. INSERT tenants rows (3 fixture clinics — Aurora AR · Mindful CL · Sanaré MX)
  2. INSERT vitalia_clinic_branches row for Sanaré (clinicId for PHI dual-filter / X-Clinic-ID)
  3. (optional --clerk-sync) create/update Clerk users + publicMetadata.{role,tenant_id,clinicId}
     so FE (reads publicMetadata.role) and BE engine (reads user_tenants.role) AGREE.
  4. INSERT users rows con clerk_id link
  5. INSERT user_tenants junction (per-role over Sanaré, demo tenant)
  6. INSERT vitalia_patients — 1 cifrado Sanaré demo (id determinístico · pgp_sym_encrypt)
  7. INSERT vitalia_leads   — 1 cifrado Sanaré demo (id determinístico · pgp_sym_encrypt)

★ Role resolution truth (2026-05-29):
  - BE engine path (get_current_user): role = user_tenants.role (DB) for the active tenant.
  - FE (useCurrentUser → RequireRole): role = Clerk publicMetadata.role.
  - PHI surfaces (crm/clinics/inbox/marketing): Slice-1 STUB decoder — REJECTS real Clerk JWT
    (returns 401). Exercising PHI roles end-to-end in dev-app needs Slice 2 (JWKS + role from
    user_tenants into ClinicContext + real repos). NOT covered by this seed.
  - NOTE enum mismatch: VitaliaRole.RECEPTIONIST == "receptionist" but the legacy recepcion
    user/role is "recepcion". Kept as-is (non-PHI) to avoid breaking existing fixtures.

★ PHI seed (2026-05-30 T-3):
  - PATIENT_SANARE_DEMO: deterministic id via uuid5. Encrypted con pgp_sym_encrypt.
    VITALIA_PHI_KEK env var MUST be set; seed fails clearly if absent (no plaintext fallback).
  - LEAD_SANARE_DEMO: idem for leads.
  - IDs are printed at the end of the run (NUNCA KEK/PHI plaintext).

Usage:
    # Full sync (host — has Clerk egress + secret). Recommended.
    CLERK_SECRET_KEY=sk_test_... \
    POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=5435 POSTGRES_DB=vitalia_dev \
    POSTGRES_USER=postgres POSTGRES_PASSWORD=password \
    .venv/bin/python vitalia/backend/scripts/seed_test_users_link.py --clerk-sync

    # DB-only (in-container, no Clerk egress — uses hardcoded CLERK_IDS):
    docker exec luana-dev-vitalia_backend_dev-1 \
      bash -c "cd /workspace/vitalia/backend && uv run python scripts/seed_test_users_link.py"

Test password (all god-matrix users): VitaliaRoles2026!  (dr.demo legacy keeps its own)

downstream-regression-na: brand-local seed script; no cross-brand consumers
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
import uuid

# ─── Deterministic UUID fixtures ───────────────────────────────────────────
NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # uuid5 namespace URL (matching seed_fixture_clinics)
TENANT_AURORA = uuid.uuid5(NAMESPACE, "aurora-dental-ar")
TENANT_MINDFUL = uuid.uuid5(NAMESPACE, "mindful-santiago-cl")
TENANT_SANARE = uuid.uuid5(NAMESPACE, "sanare-latam-mx")  # == e69a691d-070e-5caf-a053-6e74642ec100 (demo tenant)
CLINIC_SANARE = uuid.uuid5(NAMESPACE, "clinic:sanare-latam-mx:principal")  # == f035be5b-0ac4-5210-8fc3-395650ca2b83

# ─── PHI seed fixtures (T-3 · 2026-05-30) ───────────────────────────────────
# Deterministic IDs so SC-1/SC-5 integration tests read them by known id.
# PRINT these at end of seed run; NUNCA imprimir KEK/PHI plaintext.
PATIENT_SANARE_DEMO = uuid.uuid5(NAMESPACE, "patient:sanare-latam-mx:demo")
LEAD_SANARE_DEMO = uuid.uuid5(NAMESPACE, "lead:sanare-latam-mx:demo")

CLERK_API = "https://api.clerk.com/v1"
TEST_PASSWORD = "VitaliaRoles2026!"  # noqa: S105 — dev-only fixture password

# Hardcoded Clerk IDs (resolved live when --clerk-sync; fallback for in-container DB-only runs).
CLERK_IDS = {
    "dr.demo@vitalialat.com": "user_3DyTTJQK0ZQLE5XGSi5BMjKEjrR",
    "recepcion@vitalialat.com": "user_3DyTUqjKVwnb0n7Tf89OdKTAGpK",
    "admin@vitalialat.com": "user_3DyTVEiMRRHoaszcY5vQ2BuPsFx",
    "owner.demo@vitalialat.com": "user_3EQJmUfsIXZi0XhlpmXOxtF6zh5",
    "doctor.demo@vitalialat.com": "user_3EQJjxsvxiZ5exQjucSB651xnUd",
    "nurse.demo@vitalialat.com": "user_3EQJmjv6PUnrv0pmO3RLvZXwJOA",
    "admin.clinic.demo@vitalialat.com": "user_3EQJmvRj1zBKtWi64qfBnsPnYpG",
    "marketing.demo@vitalialat.com": "user_3EQJn2iflBFqDk59gqc0srYEv55",
}

TENANTS = [
    {
        "id": TENANT_AURORA,
        "name": "Clínica Dental Aurora",
        "slug": "aurora-dental-ar",
        "default_currency": "ARS",
        "timezone": "America/Argentina/Buenos_Aires",
        "location_country": "AR",
        "location_city": "Buenos Aires",
    },
    {
        "id": TENANT_MINDFUL,
        "name": "Centro Mindful Santiago",
        "slug": "mindful-santiago-cl",
        "default_currency": "CLP",
        "timezone": "America/Santiago",
        "location_country": "CL",
        "location_city": "Santiago",
    },
    {
        "id": TENANT_SANARE,
        "name": "Sanaré LATAM",
        "slug": "sanare-latam-mx",
        # PEN: demo tenant de pruebas en soles (Chris 2026-06-17 · fast-track previo a
        # la historia vitalia-tenant-currency-config que hace la moneda configurable).
        "default_currency": "PEN",
        "timezone": "America/Mexico_City",
        "location_country": "MX",
        "location_city": "Ciudad de México",
    },
]

CLINIC_BRANCHES = [
    {
        "id": CLINIC_SANARE,
        "tenant_id": TENANT_SANARE,
        "name": "Sanaré LATAM — Sede Principal",
        "slug": "sanare-principal",
        "country": "MX",
        "timezone": "America/Mexico_City",
        "plan_tier": "pro",
    },
]

# ─── Test user matrix (RBAC god-matrix over Sanaré demo tenant) ─────────────
# email -> global users.role
TEST_USERS_EMAIL_TO_ROLE = {
    "dr.demo@vitalialat.com": "doctor",  # legacy: name=doctor, but acts as owner in Sanaré (see links)
    "recepcion@vitalialat.com": "recepcion",
    "admin@vitalialat.com": "super_admin",
    "owner.demo@vitalialat.com": "owner",
    "doctor.demo@vitalialat.com": "doctor",
    "nurse.demo@vitalialat.com": "nurse",
    "admin.clinic.demo@vitalialat.com": "admin_clinic",
    "marketing.demo@vitalialat.com": "marketing",
}

# user_tenants associations — (email, tenant_id, tenant_role)
# Demo god-matrix: one user PER role over Sanaré (real RBAC; one role per (user,tenant)).
USER_TENANT_LINKS = [
    # legacy (Chris ratificó 2026-05-20 — dr.demo = owner del tenant primario)
    ("dr.demo@vitalialat.com", TENANT_SANARE, "owner"),
    ("recepcion@vitalialat.com", TENANT_SANARE, "recepcion"),
    ("admin@vitalialat.com", TENANT_AURORA, "super_admin"),
    ("admin@vitalialat.com", TENANT_MINDFUL, "super_admin"),
    ("admin@vitalialat.com", TENANT_SANARE, "super_admin"),
    # god-matrix per-role (2026-05-29)
    ("owner.demo@vitalialat.com", TENANT_SANARE, "owner"),
    ("doctor.demo@vitalialat.com", TENANT_SANARE, "doctor"),
    ("nurse.demo@vitalialat.com", TENANT_SANARE, "nurse"),
    ("admin.clinic.demo@vitalialat.com", TENANT_SANARE, "admin_clinic"),
    ("marketing.demo@vitalialat.com", TENANT_SANARE, "marketing"),
]

# Clerk publicMetadata.role per email (FE useCurrentUser reads this; align with primary tenant role).
CLERK_ROLE = {
    "dr.demo@vitalialat.com": "owner",
    "recepcion@vitalialat.com": "recepcion",
    "admin@vitalialat.com": "super_admin",
    "owner.demo@vitalialat.com": "owner",
    "doctor.demo@vitalialat.com": "doctor",
    "nurse.demo@vitalialat.com": "nurse",
    "admin.clinic.demo@vitalialat.com": "admin_clinic",
    "marketing.demo@vitalialat.com": "marketing",
}


def _get_pg_conn():
    """Get psycopg2 connection from env vars."""
    import psycopg2

    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        dbname=os.environ.get("POSTGRES_DB", "vitalia_dev"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "password"),
    )


# ─── Clerk sync (stdlib urllib — no extra deps) ─────────────────────────────
def _clerk_request(method: str, path: str, secret: str, body: dict | None = None) -> tuple[int, object]:
    """Perform a Clerk Backend API request. Returns (status, parsed_json)."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(  # noqa: S310 — fixed https Clerk host
        f"{CLERK_API}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/json",
            # Clerk fronts the API with Cloudflare; the default Python-urllib UA is 403'd
            # (CF error 1010). A non-default UA is required.
            "User-Agent": "vitalia-seed/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
            return resp.status, json.loads(resp.read() or "null")
    except urllib.error.HTTPError as e:
        try:
            payload = json.loads(e.read() or "null")
        except Exception:  # noqa: BLE001
            payload = {}
        return e.code, payload


def _clerk_sync(secret: str, clinic_id: str) -> dict[str, str]:
    """Create/update Clerk users with aligned publicMetadata. Returns email->clerk_id (live)."""
    resolved: dict[str, str] = {}
    # Currency in publicMetadata so the FE useTenantLocale reads the tenant's real
    # currency (not the hardcoded ARS fallback). Derived from the Sanaré tenant row
    # so flipping TENANTS keeps this in sync. (vitalia-tenant-currency-config wires
    # the canonical per-tenant source later; this is the fast-track for test data.)
    sanare_currency = next((t["default_currency"] for t in TENANTS if t["id"] == TENANT_SANARE), "PEN")
    for email, role in CLERK_ROLE.items():
        meta = {
            "role": role,
            "tenant_id": str(TENANT_SANARE),
            "clinicId": clinic_id,
            "currency": sanare_currency,
        }
        _, found = _clerk_request("GET", f"/users?email_address={email}", secret)
        uid = found[0]["id"] if isinstance(found, list) and found else None
        if uid:
            _clerk_request("PATCH", f"/users/{uid}/metadata", secret, {"public_metadata": meta})
            print(f"  [clerk] {email} UPDATED (role={role}, id={uid})")
        else:
            status, created = _clerk_request(
                "POST",
                "/users",
                secret,
                {
                    "email_address": [email],
                    "password": TEST_PASSWORD,
                    "skip_password_checks": True,
                    "public_metadata": meta,
                },
            )
            uid = created.get("id") if isinstance(created, dict) else None
            if not uid:
                print(f"  [clerk] {email} CREATE FAILED (status={status}) — fallback hardcoded", file=sys.stderr)
                uid = CLERK_IDS.get(email)
            else:
                print(f"  [clerk] {email} CREATED (role={role}, id={uid})")
        if uid:
            resolved[email] = uid
    return resolved


def main() -> int:  # noqa: C901
    do_clerk = "--clerk-sync" in sys.argv and not os.environ.get("NO_CLERK")
    secret = os.environ.get("CLERK_SECRET_KEY", "")

    # ─── KEK presence check (T-3 requirement: fail clearly, not silently) ────
    kek = os.environ.get("VITALIA_PHI_KEK", "")
    if not kek:
        print(
            "ERROR: VITALIA_PHI_KEK env var not set.\n"
            "Set it before running the seed (dev-only, NOT for prod):\n"
            '  export VITALIA_PHI_KEK=$(python3 -c "import secrets; print(secrets.token_hex(32))")',
            file=sys.stderr,
        )
        return 1

    # Resolve clerk_ids: live sync (if requested + secret) else hardcoded fallback.
    clerk_ids = dict(CLERK_IDS)
    if do_clerk and secret:
        print("  [clerk] syncing users (create/update + publicMetadata)...")
        try:
            clerk_ids.update(_clerk_sync(secret, str(CLINIC_SANARE)))
        except Exception as e:  # noqa: BLE001
            print(f"  WARNING: Clerk sync failed ({e}) — using hardcoded CLERK_IDS", file=sys.stderr)
    elif do_clerk and not secret:
        print("  WARNING: --clerk-sync requested but CLERK_SECRET_KEY unset — using hardcoded IDs", file=sys.stderr)

    conn = _get_pg_conn()
    cursor = conn.cursor()
    n_tenants = n_clinics = n_users = n_links = n_patients = n_leads = 0

    try:
        # ─── 1. Tenants ──────────────────────────────────────────────────────
        for t in TENANTS:
            cursor.execute(
                """
                INSERT INTO tenants
                    (id, name, slug, default_currency, timezone,
                     location_country, location_city, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, true)
                ON CONFLICT (id) DO NOTHING
                """,
                (
                    str(t["id"]),
                    t["name"],
                    t["slug"],
                    t["default_currency"],
                    t["timezone"],
                    t["location_country"],
                    t["location_city"],
                ),
            )
            n_tenants += int(cursor.rowcount > 0)

        # ─── 2. Clinic branches (PHI dual-filter clinicId) ───────────────────
        for c in CLINIC_BRANCHES:
            cursor.execute(
                """
                INSERT INTO vitalia_clinic_branches
                    (id, tenant_id, name, slug, country, timezone,
                     plan_tier, is_active, onboarding_completed)
                VALUES (%s, %s, %s, %s, %s, %s, %s, true, true)
                ON CONFLICT (id) DO NOTHING
                """,
                (
                    str(c["id"]),
                    str(c["tenant_id"]),
                    c["name"],
                    c["slug"],
                    c["country"],
                    c["timezone"],
                    c["plan_tier"],
                ),
            )
            n_clinics += int(cursor.rowcount > 0)

        # ─── 3. Users (linked Clerk IDs) ─────────────────────────────────────
        email_to_user_id: dict[str, uuid.UUID] = {}
        for email, role in TEST_USERS_EMAIL_TO_ROLE.items():
            clerk_id = clerk_ids.get(email)
            if not clerk_id:
                print(f"  [user] SKIP {email} (no Clerk id resolved)")
                continue

            user_id = uuid.uuid5(NAMESPACE, f"user:{email}")
            email_to_user_id[email] = user_id
            full_name = email.split("@")[0].replace(".", " ").title()
            cursor.execute(
                """
                INSERT INTO users
                    (id, email, clerk_id, full_name, role, is_active)
                VALUES (%s, %s, %s, %s, %s, true)
                ON CONFLICT (clerk_id) DO UPDATE SET
                    email = EXCLUDED.email,
                    role = EXCLUDED.role
                """,
                (str(user_id), email, clerk_id, full_name, role),
            )
            n_users += 1

        # ─── 4. user_tenants junction ────────────────────────────────────────
        for email, tenant_id, role in USER_TENANT_LINKS:
            user_id = email_to_user_id.get(email)
            if not user_id:
                print(f"  [link] SKIP {email} → {tenant_id} (user not seeded)")
                continue
            cursor.execute(
                """
                INSERT INTO user_tenants
                    (user_id, tenant_id, role, is_active)
                VALUES (%s, %s, %s, true)
                ON CONFLICT (user_id, tenant_id) DO UPDATE SET
                    role = EXCLUDED.role,
                    is_active = true
                """,
                (str(user_id), str(tenant_id), role),
            )
            n_links += int(cursor.rowcount > 0)

        # ─── 5. PHI patient Sanaré demo (cifrado at-rest · T-3) ──────────────
        # date_of_birth stored as ISO-format string via pgp_sym_encrypt so _parse_dob
        # in PatientRepository can reconstruct it with datetime.fromisoformat.
        # Spanish neutro LatAm — datos MX realistas. NUNCA imprimir KEK ni PHI plaintext.
        cursor.execute(
            """
            INSERT INTO vitalia_patients
                (id, tenant_id, clinic_id,
                 name, date_of_birth, dni, phone, email, address,
                 marketing_opt_in, opt_out, created_at, updated_at)
            VALUES (
                %s, %s, %s,
                pgp_sym_encrypt(%s, %s),
                pgp_sym_encrypt(%s, %s),
                pgp_sym_encrypt(%s, %s),
                pgp_sym_encrypt(%s, %s),
                pgp_sym_encrypt(%s, %s),
                pgp_sym_encrypt(%s, %s),
                false, false, NOW(), NOW()
            )
            ON CONFLICT (id) DO NOTHING
            """,
            (
                str(PATIENT_SANARE_DEMO),
                str(TENANT_SANARE),
                str(CLINIC_SANARE),
                "María Fernanda Gómez",
                kek,  # name
                "1985-03-15T00:00:00+00:00",
                kek,  # date_of_birth (ISO — _parse_dob)
                "GOMF850315MDFNRR09",
                kek,  # dni (CURP MX realista)
                "+52 55 1234 5678",
                kek,  # phone
                "mfgomez@correo.ejemplo.mx",
                kek,  # email
                "Av. Insurgentes Sur 1234, Col. Florida, CDMX",
                kek,  # address
            ),
        )
        n_patients += int(cursor.rowcount > 0)

        # ─── 6. PHI lead Sanaré demo (cifrado at-rest · T-3) ─────────────────
        cursor.execute(
            """
            INSERT INTO vitalia_leads
                (id, tenant_id,
                 name, email, phone, notes,
                 source, status, created_at, updated_at)
            VALUES (
                %s, %s,
                pgp_sym_encrypt(%s, %s),
                pgp_sym_encrypt(%s, %s),
                pgp_sym_encrypt(%s, %s),
                pgp_sym_encrypt(%s, %s),
                %s, %s, NOW(), NOW()
            )
            ON CONFLICT (id) DO NOTHING
            """,
            (
                str(LEAD_SANARE_DEMO),
                str(TENANT_SANARE),
                "Carlos Ramírez Ortega",
                kek,  # name
                "carlos.ramirez@correo.ejemplo.mx",
                kek,  # email
                "+52 55 9876 5432",
                kek,  # phone
                "Interesado en blanqueamiento dental por Instagram",
                kek,  # notes
                "instagram",  # source (plaintext)
                "new",  # status (plaintext)
            ),
        )
        n_leads += int(cursor.rowcount > 0)

        conn.commit()
        print(
            f"\n  Result: {n_tenants} tenants, {n_clinics} clinics, "
            f"{n_users} users upserted, {n_links} user_tenants links, "
            f"{n_patients} patients seeded, {n_leads} leads seeded"
        )
        print("\n  PHI seed IDs (for integration tests — NOT KEK/PHI values):")
        print(f"    PATIENT_SANARE_DEMO = {PATIENT_SANARE_DEMO}")
        print(f"    LEAD_SANARE_DEMO    = {LEAD_SANARE_DEMO}")
        return 0
    except Exception as e:  # noqa: BLE001 — top-level catch
        conn.rollback()
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    sys.exit(main())

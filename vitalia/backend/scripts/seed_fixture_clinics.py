"""Seed script — 3 LatAm fixture clinics (Story 11 T-docs-1).

Fixture clínicas programáticas para onboarding flow validation. NO son
clínicas piloto reales (defer Story 11.bis). Sirven para:
  - Test de integración del flujo de onboarding
  - Validación de la configuración de Payment gateways (MercadoPago)
  - Smoke tests de Brand Studio + Offer wizard médico
  - Demo del booking widget

Fixtures definidos en spec § 2:
  A — Clínica Dental Aurora (AR, es-AR, dental, MercadoPago)
  B — Centro Mindful Santiago (CL, es-CL, psychology, MercadoPago)
  C — Sanaré LATAM (MX, es-MX, psychiatry, MercadoPago)

Usage:
    python scripts/seed_fixture_clinics.py --check   # Validar definición sin DB
    python scripts/seed_fixture_clinics.py --apply   # Insertar en DB (requiere Postgres)
    python scripts/seed_fixture_clinics.py --reset   # Eliminar fixtures + re-insertar

Idempotency:
    --apply es idempotente: detecta por tenant_id existente antes de insertar.
    Re-ejecuciones son seguras (SELECT EXISTS antes de INSERT).

Tenant isolation:
    Cada clínica tiene tenant_id único determinista (UUIDv5 basado en clinic_slug).
    Ningún tenant_id se repite entre fixtures.
"""

from __future__ import annotations

import argparse
import sys
import uuid
from dataclasses import dataclass, field
from typing import Any

# ─── Namespace UUIDv5 para fixtures vitalia ──────────────────────────────────
# Namespace fijo para garantizar tenant_ids deterministas en re-ejecuciones.
# NUNCA cambiar — rompe idempotency.

_FIXTURE_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # UUID_NAMESPACE_URL


def _fixture_tenant_id(clinic_slug: str) -> uuid.UUID:
    """Genera tenant_id determinista para un fixture usando UUIDv5.

    Args:
        clinic_slug: identificador único del fixture (ej. 'aurora-dental-ar').

    Returns:
        UUID determinista — mismo input → mismo output en cualquier máquina.
    """
    seed = f"vitalia:fixture:clinic:{clinic_slug}"
    return uuid.uuid5(_FIXTURE_NAMESPACE, seed)


# ─── Dataclass de fixture ────────────────────────────────────────────────────


@dataclass(frozen=True)
class ClinicFixture:
    """Definición completa de una clínica fixture.

    Refleja los campos del spec § 2 (brand_identity, clinic_type, locale,
    plan_tier, payment_gateways). Se usa tanto en --check como en --apply.
    """

    clinic_slug: str
    clinic_name: str
    clinic_type: str  # dental | psychology | psychiatry | wellness
    country: str  # ISO 3166-1 alpha-2
    locale: str  # IETF BCP 47 (es-AR, es-CL, es-MX)
    city: str
    plan_tier: str  # solo_doctor | clinic | multi_site
    primary_payment_gateway: str  # mercadopago | stripe_connect
    tagline: str
    brand_primary_color: str
    brand_secondary_color: str
    compliance_level: str = "hipaa_lite"
    contains_phi: bool = False
    features_enabled: list[str] = field(default_factory=list)

    @property
    def tenant_id(self) -> uuid.UUID:
        """Tenant ID determinista para este fixture."""
        return _fixture_tenant_id(self.clinic_slug)

    def to_dict(self) -> dict[str, Any]:
        """Serialización para persistencia o logging."""
        return {
            "tenant_id": str(self.tenant_id),
            "clinic_slug": self.clinic_slug,
            "clinic_name": self.clinic_name,
            "clinic_type": self.clinic_type,
            "country": self.country,
            "locale": self.locale,
            "city": self.city,
            "plan_tier": self.plan_tier,
            "primary_payment_gateway": self.primary_payment_gateway,
            "tagline": self.tagline,
            "brand_primary_color": self.brand_primary_color,
            "brand_secondary_color": self.brand_secondary_color,
            "compliance_level": self.compliance_level,
            "contains_phi": self.contains_phi,
            "features_enabled": self.features_enabled,
        }


# ─── 3 fixtures LatAm (spec § 2) ─────────────────────────────────────────────

FIXTURE_CLINICS: list[ClinicFixture] = [
    # Fixture A — Clínica Dental Aurora (AR)
    # Basada en tuodontologa.ar · Plan: clinic ($199 USD/mo)
    # Pago primario: MercadoPago (ARS + USD)
    ClinicFixture(
        clinic_slug="aurora-dental-ar",
        clinic_name="Clínica Dental Aurora",
        clinic_type="dental",
        country="AR",
        locale="es-AR",
        city="Buenos Aires",
        plan_tier="clinic",
        primary_payment_gateway="mercadopago",
        tagline="Tu sonrisa, nuestra prioridad",
        brand_primary_color="#0EA5E9",
        brand_secondary_color="#0F172A",
        features_enabled=[
            "brand_studio_simplified",
            "offer_studio_medical",
            "booking_prepaid",
            "sales_agent_vertical_medical",
            "copilot_kb_dental",
        ],
    ),
    # Fixture B — Centro Mindful Santiago (CL)
    # Basada en mindy.cl · Plan: solo_doctor ($49 USD/mo)
    # Pago primario: MercadoPago (CLP)
    ClinicFixture(
        clinic_slug="mindful-santiago-cl",
        clinic_name="Centro Mindful Santiago",
        clinic_type="psychology",
        country="CL",
        locale="es-CL",
        city="Santiago",
        plan_tier="solo_doctor",
        primary_payment_gateway="mercadopago",
        tagline="Conecta con tu salud mental",
        brand_primary_color="#7C3AED",
        brand_secondary_color="#10B981",
        features_enabled=[
            "brand_studio_simplified",
            "offer_studio_medical",
            "booking_prepaid",
            "sales_agent_vertical_medical",
            "copilot_kb_psychology",
        ],
    ),
    # Fixture C — Sanaré LATAM (MX)
    # Basada en sanarai.com · Plan: multi_site ($599 USD/mo)
    # Pago primario: MercadoPago (USD + MXN)
    ClinicFixture(
        clinic_slug="sanare-latam-mx",
        clinic_name="Sanaré LATAM",
        clinic_type="psychiatry",
        country="MX",
        locale="es-MX",
        city="Ciudad de México",
        plan_tier="multi_site",
        primary_payment_gateway="mercadopago",
        tagline="Atención psicológica online, 24/7, en español",
        brand_primary_color="#06B6D4",
        brand_secondary_color="#8B5CF6",
        features_enabled=[
            "brand_studio_simplified",
            "offer_studio_medical",
            "booking_prepaid",
            "sales_agent_vertical_medical",
            "copilot_kb_psychology",
            "copilot_kb_psychiatry",
            "multi_currency",
        ],
    ),
]

# Verificación de unicidad de tenant_ids en la lista de fixtures
_TENANT_IDS = [str(f.tenant_id) for f in FIXTURE_CLINICS]
assert len(set(_TENANT_IDS)) == len(_TENANT_IDS), (
    "BUG: clinic_slugs producen tenant_ids duplicados — revisar _fixture_tenant_id()"
)


# ─── Operaciones de seed ──────────────────────────────────────────────────────


def check_fixtures() -> int:
    """Valida la definición de fixtures sin conectar a la base de datos.

    Ejecutado por V-F-15: `python scripts/seed_fixture_clinics.py --check`

    Verifica:
    - Número correcto de fixtures (3)
    - Campos obligatorios presentes y no vacíos
    - tenant_ids únicos (UUIDv5 deterministas)
    - compliance_level=hipaa_lite + contains_phi=false
    - Países LatAm (AR/CL/MX/PE/CO/BR)
    - Payment gateway = mercadopago o stripe_connect
    - Localización válida

    Returns:
        0 si todos los checks pasan, 1 si algún check falla.
    """
    errors: list[str] = []
    _allowed_countries = {"AR", "CL", "MX", "PE", "CO", "BR"}
    _allowed_clinic_types = {"dental", "psychology", "psychiatry", "wellness"}
    _allowed_gateways = {"mercadopago", "stripe_connect"}
    _allowed_plan_tiers = {"solo_doctor", "clinic", "multi_site"}

    print(f"=== Vitalia Fixture Clinics — CHECK ({len(FIXTURE_CLINICS)} fixtures) ===")

    # Check 1: Cantidad de fixtures
    if len(FIXTURE_CLINICS) != 3:
        errors.append(f"Expected 3 fixtures, got {len(FIXTURE_CLINICS)}")

    # Check 2: Tenant IDs únicos
    tenant_ids = [str(f.tenant_id) for f in FIXTURE_CLINICS]
    if len(set(tenant_ids)) != len(tenant_ids):
        errors.append("Duplicate tenant_ids detected — clinic slugs must be unique")

    # Check 3: Cada fixture pasa validaciones de campo
    for fixture in FIXTURE_CLINICS:
        prefix = f"[{fixture.clinic_slug}]"

        if not fixture.clinic_name.strip():
            errors.append(f"{prefix} clinic_name is empty")
        if fixture.country not in _allowed_countries:
            errors.append(f"{prefix} country '{fixture.country}' not in allowed LatAm set {_allowed_countries}")
        if fixture.clinic_type not in _allowed_clinic_types:
            errors.append(f"{prefix} clinic_type '{fixture.clinic_type}' not in {_allowed_clinic_types}")
        if fixture.primary_payment_gateway not in _allowed_gateways:
            errors.append(f"{prefix} gateway '{fixture.primary_payment_gateway}' not in {_allowed_gateways}")
        if fixture.plan_tier not in _allowed_plan_tiers:
            errors.append(f"{prefix} plan_tier '{fixture.plan_tier}' not in {_allowed_plan_tiers}")
        if fixture.compliance_level != "hipaa_lite":
            errors.append(f"{prefix} compliance_level must be 'hipaa_lite', got '{fixture.compliance_level}'")
        if fixture.contains_phi is not False:
            errors.append(f"{prefix} contains_phi must be False (D7 — no PHI in fixture metadata)")
        if not fixture.tagline.strip():
            errors.append(f"{prefix} tagline is empty")
        if not fixture.brand_primary_color.startswith("#"):
            errors.append(f"{prefix} brand_primary_color must be hex (starts with '#')")
        if not fixture.locale or "-" not in fixture.locale:
            errors.append(f"{prefix} locale '{fixture.locale}' must be IETF BCP 47 format (e.g. es-AR)")
        if not fixture.features_enabled:
            errors.append(f"{prefix} features_enabled list is empty — at least booking_prepaid required")

    # Imprimir resultados
    for f in FIXTURE_CLINICS:
        status = "OK" if not any(f.clinic_slug in e for e in errors) else "FAIL"
        print(f"  [{status}] {f.clinic_slug} — tenant_id={f.tenant_id} country={f.country}")

    if errors:
        print("\nERRORS:")
        for err in errors:
            print(f"  - {err}")
        print(f"\nResult: FAIL ({len(errors)} error(s))")
        return 1

    print("\nAll fixtures valid.")
    print(f"Result: OK ({len(FIXTURE_CLINICS)} fixtures, all checks passed)")
    return 0


def _try_import_db_deps() -> tuple[Any, Any] | None:
    """Intenta importar dependencias de DB.

    Returns None si psycopg2/sqlalchemy no están disponibles.
    Permite que --check corra sin DB en entornos sin Postgres.
    """
    try:
        import os

        import psycopg2  # type: ignore[import-untyped]

        return psycopg2, os
    except ImportError:
        return None


def _get_dsn() -> str:
    """Construye DSN de Postgres desde variables de entorno.

    Variables esperadas (mismas que el backend principal):
        POSTGRES_HOST (default: localhost)
        POSTGRES_PORT (default: 5432)
        POSTGRES_DB   (default: vitalia_dev)
        POSTGRES_USER (default: postgres)
        POSTGRES_PASSWORD (default: postgres)
    """
    import os

    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "vitalia_dev")
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "postgres")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


def _exists_tenant(cursor: Any, tenant_id: uuid.UUID) -> bool:
    """Verifica si el tenant_id ya existe en vitalia_medical_audit_log.

    Usamos vitalia_medical_audit_log como proxy de existencia del tenant
    (siempre creado en el onboarding — T-be-4). Si la tabla existe y el
    tenant tiene al menos un evento de audit, consideramos que ya fue
    seeded.

    Fallback: si la tabla no existe (pre-migration), retorna False.
    """
    try:
        cursor.execute(
            """
            SELECT EXISTS(
                SELECT 1 FROM vitalia_medical_audit_log
                WHERE tenant_id = %s
                LIMIT 1
            )
            """,
            (str(tenant_id),),
        )
        row = cursor.fetchone()
        return bool(row[0]) if row else False
    except Exception:  # noqa: BLE001 — tabla puede no existir aún
        return False


def _insert_fixture_audit_event(cursor: Any, fixture: ClinicFixture) -> None:
    """Inserta un evento de audit log como registro de existencia del fixture.

    Crea un tenant_created audit event que actúa como "seed marker":
    - Idempotente: _exists_tenant verifica este registro antes de insertar.
    - Solo crea el evento, NO el perfil completo de la clínica.
      El perfil real se crea via OnboardingService (T-be-7 API endpoint).
    - No PHI en metadata (D7 — compliance_level=hipaa_lite, contains_phi=false).
    """
    import json
    from datetime import datetime, timezone

    event_id = uuid.uuid5(fixture.tenant_id, "seed:tenant_created")
    now = datetime.now(tz=timezone.utc).isoformat()

    metadata = json.dumps(
        {
            "event": "fixture_seed",
            "clinic_slug": fixture.clinic_slug,
            "clinic_type": fixture.clinic_type,
            "country": fixture.country,
            "plan_tier": fixture.plan_tier,
            "compliance_level": fixture.compliance_level,
            "contains_phi": fixture.contains_phi,
            # No PHI: sin nombre paciente, email, teléfono, dirección real
        }
    )

    cursor.execute(
        """
        INSERT INTO vitalia_medical_audit_log
            (id, tenant_id, event_type, severity, payload_redacted, created_at, actor_type)
        VALUES
            (%s, %s, %s, %s, %s::jsonb, %s, %s)
        ON CONFLICT (id) DO NOTHING
        """,
        (
            str(event_id),
            str(fixture.tenant_id),
            "fixture_seed_tenant_created",
            "info",
            metadata,
            now,
            "system:seed_fixture_clinics",
        ),
    )


def apply_fixtures(reset: bool = False) -> int:
    """Inserta los 3 fixtures en la base de datos (idempotente).

    Args:
        reset: si True, elimina los registros de fixtures existentes antes
               de re-insertar. Útil para tests que requieren estado limpio.

    Returns:
        0 si exitoso, 1 si error (Postgres no disponible o error de schema).
    """
    deps = _try_import_db_deps()
    if deps is None:
        print("ERROR: psycopg2 no disponible. Instala: uv add psycopg2-binary")
        print("Para validar sin DB: usa --check en lugar de --apply")
        return 1

    psycopg2, _ = deps

    try:
        dsn = _get_dsn()
        conn = psycopg2.connect(dsn)
        conn.autocommit = False
        cursor = conn.cursor()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: No se pudo conectar a Postgres: {exc}")
        print("Variables de entorno disponibles:")
        print("  POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD")
        return 1

    try:
        if reset:
            print("=== --reset: eliminando fixtures existentes... ===")
            for fixture in FIXTURE_CLINICS:
                cursor.execute(
                    "DELETE FROM vitalia_medical_audit_log WHERE tenant_id = %s",
                    (str(fixture.tenant_id),),
                )
                print(f"  Eliminado: {fixture.clinic_slug}")
            conn.commit()

        print(f"=== Vitalia Fixture Clinics — APPLY ({len(FIXTURE_CLINICS)} fixtures) ===")
        inserted = 0
        skipped = 0

        for fixture in FIXTURE_CLINICS:
            if _exists_tenant(cursor, fixture.tenant_id):
                print(f"  [SKIP] {fixture.clinic_slug} — ya existe (tenant_id={fixture.tenant_id})")
                skipped += 1
                continue

            _insert_fixture_audit_event(cursor, fixture)
            print(f"  [OK]   {fixture.clinic_slug} — insertado (tenant_id={fixture.tenant_id})")
            inserted += 1

        conn.commit()
        print(f"\nResult: {inserted} insertados, {skipped} ya existían")
        return 0

    except Exception as exc:  # noqa: BLE001
        conn.rollback()
        print(f"ERROR durante apply: {exc}")
        return 1
    finally:
        cursor.close()
        conn.close()


# ─── CLI entrypoint ───────────────────────────────────────────────────────────


def main() -> int:
    """Punto de entrada CLI.

    Uso:
        python scripts/seed_fixture_clinics.py --check   # V-F-15 validator
        python scripts/seed_fixture_clinics.py --apply   # Insertar en DB
        python scripts/seed_fixture_clinics.py --reset   # Reset + re-insertar
    """
    parser = argparse.ArgumentParser(
        description="Vitalia fixture clinics seed — Story 11 T-docs-1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python scripts/seed_fixture_clinics.py --check
      Valida la definición de los 3 fixtures sin conectar a la DB.
      Usado por el validator V-F-15 del build pipeline.

  python scripts/seed_fixture_clinics.py --apply
      Inserta los fixtures en Postgres (idempotente — re-ejecución segura).
      Requiere variables de entorno: POSTGRES_HOST, POSTGRES_PORT,
      POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD

  python scripts/seed_fixture_clinics.py --reset
      Elimina los fixtures existentes y los re-inserta (para tests).
        """,
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Validar fixtures sin DB (V-F-15)")
    mode.add_argument("--apply", action="store_true", help="Insertar fixtures en Postgres")
    mode.add_argument("--reset", action="store_true", help="Eliminar + re-insertar fixtures")

    args = parser.parse_args()

    if args.check:
        return check_fixtures()
    if args.apply:
        return apply_fixtures(reset=False)
    if args.reset:
        return apply_fixtures(reset=True)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

# vitalia

Medical/health vertical brand on Luana Platform.

**Purpose:** Brand-specific SaaS application for the medical/dental/wellness niche,
consuming `core/` engine for AI sales and marketing automation. First vertical brand
validating the Luana Platform Extension SDK (EP-1..EP-18) post Story 10 migration.

**Target market:** Clinics in Argentina, Chile, México, Brasil, Colombia, Perú.

See [docs/architecture/luana-platform/00-overview.md](../docs/architecture/luana-platform/00-overview.md) for full monorepo topology.

---

## Vertical-medical extensions summary

Vitalia extends the Luana Platform base with:

| Extension | Description |
|---|---|
| `vitalia_booking_prepaid` | Prepaid booking flow (MercadoPago + Stripe Connect) with deposit/balance split |
| `vitalia_medical_consent` | Informed consent capture with HMAC-verified URLs + 7-year retention |
| `vitalia_hipaa_lite` | HIPAA-lite compliance layer: PII scanner, no-diagnosis guardrail, no-prescription guardrail |
| `vitalia_vertical_medical_tools` | 4 agentic tools: prepaid_payment_check, treatment_followup_check, medical_consent_request, appointment_reschedule_with_doctor |
| `vitalia_medical_kb` | 3 KB packs: dental (implants, procedures), psychology (CBT/systemic, crisis lines), psychiatry (medication classes, disclaimers) |
| `vitalia_plan_tiers` | 3 pricing tiers: solo_doctor ($49/mo), clinic ($199/mo), multi_site ($599/mo) |

**Compliance level:** `hipaa_lite` (LatAm data protection laws — NOT US HIPAA).
See [docs/compliance.md](docs/compliance.md) for full compliance documentation.

---

## Quick start

### 1. Environment variables

Copy the example env file and fill in your credentials:

```bash
cp vitalia/.env.dev.template vitalia/.env.dev
```

Required variables:

```bash
# Postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=vitalia_dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Clerk App #2 (vitalia-specific Clerk application)
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
CLERK_WEBHOOK_SECRET=whsec_...

# MercadoPago (primary payment gateway)
MERCADOPAGO_ACCESS_TOKEN=APP_USR-...
MERCADOPAGO_WEBHOOK_SECRET=...

# Stripe Connect (fallback — US/EU)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Qdrant (medical KB)
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### 2. Install backend dependencies

```bash
cd vitalia/backend
uv sync
```

### 3. Run database migrations

```bash
cd vitalia/backend
docker exec luana-dev-vitalia_backend_dev-1 bash -c "cd /workspace/vitalia/backend && /workspace/.venv/bin/alembic upgrade head"
```

### 4. Seed fixture clinics (dev/test only)

Inserta las 3 clínicas fixture LatAm para testing del flujo de onboarding:

```bash
cd vitalia/backend

# Validar definición sin DB (CI check — V-F-15)
.venv/bin/python scripts/seed_fixture_clinics.py --check

# Insertar en DB (idempotente — re-ejecución segura)
.venv/bin/python scripts/seed_fixture_clinics.py --apply

# Reset + re-insertar (entorno limpio para tests)
.venv/bin/python scripts/seed_fixture_clinics.py --reset
```

Fixtures disponibles:

| Fixture | País | Tipo | Plan | Gateway |
|---|---|---|---|---|
| `aurora-dental-ar` (Clínica Dental Aurora) | AR | dental | clinic ($199/mo) | MercadoPago |
| `mindful-santiago-cl` (Centro Mindful Santiago) | CL | psychology | solo_doctor ($49/mo) | MercadoPago |
| `sanare-latam-mx` (Sanaré LATAM) | MX | psychiatry | multi_site ($599/mo) | MercadoPago |

### 5. Seed medical KB (Qdrant)

Ingesta el contenido médico de referencia en Qdrant (dental + psychology + psychiatry packs):

```bash
cd vitalia/backend
uv run python -m scripts.seed_medical_kb
```

### 6. Start dev server

```bash
cd "$(git rev-parse --show-toplevel)"
make dev-vitalia   # o: docker compose -f vitalia/docker-compose.yml up -d
```

La API estará disponible en `http://localhost:8002/api/v1/vitalia/`.

---

## Key documentation

| Doc | Description |
|---|---|
| [docs/compliance.md](docs/compliance.md) | HIPAA-lite vs HIPAA full, LatAm laws (Ley 25.326/LGPD/LFPDPPP/Ley 19.628/Ley 29.733/Ley 1.581), 7-year audit retention, consent flow, HMAC verification, PII patterns, data rights |
| [docs/booking-widget-embed.md](docs/booking-widget-embed.md) | Copy-paste iframe snippet, postMessage protocol (widget:loaded/widget:resize/widget:booking-confirmed/widget:payment-redirect), URL canónica alternativa, CDN hosting, origin validation |
| [../docs/architecture/luana-platform/00-overview.md](../docs/architecture/luana-platform/00-overview.md) | Full monorepo topology, Extension SDK EP-1..EP-18 |

---

## Backend structure

```
vitalia/backend/
├── src/modules/vitalia/
│   ├── domain/           # Entidades puras (Booking, ConsentRecord, etc.)
│   ├── infrastructure/   # ORM models + repositories + payment adapters
│   ├── application/      # Services (OnboardingService, BookingService, etc.)
│   ├── api/              # FastAPI routes + DTOs
│   ├── copilot/          # Medical KB packs + module registry
│   ├── extensions.py     # EP-1..EP-18 Extension SDK registrations
│   └── payment/          # MercadoPago + Stripe Connect adapters
├── scripts/
│   ├── seed_medical_kb.py        # Ingesta KB médica en Qdrant
│   └── seed_fixture_clinics.py   # Fixtures LatAm (Aurora/Mindful/Sanaré)
├── tests/
│   ├── architecture/     # Fitness tests (tenant isolation, HIPAA-lite invariants)
│   ├── integration/      # Tests con Postgres + gateway sandboxes
│   ├── unit/             # Tests de application layer (mocks)
│   └── e2e/              # Flujos end-to-end (onboarding + booking + payment)
└── alembic/
    └── versions/
        └── 001_vitalia_initial_snapshot.py   # Schema completo + seed plan tiers
```

---

## Running tests

```bash
cd vitalia/backend

# Lint + format
.venv/bin/ruff check src/ tests/ --no-cache
.venv/bin/ruff format --check src/ tests/

# Type check
.venv/bin/mypy src/

# All tests
.venv/bin/pytest tests/ -v

# Architecture fitness only
.venv/bin/pytest tests/architecture/ -v

# Integration tests (requiere Postgres + gateway sandboxes)
.venv/bin/pytest tests/integration/ -v -m integration
```

---

*Vitalia — Story 11 luana-vitalia-bootstrap · Luana Platform v0.1.0+*

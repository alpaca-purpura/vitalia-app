# 03-arch-brief.md — vitalia-auth-base-functional

> **Brief** (no full `/architect` orchestrator run — scope hot-fix per D1 spec).
> Decisiones técnicas atómicas + paths exactos + patterns required.
> Builder consume este brief + `01-spec.md` + `05-guidelines.md` + `06-tickets.yaml`.

## § 1 — Surface FE

### 1.1 — Middleware Clerk (`vitalia/frontend/src/middleware.ts`)

**NEW file.** Espejar pattern Clerk Next.js 16 App Router:

```typescript
// vitalia/frontend/src/middleware.ts
import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isPublicRoute = createRouteMatcher([
  "/sign-in(.*)",
  "/sign-up(.*)",
  "/public/(.*)",                 // landing público clínicas
  "/api/v1/vitalia/webhooks/(.*)", // Clerk webhook + future webhooks
  "/api/health(.*)",              // healthcheck K8s
]);

export default clerkMiddleware(async (auth, req) => {
  if (!isPublicRoute(req)) {
    await auth.protect();
  }
});

export const config = {
  matcher: [
    // Skip Next.js internals + static files
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
```

**Decisiones inline:**
- Sin redirect manual a `/sign-in` — `auth.protect()` lo hace nativo Clerk.
- Sin RBAC chequeo en middleware (defer Slice 1+).
- Cookie domain debe matchear `dev-app.vitalialat.com` — Clerk lo maneja vía `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` con domain configurado en Clerk dashboard.

### 1.2 — Páginas Clerk reales

**EDIT `vitalia/frontend/src/app/(auth)/sign-in/page.tsx`:**

```typescript
import { SignIn } from "@clerk/nextjs";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Iniciar sesión — Vitalia",
};

export default function SignInPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-vitalia-bg p-6">
      <SignIn
        appearance={{
          variables: {
            colorPrimary: "var(--vitalia-primary)",
            borderRadius: "var(--vitalia-radius-md)",
          },
        }}
      />
    </main>
  );
}
```

**EDIT `vitalia/frontend/src/app/(auth)/sign-up/page.tsx`:** idéntico con `<SignUp />`.

**DELETE legacy stubs** (per D3 spec):
- `vitalia/frontend/src/app/onboarding/step-1/page.tsx`
- `vitalia/frontend/src/app/onboarding/step-2/page.tsx`
- `vitalia/frontend/src/app/onboarding/step-3/page.tsx`
- Sus directorios `step-1/`, `step-2/`, `step-3/` (vacíos post delete).

> Wizard único vive en `/onboarding/wizard` (Story `vitalia-slice-1-onboarding-wizard` shipped).

### 1.3 — Dashboard `/` mínimo welcome

**EDIT `vitalia/frontend/src/app/(dashboard)/page.tsx`:**

Renderiza componente nuevo `<DashboardWelcome />` en feature `features/dashboard/`
(NEW feature folder, mínimo).

```typescript
// vitalia/frontend/src/app/(dashboard)/page.tsx
import { DashboardWelcome } from "@/features/dashboard";
import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

export default async function DashboardPage() {
  const { userId } = await auth();
  if (!userId) redirect("/sign-in");
  return <DashboardWelcome userId={userId} />;
}
```

**NEW `vitalia/frontend/src/features/dashboard/` FSD-Lite structure:**
```
features/dashboard/
├── index.ts                        # exports DashboardWelcome
├── components/
│   ├── DashboardWelcome.tsx        # Server Component — fetch user+tenant + render
│   ├── DashboardWelcome.client.tsx # Client (small interactivity if any — optional)
│   └── SliceOneStubsRow.tsx        # 5 stubs grid (Inbox/Pipeline/Agenda/Fideliz/Marketing)
├── api/
│   └── useDashboardData.ts         # React Query hook fetching /api/v1/iam/me + tenant context
├── types/
│   └── DashboardData.ts            # TS types
└── __tests__/
    └── DashboardWelcome.test.tsx   # Vitest unit
```

**Server Component default.** Solo `"use client"` si requiere interactividad mínima (CTA navigation usa `<Link>` nativo, no requiere client).

### 1.4 — `(dashboard)/layout.tsx` (NEW si no existe — TBD)

Si no existe layout `(dashboard)/layout.tsx` con shell mínimo (Vitalia logo + UserButton), crear:

```typescript
import { UserButton } from "@clerk/nextjs";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-vitalia-bg">
      <header className="flex items-center justify-between border-b border-vitalia-border px-6 py-4">
        <VitaliaLogo />
        <UserButton afterSignOutUrl="/sign-in" />
      </header>
      <main className="container mx-auto px-6 py-8">{children}</main>
    </div>
  );
}
```

## § 2 — Surface BE (Admin Streamlit)

### 2.1 — Layout per `.claude/rules/admin-panel.md` + pattern Nicolify

**NEW `vitalia/backend/src/modules/vitalia/admin/`** espejando pattern Nicolify
**SOLO scope tenants + usuarios** (per D2 spec):

```
vitalia/backend/src/modules/vitalia/admin/
├── __init__.py
├── app.py                  # Streamlit entry, st.set_page_config único, st.navigation registry
├── pages/
│   ├── __init__.py
│   ├── tenants.py          # wrapper thin → calls modules.tenants.render_tenants()
│   └── usuarios.py         # wrapper thin → calls modules.users.render_users()
├── modules/
│   ├── __init__.py
│   ├── tenants.py          # lógica render — Streamlit forms + queries DB
│   └── users.py            # lógica render — Streamlit forms + Clerk Backend API
└── _shared/
    ├── __init__.py
    ├── auth.py             # Streamlit Authenticator basic auth (super-admin)
    └── db.py               # SQLAlchemy session factory para admin (read+write)
```

**`app.py` shape** (espejar nicolify pero scope mínimo):

```python
"""Vitalia admin Streamlit panel — scope mínimo: tenants + users.

Per .claude/rules/admin-panel.md — brand-aislado, registry-based.
Super-admin auth via Streamlit Authenticator (basic auth bcrypt).
"""
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import streamlit as st

sys.path.append(str((Path(__file__).parent / "../..").resolve()))

import luana_core_platform.infrastructure.agent_observability_bootstrap  # noqa: F401
import src.modules.vitalia.persistence.model_registry  # noqa: F401

st.set_page_config(
    page_title="Vitalia Admin",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

@dataclass
class PageSpec:
    file_path: str
    title: str
    icon: str

PAGE_SPECS: list[PageSpec] = [
    PageSpec("pages/tenants.py", "Tenants", "🏥"),
    PageSpec("pages/usuarios.py", "Usuarios", "👤"),
]

# Auth gate ANTES nav (super-admin only)
from src.modules.vitalia.admin._shared.auth import require_super_admin
if not require_super_admin():
    st.stop()

# Streamlit native navigation
pg = st.navigation([
    st.Page(spec.file_path, title=spec.title, icon=spec.icon)
    for spec in PAGE_SPECS
])
pg.run()
```

### 2.2 — `modules/tenants.py` (lógica tenant create + list)

Fields del form:
- `clinic_name: str` (required, ≤ 100 chars)
- `country: str` (selectbox: AR / CL / MX / CO / PE / UY)
- `locale: str` (selectbox: es-AR / es-CL / es-MX / es-CO / es-PE / es-UY)
- `timezone: str` (selectbox derivado de country)
- `vertical: str` (selectbox: dental / psychology / psychiatry / aesthetic / general)
- `plan_tier: str` (selectbox: solo_doctor / clinic / multi_site)

Submit:
- `tenant_id = uuid5(NAMESPACE_URL, f"vitalia:admin:tenant:{clinic_slug}")` — determinista
- INSERT en `tenants` + `clinics` + `tenant_locations` (per HIPAA-lite dual filter en SC-08)
- Audit log row en `vitalia_audit_log` (action="admin.tenant.create")
- Success message + refresh list

Listar tenants: query simple `SELECT id, name, country, plan_tier FROM clinics ORDER BY created_at DESC LIMIT 50`.

### 2.3 — `modules/users.py` (lógica user create vía Clerk Backend API)

Fields:
- `email: str` (required)
- `first_name: str`
- `last_name: str`
- `tenant_id: str` (selectbox de tenants existentes)
- `clinic_id: str` (auto from tenant)
- `role: str` (selectbox: clinic_owner / doctor / nurse / receptionist)

Submit:
- Call `clerk_client.users.create(email_address=[email], first_name=..., ...)`
  vía `clerk-backend-api` SDK (ya disponible — verificar `vitalia/backend/pyproject.toml`)
- Receive `clerk_user_id`
- INSERT en `vitalia.user_profiles` (clerk_user_id, tenant_id, clinic_id, role)
- Generar magic sign-in link: `clerk_client.sign_in_tokens.create(user_id=...)`
- Audit log row (action="admin.user.create")
- Success message + magic link copyable

### 2.4 — `_shared/auth.py` super-admin basic auth

```python
"""Super-admin auth para admin Streamlit (scope mínimo)."""
import os
import streamlit as st
from passlib.hash import bcrypt

def require_super_admin() -> bool:
    """Returns True si user authenticated, False sino (renderiza login form)."""
    if st.session_state.get("super_admin_authenticated"):
        return True

    st.title("🔒 Vitalia Admin — Acceso super-admin")
    password = st.text_input("Password", type="password")
    if st.button("Ingresar"):
        expected_hash = os.environ.get("VITALIA_ADMIN_PASSWORD_HASH")
        if not expected_hash:
            st.error("VITALIA_ADMIN_PASSWORD_HASH no configurado en K8s secret")
            return False
        if bcrypt.verify(password, expected_hash):
            st.session_state.super_admin_authenticated = True
            st.rerun()
        else:
            st.error("Password incorrecto")
    return False
```

### 2.5 — Contract test admin

**NEW `vitalia/backend/tests/admin/test_admin_contract.py`** espejando
`nicolify/backend/tests/admin/test_admin_contract.py`:

- Cada `pages/*.py` registered en `PAGE_SPECS`.
- Cada PageSpec referencia file que existe + función `render_*()` callable.
- No slug duplicado.

## § 3 — Surface ops (Deploy)

### 3.1 — K8s secrets (verify, not create)

Verify K8s `vitalia-secrets` Secret tiene:
- `VITALIA_CLERK_PUBLISHABLE_KEY` (real, no REPLACE_ME)
- `VITALIA_CLERK_SECRET_KEY`
- `VITALIA_CLERK_WEBHOOK_SECRET`
- `VITALIA_ADMIN_PASSWORD_HASH` (NEW — bcrypt hash, generate via `python -c "from passlib.hash import bcrypt; print(bcrypt.hash('YOUR_PASSWORD'))"`)
- `CLERK_ISSUER` (frontend API URL Clerk Vitalia)

Si falta alguno → ticket T-5 actualiza `secrets.template.yaml` + emite checklist a Chris para `kubectl apply`.

### 3.2 — Admin Streamlit deploy K8s

**NEW container deploy**:
- `vitalia/deploy/Dockerfile.admin` — base python + Streamlit + COPY admin/ — entry `streamlit run src/modules/vitalia/admin/app.py --server.port=8501 --server.address=0.0.0.0`
- `vitalia/deploy/k8s/admin-deployment.yaml` — Deployment 1 replica
- `vitalia/deploy/k8s/admin-service.yaml` — Service ClusterIP port 8501
- `vitalia/deploy/k8s/admin-ingress.yaml` — Ingress host `vitalia-admin.vitalialat.com` → service:8501

(Asumimos cluster + cert-manager + DNS configurado — Chris valida).

### 3.3 — Seed fixture clinics ejecución

Post deploy:
```bash
kubectl exec -it deployment/vitalia-backend -- python scripts/seed_fixture_clinics.py --apply
```

Resultado esperado: 3 tenants insertados (aurora-dental-ar, mindful-cl, sanare-mx) o `already exists` si idempotency OK.

## § 4 — Surface tests (Playwright LIVE)

### 4.1 — Specs

**NEW `vitalia/frontend/e2e/auth/sign-in-redirect.spec.ts`:**
```typescript
import { test, expect } from "@playwright/test";

test("SC-01 — unauthenticated root redirects to /sign-in", async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });
  await expect(page).toHaveURL(/\/sign-in/);
});

test("SC-02 — public route accessible without auth", async ({ page }) => {
  await page.goto("/public/aurora-dental-ar");
  await expect(page).toHaveURL(/\/public\/aurora-dental-ar/);
  // No redirect to sign-in
});
```

**NEW `vitalia/frontend/e2e/auth/sign-in-form.spec.ts`:**
```typescript
test("SC-03 — sign-in page renders Clerk form", async ({ page }) => {
  await page.goto("/sign-in");
  await expect(page.locator('input[name="identifier"]')).toBeVisible();
  await expect(page.locator('text=pendiente T-fe-3')).toHaveCount(0);
});

test("SC-04 — sign-up page renders Clerk form", async ({ page }) => {
  await page.goto("/sign-up");
  await expect(page.locator('input[name="emailAddress"]')).toBeVisible();
});
```

**NEW `vitalia/frontend/e2e/dashboard/welcome.spec.ts`** (auth-fixture required):
```typescript
import { test, expect } from "@/e2e/auth.fixture";  // existing fixture from onboarding-wizard story

test("SC-06 — authenticated dashboard renders welcome", async ({ authenticatedPage }) => {
  await authenticatedPage.goto("/");
  await expect(authenticatedPage.locator("h1")).toContainText("Hola");
  await expect(authenticatedPage.locator('text=pendiente T-fe-3')).toHaveCount(0);
});

test("SC-07 — onboarding CTA opens wizard", async ({ authenticatedPage }) => {
  await authenticatedPage.goto("/");
  await authenticatedPage.click('text=Configurar tu clínica');
  await expect(authenticatedPage).toHaveURL(/\/onboarding\/wizard/);
});
```

**NEW `vitalia/frontend/e2e/admin/tenants-users.spec.ts`** (super-admin separate auth):
```typescript
test.use({ baseURL: "https://vitalia-admin.vitalialat.com" });

test("SC-08 — create tenant via admin", async ({ page }) => {
  await page.goto("/");
  await page.fill('input[type="password"]', process.env.VITALIA_ADMIN_PASSWORD!);
  await page.click('button:has-text("Ingresar")');
  await page.click('text=Tenants');
  await page.fill('input[aria-label="Clinic name"]', "Test Clínica Demo");
  // ... fill all fields
  await page.click('button:has-text("Crear tenant")');
  await expect(page.locator('text=Tenant creado')).toBeVisible();
});

test("SC-09 — create user via admin", async ({ page }) => {
  // ... idem flow Usuarios
});
```

### 4.2 — Clerk testing token

Auth fixture `vitalia/frontend/e2e/auth.fixture.ts` ya existe (from
onboarding-wizard story). Reusar. Requires `CLERK_TESTING_TOKEN` env var
(Chris debe generar en Clerk dashboard Vitalia → Settings → Testing).

### 4.3 — Run command

```bash
cd vitalia/frontend && \
  E2E_BASE_URL=https://dev-app.vitalialat.com \
  CLERK_TESTING_TOKEN=$CLERK_TESTING_TOKEN_VITALIA \
  VITALIA_ADMIN_PASSWORD=$VITALIA_ADMIN_PASSWORD \
  npx playwright test --project=smoke --grep "vitalia-auth-base-functional"
```

## § 5 — Cross-cutting

- **No engine modifications** (`core/luana-core-*/` read-only).
- **No cross-brand mirror** (admin pattern brand-aislado per `.claude/rules/admin-panel.md`).
- **HIPAA-lite**: admin audit_log obligatorio (SC-08, SC-09).
- **Tenant isolation**: UUIDv5 determinista (no random UUID).
- **Spanish neutro**: textos UI sin voseo.

## § 6 — Files inventory

| File | Action | Surface | Owner ticket |
|---|---|---|---|
| `vitalia/frontend/src/middleware.ts` | NEW | FE | T-1 |
| `vitalia/frontend/src/app/(auth)/sign-in/page.tsx` | EDIT | FE | T-2 |
| `vitalia/frontend/src/app/(auth)/sign-up/page.tsx` | EDIT | FE | T-2 |
| `vitalia/frontend/src/app/onboarding/step-{1,2,3}/page.tsx` | DELETE | FE | T-2 |
| `vitalia/frontend/src/app/onboarding/step-{1,2,3}/` (dirs) | DELETE | FE | T-2 |
| `vitalia/frontend/src/app/(dashboard)/page.tsx` | EDIT | FE | T-3 |
| `vitalia/frontend/src/app/(dashboard)/layout.tsx` | NEW (if absent) | FE | T-3 |
| `vitalia/frontend/src/features/dashboard/**` | NEW | FE | T-3 |
| `vitalia/backend/src/modules/vitalia/admin/**` | NEW (7 files) | BE | T-4 |
| `vitalia/backend/tests/admin/test_admin_contract.py` | NEW | BE tests | T-4 |
| `vitalia/backend/pyproject.toml` | EDIT (add streamlit + passlib + clerk-backend-api) | BE deps | T-4 |
| `vitalia/deploy/Dockerfile.admin` | NEW | ops | T-5 |
| `vitalia/deploy/k8s/admin-{deployment,service,ingress}.yaml` | NEW | ops | T-5 |
| `vitalia/deploy/k8s/secrets.template.yaml` | EDIT (add VITALIA_ADMIN_PASSWORD_HASH) | ops | T-5 |
| `vitalia/frontend/e2e/auth/sign-{in,up}-{redirect,form}.spec.ts` | NEW | tests | T-6 |
| `vitalia/frontend/e2e/dashboard/welcome.spec.ts` | NEW | tests | T-6 |
| `vitalia/frontend/e2e/admin/tenants-users.spec.ts` | NEW | tests | T-6 |

**Total estimated:** ~20 file changes (12 NEW + 7 EDIT + 4 DELETE).

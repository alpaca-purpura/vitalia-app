# T-BE-7 — R2 provisioning prep (Chris manual action gate)

**Surface:** backend-ops · **Owner:** orchestrator (trivial docs, no code) · **State:** pushed (doc-only)
**Depends on:** T-BE-6 (assets proxy upload — DONE, commit be916f1c)

## What code already handles (T-BE-6, DONE)
- `POST /api/v1/vitalia/clinics/assets/upload` proxy router consuming `luana_core_assets.AssetsService.upload_asset`.
- Tests run with `LocalStorageStrategy` (no live R2 needed for build/audit/E2E-mocked).

## Chris manual action required (unblocks LIVE prod avatar/credential upload)
The avatar + bio-attachment flow works end-to-end against **local storage** today. To enable **live R2** in dev/staging/prod, Chris must:

1. **Generate R2 S3 credentials** — Cloudflare dashboard → R2 → *Manage R2 API Tokens* → **S3 credentials** (the `cfat_…` token already shared is a CF API token for wrangler/provisioning, **NOT** a boto3 S3 key).
2. **Create bucket** `vitalia-assets` (+ optional `vitalia-assets-public` for landing avatars).
3. **CORS** on the bucket allowing `POST`/`PUT` from the frontend origin (`http://localhost:3002` dev; prod domain later).
4. **Load env vars** into `vitalia/.env.dev` (gitignored — NEVER commit):
   - `ASSETS_R2_ENDPOINT_URL=https://298e02eb64fc6d67d4f7737f1c48cab6.r2.cloudflarestorage.com`
   - `ASSETS_R2_ACCESS_KEY_ID=<S3 access key>`
   - `ASSETS_R2_SECRET_ACCESS_KEY=<S3 secret>`
   - `ASSETS_R2_BUCKET=vitalia-assets`
   - `ASSETS_R2_REGION=auto`
5. **Rotate the `cfat_…` token** that was pasted in chat plaintext (security hygiene).

## Verification (after Chris loads creds)
`curl -F file=@avatar.jpg -F kind=avatar http://127.0.0.1:8002/api/v1/vitalia/clinics/assets/upload -H "X-Tenant-ID: <tid>"` → `{key, url}` with a real R2 object URL.

## Status
- **Code/tests:** DONE (T-BE-6, mocked storage) — does NOT block audit or merge.
- **Live R2 creds:** ⏸ Chris manual action — gate flagged for post-merge ops.

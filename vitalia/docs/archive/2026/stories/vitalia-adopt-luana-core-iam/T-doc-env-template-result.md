# T-doc-env-template — Result

**Ticket:** T-doc-env-template
**Title:** Comment en vitalia/.env.dev.template re single-quote requirement + VITALIA_INTERNAL_API_TOKEN var
**State:** DONE
**Builder:** builder-backend (Sonnet 4.6)
**Session:** 2026-05-19 autonomous E2E

## Summary

Added documentation comments in `vitalia/.env.dev.template` clarifying:
1. Single-quote requirement for values containing `$`, `!`, spaces (shell interpretation prevention)
2. `VITALIA_INTERNAL_API_TOKEN` variable for Playwright admin-smoke DB verification
3. `VITALIA_ADMIN_PASSWORD` variable for Streamlit admin panel access

## Files touched

- `vitalia/.env.dev.template` — Added `VITALIA_ADMIN_PASSWORD` + `VITALIA_INTERNAL_API_TOKEN` entries with comments

## Validators

- ✅ `val-doc-1`: env.dev.template has VITALIA_ADMIN_PASSWORD entry with comment
- ✅ `val-doc-2`: env.dev.template has VITALIA_INTERNAL_API_TOKEN entry with comment
- ✅ No secrets hardcoded (all values are placeholders)

## Notes

`VITALIA_ADMIN_PASSWORD` is consumed by `admin_auth.fixture.ts` — test SKIPS if absent (never fails CI).
`VITALIA_INTERNAL_API_TOKEN` is consumed by `utils/db_verify.ts` — test SKIPS if absent.
Both values are injected via env var at E2E run time.

> ⚠️ v0.1.0 one-time — superseded by docs/process/release-protocol.md

# Releases — Luana Platform

## Release v0.1.0 (2026-05-12) — first publication

**Luana Platform v0.1.0 — first production-grade alpha release.**

Stories 1-9 complete. 26 packages published to GitHub Packages (private).
Cross-package SemVer cement. See [CHANGELOG.md](../CHANGELOG.md) for full story summary.

### Procedure to publish v0.1.0 (manual first-tag)

release-please takes over for v0.2.0+. For v0.1.0, the first tag is manual:

```bash
# 1. Verify all 26 packages are at 0.1.0 (no -alpha)
grep -r 'version = "0.1.0"' core/*/pyproject.toml | wc -l  # expect 26

# 2. Verify tests pass
uv run pytest core/ -q --tb=line --ignore=core/luana-core-sales-agent
uv run pytest tests/architecture/ -q

# 3. Create and push the tag (triggers release.yml workflow)
git tag v0.1.0
git push origin v0.1.0

# 4. Monitor the workflow
gh run list --workflow=release.yml --limit=3

# 5. Verify packages published
gh api /orgs/alpacapurpura/packages --jq '.[].name' | grep luana
```

### Post-tag verification

```bash
# Verify GitHub release created
gh release view v0.1.0

# Run smoke test against published packages
UV_PUBLISH_TOKEN="$(gh auth token)" NODE_AUTH_TOKEN="$(gh auth token)" \
  bash scripts/publish_smoke_test.sh 0.1.0
```

---

## Token setup (GH Packages auth)

Two authentication paths for publishing to GitHub Packages:

### Path A: `GITHUB_TOKEN` (default CI)

Auto-injected in GitHub Actions workflows. Requires the workflow to have `permissions.packages: write`.
The `release.yml` workflow already configures this permission.

**HALT criterion — V-X-1:** If `GITHUB_TOKEN` lacks `write:packages` scope AND no `GH_PACKAGES_TOKEN`
is configured → workflow exits with explicit error:
```
::error::No GH Packages token. Set GH_PACKAGES_TOKEN secret OR ensure GITHUB_TOKEN has
write:packages scope. See docs/process/release-procedure-v0.1.0.md §Token-setup
```
This requires Chris (org admin) to configure token permissions at the org level.
**This is not autonomously resolvable. Escalate to org admin.**

### Path B: `GH_PACKAGES_TOKEN` (custom PAT — recommended for long-lived automation)

```bash
# Create PAT with read:packages + write:packages scope
# Settings → Developer settings → Personal access tokens → Fine-grained tokens

# Set as repository secret
gh secret set GH_PACKAGES_TOKEN --body "ghp_XXXX"

# Verify secret is set
gh secret list
```

For local development / smoke tests:
```bash
export GH_PACKAGES_TOKEN=$(gh auth token)
```

---

## SemVer F1-F6 cement

All commits from v0.1.0 onwards follow [Conventional Commits](https://www.conventionalcommits.org/).
release-please derives the next version from commit types (F3→patch, F2→minor, F1/F5→major).

| Rule | Trigger | Version bump | Commit example |
|---|---|---|---|
| F1 | EP signature change (breaking API) | **MAJOR** | `feat!: rename EP-3 handler signature` + `BREAKING CHANGE: ...` footer |
| F2 | New EP added OR additive BrandContext field | **MINOR** | `feat(extension-sdk): add EP-19 scheduling hook` |
| F3 | Bug fix without API change | **PATCH** | `fix(copilot): correct phase F3 retry logic` |
| F4 | BrandContext optional field with default | **MINOR** | `feat(brand-studio): add optional brand_tagline field` |
| F5 | BrandContext field removal | **MAJOR** | `feat!: remove deprecated brand_voice_tone field` + `BREAKING CHANGE:` |
| F6 | Default flag flip with side-effect | **MAJOR** | `feat!: flip USE_OUTBOX_PATTERN default True→False` + body audit section |

Enforcement layers:
1. release-please conventional-commits parser (auto from v0.2.0+)
2. Pre-commit `commitlint` hook (Story 10+ enforcement — `commitlint.config.cjs` seeded Story 9)
3. Auditor C4 manual review on PRs
4. This document (SSoT for F1-F6 rules)

---

## Manual first-tag procedure (v0.1.0 special case)

release-please requires a Conventional Commits history to auto-derive the next version.
The v0.0.x-alpha period used ad-hoc commit messages (pre-SDD), so v0.1.0 uses a manual tag.

From v0.2.0 onwards, release-please will automatically open a PR with version bumps when
`feat:` or `fix:` commits land on `main`.

```bash
# Manual tag command (run once, after all 26 packages are at 0.1.0)
git tag v0.1.0
git push origin v0.1.0
# This triggers .github/workflows/release.yml automatically
```

---

## Rollback procedure

If `release.yml` fails after partial publish (some Python packages published, TS not yet):

```bash
# Interactive rollback script (requires gh CLI + write:packages)
bash scripts/rollback_partial_publish.sh 0.1.0
```

The script:
1. Lists all version entries for each package in GH Packages registry
2. Deletes the matching version entries (Python + TypeScript)
3. Prints next steps (delete tag → fix issue → re-tag)

**Manual rollback commands** (if script unavailable):
```bash
# Delete a specific Python package version
gh api -X DELETE /orgs/alpacapurpura/packages/pypi/luana-core-platform/versions/VERSION_ID

# Delete a specific TS package version
gh api -X DELETE /orgs/alpacapurpura/packages/npm/api-client/versions/VERSION_ID
```

---

## Halt criteria (Scenario 5 + 6)

**Scenario 5 — GH Packages auth missing (HALT criterion V-X-1):**
- Trigger: `GITHUB_TOKEN` lacks `write:packages` AND `GH_PACKAGES_TOKEN` not set
- Detection: `publish-python` job exits with `::error::No GH Packages token.`
- Resolution: **ESCALATE to Chris (org admin) for token setup** — NOT autonomously resolvable
- Workaround: none (can't publish without write:packages permission)

**Scenario 6 — release-please config conflict:**
- Trigger: release-please fails to parse `release-please-config.json` (plugin version mismatch)
- Detection: `release-please` GitHub Action exits with config parse error
- Fallback: Switch to `changesets` (TS) + custom Python bash publish loop per `03-arch.md §2`
- Document fallback decision in this file under "## Release v0.2.0 — fallback path"

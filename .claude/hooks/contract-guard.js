#!/usr/bin/env node

// tier: hybrid · core kernel = the PostToolUse SSoT-guard DISPATCH (regex-match an edited
//       path → emit a terse regen/test reminder) · project half = the RULES array below
//       (engine/brand paths + regen commands + messages).
//
// W5b decision (2026-06-09 · charter §3): the RULES are NOT seamed to project.config.yaml.
// Rationale (maintainability > forced DIP): node has no built-in YAML parser, so reading the
// seam here would mean execSync→python on EVERY Write/Edit (latency + a hard python dep on a
// JS hook) OR a second store; and the RULES' shape (per-rule regex + multi-line message) is
// richer than the ratified `domain_modules.contract_guard_watch` ({name,regen}) slot. The
// RULES are PROJECT config that lives in this PROJECT hook — a new product ships its own
// contract-guard.js RULES (the portable IP is the dispatch loop, not luana's catalog paths).
// (Lift the dispatch kernel to core only when a 2nd product needs it — YAGNI now.)
//
// PostToolUse hook. Reminds Claude when editing SSoT files (contracts,
// catalogs, registries) what regen/test command to run. Output is
// intentionally terse (≤2 lines per match) to minimize token cost.
// Silent on non-match.
//
// Multibrand (refactor 2026-05-15 post multibrand reorg):
// Cada regla distingue ENGINE (core/luana-core-*/src/luana_core_*/) de
// BRAND EXTENSION ({brand}/backend/src/modules/{brand}/) y legacy
// (backend/src/modules/). El mensaje hint cambia según dónde vive el file:
//   - ENGINE: afecta TODAS las brands consumidoras → run en TODAS.
//   - BRAND: scoped a esa brand → run scoped.
//   - LEGACY: heredado pre-multibrand → mantenido por backcompat.
//
// Brands activas (hardcoded por ahora): vitalia, nicolify, comunify, lupulo.
// 6 pendientes bootstrap: saasora, inmoflow, retailly, fixia, guestly, fitflow.

const RULES = [
  // ──────────────────────────────────────────────────────────────
  // 1. ETL contract — analytics providers / etl / etl_service / workers
  // ──────────────────────────────────────────────────────────────
  {
    name: 'etl-contract-engine',
    patterns: [
      /^core\/luana-core-analytics-engine\/src\/luana_core_analytics_engine\/infrastructure\/providers\/[^/]+\.py$/,
      /^core\/luana-core-analytics-engine\/src\/luana_core_analytics_engine\/infrastructure\/etl\/[^/]+\.py$/,
      /^core\/luana-core-analytics-engine\/src\/luana_core_analytics_engine\/application\/services\/etl_service\.py$/,
      /^core\/luana-core-analytics-engine\/src\/luana_core_analytics_engine\/workers\/(scheduler|tasks)\.py$/,
      /^core\/luana-core-analytics-engine\/src\/luana_core_analytics_engine\/domain\/extraction_contract\.py$/,
    ],
    msg: 'ETL SSoT (ENGINE) touched — afecta TODAS las brands consumidoras. Run: `make extraction-contract && .venv/bin/pytest core/luana-core-analytics-engine/tests/architecture/test_extraction_contract.py -x -q` (rule: .claude/rules/etl-extraction-contract.md)',
  },
  {
    name: 'etl-contract-brand',
    patterns: [
      /^[a-z][a-z0-9_-]*\/backend\/src\/modules\/[a-z][a-z0-9_-]*\/analytics\/(providers|etl)\/[^/]+\.py$/,
      /^[a-z][a-z0-9_-]*\/backend\/src\/modules\/[a-z][a-z0-9_-]*\/analytics\/(application\/services\/etl_service|workers\/(scheduler|tasks))\.py$/,
    ],
    msg: 'ETL SSoT (BRAND extension) touched — brand-specific. Run: `make extraction-contract-{brand}` (si soporta) o scoped pytest a esa brand backend (rule: .claude/rules/etl-extraction-contract.md)',
  },
  {
    name: 'etl-contract-legacy',
    patterns: [
      /^backend\/src\/modules\/analytics\/infrastructure\/providers\/[^/]+\.py$/,
      /^backend\/src\/modules\/analytics\/infrastructure\/etl\/[^/]+\.py$/,
      /^backend\/src\/modules\/analytics\/application\/services\/etl_service\.py$/,
      /^backend\/src\/modules\/analytics\/workers\/(scheduler|tasks)\.py$/,
      /^backend\/src\/modules\/analytics\/domain\/extraction_contract\.py$/,
      /^backend\/src\/workers\/settings\.py$/,
    ],
    msg: 'ETL SSoT (LEGACY backend/) touched. Run: `make extraction-contract && cd backend && .venv/bin/pytest tests/architecture/test_extraction_contract.py -x -q` (rule: .claude/rules/etl-extraction-contract.md)',
  },

  // ──────────────────────────────────────────────────────────────
  // 2. Metric catalog — analytics/domain/metric_catalog.py
  // ──────────────────────────────────────────────────────────────
  {
    name: 'metric-catalog-engine',
    patterns: [
      /^core\/luana-core-analytics-engine\/src\/luana_core_analytics_engine\/domain\/metric_catalog\.py$/,
    ],
    msg: 'metric_catalog.py (ENGINE) edited — afecta TODAS las brands. Run: `.venv/bin/pytest core/luana-core-analytics-engine/tests/architecture/test_extraction_contract.py -x -q` (verify catalog↔contract alignment).',
  },
  {
    name: 'metric-catalog-brand',
    patterns: [
      /^[a-z][a-z0-9_-]*\/backend\/src\/modules\/[a-z][a-z0-9_-]*\/analytics\/metric_catalog_extension\.py$/,
    ],
    msg: 'metric_catalog_extension.py (BRAND) edited — scoped. Verify brand-specific metric catalog alignment vs engine contract.',
  },
  {
    name: 'metric-catalog-legacy',
    patterns: [/^backend\/src\/modules\/analytics\/domain\/metric_catalog\.py$/],
    msg: 'metric_catalog.py (LEGACY) edited. Run: `cd backend && .venv/bin/pytest tests/architecture/test_extraction_contract.py -x -q` (verify catalog↔contract alignment).',
  },

  // ──────────────────────────────────────────────────────────────
  // 3. Offer catalogs — archetype/value_level/format + expert_business_type
  // ──────────────────────────────────────────────────────────────
  {
    name: 'offer-catalogs-engine',
    patterns: [
      /^core\/luana-core-offer-studio\/src\/luana_core_offer_studio\/domain\/(archetype|format|offer_type_preset|section|value_level|variant_structure)_catalog\.py$/,
      /^core\/luana-core-extension-sdk\/src\/luana_core_extension_sdk\/.*\/expert_business_type\.py$/,
      /^core\/luana-core-platform\/src\/luana_core_platform\/.*\/expert_business_type\.py$/,
    ],
    msg: 'Offer catalog SSoT (ENGINE) touched — afecta TODAS las brands (vitalia, nicolify, comunify, lupulo + futuras). Bump _CATALOG_VERSION en matching API + run arch tests both stacks PER cada brand consumidora. Run: `.venv/bin/pytest core/luana-core-offer-studio/tests/architecture/ -x -q` + per-brand `cd {brand}/frontend && npx vitest run src/__tests__/architecture/test-no-catalog-duplicates.test.ts` (rule: .claude/rules/offer-catalogs.md)',
  },
  {
    name: 'offer-catalogs-legacy',
    patterns: [
      /^backend\/src\/modules\/offer\/domain\/(archetype|value_level|format)_catalog\.py$/,
      /^backend\/src\/shared\/domain\/expert_business_type\.py$/,
    ],
    msg: 'Offer catalog SSoT (LEGACY) touched. Bump _CATALOG_VERSION en matching API + run: `cd backend && .venv/bin/pytest tests/architecture/ -x -q` AND `cd frontend && npx vitest run src/__tests__/architecture/test-no-catalog-duplicates.test.ts` (rule: .claude/rules/offer-catalogs.md)',
  },

  // ──────────────────────────────────────────────────────────────
  // 4. Channel registry — analytics/application/services/channel_registry.py
  // ──────────────────────────────────────────────────────────────
  {
    name: 'channel-registry-engine',
    patterns: [
      /^core\/luana-core-analytics-engine\/src\/luana_core_analytics_engine\/application\/services\/channel_registry\.py$/,
    ],
    msg: 'channel_registry.py (ENGINE) edited — afecta TODAS las brands. Do NOT duplicate STAGE_CHANNEL_MAP / PROVIDER_TO_CHANNEL_TYPES en stage services per-brand (rule: .claude/rules/analytics-metrics.md).',
  },
  {
    name: 'channel-registry-legacy',
    patterns: [/^backend\/src\/modules\/analytics\/application\/services\/channel_registry\.py$/],
    msg: 'channel_registry.py (LEGACY) edited. Do NOT duplicate STAGE_CHANNEL_MAP / PROVIDER_TO_CHANNEL_TYPES in stage services (rule: .claude/rules/analytics-metrics.md).',
  },

  // ──────────────────────────────────────────────────────────────
  // 5. Copilot module registry — copilot/domain/module_registry.py
  // ──────────────────────────────────────────────────────────────
  {
    name: 'copilot-registry-engine',
    patterns: [
      /^core\/luana-core-copilot\/src\/luana_core_copilot\/domain\/module_registry\.py$/,
    ],
    msg: 'module_registry.py (ENGINE) edited — afecta TODAS las brands. New modules need ModuleDescriptor entry. Per-brand copilot extensions registran sus modules via Extension SDK (rule: .claude/rules/copilot-resilience.md).',
  },
  {
    name: 'copilot-registry-legacy',
    patterns: [/^backend\/src\/modules\/copilot\/domain\/module_registry\.py$/],
    msg: 'module_registry.py (LEGACY) edited. New modules need a ModuleDescriptor entry (rule: .claude/rules/copilot-resilience.md).',
  },
];

function readStdin() {
  return new Promise((resolve) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => { data += chunk; });
    process.stdin.on('end', () => resolve(data));
    process.stdin.on('error', () => resolve(''));
    // If no stdin (run manually), don't hang.
    setTimeout(() => resolve(data), 200);
  });
}

async function main() {
  const raw = await readStdin();
  if (!raw) process.exit(0);

  let data;
  try { data = JSON.parse(raw); } catch { process.exit(0); }

  if (!['Write', 'Edit', 'MultiEdit'].includes(data.tool_name)) process.exit(0);

  const filePath = data.tool_input?.file_path || data.tool_input?.path || '';
  if (!filePath) process.exit(0);

  // Normalize to repo-relative path so the multibrand patterns (anchored with ^)
  // match consistently whether the hook receives an absolute or relative file_path.
  // WORKTREE-AGNOSTIC: must work from the main hub (luana-platform) AND from every
  // per-worktree clone (luana-vitalia, luana-nicolify, luana-comunify, ...). Prefer
  // CLAUDE_PROJECT_DIR (the actual project root); fall back to stripping up to and
  // including the luana workspace-root dir (last occurrence).
  let relPath = filePath;
  const projDir = process.env.CLAUDE_PROJECT_DIR;
  if (projDir && relPath.startsWith(projDir)) {
    relPath = relPath.slice(projDir.length).replace(/^\/+/, '');
  } else {
    const re = /\/luana-[a-z0-9-]+\//g;
    let lastEnd = -1, m;
    while ((m = re.exec(relPath)) !== null) lastEnd = m.index + m[0].length;
    if (lastEnd !== -1) {
      relPath = relPath.slice(lastEnd);
    } else if (relPath.startsWith('/')) {
      // Path not under any recognizable luana root — strip leading slash so
      // anchored patterns can still match on the tail (e.g. core/luana-core-X/...).
      relPath = relPath.replace(/^\/+/, '');
    }
  }

  for (const rule of RULES) {
    if (rule.patterns.some((p) => p.test(relPath))) {
      console.error(`[contract-guard:${rule.name}] ${rule.msg}`);
      process.exit(0);
    }
  }

  process.exit(0);
}

main();

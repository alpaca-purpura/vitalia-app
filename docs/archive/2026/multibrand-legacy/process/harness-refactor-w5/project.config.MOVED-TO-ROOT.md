# ⤴ project.config.PROPOSED.yaml — MOVED TO ROOT (W5b · 2026-06-09)

The W5a ratified seam schema (`project.config.PROPOSED.yaml`) was **promoted to the live root file** in W5b:

```
docs/process/harness-refactor-w5/project.config.PROPOSED.yaml  →  project.config.yaml   (repo root)
```

It is now the single live store read by `scripts/harness_config.py` (the loader) + the cockpit `lib/project-config.ts` + the markdown `{slot}` convention. **There is no second store** — this tombstone exists only so the W5a artifact trail (`W5-OUTPUT.md` §8 pointer) resolves; the file's design history lives in git (`git log --follow project.config.yaml`).

- **Live store:** `project.config.yaml` (repo root)
- **Loader:** `scripts/harness_config.py` (`<slot>` / `--doctor` / `from harness_config import load`)
- **W5b output:** `W5-OUTPUT.md` § W5b

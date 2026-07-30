#!/usr/bin/env python3
"""Generate code-to-cap index by grepping `# cap:` / `// cap:` headers.

Produces ``{brand}/docs/product/capabilities/_code-index.json`` (gitignored R3 v2)
with:
  - code_to_cap: file → cap_id (or list if multi-cap)
  - cap_to_files: cap_id → list of files
  - orphans: list of files marked `# cap: __orphan__`
  - shared: list of files marked `# cap: __shared__`
  - multi_cap_files: files with >1 cap declared
  - summary stats

Header format (per docs/process/lifecycle.md — atomics killed 2026-05-28):
  Python: `# cap: module.slug` OR `# cap: [a.b, c.d]`
  TS/TSX: `// cap: module.slug` OR `// cap: [a.b, c.d]`

Special markers:
  __orphan__   archivo sin cap owner principal (revisar refactor)
  __shared__   archivo cross-cap consumer multi-feature
  __skip__     archivo intencionalmente sin header

Usage:
  python3 scripts/generate_code_to_cap_index.py --brand vitalia [--out PATH] [--verbose] [--strict]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Resolver único (HB-51 · Capa 5): unifica las DOS convenciones de header
# (`inbox.adrian-inbox` cap_id + `adrian.inbox` functional_area) → mismo cap_id canónico.
_RC_SPEC = importlib.util.spec_from_file_location("resolve_cap", Path(__file__).resolve().parent / "resolve_cap.py")
resolve_cap = importlib.util.module_from_spec(_RC_SPEC)  # type: ignore[arg-type]
_RC_SPEC.loader.exec_module(resolve_cap)  # type: ignore[union-attr]

# Regex para parsear `# cap:` / `// cap:` headers
HEADER_PY = re.compile(r"^\s*#\s*cap:\s*(.+?)\s*$", re.MULTILINE)
HEADER_TS = re.compile(r"^\s*//\s*cap:\s*(.+?)\s*$", re.MULTILINE)

STORY_PY = re.compile(r"^\s*#\s*story-origin:\s*(.+?)\s*$", re.MULTILINE)
STORY_TS = re.compile(r"^\s*//\s*story-origin:\s*(.+?)\s*$", re.MULTILINE)


def parse_cap_list(raw: str) -> list[str]:
    """Parse cap field which can be 'a.b', '[a.b, c.d]', or special marker."""
    raw = raw.strip()
    if not raw:
        return []
    # Special markers
    if raw in {"__orphan__", "__shared__", "__skip__", "TBD"}:
        return [raw]
    # Multi-cap array notation
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1]
        return [c.strip() for c in inner.split(",") if c.strip()]
    # Single cap
    return [raw]


def scan_file(path: Path) -> dict[str, Any]:
    """Scan a single file for header. Returns dict with caps/story-origin."""
    try:
        # Only read first 20 lines for performance (header should be at top)
        with path.open(encoding="utf-8") as fh:
            head = "".join(fh.readline() for _ in range(20))
    except (OSError, UnicodeDecodeError):
        return {"caps": [], "story_origin": None}

    is_py = path.suffix == ".py"
    cap_re = HEADER_PY if is_py else HEADER_TS
    story_re = STORY_PY if is_py else STORY_TS

    cap_match = cap_re.search(head)
    if not cap_match:
        return {"caps": [], "story_origin": None}

    caps = parse_cap_list(cap_match.group(1))

    story_origin = None
    story_match = story_re.search(head)
    if story_match:
        story_origin_raw = story_match.group(1).strip()
        if story_origin_raw and story_origin_raw != "TBD":
            story_origin = story_origin_raw

    return {"caps": caps, "story_origin": story_origin}


def process_brand(brand: str, workspace_root: Path, verbose: bool) -> dict[str, Any]:
    """Scan all .py/.ts/.tsx files in brand + collect headers."""
    backend_root = workspace_root / brand / "backend" / "src"
    frontend_root = workspace_root / brand / "frontend" / "src"

    scan_paths: list[Path] = []
    if backend_root.exists():
        scan_paths.extend(p for p in backend_root.rglob("*.py") if "__pycache__" not in p.parts)
    if frontend_root.exists():
        for ext in ("*.ts", "*.tsx"):
            for p in frontend_root.rglob(ext):
                # Skip test files for cleaner index
                if any(part in {"__tests__"} for part in p.parts):
                    continue
                if p.name.endswith((".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx")):
                    continue
                scan_paths.append(p)

    code_to_cap: dict[str, list[str]] = {}
    cap_to_files: dict[str, list[str]] = defaultdict(list)
    orphans: list[str] = []
    shared_files: list[str] = []
    multi_cap_files: list[dict[str, Any]] = []
    no_header: list[str] = []

    total = len(scan_paths)
    if not verbose:
        print(f"Scanning {total} archivos en {brand}...", end="", flush=True)

    for idx, path in enumerate(scan_paths):
        if not verbose and (idx + 1) % 100 == 0:
            print(".", end="", flush=True)

        rel_path = str(path.relative_to(workspace_root))
        info = scan_file(path)
        caps = info["caps"]

        if not caps:
            no_header.append(rel_path)
            continue

        code_to_cap[rel_path] = caps if len(caps) > 1 else caps[0]

        # Special markers
        if caps == ["__orphan__"]:
            orphans.append(rel_path)
            continue
        if caps == ["__shared__"]:
            shared_files.append(rel_path)
            continue
        if caps == ["__skip__"]:
            continue

        # Regular caps
        for cap in caps:
            if cap in {"__orphan__", "__shared__", "__skip__", "TBD"}:
                continue
            cap_to_files[cap].append(rel_path)

        if len(caps) > 1:
            multi_cap_files.append({"path": rel_path, "caps": caps})

        if verbose:
            print(f"  {rel_path:<80} caps={caps}")

    if not verbose:
        print()

    # Convert defaultdicts
    cap_to_files_final = {k: sorted(v) for k, v in cap_to_files.items()}

    # ── HB-51 · Capa 5: índice RESUELTO por cap_id canónico ──────────────────
    # `cap_to_files` keyea el header literal (`adrian.inbox` ≠ `inbox.adrian-inbox`).
    # `resolved_cap_to_files` keyea el cap_id CANÓNICO → ambas convenciones merge bajo el
    # mismo cap (esto es lo que el architect grepea + el cockpit consume). Los headers que
    # NO resuelven a ninguna cap caen en `unresolved_headers` (orphans · input de G1/cap-doctor).
    resolve_cap.clear_resolver_cache()
    caps_root = workspace_root / brand / "docs" / "product" / "capabilities"
    resolved_cap_to_files: dict[str, set[str]] = defaultdict(set)
    unresolved_headers: dict[str, list[str]] = defaultdict(list)
    for header, files in cap_to_files_final.items():
        canon_ids = resolve_cap.resolve_cap_ids(brand, header, root=caps_root)
        if canon_ids:
            for cid in canon_ids:
                resolved_cap_to_files[cid].update(files)
        else:
            unresolved_headers[header].extend(files)
    resolved_final = {k: sorted(v) for k, v in resolved_cap_to_files.items()}
    unresolved_final = {k: sorted(v) for k, v in unresolved_headers.items()}

    return {
        "code_to_cap": code_to_cap,
        "cap_to_files": cap_to_files_final,
        "resolved_cap_to_files": resolved_final,
        "unresolved_headers": unresolved_final,
        "orphans": sorted(orphans),
        "shared_files": sorted(shared_files),
        "multi_cap_files": multi_cap_files,
        "no_header": sorted(no_header),
        "summary": {
            "total_files_scanned": total,
            "files_with_header": len(code_to_cap),
            "files_no_header": len(no_header),
            "orphans": len(orphans),
            "shared_files": len(shared_files),
            "multi_cap_files": len(multi_cap_files),
            "caps_with_files": len(cap_to_files_final),
            "resolved_caps": len(resolved_final),
            "unresolved_headers": len(unresolved_final),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera index code↔cap por grep headers.")
    parser.add_argument("--brand", required=True)
    parser.add_argument("--out", default=None)
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 si hay archivos no-header inesperados",
    )
    parser.add_argument("--repo", default=None)
    args = parser.parse_args()

    if args.repo:
        workspace_root = Path(args.repo).resolve()
    else:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
            )
            workspace_root = Path(result.stdout.strip())
        except (subprocess.CalledProcessError, FileNotFoundError):
            workspace_root = Path.cwd()

    out_path = (
        Path(args.out).resolve()
        if args.out
        else workspace_root / args.brand / "docs" / "product" / "capabilities" / "_code-index.json"
    )

    if args.verbose:
        print(f"Workspace root : {workspace_root}")
        print(f"Brand          : {args.brand}")
        print(f"Output         : {out_path}")
        print()

    result_data = process_brand(args.brand, workspace_root, args.verbose)

    now_iso = datetime.now(tz=timezone.utc).astimezone().isoformat(timespec="seconds")
    output: dict[str, Any] = {
        "generated_at": now_iso,
        "brand": args.brand,
        **result_data,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(output, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    s = result_data["summary"]
    print(
        f"Completed: {s['total_files_scanned']} files · "
        f"with_header={s['files_with_header']} · "
        f"no_header={s['files_no_header']} · "
        f"caps={s['caps_with_files']} · "
        f"orphans={s['orphans']} · "
        f"shared={s['shared_files']} · "
        f"multi={s['multi_cap_files']}"
    )
    print(f"Saved to: {out_path}")

    if args.strict and s["files_no_header"] > 0:
        print(f"[STRICT] {s['files_no_header']} archivos sin header", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

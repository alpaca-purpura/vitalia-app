# test-brand v0.0.8-alpha

Test brand: SDK smoke validation, NOT a deployable product.

## Purpose

`apps/test-brand` is a minimal FastAPI application that exercises the `luana-core-extension-sdk`
smoke pack — registering all 18 extension points (5 executable + 13 signature-only stubs)
and validating CC-1..CC-5 cross-cutting policies at startup.

## Usage

```bash
cd ~/luana-platform
uv run pytest apps/test-brand/tests/ -v
```

## Structure

```
apps/test-brand/
├── pyproject.toml                # workspace member, version 0.0.8-alpha
├── src/test_brand/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app + lifespan event (CC-3 lock)
│   └── extensions.py            # register_all — 18 handlers (5 executable + 13 stubs)
└── tests/
    ├── __init__.py
    └── test_sdk_smoke.py         # 10 smoke scenarios D1-D3 + C1-C5 + E1
```

## Extension points registered

- **EP-1..EP-5 executable**: real handlers returning typed results
- **EP-6..EP-18 stubs**: registration succeeds; semantic dispatch raises `NotImplementedError`

All names use `test-brand.` prefix (CC-4 namespace enforcement).

See `docs/architecture/luana-platform/extension-points.md` for full recipe and per-vertical examples.

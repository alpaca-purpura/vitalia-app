# luana-core-extension-sdk v0.0.8-alpha

18 extension points formalized contract for the Luana platform.

- **EP-1..EP-5 critical:** EXECUTABLE (registry stores + dispatch helpers callable from core)
- **EP-6..EP-18 backlog:** SIGNATURE-ONLY (registry stores; dispatch raises NotImplementedError)
- **Cross-cutting policies CC-1..CC-5:** runtime enforcement (startup-only, namespaced obligatorio, immutable)

See `docs/architecture/luana-platform/extension-points.md` for usage examples + recipe.

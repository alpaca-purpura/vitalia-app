<!-- voseo-allowed: doc de proceso interno (guion de demo), no user-facing -->
# Demo Script — estabilizar-harness-e2e-lisa-marca

> **Critical Rule #37 §5 · `definition-of-done-live-verify.md`.** Guion de **product demo** para que Chris
> valide manualmente la story contra el MISMO `dev-app` que usó el dev. En lenguaje de usuario.
> Esta story es un **bugfix + harness** cuya parte funcional user-reachable es **la configuración de marca
> de Lisa** (nombre, colores, tipografía, logo): los 4 guardados que el de-mock destapó como rotos contra el
> backend real + el logo ahora con storage real en R2.

## SETUP (estado inicial)

- **Entorno:** `make dev-app-vitalia` → `https://dev-app.vitalialat.com` (stack UP, backend recreado con
  `STORAGE_PROVIDER=R2` + creds del bucket `vitalia-assets-dev`).
- **Usuario de prueba:** `dr.demo@vitalialat.com` (rol owner del tenant Sanaré · creds en `vitalia/.env.dev` →
  `DEV_APP_TEST_*`).
- **Dónde:** tras login → **Lisa → Marca** (la pestaña de identidad de marca).
- **Tip:** después de cada guardado, **recargá con F5** y confirmá que el valor persiste (esa es la prueba de
  que se guardó de verdad — no solo en pantalla).

## HAPPY PATH (1 acción = 1 paso · resultado esperado inline)

1. Entrá a **Lisa → Marca → Identidad** → **esperado:** la pantalla carga (sin burbuja roja de error, sin
   "No se pudo cargar"); el nombre actual de la clínica aparece en el campo.
2. Cambiá el **nombre de la clínica** (ej. "Clínica Sanaré Centro") → **esperado:** badge "guardado" (autosave);
   **al recargar (F5) el nombre nuevo persiste**.
3. Cambiá el **color primario** de la marca (ej. a un verde) → **esperado:** el color se aplica y **persiste tras F5**
   (el selector NO revierte al valor viejo — ese era el bug 422 que arreglamos).
4. Cambiá la **tipografía** (heading o body, ej. de Inter a otra) → **esperado:** se aplica y **persiste tras F5**.
5. **Subí un logo** (una imagen PNG/JPG/WebP < 5 MB) → **esperado:** el logo aparece en la vista **y al recargar
   (F5) sigue ahí** (ahora se guarda de verdad en almacenamiento R2; antes daba "ok" pero la imagen se perdía).

## EDGE CASES (reglas de negocio negativas / límite)

- En **Voz/Tono**, escribí una **frase prohibida** de la lista → **esperado:** aparece una **advertencia suave**
  que **NO bloquea** el guardado (es un aviso, no un error).
- Intentá subir un **logo que supere el tamaño máximo** (> 5 MB) → **esperado:** se **rechaza antes de subir**
  con un mensaje claro de límite de tamaño.

## TEARDOWN (si aplica)

- Revertí el nombre / color / tipografía / logo de prueba a los valores que tenía la clínica antes de la demo
  (opcional — es el tenant de prueba Sanaré).

---

## Notas para Chris (contexto técnico — NO parte del guion)

- **Lo que esta story arregló de verdad** (todo verificado live por mí contra dev-app, no "GET 200"):
  - El harness e2e de lisa-marca dejó de **mockear el backend** (era verde-teatro) → ahora corre contra el
    backend real con asserts web-first. Suite **94% determinista ×3**; los 2 residuales son throttle del Clerk
    dev (infra externa, no bug) → aceptado con retries + harness-story aparte (tu decisión de hoy).
  - 4 guardados que estaban **rotos contra el backend real** y el mock ocultaba: nombre (keystone), colores,
    tipografía, logo. Más 2 sub-bugs de headers de auth (audit actor real + prohibited-phrases).
  - **Logo R2 (decisión de hoy):** dejó de ser stub. Ahora `upload_logo` consume el módulo engine
    `luana-core-assets` (no se recreó nada) → guarda los bytes reales en el bucket R2 `vitalia-assets-dev` y
    devuelve una URL pública renderable. Verificado: subida → bucket → `GET <url> → 200 image/png`.
- **Lo único que falta para `done`:** tu **sign-off** de esta demo (gate rule #37). No marco `done` sin él.

## Resultado (lo firma Chris)

```yaml
demo_signoff:
  signed_by: Chris
  date: 2026-06-03
  result: APPROVED
  notes: >-
    Re-demo live contra dev-app OK tras varias rondas que cazaron bugs reales (logo 3 capas:
    FK 500 + persist-location + next/image host · autosave-on-load · badge nivel-página ·
    preview de tipografía cargaba las fuentes · placement de "Eliminar logo"). Chris confirmó
    "recargué y todo bien". Notas no-bloqueantes: (1) avatares de doctores (lisa-doctores) tienen
    el mismo 500 latente del AssetsService → flagged para /pm-vitalia (otra story). (2) R2 secret
    vive solo en vitalia/.env.dev (gitignored). (3) STORAGE_PROVIDER=R2 es global (avatares también).
    (4) prod conviene self-hostear fuentes (next/font) en vez del CDN de Google.
  open_items: []
```

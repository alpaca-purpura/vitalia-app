---
title: "Dynamic-SSR shells break the first-Tab starting point in E2E (skip-link unreachable)"
date: 2026-05-28
brand: vitalia
slug: dynamic-ssr-tab-start-anchor
promotable: candidate
applies_to_other_brands_potentially: [nicolify, comunify, lupulo, saasora, fitflow]
target_core_package: "n/a — E2E test pattern (POM helper), not runtime code"
type: technical
ratified_by: chris
tags: [e2e, playwright, a11y, wcag, skip-link, focus-order, dynamic-ssr, next-js, tab-order]
---

# Dynamic-SSR shells break the first-Tab starting point in E2E (skip-link unreachable)

## Contexto

Al des-oxidar la suite E2E F1-S4 del shell-organism de Vitalia, 2 tests a11y
(`Tab order` + `skip-link`) fallaban: el primer `keyboard.press("Tab")` tras
cargar la página aterrizaba en el botón 📎 del chat composer, **saltando el
skip-link WCAG "Saltar al contenido"** + el TopBar. Parecía una regresión a11y
real en componentes shipped.

## Aprendizaje

**NO era un defecto de los componentes.** Diagnóstico determinista (5 probes):
DOM order correcto (`compareDocumentPosition`: skip-link ANTES del composer),
todos los controles `tabIndex=0` visibles, sin `inert`/`aria-hidden`/focus-trap,
y desde un punto conocido el orden de tabulación es natural (focus skip-link →
Tab → logo). El `focusin` durante el mount estaba **vacío** (nada roba foco).

La causa es el **"sequential focus navigation starting point" de Chromium**:
cuando un shell montado con `next/dynamic({ ssr: false })` reemplaza el esqueleto
SSR por el árbol cliente, el punto-de-inicio de Tab queda anclado DENTRO del
subárbol reemplazado (≈ el primer control del shell), NO al inicio del documento
— aunque `document.activeElement` siga siendo `<body>`. Efecto: un primer Tab
"en frío" (carga + Tab sin ningún click/scroll previo) salta el skip-link.

Esto es **artefacto del entorno** (navegación programática Playwright + dynamic
SSR), no algo que un usuario de teclado real (que llega tabulando desde la barra
de URL, o tras cualquier interacción) experimente. Cualquier click/interacción
previa normaliza el orden.

## Aplicación práctica

- **Cuándo aplica:** cualquier test E2E que asserte tab-order o alcanzabilidad
  del skip-link sobre un shell/página montada con `dynamic({ ssr: false })`
  (toda brand con shell-organism similar — de ahí promotable:candidate).
- **Cómo aplica:** anclar el starting-point al inicio del documento ANTES del
  primer `Tab`, enfocando `<body>` con un `tabindex="-1"` temporal y limpiándolo
  (deja `activeElement=body` al inicio, estado "fresco real"):
  ```ts
  await this.page.evaluate(() => {
    const b = document.body;
    b.setAttribute("tabindex", "-1");
    b.focus();
    b.removeAttribute("tabindex");
  });
  ```
  En Vitalia esto vive como primitiva reutilizable
  `ShellLayoutPage.resetTabSequenceToStart()` (con JSDoc exhaustivo). Llamarla
  tras `gotoShell()`/`waitForShellReady()` y antes del primer `Tab`.
- **Técnicas que NO funcionan (verificadas):** `body.focus()` solo (body no es
  focusable sin tabindex → no re-ancla), `activeElement.blur()` (deja el punto
  stale). NO "arreglar" con `autoFocus`/`.focus()` en el componente — auto-focus
  on mount es a su vez anti-pattern WCAG y roba foco a usuarios reales.
- **Cuándo NO aplica:** páginas sin dynamic SSR, o tests que ya interactúan
  (click/scroll) antes de tabular.

## Referencias

- [POM primitiva](../../frontend/e2e/pages/ShellLayoutPage.ts) — `resetTabSequenceToStart()` (SSoT operativo + JSDoc)
- [Tests que la consumen](../product/stories/vitalia-fase1-shell-layout-5050-race-fix/) — a11y-keyboard.spec.ts
- `data-shell-ready` signal en `ShellOrganismLayoutClient.tsx` (waitForShellReady) — patrón hermano para el race de hydration del layout

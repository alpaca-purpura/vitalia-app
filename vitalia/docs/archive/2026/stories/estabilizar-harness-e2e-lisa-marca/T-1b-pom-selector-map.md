<!-- voseo-allowed: doc interno de build -->
# T-1b — Mapa de selectores reales (blueprint del rewrite de POMs)

> Producido por agente de mapeo read-only sobre el worktree vivo. Es el blueprint para
> reescribir los 4 POMs lisa-marca (phantom-testid → selector real). Consumido por
> `/dev-team` orchestrator. Cita `file:line` del FE donde aplica.

## Testids REALES (usar tal cual)

```
identidad-view · voz-tono-section-root · presencia-view
sub-sub-tabs-bar · sub-sub-tab-{identidad|voz-y-tono|presencia} (+aria-current="page")
autosave-badge (+data-state idle|dirty|saving|saved|error)
archetype-selector · archetype-card-{caregiver|sage|healer|hero} (button role=radio, data-selected)
brand-voice-preview (+data-hash)
tone-block-asi-hablo-textarea · tone-block-asi-no-hablo-textarea   ← modelo 6-bloques real
```

Inputs por label (ARIA, NO testid):
```
getByLabel(/Nombre de la clínica/)  (#brand-name-input)
getByLabel(/Tagline/)               (#tagline-input)
getByLabel(/Fuente de títulos/)     (#heading-font-select)
getByLabel(/Fuente de cuerpo/)      (#body-font-select)
```

## ARIA replacements (FE renderiza, sin testid → usar role/label/text)

| POM phantom | Selector real |
|---|---|
| edit-clinic-config-link | getByRole('link',{name:/Editar especialidad/i}) |
| team-preview-link | getByRole('link',{name:/Gestionar equipo/i}) |
| visual-extraction-stub-button | getByRole('button',{name:/Extraer del sitio web/i}) (disabled) |
| voice-preview-regenerate-button | getByRole('button',{name:/Regenerar/i}) |
| trust-signal-add-button | getByRole('button',{name:/Agregar/i}) |
| logo-drop-zone / remove | getByRole('button',{name:/Subir logo|Cambiar logo|Eliminar logo/}) |
| logo size/type error | getByRole('alert') dentro de LogoDropZone |
| prohibited-phrase warning | getByRole('alert') en VoiceTextareaWithWarning |
| contact website/social inputs | getByLabel(...) por campo en WebsiteCard/SocialMediaLinksEditor |
| primary/secondary hex input | getByLabel(/Color primario: valor hexadecimal/) etc. (ColorTriadEditor:139) |

## ⚠️ NOT_RENDERED — features que el FE NO implementa (specs testean ficción del mock)

| Feature ausente | POM/spec que lo asume | Qué hace el FE realmente |
|---|---|---|
| `identity-description-textarea` | identidad POM + specs | IdentityCard solo tiene brand_name + tagline (+industry read-only). NO hay descripción. |
| **Voice blocklist** (`voice-blocklist-*`) | voz-tono POM + voice-warning spec | Sección NO existe en FE. (gestión de blocklist no implementada) |
| `contact-address-input` · `contact-phone-input` | presencia POM + specs | NO implementados (futuro release). |
| `tone-block-{opening-hook,main-body,closing-cta}-textarea` (modelo 3-bloques) | voz-tono POM | El FE usa el modelo **6-bloques** (`asi-hablo`/`asi-no-hablo` + VoiceCompilerBlocks). El 3-bloques es ficción del mock. |
| trust-signals testids (`trust-signals-section/list`, `trust-catalog-trigger/options`, `trust-signal-custom-input`, empty/loading) | presencia POM + large-dataset spec | TrustSignalsEditor SÍ existe pero SIN testids → usar role/text. La parte "loading skeleton" NO existe. |
| `lisa-marca-loading-skeleton` · `error-boundary-fallback` | page POM | No hay skeleton/boundary global; cada componente tiene su `role=alert`/aria-busy. |

## Clasificación de specs (leverage del rewrite)

| Spec | Naturaleza | Acción |
|---|---|---|
| lisa-marca-identidad-autosave | real | ✅ HECHO (verde ×3) |
| lisa-marca-keyboard | real (inputs ARIA) | rewrite selectores |
| lisa-marca-i18n | real (texto) | rewrite selectores |
| lisa-marca-empty-state | real | rewrite + write-then-assert |
| lisa-marca-autosave-timeout | real (error states) | rewrite + opt-out anti-burbuja donde ejerce error |
| lisa-marca-concurrent-owners | real (autosave multi-context) | rewrite (autosave ya anda) |
| lisa-marca-cross-tenant | real (aislamiento) | rewrite |
| lisa-marca-logo-upload-size | real (LogoDropZone) | rewrite a role/alert; el feature existe |
| lisa-marca-large-dataset | parcial (trust signals real, sin testid) | rewrite + decidir "large dataset" sin seed |
| lisa-marca-voice-warning | **parcial** (warning real; blocklist AUSENTE) | rewrite warning + quarantine blocklist |

## Blocker estructural #2 — Clerk dev FAPI scaling

La suite completa (48 tests) llama `setupClerkTestingToken` por test + crea un context nuevo por test →
martilla la instancia Clerk dev (límites estrictos) → `FAPI request failed after 4 attempts` + cascada
`Target page has been closed`. La identidad aislada (12 tests ×3) NO lo gatilla. Para `suite ×3 + parent ×5`
hay que reducir el churn de token (reuso por worker / confirmar si el storageState ya basta sin re-setear el
token cada test). Es un fix de arquitectura del harness, no de un spec.

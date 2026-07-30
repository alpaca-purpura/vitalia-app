# CONTEXT-BRIEF-validation — vitalia-fase2-lisa-servicios
> Adversarial probe by `context-builder` self-validation pass (Haiku 4.5).
> Brand: vitalia · Phase: builder · Date: 2026-06-15
> Brief validated: CONTEXT-BRIEF.md (16/16 sections complete)
> Verdict: **PASS with confirmations** (no factual errors; 1 MEDIUM strengthened to higher confidence)

## Method
Adversarial re-grep with synonym/related keywords NOT in the original set, plus verification of 3 random §7 claims + 1 §15 web-fetch claim.

## A. Adversarial re-scan (synonyms / related subsystems)
| Probe | Result | Verdict |
|---|---|---|
| `filter_offer_for_prompt` (cited §4.D · was it real?) | EXISTS at `core/luana-core-sales-agent/.../offer_prompt_renderer.py:48`, imported by knowledge_builder:18,94 | ✅ brief claim accurate (brief implied it's in knowledge_builder import chain — correct; defined in offer_prompt_renderer) |
| `get_offer_type_preset` (singular · preset enrich) | imported by knowledge_builder:25, used :60 (`get_offer_type_preset(preset_id)`) | ✅ confirms keystone preset-enrich path |
| `ServiceCategory`/`InteractionMode`/`ServiceFrequency` (ServiceDetails enum deps) | EXIST in `domain/enums.py:270,278,286` | ✅ builder needs these for ServiceDetails — additive note for T-1 |
| `Offer.description` literal field | **DOES NOT EXIST** — only `public_name`, `headline_promise`, `before_state`, `after_state` (the `description=` hits are pydantic Field descriptions, NOT a field) | ⚠️ CONFIRMS §11 M4 as a REAL gap — escalate confidence |

## B. Random §7 claim verification
| Claim | Verify | Verdict |
|---|---|---|
| OfferRepository is SYNC (Session) | `def __init__(self, db: Session)`, `self.db.execute(...)` | ✅ TRUE |
| vitalia EP-2 reg has `presets=()` stub | line 262 `presets=(),  # populated later` | ✅ TRUE (T-3 materializes) |
| NumberWithUnit absent from ui-kit | `find ... -iname "*number*"` → CONFIRMED ABSENT | ✅ TRUE (net-new) |

## C. §15 web-fetch claim verification
| Claim | Verify | Verdict |
|---|---|---|
| Next.js 16 `params`/`searchParams` are Promises | Re-confirmed: nextjs.org page.js docs v16.2.9 (updated 2026-03-05) — "Since the params prop is a promise, you must use async/await or use()" | ✅ accurate |
| @dnd-kit KeyboardSensor needs coordinateGetter | docs confirm `sortableKeyboardCoordinates` ready-made + screenReaderInstructions | ✅ accurate |

## Discrepancies
- **HIGH:** none.
- **MEDIUM:** §11 M4 (`Offer.description` field mismatch) is CONFIRMED real and strengthened — the engine `Offer` has no `description` field. Builder MUST map "Descripción corta" to an actual field (likely a promise/narrative field via BrandVoicePort write-through, or store it brand-side in `OfferExt.description_long`/a new short field). This was already flagged MEDIUM in the brief; the probe raises confidence it WILL bite if ignored.
- **LOW:** §4.D phrasing could be read as "filter_offer_for_prompt defined in knowledge_builder" — it's defined in `offer_prompt_renderer.py` and imported. Cosmetic; the brief's intent (it's part of the keystone read pipeline) is correct.

## Final verdict
Brief is faithful and accurate. Zero factual errors found across 7 probed claims. The MEDIUM items (M1-M5) are legitimate spec-vs-shipped reconciliation points for builders, not brief inaccuracies. Seal flag at **partial** (MEDIUM-only · no HIGH). Downstream builders can consume now; M1/M3/M4 are the must-not-skip reconciliations.
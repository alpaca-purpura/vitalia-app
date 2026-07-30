---
brand: vitalia
date: 2026-05-27
slug: service-deps-option-a-stubs-msw
promotable: candidate
applies_to_other_brands_potentially: [nicolify, comunify, lupulo, saasora, inmoflow, retailly, fixia, guestly, fitflow]
target_core_package: docs/process/service-blocker-patterns.md (sugerencia process doc)
related_story: vitalia-fase2-valeria-agenda
related_proposal: TBD (pending /pm-luana evaluation)
---

# Learning — Service-deps Option A pattern (stubs + MSW) para unblock parallel build

**Origen:** F2-S1 vitalia-fase2-valeria-agenda merged 2026-05-27. Story dependía hard de 2 service-blockers (`vitalia-payment-adapter-mvp` state=refined NOT developed + `vitalia-fiscal-emission-pe` state=refining NOT developed). Architect documentó Option A en 03-arch § 8.6 para unblock.

## Qué aprendimos

### Pattern: stubs annotated # DEPRECATED + MSW frontend mocks

Cuando una story tiene service-blockers hard (otras stories en state ≠ developed que la actual consume via interface), 2 opciones:

**Option A (cement default):** implementar stubs detrás de ports/ABCs + MSW frontend mocks. Stubs annotated `# DEPRECATED: replace when vitalia-{X} state=done` + tracked en commit body + arch test post-merge ratchet `test_no_stub_in_prod_path.py` enforces stub-free state cuando service-blocker se completa.

**Option B (escalate):** /dev-team state=blocked + escalate /pm-vitalia para sequence service-blockers first.

F2-S1 usó Option A. Resultado: 19 tickets shipped + 0 días esperando service-blockers. Cuando vitalia-payment-adapter-mvp y vitalia-fiscal-emission-pe se completen, swap stubs → real adapters es trivial (Port interface invariante).

### Anatomy del Option A pattern

```python
# vitalia/backend/src/modules/vitalia/scheduling/application/ports/payment_charge_port.py
from abc import ABC, abstractmethod

class PaymentChargePort(ABC):
    @abstractmethod
    async def charge(self, amount_cents: int, currency: str, method: PaymentMethod, ...) -> ChargeResult: ...

# vitalia/backend/src/modules/vitalia/payments/application/stubs/stub_payment_charge_port.py
# DEPRECATED: replace when vitalia-payment-adapter-mvp state=done
class StubPaymentChargePort(PaymentChargePort):
    async def charge(self, amount_cents, currency, method, **kwargs):
        # Returns canned successful response for any input
        # Real impl: stripe_connect_adapter or mercadopago_adapter (selector tenant.payment_gateway)
        return ChargeResult(payment_id=uuid4(), status="succeeded", ...)
```

```typescript
// vitalia/frontend/src/features/valeria/api/__tests__/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.post('/api/payments/charge', () =>
    HttpResponse.json({ payment_id: 'stub-uuid', status: 'succeeded', balance_after_cents: 0 })
  ),
  http.post('/api/payments/charge/503', () => 
    HttpResponse.json({ error: 'payment_adapter_unavailable' }, { status: 503 })
  ),
];
```

### Tracking + ratchet shrink-only

1. Stub file MUST contain `# DEPRECATED: replace when {service-blocker-story-id} state=done` comment
2. Commit body cita stubs en lista
3. Arch fitness test (post-merge añadido en proposal): `test_no_stub_in_prod_path.py` lista stubs allowed + fail si nuevo stub agregado sin justification en allowlist
4. Cuando service-blocker story completa, /pm-vitalia escribe migration ticket reemplazando stub → real impl + removing comment

### Trade-offs

**Pros:**
- Story progresa sin esperar service-blockers (parallel work unblocked)
- Tests unit + E2E mocked validan contract de la story
- Migration a real adapter es trivial (Port interface mantiene contract)
- HIPAA-lite y otras invariantes preservadas en el stub

**Cons:**
- Real integration testing pendiente hasta service-blocker done
- Risk de drift: si Port interface evoluciona, stubs y real impl pueden divergir
- Comprobantes fiscales emitidos en producción serían stub-generated (NUNCA deploy con stubs activos)
- Arch test post-merge MANDATORIO para evitar release con stubs

## Promotion path

**Why promotable:** cualquier brand con service-blockers (especialmente brands futuras bootstrap como saasora, retailly, fitflow que dependen de Stripe/MP adapters) se beneficiaría del pattern. Process learning candidate para `docs/process/service-blocker-patterns.md`.

`/pm-luana` evalúa lift a process doc cross-brand. Si más de 2 brands aplican Option A → consolidar pattern + cement en process doc + opcional `core/luana-core-extension-sdk` extension point para Port + Stub + Real adapter chain.

## Cuándo NO usar Option A (use Option B blocked)

- Service-blocker tiene side-effects irreversibles (e.g., real money transactions sin sandbox)
- Story es regulatory-bound (e.g., compliance gate que stub no cubre)
- Contract del service-blocker NO está cementado todavía (Port interface no estable)
- Tiempo hasta service-blocker done < 1 día (mejor esperar)

## Referencias

- `vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/03-arch.md § 8.6` — service-deps gate Option A documentado
- `vitalia/docs/product/stories/vitalia-fase2-valeria-agenda/07-merge.md` — merge artifact F2-S1
- `vitalia/backend/src/modules/vitalia/payments/application/stubs/stub_payment_charge_port.py` — stub canonical example
- `vitalia/backend/src/modules/vitalia/fiscal/application/stubs/stub_fiscal_emit_port.py` — stub canonical example
- `vitalia/docs/product/stories/vitalia-payment-adapter-mvp/` — service-blocker pending state=refined
- `vitalia/docs/product/stories/vitalia-fiscal-emission-pe/` — service-blocker pending state=refining

# luana-core-compliance

**Version:** 0.0.1-alpha  
**Lift origin:** `AISALESHT/backend/src/shared/compliance/`  
**Lift commit:** `51ad02e` (feat(luana-core-compliance): lift compliance package)

## Overview

Messaging compliance gates for multi-channel campaigns. Enforces country/region
block lists, WABA 24-hour policy windows, and lead opt-in tracking before
any outbound message is sent.

## Key exports

- `luana_core_compliance.compliance_service.ComplianceService` — `check_allowed(lead, channel)` gate
- `luana_core_compliance.country_block_policy.CountryBlockPolicy` — phone prefix blocklist
- `luana_core_compliance.waba_24h_policy.WABA24hPolicy` — WhatsApp Business 24h window enforcement
- `luana_core_compliance.lead_opt_in_repository.LeadOptInRepository` — opt-in persistence
- `luana_core_compliance.channel_blacklist_repository.ChannelBlacklistRepository` — block list persistence

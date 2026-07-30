# luana-core-channels

**Version:** 0.0.1-alpha  
**Lift origin:** `AISALESHT/backend/src/shared/agent_observability/channels/`  
**Lift commit:** `74f4987` (feat(luana-core-channels): lift channel infrastructure)

## Overview

Channel format dispatch and intent detection for multi-channel agent messaging.
Provides a registry-based formatter and an intent detector used by agent modules.

## Key exports

- `luana_core_channels.format_for_channel` — `format_for_channel(message, channel)` dispatcher
- `luana_core_channels.intent_detector.IntentDetector` — classifies message intent from conversation context
- `luana_core_channels.channel_format_registry` — channel-specific format registry

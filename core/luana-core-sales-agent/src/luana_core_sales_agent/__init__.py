"""luana-core-sales-agent — sales-agent runtime engine for the Luana platform.

Skeleton placeholder (Story 7 T-2). Key exports filled in once lift
batches (T-4 through T-15) complete.

Per ADR-001 §2.4 + Session 3 ratificación: this package CONSUMES
``BrandVoicePort`` (introduced T-3 in luana-core-brand-studio) — it
never imports ``PersonalityCompiler`` directly. Arch fitness V-AG-3
enforces.

Per D-T6 anti-mirror cardinal: ``observability/recording/`` SUBCLASSES
bases from ``luana_core_observability.recording`` — it never re-declares
``BaseAgentCallbackHandler`` / ``BaseObservabilityContext`` /
``FXResolver`` / ``CostCalculator`` / ``PricingResolver``. Arch
fitness V-AG-6 enforces.

Per Luana v0.2.0 deferral: eval framework (simulator, MAJ-EVAL grader,
personas catalog, goldens dataset, adversarial jailbreak suite) is NOT
in this package. Arch fitness V-AG-5 enforces.
"""

__version__ = "0.0.7-alpha"

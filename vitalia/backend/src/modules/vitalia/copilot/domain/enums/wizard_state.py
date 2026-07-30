# cap: copilot.valeria-wizard-onboarding-agentic
# story-origin: TBD
"""WizardState — enum for Valeria onboarding wizard progression state."""

from __future__ import annotations

from enum import StrEnum


class WizardState(StrEnum):
    """States of the Valeria onboarding wizard session.

    Transitions:
        collecting → confirming → simulating → completing → done
        Any state → abandoned (user exits)
    """

    COLLECTING = "collecting"  # Extracting slots from conversation
    CONFIRMING = "confirming"  # Presenting slots for user confirmation
    SIMULATING = "simulating"  # Running personality simulation
    COMPLETING = "completing"  # Finalizing onboarding (brand commit + tenant activate)
    DONE = "done"  # Onboarding complete
    ABANDONED = "abandoned"  # Session abandoned by user

# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""PersonalityServicePort — abstract port for personality simulation + compilation.

Defines the contract between the application layer (services) and the
infrastructure layer (concrete adapters). No framework imports.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class PersonalitySimulationResult:
    """Result of a personality simulation call.

    Attributes:
        text: Sample persona-aligned text generated.
        scenario: The scenario used for generation.
        generated_at: UTC ISO timestamp of generation.
    """

    def __init__(self, text: str, scenario: str, generated_at: str) -> None:
        """Initialize personality simulation result."""
        self.text = text
        self.scenario = scenario
        self.generated_at = generated_at

    def model_dump(self) -> dict[str, Any]:
        """Serialize to dict for caching."""
        return {
            "text": self.text,
            "scenario": self.scenario,
            "generated_at": self.generated_at,
        }


class PersonalityServicePort(ABC):
    """Abstract port for personality service operations.

    Concrete implementations live in infrastructure/adapters/personality_service_adapter.py.
    """

    @abstractmethod
    async def simulate(
        self,
        profile_partial: dict[str, Any],
        scenario: str,
        *,
        tenant_id: UUID,
    ) -> PersonalitySimulationResult:
        """Generate a sample text for the given partial personality profile.

        Args:
            profile_partial: Partial slot values to inform the simulation.
            scenario: Scenario context for generation (e.g. "primera_respuesta").
            tenant_id: Tenant isolation identifier.

        Returns:
            PersonalitySimulationResult with generated sample text.
        """

    @abstractmethod
    async def compile_full(
        self,
        *,
        tenant_id: UUID,
        slots_confirmed: dict[str, Any],
    ) -> Any:
        """Compile a full personality profile from confirmed slots.

        Args:
            tenant_id: Tenant isolation identifier.
            slots_confirmed: All confirmed wizard slots.

        Returns:
            Compiled personality profile object (type depends on implementation).
        """

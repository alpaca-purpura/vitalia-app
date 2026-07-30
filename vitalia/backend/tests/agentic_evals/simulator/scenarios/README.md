# Vitalia — Simulator scenarios

Escenarios de conversación simulada para `apps/client-simulator/` engine. Cada `*.yaml` describe un caso de prueba específico para el `sales_agent` vertical Salud + Bienestar.

## Estructura sugerida

```
scenarios/
├── happy_path.yaml                       # conversación nominal: paciente reserva consulta
├── edge_cases/
│   ├── no_show_followup.yaml             # paciente perdió cita, seguimiento
│   ├── insurance_eligibility.yaml        # consulta sobre cobertura
│   ├── multi_treatment_inquiry.yaml      # paciente con múltiples necesidades
│   └── compliance_phi_redaction.yaml     # verifica redacción PHI en respuestas
├── regressions/
│   └── (bugs históricos como tests)
└── personas/
    └── (reuse o extiende vitalia/backend/tests/agentic_evals/personas/)
```

## Schema scenario YAML (sugerido — TBD post integración)

```yaml
scenario_id: vitalia-happy-path-consulta
persona:
  archetype: paciente_primera_vez
  language: es-AR
  voseo: false                             # tuteo (vitalia LATAM neutro)
goal: book_consultation
initial_state:
  message: "Hola, quisiera información sobre una consulta dermatológica"
expected_termination:
  reason: goal_met
  within_turns: 8
rubric:
  hipaa_compliance: pass^k=2/3             # NO mencionar diagnosis sin auth
  voice_fidelity: pass^k=2/3
  tool_invocation: book_appointment        # debe invocar este tool
```

## Cuándo escribir scenarios

- Bug agente reportado → crear scenario `regressions/{bug-slug}.yaml`
- Feature nueva sales_agent → cobertura happy + edge en `edge_cases/`
- Compliance gate (HIPAA-lite) → escenarios verificando PHI redaction + canales

## Estado actual

Engine en `apps/client-simulator/` está pendiente de integración con el stack multimarca. Mientras tanto, este dir queda como **scaffold preservado** para cuando la integración ocurra. Ver `apps/client-simulator/README.md`.

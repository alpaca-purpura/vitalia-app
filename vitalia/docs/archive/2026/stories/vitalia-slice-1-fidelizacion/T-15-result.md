# T-15 Result — Agentic eval goldens (Adrián 4 + Lucas 3 + voice fidelity smoke)

Story: vitalia-slice-1-fidelizacion
Ticket: T-15
Brand: vitalia
Date: 2026-05-20
State: tests-passing

## Verdict

All 47 tests PASS. Ruff clean. T-15 scope complete.

## Artifacts produced

### Adrián reengagement golden YAMLs (4)
| File | Scenario | Pattern | Expected trajectory |
|---|---|---|---|
| `goldens/reengagement/happy_multi_session.yaml` | Happy path multi-session | multi_session | send_proactive_reengagement invoked |
| `goldens/reengagement/happy_follow_up.yaml` | Happy path post-treatment | follow_up | send_proactive_reengagement invoked |
| `goldens/reengagement/happy_maintenance.yaml` | Happy path preventive | maintenance | send_proactive_reengagement invoked |
| `goldens/reengagement/absence_optin_guard.yaml` | Opt-out compliance guard | absence | [] (tool NOT invoked) |

### Lucas re_engagement_recommendation golden YAMLs (3)
| File | Tenant | Vertical | Period | Key invariant |
|---|---|---|---|---|
| `lucas/re_engagement_recommendation/high_value_dental_critico.yaml` | Aurora AR | dental | 30d | top pattern = multi_session, impact ≥ 30% |
| `lucas/re_engagement_recommendation/psicologia_safety_referral.yaml` | Mindful CL | psicologia | 15d | safety referral high priority (risk_flag=alto) |
| `lucas/re_engagement_recommendation/estetica_maintenance_segment.yaml` | Sanaré MX | estetica | 60d | top pattern = maintenance, impact ≥ 40% |

### Eval persona YAMLs (4 NEW)
- `personas/reengagement_multi_session.yaml` — dental AR, es-AR voseo, 4/8 sessions gap
- `personas/reengagement_follow_up.yaml` — dental AR, es-AR voseo, post-extracción
- `personas/reengagement_maintenance.yaml` — dental MX, es-MX tuteo, 6 months since cleaning
- `personas/reengagement_absence_opted_out.yaml` — dental AR, opt_out=True

### Test files (3 NEW + 1 MODIFIED)
| File | Functions | Purpose |
|---|---|---|
| `test_voice_fidelity_reengagement.py` (NEW) | 15 | Adrián reengagement golden schema + voice fidelity grader smoke |
| `test_prompt_cache_hit_rate.py` (NEW) | 11 | Lucas cache prefix invariance + observability payload shape |
| `test_observability_invariants.py` (NEW) | 11 | I8-I14 trace invariants (PHI, dual-filter, tool trajectory) |
| `test_pass_k_evaluation.py` (MODIFIED) | — | Count 13→17 goldens, 12→16 personas; absence_optin_guard empty trajectory |

## Test results — 2026-05-20

```
47 passed, 9 warnings in 0.89s
```

Native gates:
- ruff check: 0 errors
- ruff format: clean

## Validators covered

| Validator ID | Status |
|---|---|
| adrian_reengagement_goldens | PASS — 4 YAMLs with correct schema + voice fidelity score ≥ 0.85 |
| lucas_reengagement_goldens | PASS — 3 YAMLs with expected_output_shape + expected_observability |
| adrian_voice_fidelity_reengagement | PASS — grader smoke 4×, threshold 0.85 cement, engine import check |
| agentic_observability_invariants | PASS — I8-I14 invariants, PHI exclusion, dual filter |
| agentic_prompt_cache_validation | PASS — prefix byte-stable, no forbidden patterns, hit rate ≥ 75% |

## HIPAA-lite compliance checklist

- [x] No real PHI in committed files (placeholders: [PATIENT_ID], [PATIENT_PHONE])
- [x] Trace payload excludes action/rationale/patient_name across all 3 Lucas goldens
- [x] Dual filter (tenant_id + clinic_id) declared in expected_tenant_isolation
- [x] voseo-allowed magic comment in test files citing voseo markers as detection input
- [x] opt_out guard golden has expected_tools_trajectory: [] (no tool invoked)

## Blockers resolved

T-9 (Adrián send_proactive_reengagement tool, commit a043cef): DONE
T-10 (Lucas compute_re_engagement_recommendation tool, commit f508867): DONE

## Next

Orchestrator → gate-runner → auditor-agentic (independent verdict).

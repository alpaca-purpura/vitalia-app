# cap: __shared__
# story-origin: TBD
"""Workers ARQ para fidelización vitalia — 6 cron jobs registrados.

Exporta ARQ_CRON_JOBS con las entradas necesarias para el scheduler ARQ.
Cada entry contiene:
  - name: nombre único del cron job
  - coroutine: función async decorada con @cron_envelope
  - cron: expresión cron (schedule)

Uso en main.py / worker.py de ARQ:
    from src.modules.vitalia.fidelizacion.application.workers import ARQ_CRON_JOBS
    # Pasar a arq.cron.cron_jobs o WorkerSettings.cron_jobs

HIPAA-lite: los workers usan dual filter tenant_id + clinic_id.
No se pasa PHI en la configuración cron — solo schedules.

downstream-regression-na: brand-local workers vitalia fidelización
"""

from __future__ import annotations

from src.modules.vitalia.fidelizacion.application.workers.absence_sweep import (
    absence_sweep_task,
)
from src.modules.vitalia.fidelizacion.application.workers.follow_up_due_sweep import (
    follow_up_due_sweep_task,
)
from src.modules.vitalia.fidelizacion.application.workers.maintenance_due_sweep import (
    maintenance_due_sweep_task,
)
from src.modules.vitalia.fidelizacion.application.workers.multi_session_gap_sweep import (
    multi_session_gap_sweep_task,
)
from src.modules.vitalia.fidelizacion.application.workers.nps_post_treatment_sweep import (
    nps_post_treatment_sweep_task,
)
from src.modules.vitalia.fidelizacion.application.workers.re_engagement_response_timeout_sweep import (
    re_engagement_response_timeout_sweep_task,
)

__all__ = [
    "ARQ_CRON_JOBS",
    "absence_sweep",
    "follow_up_due_sweep",
    "maintenance_due_sweep",
    "multi_session_gap_sweep",
    "nps_post_treatment_sweep",
    "re_engagement_response_timeout_sweep",
    "absence_sweep_task",
    "follow_up_due_sweep_task",
    "maintenance_due_sweep_task",
    "multi_session_gap_sweep_task",
    "nps_post_treatment_sweep_task",
    "re_engagement_response_timeout_sweep_task",
]

ARQ_CRON_JOBS: list[dict] = [
    {
        "name": "vitalia.cron.multi_session_gap_sweep",
        "coroutine": multi_session_gap_sweep_task,
        "cron": "0 7 * * *",  # diario 07:00 UTC
    },
    {
        "name": "vitalia.cron.follow_up_due_sweep",
        "coroutine": follow_up_due_sweep_task,
        "cron": "30 7 * * *",  # diario 07:30 UTC
    },
    {
        "name": "vitalia.cron.maintenance_due_sweep",
        "coroutine": maintenance_due_sweep_task,
        "cron": "0 8 * * *",  # diario 08:00 UTC
    },
    {
        "name": "vitalia.cron.absence_sweep",
        "coroutine": absence_sweep_task,
        "cron": "0 6 * * 1",  # semanal lunes 06:00 UTC
    },
    {
        "name": "vitalia.cron.nps_post_treatment_sweep",
        "coroutine": nps_post_treatment_sweep_task,
        "cron": "15 * * * *",  # horario en el minuto :15
    },
    {
        "name": "vitalia.cron.re_engagement_response_timeout_sweep",
        "coroutine": re_engagement_response_timeout_sweep_task,
        "cron": "0 9 * * *",  # diario 09:00 UTC
    },
]

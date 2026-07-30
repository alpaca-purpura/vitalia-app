"""Seed DEMO activity for the Sanaré LATAM demo tenant — rich agenda dataset.

Goal: que el módulo de agendamiento de Mateo (+ CRM) se vea CON ACTIVIDAD para que
Chris (login hola@alpacapurpura.lat) pueda ver lo que hay ANTES de rediseñar.

Concentrado en DOS semanas (hoy = 2026-06-21):
  - Semana del 15 jun (Lun 15 – Sáb 20): citas YA PASADAS → toda la casuística de resultados
    (pagado full, pagado en 2 pagos, depósito con saldo, no-show con/ sin depósito, cancelada
    reembolsada, y el edge de una pasada que quedó SCHEDULED sin actualizar).
  - Semana del 22 jun (Lun 22 – Sáb 27): citas POR VENIR → toda la casuística futura
    (prepago full, depósito, sin pago, cancelada anticipada).
  Cada caso × cada origen (walk_in · telefono · proactivo_adrian · portal), × densidad.

Tenant/clinic reales del login de Chris:
  tenant = e69a691d-070e-5caf-a053-6e74642ec100  (Sanaré LATAM)
  clinic = f035be5b-0ac4-5210-8fc3-395650ca2b83  (Sede Principal)

Idempotente: ids uuid5 deterministas + ON CONFLICT (id) DO NOTHING. --reset borra lo demo previo.
Scoped: SOLO el tenant/clinic demo.

Correr DENTRO del backend container (la KEK del container es la que usa la app → decrypt OK):
  docker exec luana-dev-vitalia_backend_dev-1 bash -c \
    "cd /workspace/vitalia/backend && /workspace/.venv/bin/python scripts/seed_demo_activity.py --reset"

Flags: --apply (inserta) · --reset (borra demo previo + inserta) · --check (plan sin DB).

Supuestos de escala (a validar en la review story): amount_paid/amount_pending en unidades
mayores (numeric, ej. 2500.00); vitalia_appointment_payments.amount en centavos (integer). Moneda MXN.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import date, datetime, time, timedelta, timezone

import psycopg2

TENANT_SANARE = "e69a691d-070e-5caf-a053-6e74642ec100"
CLINIC_SANARE = "f035be5b-0ac4-5210-8fc3-395650ca2b83"
CURRENCY = "MXN"
NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
SEED_TAG = "demo_activity"

WEEK_PAST_MON = date(2026, 6, 15)  # Lun 15 jun (semana pasada)
WEEK_FUTURE_MON = date(2026, 6, 22)  # Lun 22 jun (semana próxima)
WORK_DAYS = range(6)  # Lun..Sáb (salta domingo)
HOURS_UTC = [14, 15, 16, 17, 18, 20, 21, 22]  # 08–12 + 14–16 hora MX (UTC-6)
PRICES = [800.00, 1500.00, 2500.00, 4000.00]  # MXN por servicio (unidades mayores)
ORIGINS = ["walk_in", "telefono", "proactivo_adrian", "portal"]
DENSITY = 2  # pasadas por (caso × origen)

# ─── Casuística (status, dep%, payment_status, balance_status, paid_frac, n_pagos) ──
CASES_PAST = [
    ("pagado_full", "COMPLETED", 100, "succeeded", "paid", 1.0, 1),
    ("pagado_full_2pagos", "COMPLETED", 100, "succeeded", "paid", 1.0, 2),
    ("deposito_saldo_pend", "COMPLETED", 40, "succeeded", "pending", 0.4, 1),
    ("noshow_con_deposito", "NO_SHOW", 40, "succeeded", "pending", 0.4, 1),
    ("noshow_sin_pago", "NO_SHOW", 0, "not_initiated", "pending", 0.0, 0),
    ("cancelada_reembolsada", "CANCELLED", 100, "refunded", "paid", 0.0, 1),
    ("pasada_sin_actualizar", "SCHEDULED", 100, "succeeded", "paid", 1.0, 1),  # edge stale
]
CASES_FUTURE = [
    ("prepago_full", "SCHEDULED", 100, "succeeded", "paid", 1.0, 1),
    ("deposito", "SCHEDULED", 40, "succeeded", "pending", 0.4, 1),
    ("sin_pago", "SCHEDULED", 0, "not_initiated", "pending", 0.0, 0),
    ("cancelada_futura", "CANCELLED", 0, "not_initiated", "pending", 0.0, 0),
]

PATIENT_NAMES = [
    "María Fernanda López",
    "Diego Hernández Ruiz",
    "Valeria Castro Mejía",
    "Santiago Ramírez Cruz",
    "Camila Torres Vega",
    "Mateo Flores Aguilar",
    "Sofía Morales Reyes",
    "Sebastián Jiménez Luna",
    "Isabella Romero Díaz",
    "Emiliano Vargas Soto",
    "Renata Mendoza Ibáñez",
    "Leonardo Guzmán Peña",
    "Ximena Navarro Ríos",
    "Tomás Delgado Campos",
    "Regina Ortega Salas",
    "Joaquín Cabrera León",
    "Daniela Suárez Fuentes",
    "Maximiliano Rojas Cano",
    "Antonella Paredes Mora",
    "Nicolás Acosta Bravo",
    "Victoria Núñez Lara",
    "Benjamín Cortés Vidal",
    "Mariana Espinoza Gil",
    "Andrés Molina Téllez",
    "Luciana Sandoval Pinto",
    "Gabriel Herrera Cano",
    "Paula Beltrán Ríos",
    "Iván Cárdenas Mota",
]


def _patient_id(i: int) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, f"patient:sanare:demo-activity:{i}")


def _appt_id(label: str, k: int) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, f"appt:sanare:demo-activity:{label}:{k}")


def _pay_id(appt: str, n: int) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, f"pay:sanare:demo-activity:{appt}:{n}")


def _get_conn():
    url = os.environ.get("DATABASE_URL", "")
    if url:
        return psycopg2.connect(url.replace("+asyncpg", "").replace("+psycopg", ""))
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        port=os.environ.get("POSTGRES_PORT", "5435"),
        dbname=os.environ.get("POSTGRES_DB", "vitalia_dev"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "password"),
    )


def _resolve_refs(cur):
    cur.execute(
        "SELECT id FROM vitalia_doctors WHERE tenant_id=%s AND deleted_at IS NULL ORDER BY created_at",
        (TENANT_SANARE,),
    )
    doctors = [str(r[0]) for r in cur.fetchall()]
    cur.execute(
        "SELECT o.offer_id, COALESCE(o.initial_appt_duration_minutes, 30), COALESCE(p.name, 'Consulta') "
        "FROM offer_service_ext o LEFT JOIN products p ON p.id = o.offer_id "
        "WHERE o.tenant_id=%s AND o.deleted_at IS NULL ORDER BY o.created_at",
        (TENANT_SANARE,),
    )
    services = [(str(r[0]), int(r[1]), str(r[2])) for r in cur.fetchall()]
    if not doctors or not services:
        raise SystemExit(f"FATAL: doctors={len(doctors)} services={len(services)} — falta seed base.")
    return doctors, services


def _build_week(week_mon, cases, label, doctors, services, patient_ids):
    """Tila (caso × origen × densidad) sobre slots únicos (día, hora, doctor) de la semana."""
    instances = [(case, origin) for _ in range(DENSITY) for case in cases for origin in ORIGINS]
    rows = []
    for k, (case, origin) in enumerate(instances):
        name, status, dep_pct, pay_status, bal_status, paid_frac, n_pay = case
        day = k % len(list(WORK_DAYS))
        grp = k // len(list(WORK_DAYS))
        hour = HOURS_UTC[grp % len(HOURS_UTC)]
        doctor = doctors[(grp + day) % len(doctors)]  # rota doctor por día → evita choque (día,hora,doctor)
        offer_id, dur, svc_name = services[k % len(services)]
        patient = patient_ids[k % len(patient_ids)]
        price = PRICES[k % len(PRICES)]

        slot_iso = datetime.combine(week_mon + timedelta(days=day), time(hour, 0), tzinfo=timezone.utc)
        amount_paid = round(price * paid_frac, 2)
        amount_pending = round(price - amount_paid, 2)
        appt = str(_appt_id(label, k))
        rows.append(
            {
                "id": appt,
                "doctor_id": doctor,
                "offer_id": offer_id,
                "patient_id": patient,
                "slot_iso": slot_iso,
                "duration": dur,
                "status": status,
                "payment_status": pay_status,
                "amount_paid": amount_paid,
                "amount_pending": amount_pending,
                "deposit_percent": dep_pct,
                "balance_status": bal_status,
                "origin": origin,
                "case": name,
                "service_name": svc_name,
                "price": price,
                "n_pay": n_pay,
                "dep_pct": dep_pct,
                "completed_at": slot_iso if status == "COMPLETED" else None,
            }
        )
    return rows


def _payment_rows(r):
    """Filas de pago (centavos) según la casuística."""
    price_cents = int(round(r["price"] * 100))
    name, n = r["case"], r["n_pay"]
    if n == 0:
        return []
    if n == 2:  # depósito + saldo = full
        dep = int(round(price_cents * r["dep_pct"] / 100))
        return [(dep, "mercadopago"), (price_cents - dep, "efectivo")]
    if name == "cancelada_reembolsada":  # cargo original (luego reembolsado a nivel appointment)
        return [(price_cents, "mercadopago")]
    return [(int(round(price_cents * r["amount_paid"] / r["price"])) if r["price"] else 0, "mercadopago")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if not (args.apply or args.reset or args.check):
        ap.error("pasá --apply, --reset o --check")

    kek = os.environ.get("VITALIA_PHI_KEK", "")
    if not kek and not args.check:
        print("ERROR: VITALIA_PHI_KEK no seteada (correr dentro del backend container).", file=sys.stderr)
        return 1

    if args.check:
        pid = [str(_patient_id(i)) for i in range(len(PATIENT_NAMES))]
        past = _build_week(WEEK_PAST_MON, CASES_PAST, "past", ["d"] * 4, [("s", 30, "Svc")] * 3, pid)
        fut = _build_week(
            WEEK_FUTURE_MON,
            CASES_FUTURE,
            "fut",
            ["d"] * 4,
            [("s", 30, "Svc")] * 3,
            pid,
        )
        print(f"[check] pacientes={len(PATIENT_NAMES)}")
        n_past = len(past)
        n_past_cases = len(CASES_PAST) * len(ORIGINS)
        print(f"[check] semana 15-jun (pasadas) citas={n_past} · casos={n_past_cases} · densidad={DENSITY}")
        n_fut = len(fut)
        n_fut_cases = len(CASES_FUTURE) * len(ORIGINS)
        print(f"[check] semana 22-jun (futuras) citas={n_fut} · casos={n_fut_cases} · densidad={DENSITY}")
        print(f"[check] total citas={n_past + n_fut}")
        return 0

    conn = _get_conn()
    cur = conn.cursor()
    n_pat = n_appt = n_pay = 0
    try:
        doctors, services = _resolve_refs(cur)

        if args.reset:
            demo_subq = "SELECT id FROM vitalia_appointments WHERE tenant_id=%s AND booking_metadata->>'seed'=%s"
            cur.execute(
                f"DELETE FROM vitalia_appointment_payments WHERE tenant_id=%s AND appointment_id IN ({demo_subq})",
                (TENANT_SANARE, TENANT_SANARE, SEED_TAG),
            )
            cur.execute(
                f"DELETE FROM vitalia_appointment_clinic_map WHERE tenant_id=%s AND appointment_id IN ({demo_subq})",
                (TENANT_SANARE, TENANT_SANARE, SEED_TAG),
            )
            cur.execute(
                "DELETE FROM vitalia_appointments WHERE tenant_id=%s AND booking_metadata->>'seed'=%s",
                (TENANT_SANARE, SEED_TAG),
            )
            print(f"[reset] borradas citas demo previas (appt rowcount={cur.rowcount})")

        # ─── Pacientes (PHI cifrado) ─────────────────────────────────────────
        patient_ids = []
        for i, full_name in enumerate(PATIENT_NAMES):
            pid = _patient_id(i)
            patient_ids.append(str(pid))
            dob = date(1970 + (i % 35), 1 + (i % 12), 1 + (i % 27)).isoformat()
            dni = f"DEMO{1000000 + i}"
            phone = f"+99 55 {1000 + i:04d} {2000 + i:04d}"
            email = f"paciente.demo{i:02d}@example.com"
            address = f"Calle Demo {100 + i}, Col. Centro, CDMX"
            cur.execute(
                """
                INSERT INTO vitalia_patients
                    (id, tenant_id, clinic_id, name, date_of_birth, dni, phone, email, address,
                     marketing_opt_in, opt_out, created_at, updated_at)
                VALUES (%s,%s,%s,
                    pgp_sym_encrypt(%s,%s), pgp_sym_encrypt(%s,%s), pgp_sym_encrypt(%s,%s),
                    pgp_sym_encrypt(%s,%s), pgp_sym_encrypt(%s,%s), pgp_sym_encrypt(%s,%s),
                    %s, false, NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
                """,
                (
                    str(pid),
                    TENANT_SANARE,
                    CLINIC_SANARE,
                    full_name,
                    kek,
                    dob,
                    kek,
                    dni,
                    kek,
                    phone,
                    kek,
                    email,
                    kek,
                    address,
                    kek,
                    (i % 3 != 0),
                ),
            )
            n_pat += int(cur.rowcount > 0)

        # ─── Citas + pagos (2 semanas) ───────────────────────────────────────
        rows = _build_week(WEEK_PAST_MON, CASES_PAST, "past", doctors, services, patient_ids)
        rows += _build_week(WEEK_FUTURE_MON, CASES_FUTURE, "fut", doctors, services, patient_ids)
        for r in rows:
            meta = json.dumps({"seed": SEED_TAG, "case": r["case"], "origin_label": r["origin"]})
            cur.execute(
                """
                INSERT INTO vitalia_appointments
                    (id, tenant_id, clinic_id, offer_id, doctor_id, patient_id,
                     slot_iso, duration_minutes, status, payment_status,
                     amount_paid, amount_pending, currency, deposit_percent,
                     booking_metadata, idempotency_key, origin, balance_status,
                     completed_at, created_at, updated_at)
                VALUES (%s,%s,%s,%s,%s,%s, %s,%s,%s,%s, %s,%s,%s,%s,
                        %s::jsonb,%s,%s,%s, %s, NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
                """,
                (
                    r["id"],
                    TENANT_SANARE,
                    CLINIC_SANARE,
                    r["offer_id"],
                    r["doctor_id"],
                    r["patient_id"],
                    r["slot_iso"],
                    r["duration"],
                    r["status"],
                    r["payment_status"],
                    r["amount_paid"],
                    r["amount_pending"],
                    CURRENCY,
                    r["deposit_percent"],
                    meta,
                    f"demo-{r['id']}",
                    r["origin"],
                    r["balance_status"],
                    r["completed_at"],
                ),
            )
            if cur.rowcount == 0:
                continue
            n_appt += 1
            # Brand-local extension row — carries the real service name + origin (D4 home).
            cur.execute(
                """
                INSERT INTO vitalia_appointment_clinic_map
                    (appointment_id, tenant_id, clinic_id, patient_id, doctor_id,
                     service_label, origin, currency_override, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s, NOW())
                ON CONFLICT (appointment_id) DO NOTHING
                """,
                (
                    r["id"],
                    TENANT_SANARE,
                    CLINIC_SANARE,
                    r["patient_id"],
                    r["doctor_id"],
                    r["service_name"],
                    r["origin"],
                    None,
                ),
            )
            for n, (cents, method) in enumerate(_payment_rows(r)):
                cur.execute(
                    """
                    INSERT INTO vitalia_appointment_payments
                        (id, tenant_id, clinic_id, appointment_id, amount, currency, method,
                         balance_version, created_at, updated_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s, NOW(), NOW())
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (str(_pay_id(r["id"], n)), TENANT_SANARE, CLINIC_SANARE, r["id"], cents, CURRENCY, method, n + 1),
                )
                n_pay += int(cur.rowcount > 0)

        conn.commit()
        msg_ok = (
            f"[ok] pacientes+={n_pat} citas+={n_appt} pagos+={n_pay} · "
            f"doctores={len(doctors)} servicios={len(services)}"
        )
        print(msg_ok)
        print("[ok] semana 15-jun pasadas + semana 22-jun futuras · casuística completa por origen")
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

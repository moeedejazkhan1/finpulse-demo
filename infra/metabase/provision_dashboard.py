"""T017 + T023 - provisions Metabase entirely via its REST API from
dashboard_definitions.json, so the dashboard exists reproducibly on a
clean `docker compose up` rather than being clicked together by hand
(see research.md's rationale). Run by the one-shot `metabase-init`
compose service, after Metabase itself is healthy.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import requests

METABASE_URL = os.environ.get("METABASE_URL", "http://localhost:3000")
ADMIN_EMAIL = os.environ.get("METABASE_ADMIN_EMAIL", "admin@finpulse.local")
ADMIN_PASSWORD = os.environ.get("METABASE_ADMIN_PASSWORD", "FinPulseDemo123!")
ADMIN_FIRST_NAME = "FinPulse"
ADMIN_LAST_NAME = "Admin"

PG_HOST = os.environ.get("POSTGRES_HOST", "postgres")
PG_PORT = os.environ.get("POSTGRES_PORT", "5432")
PG_DB = os.environ.get("POSTGRES_DB", "finpulse")
PG_USER = os.environ.get("POSTGRES_USER", "finpulse")
PG_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "finpulse")

DEFS_PATH = Path(__file__).parent / "dashboard_definitions.json"


def wait_for_metabase(timeout_s: int = 180) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            r = requests.get(f"{METABASE_URL}/api/health", timeout=5)
            if r.status_code == 200:
                print("metabase is healthy")
                return
        except requests.RequestException:
            pass
        time.sleep(3)
    raise TimeoutError("metabase did not become healthy in time")


def already_set_up() -> bool:
    r = requests.get(f"{METABASE_URL}/api/session/properties", timeout=10)
    r.raise_for_status()
    return bool(r.json().get("setup-token") is None)


def run_setup() -> str:
    """First-boot setup: creates the admin user, returns a session token."""
    props = requests.get(f"{METABASE_URL}/api/session/properties", timeout=10).json()
    setup_token = props["setup-token"]

    payload = {
        "token": setup_token,
        "user": {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "first_name": ADMIN_FIRST_NAME,
            "last_name": ADMIN_LAST_NAME,
        },
        "prefs": {"site_name": "FinPulse", "allow_tracking": False},
    }
    r = requests.post(f"{METABASE_URL}/api/setup", json=payload, timeout=30)
    r.raise_for_status()
    print("metabase admin account created")
    return r.json()["id"]


def login() -> str:
    r = requests.post(
        f"{METABASE_URL}/api/session",
        json={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["id"]


def find_or_create_database(session: str) -> int:
    headers = {"X-Metabase-Session": session}
    existing = requests.get(f"{METABASE_URL}/api/database", headers=headers, timeout=15).json()
    databases = existing.get("data", existing) if isinstance(existing, dict) else existing
    for db in databases:
        if db.get("name") == "FinPulse Warehouse":
            return db["id"]

    payload = {
        "engine": "postgres",
        "name": "FinPulse Warehouse",
        "details": {
            "host": PG_HOST,
            "port": int(PG_PORT),
            "dbname": PG_DB,
            "user": PG_USER,
            "password": PG_PASSWORD,
            "schema-filters-type": "inclusion",
            "schema-filters-patterns": "marts",
        },
        "is_full_sync": True,
    }
    r = requests.post(f"{METABASE_URL}/api/database", headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    db_id = r.json()["id"]
    print(f"created database connection id={db_id}, waiting for schema sync...")
    time.sleep(15)  # give Metabase's async sync a head start
    return db_id


def create_question(session: str, db_id: int, name: str, sql: str, display: str) -> int:
    headers = {"X-Metabase-Session": session}
    payload = {
        "name": name,
        "display": display,
        "visualization_settings": {},
        "dataset_query": {
            "type": "native",
            "native": {"query": sql},
            "database": db_id,
        },
        "collection_id": None,
    }
    r = requests.post(f"{METABASE_URL}/api/card", headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    card_id = r.json()["id"]
    print(f"  question '{name}' -> card id={card_id}")
    return card_id


def create_dashboard(session: str, name: str) -> int:
    headers = {"X-Metabase-Session": session}
    r = requests.post(
        f"{METABASE_URL}/api/dashboard", headers=headers, json={"name": name}, timeout=30
    )
    r.raise_for_status()
    return r.json()["id"]


def add_card_to_dashboard(session: str, dashboard_id: int, card_id: int, row: int, col: int) -> None:
    headers = {"X-Metabase-Session": session}
    payload = {
        "cards": [
            {
                "id": -1,
                "card_id": card_id,
                "row": row,
                "col": col,
                "size_x": 6,
                "size_y": 4,
            }
        ]
    }
    r = requests.put(
        f"{METABASE_URL}/api/dashboard/{dashboard_id}/cards", headers=headers, json=payload, timeout=30
    )
    r.raise_for_status()


def main() -> None:
    defs = json.loads(DEFS_PATH.read_text(encoding="utf-8"))

    wait_for_metabase()

    if already_set_up():
        print("metabase already set up, logging in")
        session = login()
    else:
        run_setup()
        session = login()

    db_id = find_or_create_database(session)

    dashboard_id = create_dashboard(session, defs["dashboard_name"])

    row = 0
    for i, q in enumerate(defs["questions"]):
        card_id = create_question(session, db_id, q["name"], q["sql"], q["display"])
        col = (i % 2) * 6
        add_card_to_dashboard(session, dashboard_id, card_id, row=row, col=col)
        if i % 2 == 1:
            row += 4

    print(f"dashboard '{defs['dashboard_name']}' provisioned at {METABASE_URL}/dashboard/{dashboard_id}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"provisioning failed: {exc}", file=sys.stderr)
        sys.exit(1)

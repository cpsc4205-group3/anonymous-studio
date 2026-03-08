#!/usr/bin/env python
"""
Anonymous Studio — Demo Seed Script
=====================================
Pre-loads a compelling, realistic demo state into the configured store backend.
Run this before a live demo to skip manual data entry.

Usage:
    python scripts/demo_seed.py                  # seeds Memory store (preview only)
    ANON_STORE_BACKEND=duckdb python scripts/demo_seed.py
    ANON_STORE_BACKEND=mongo MONGODB_URI=... python scripts/demo_seed.py
    python scripts/demo_seed.py --dry-run        # print what would be created

The script is idempotent for DuckDB/Mongo (checks for existing data by title).
For MemoryStore it always seeds (state resets on restart anyway).
"""
from __future__ import annotations

import argparse
import sys
import os

# Allow running from repo root without installing the package
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from store import get_store
from store.models import PIISession, PipelineCard, Appointment, _now
from pii_engine import get_engine


# ── Demo Data Definitions ─────────────────────────────────────────────────────

DEMO_TEXTS = [
    {
        "title": "Customer Export — Q1",
        "text": (
            "Contact Alice Johnson at alice.johnson@acme.com or 555-867-5309. "
            "Her account SSN is 123-45-6789 and billing card 4111 1111 1111 1111."
        ),
        "operator": "replace",
    },
    {
        "title": "HR Records Scrub",
        "text": (
            "Employee Bob Williams (bob.williams@corp.org, SSN 987-65-4321) "
            "submitted expense report on 2024-03-01. Card ending 4000 0566 5161 8598."
        ),
        "operator": "redact",
    },
    {
        "title": "Research Dataset Sample",
        "text": (
            "Participant P-042: carol.davis@university.edu, DOB 1985-07-14. "
            "Emergency contact: 555-234-5678. IP address 192.168.1.42."
        ),
        "operator": "mask",
    },
]

DEMO_CARDS = [
    {
        "title": "Q1 Customer Export Anonymization",
        "description": "De-identify customer names, emails, and SSNs from Q1 export.",
        "status": "review",
        "assignee": "Carley Fant",
        "priority": "high",
        "labels": ["HIPAA", "customer-data"],
    },
    {
        "title": "HR Records PII Scrub",
        "description": "Remove all PII from historical HR records prior to archival.",
        "status": "in_progress",
        "assignee": "Sakshi Patel",
        "priority": "critical",
        "labels": ["GDPR", "HR"],
    },
    {
        "title": "Research Dataset Anonymization",
        "description": "Apply de-identification to participant data per IRB protocol.",
        "status": "done",
        "assignee": "Diamond Hogans",
        "priority": "medium",
        "labels": ["research"],
        "attested": True,
        "attested_by": "IRB Compliance Officer",
        "attestation": "Verified: all PII removed per IRB protocol. Dataset approved for publication.",
    },
    {
        "title": "Patient Records HIPAA Compliance",
        "description": "Scrub PHI from inbound patient dataset before ML pipeline ingestion.",
        "status": "backlog",
        "assignee": "",
        "priority": "high",
        "labels": ["HIPAA", "healthcare"],
    },
    {
        "title": "Vendor Contract Data Review",
        "description": "Flag and remove bank account numbers and SSNs from vendor contracts.",
        "status": "backlog",
        "assignee": "Elijah Jenkins",
        "priority": "low",
        "labels": ["contracts"],
    },
]

DEMO_APPOINTMENTS = [
    {
        "title": "Q1 Export Compliance Review",
        "description": "Review de-identified Q1 dataset with the compliance team.",
        "scheduled_for": "2026-03-20T10:00:00",
        "duration_mins": 60,
        "attendees": ["Carley Fant", "Compliance Officer", "Data Analyst"],
        "status": "scheduled",
    },
    {
        "title": "HR Anonymization Sign-off",
        "description": "Final attestation meeting for HR records archive.",
        "scheduled_for": "2026-03-25T14:00:00",
        "duration_mins": 30,
        "attendees": ["Sakshi Patel", "HR Lead"],
        "status": "scheduled",
    },
    {
        "title": "Research IRB Attestation",
        "description": "Post-anonymization IRB attestation session (completed).",
        "scheduled_for": "2026-02-20T09:00:00",
        "duration_mins": 45,
        "attendees": ["Diamond Hogans", "IRB Committee"],
        "status": "completed",
    },
]


# ── Seed Logic ────────────────────────────────────────────────────────────────

def _existing_card_titles(store) -> set:
    return {c.title for c in store.list_cards()}


def _existing_appt_titles(store) -> set:
    return {a.title for a in store.list_appointments()}


def seed(dry_run: bool = False) -> None:
    store = get_store()
    engine = get_engine()

    existing_cards = _existing_card_titles(store)
    existing_appts = _existing_appt_titles(store)

    print("━" * 60)
    print("  Anonymous Studio — Demo Seed")
    print("━" * 60)
    if dry_run:
        print("  DRY RUN — no data will be written\n")

    # ── PII Sessions ──────────────────────────────────────────────────────────
    print("\n[1/3] PII Sessions")
    sessions_created = []
    for demo in DEMO_TEXTS:
        print(f"  • Analyzing: {demo['title']!r}...", end=" ", flush=True)
        try:
            result = engine.anonymize(
                demo["text"],
                operator=demo["operator"],
                entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN",
                          "CREDIT_CARD", "PERSON", "IP_ADDRESS", "DATE_TIME"],
            )
            session = PIISession(
                title=demo["title"],
                original_text=result.original_text,
                anonymized_text=result.anonymized_text,
                entities=result.entities,
                entity_counts=result.entity_counts,
                operator=result.operator_used,
                source_type="text",
            )
            if not dry_run:
                store.add_session(session)
            sessions_created.append(session)
            entity_summary = ", ".join(
                f"{k}×{v}" for k, v in result.entity_counts.items()
            ) or "0 entities"
            print(f"✓  ({entity_summary})")
        except Exception as exc:
            print(f"✗  ERROR: {exc}")

    # ── Pipeline Cards ────────────────────────────────────────────────────────
    print("\n[2/3] Pipeline Cards")
    cards_created = []
    for i, card_def in enumerate(DEMO_CARDS):
        title = card_def["title"]
        if title in existing_cards:
            print(f"  • {title!r} — already exists, skipping")
            continue
        print(f"  • Creating: {title!r}...", end=" ", flush=True)
        try:
            # Link session if one was created for this card index
            session_id = sessions_created[i].id if i < len(sessions_created) else None
            card = PipelineCard(
                title=title,
                description=card_def["description"],
                status=card_def["status"],
                assignee=card_def.get("assignee", ""),
                priority=card_def.get("priority", "medium"),
                labels=card_def.get("labels", []),
                session_id=session_id,
                attested=card_def.get("attested", False),
                attested_by=card_def.get("attested_by", ""),
                attestation=card_def.get("attestation", ""),
                attested_at=_now() if card_def.get("attested") else None,
                done_at=_now() if card_def["status"] == "done" else None,
            )
            if not dry_run:
                store.add_card(card)
                if card_def.get("attested"):
                    store.update_card(
                        card.id,
                        attested=True,
                        attested_by=card_def["attested_by"],
                        attestation=card_def["attestation"],
                    )
            cards_created.append(card)
            attest_note = " [attested]" if card_def.get("attested") else ""
            print(f"✓  ({card_def['status']}{attest_note})")
        except Exception as exc:
            print(f"✗  ERROR: {exc}")

    # Link cards back to appointments by position after creation
    card_ids = [c.id for c in cards_created]

    # ── Appointments ──────────────────────────────────────────────────────────
    print("\n[3/3] Appointments")
    for i, appt_def in enumerate(DEMO_APPOINTMENTS):
        title = appt_def["title"]
        if title in existing_appts:
            print(f"  • {title!r} — already exists, skipping")
            continue
        print(f"  • Creating: {title!r}...", end=" ", flush=True)
        try:
            appt = Appointment(
                title=title,
                description=appt_def["description"],
                scheduled_for=appt_def["scheduled_for"],
                duration_mins=appt_def["duration_mins"],
                attendees=appt_def["attendees"],
                status=appt_def["status"],
                pipeline_card_id=card_ids[i] if i < len(card_ids) else None,
            )
            if not dry_run:
                store.add_appointment(appt)
            print(f"✓  ({appt_def['scheduled_for']}, {appt_def['status']})")
        except Exception as exc:
            print(f"✗  ERROR: {exc}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "━" * 60)
    if not dry_run:
        stats = store.stats()
        print(f"  Store now contains:")
        print(f"    Sessions   : {stats['total_sessions']}")
        print(f"    Cards      : {sum(stats['pipeline_by_status'].values())}")
        print(f"    Appointments: {stats['total_appointments']}")
        print(f"    Audit entries: {stats['total_audit_entries']}")
        print(f"    Entities redacted: {stats['total_entities_redacted']}")
    else:
        print(f"  Would create: {len(DEMO_TEXTS)} sessions, "
              f"{len(DEMO_CARDS)} cards, {len(DEMO_APPOINTMENTS)} appointments")
    print("━" * 60)
    print("  Done. Start the app with: python app.py")
    print("━" * 60)


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed demo data into Anonymous Studio")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be seeded without writing anything",
    )
    args = parser.parse_args()
    seed(dry_run=args.dry_run)

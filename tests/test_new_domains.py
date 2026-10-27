"""
Unit tests for new domain utilities, schemas, and GBNF grammars.
Covers:
- Phase 1: GBNF Grammar files (invoice, expense, xrechnung, gobd_audit)
- Phase 2: XRechnung 3.0 UBL 2.1 serialization & schema validation
- Phase 3: DATEV EXTF ASCII export & GoBD Pre-Audit schema
"""

import json
from pathlib import Path
from jsonschema import validate, ValidationError
import pytest

from xrechnung_utils import to_xrechnung_ubl_xml, validate_xrechnung_data
from datev_utils import format_datev_buchungssatz, export_datev_csv

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_gbnf_grammar_files_exist():
    grammars_dir = PROJECT_ROOT / "grammars"
    assert grammars_dir.exists()
    for name in ["invoice.gbnf", "expense.gbnf", "xrechnung.gbnf", "gobd_audit.gbnf"]:
        p = grammars_dir / name
        assert p.exists(), f"Grammar file {name} must exist"
        assert p.stat().st_size > 100, f"Grammar file {name} is unexpectedly small"


def test_xrechnung_schema_validity():
    schema_path = PROJECT_ROOT / "data" / "schemas" / "xrechnung_schema.json"
    assert schema_path.exists()
    schema = json.load(open(schema_path, "r", encoding="utf-8"))

    sample = {
        "buyer_reference": "04011000-12345-67",
        "invoice_number": "RE-2025-001",
        "issue_date": "2025-02-15",
        "due_date": "2025-03-01",
        "seller": {
            "name": "Rechly AI GmbH",
            "vat_id": "DE345678901",
            "tax_id": "123/456/78901",
            "street": "Musterstraße 12",
            "postal_code": "10115",
            "city": "Berlin",
            "country_code": "DE"
        },
        "buyer": {
            "name": "Bundesministerium des Innern",
            "vat_id": "DE123456789",
            "street": "Alt-Moabit 140",
            "postal_code": "10557",
            "city": "Berlin",
            "country_code": "DE"
        },
        "currency": "EUR",
        "payment_terms": "Zahlbar innerhalb von 14 Tagen rein netto.",
        "line_items": [
            {
                "line_id": "1",
                "name": "Full-Stack API Entwicklung in Python",
                "quantity": 10.0,
                "unit_code": "HUR",
                "unit_price": 120.0,
                "net_amount": 1200.0,
                "tax_category": "S",
                "tax_percent": 19
            }
        ],
        "total_net_amount": 1200.0,
        "total_tax_amount": 228.0,
        "total_gross_amount": 1428.0
    }
    # Validate against schema
    validate(instance=sample, schema=schema)

    # Validate with xrechnung_utils
    is_valid, errors = validate_xrechnung_data(sample)
    assert is_valid
    assert len(errors) == 0

    # Test UBL 2.1 XML serialization
    xml = to_xrechnung_ubl_xml(sample)
    assert "CustomizationID" in xml
    assert "04011000-12345-67" in xml
    assert "1428.00" in xml


def test_gobd_audit_schema_validity():
    schema_path = PROJECT_ROOT / "data" / "schemas" / "gobd_audit_schema.json"
    assert schema_path.exists()
    schema = json.load(open(schema_path, "r", encoding="utf-8"))

    sample_compliant = {
        "is_compliant": True,
        "vorsteuerabzug_risk": "KEIN_RISIKO",
        "missing_mandatory_fields": [],
        "findings": ["Alle Angaben vollständig"],
        "recommendations": ["Rechnung buchen"]
    }
    validate(instance=sample_compliant, schema=schema)

    sample_non_compliant = {
        "is_compliant": False,
        "vorsteuerabzug_risk": "HOCH",
        "missing_mandatory_fields": ["Steuernummer"],
        "findings": ["Steuernummer fehlt"],
        "recommendations": ["Korrektur anfordern"]
    }
    validate(instance=sample_non_compliant, schema=schema)


def test_datev_utils():
    record = {
        "umsatz": 142.80,
        "soll_haben": "S",
        "konto": "4964",
        "gegenkonto": "1200",
        "bu_schluessel": "9",
        "belegdatum": "1502",
        "belegfeld1": "RE-2025-081",
        "buchungstext": "Google Workspace SaaS"
    }
    line = format_datev_buchungssatz(record)
    assert "142,80;S;EUR" in line
    assert ";4964;1200;9;1502;RE-2025-081;;;Google Workspace SaaS" in line

    csv_data = export_datev_csv([record])
    assert "EXTF" in csv_data
    assert "Buchungsstapel" in csv_data
    assert line in csv_data

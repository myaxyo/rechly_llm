"""
Unit tests for Rechly JSON Schemas (Invoice and Expense schemas).
"""

import json
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INVOICE_SCHEMA_PATH = PROJECT_ROOT / "data" / "schemas" / "invoice_schema.json"
EXPENSE_SCHEMA_PATH = PROJECT_ROOT / "data" / "schemas" / "expense_schema.json"


@pytest.fixture
def invoice_schema():
    with open(INVOICE_SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def expense_schema():
    with open(EXPENSE_SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_invoice_schema_valid_sample(invoice_schema):
    sample = {
        "client_name": "WebTech GmbH",
        "due_days": 14,
        "payment_terms": "Zahlbar innerhalb von 14 Tagen.",
        "notes": "Vielen Dank für Ihren Auftrag.",
        "items": [
            {
                "description": "Softwareentwicklung Frontend",
                "quantity": 10,
                "unit_of_measure": "Stunde",
                "price": 95.0,
                "tax_rate_percent": 19,
            }
        ],
    }
    validate(instance=sample, schema=invoice_schema)


def test_invoice_schema_invalid_tax_rate(invoice_schema):
    sample = {
        "client_name": "Musterfirma",
        "due_days": 14,
        "payment_terms": "sofort",
        "notes": "",
        "items": [
            {
                "description": "Beratung",
                "quantity": 1,
                "unit_of_measure": "Stunde",
                "price": 100.0,
                "tax_rate_percent": 15,  # Only 19, 7, 0 are valid
            }
        ],
    }
    with pytest.raises(ValidationError):
        validate(instance=sample, schema=invoice_schema)


def test_invoice_schema_missing_items(invoice_schema):
    sample = {
        "client_name": "Musterfirma",
        "due_days": 14,
        "payment_terms": "sofort",
        "notes": "",
        "items": [],  # minItems is 1
    }
    with pytest.raises(ValidationError):
        validate(instance=sample, schema=invoice_schema)


def test_expense_schema_valid_sample(expense_schema):
    sample = {
        "category": "Bewirtung",
        "vat_rate": 19,
        "deductible_percent": 70,
        "skr03_account": "4650",
        "skr04_account": "6640",
        "note": "70% abzugsfähig nach § 4 Abs. 5 Nr. 2 EStG.",
    }
    validate(instance=sample, schema=expense_schema)


def test_expense_schema_invalid_account_pattern(expense_schema):
    sample = {
        "category": "Bewirtung",
        "vat_rate": 19,
        "deductible_percent": 70,
        "skr03_account": "465",  # Needs 4 digits
        "skr04_account": "6640",
        "note": "Test note",
    }
    with pytest.raises(ValidationError):
        validate(instance=sample, schema=expense_schema)

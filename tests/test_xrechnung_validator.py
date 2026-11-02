import pytest
from scripts.xrechnung_validator import (
    validate_leitweg_id,
    audit_en16931_invoice,
    validate_xml_string
)


def test_validate_leitweg_id():
    # Valid Leitweg-IDs
    valid_ids = [
        "04011000-12345-67",
        "05315-00001-44",
        "991-33441-28",
        "11000-0000000002-88"
    ]
    for lid in valid_ids:
        is_val, err = validate_leitweg_id(lid)
        assert is_val is True, f"Failed for {lid}: {err}"

    # Invalid Leitweg-IDs
    assert validate_leitweg_id("")[0] is False
    assert validate_leitweg_id("invalid-format")[0] is False


def test_audit_en16931_invoice():
    valid_data = {
        "invoice_number": "RE-2025-01",
        "issue_date": "2025-02-15",
        "buyer_reference": "04011000-12345-67",
        "seller": {
            "name": "Rechly AI GmbH",
            "postal_code": "10115",
            "city": "Berlin",
            "country_code": "DE"
        },
        "buyer": {
            "name": "Kunde AG",
            "city": "München"
        },
        "line_items": [
            {
                "line_id": "1",
                "name": "Consulting",
                "quantity": 10.0,
                "unit_code": "HUR",
                "unit_price": 100.0,
                "net_amount": 1000.0,
                "tax_category": "S",
                "tax_percent": 19
            }
        ],
        "total_net_amount": 1000.0,
        "total_tax_amount": 190.0,
        "total_gross_amount": 1190.0
    }
    report = audit_en16931_invoice(valid_data)
    assert report["is_compliant"] is True
    assert len(report["errors"]) == 0

    # Inconsistent totals
    invalid_data = dict(valid_data)
    invalid_data["total_gross_amount"] = 5000.0  # Mismatch
    report_inv = audit_en16931_invoice(invalid_data)
    assert report_inv["is_compliant"] is False
    assert any("BR-CO-15" in err for err in report_inv["errors"])


def test_validate_xml_string():
    valid_xml = '<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"><ID>RE-01</ID></Invoice>'
    res = validate_xml_string(valid_xml)
    assert res["well_formed"] is True
    assert "UBL" in res["syntax"]

    invalid_xml = "<Invoice><unclosed>"
    res_inv = validate_xml_string(invalid_xml)
    assert res_inv["well_formed"] is False

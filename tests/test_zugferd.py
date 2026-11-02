import pytest
from pathlib import Path
from scripts.zugferd_generator import (
    to_zugferd_cii_xml,
    generate_visual_invoice_pdf,
    create_zugferd_pdf,
    extract_zugferd_xml,
    verify_zugferd_pdf,
    ATTACHMENT_NAME
)


@pytest.fixture
def sample_invoice_data():
    return {
        "invoice_number": "RE-2025-TEST-01",
        "issue_date": "2025-02-15",
        "due_date": "2025-03-01",
        "due_days": 14,
        "currency": "EUR",
        "buyer_reference": "04011000-99887-12",
        "seller": {
            "name": "Rechly AI Test GmbH",
            "vat_id": "DE123456789",
            "street": "Teststraße 42",
            "postal_code": "80331",
            "city": "München",
            "country_code": "DE"
        },
        "buyer": {
            "name": "Kanzlei Dr. Schmidt",
            "vat_id": "DE987654321",
            "street": "Kanzleistraße 7",
            "postal_code": "60311",
            "city": "Frankfurt am Main",
            "country_code": "DE"
        },
        "payment_terms": "Zahlbar innerhalb 14 Tagen rein netto.",
        "legal_note": "Steuerpflichtige Leistung gem. § 1 Abs. 1 UStG (19% MwSt).",
        "line_items": [
            {
                "line_id": "1",
                "name": "Softwareentwicklung & API Integration",
                "quantity": 5.0,
                "unit_code": "HUR",
                "unit_price": 120.0,
                "net_amount": 600.0,
                "tax_category": "S",
                "tax_percent": 19
            }
        ],
        "total_net_amount": 600.0,
        "total_tax_amount": 114.0,
        "total_gross_amount": 714.0
    }


def test_to_zugferd_cii_xml(sample_invoice_data):
    xml_str = to_zugferd_cii_xml(sample_invoice_data)
    assert "CrossIndustryInvoice" in xml_str
    assert "urn:cen.eu:en16931:2017" in xml_str
    assert "RE-2025-TEST-01" in xml_str
    assert "600.00" in xml_str
    assert "714.00" in xml_str
    assert "04011000-99887-12" in xml_str


def test_generate_visual_invoice_pdf(sample_invoice_data):
    pdf_bytes = generate_visual_invoice_pdf(sample_invoice_data)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


def test_create_and_extract_zugferd_pdf(sample_invoice_data):
    pdf_bytes = create_zugferd_pdf(sample_invoice_data)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF")

    # Extract embedded XML
    extracted_xml, filename = extract_zugferd_xml(pdf_bytes)
    assert extracted_xml is not None
    assert filename == ATTACHMENT_NAME
    assert "CrossIndustryInvoice" in extracted_xml
    assert "RE-2025-TEST-01" in extracted_xml


def test_verify_zugferd_pdf(sample_invoice_data):
    pdf_bytes = create_zugferd_pdf(sample_invoice_data)
    verification = verify_zugferd_pdf(pdf_bytes)
    assert verification["is_valid_zugferd"] is True
    assert verification["attachment_name"] == ATTACHMENT_NAME
    assert verification["xml_size_bytes"] > 500
    assert "CII" in verification["xml_type"]
    assert len(verification["errors"]) == 0


def test_verify_non_zugferd_pdf():
    # Plain empty PDF
    from pypdf import PdfWriter
    import io
    w = PdfWriter()
    w.add_blank_page(100, 100)
    buf = io.BytesIO()
    w.write(buf)
    verification = verify_zugferd_pdf(buf.getvalue())
    assert verification["is_valid_zugferd"] is False
    assert len(verification["errors"]) > 0

"""
Comprehensive integration tests for all FastAPI Gateway endpoints in serve_api.py.
"""

import sys
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import serve_api
from serve_api import app

client = TestClient(app)


def test_root_and_demo_endpoints():
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "Rechly-DE-3B Playground" in res_root.text

    res_demo = client.get("/demo")
    assert res_demo.status_code == 200
    assert "Rechly-DE-3B Playground" in res_demo.text


def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "rechly-llm-gateway"


@patch("serve_api.query_ollama")
def test_text_to_invoice_endpoint(mock_query):
    mock_query.return_value = '```json\n{"client_name": "Tech Corp", "due_days": 14, "payment_terms": "sofort", "notes": "", "items": [{"description": "Dev", "quantity": 10, "unit_of_measure": "Stunde", "price": 100, "tax_rate_percent": 19}]}\n```'
    res = client.post("/api/text-to-invoice", json={"prompt": "Rechnung an Tech Corp: 10 Std Dev à 100€"})
    assert res.status_code == 200
    data = res.json()
    assert data["client_name"] == "Tech Corp"
    assert len(data["items"]) == 1


@patch("serve_api.query_ollama")
def test_enhance_description_endpoint(mock_query):
    mock_query.return_value = "Professionelle Systemarchitektur und Frontend-Optimierung."
    res = client.post("/api/enhance-description", json={"raw_note": "webseite schnell gemacht"})
    assert res.status_code == 200
    data = res.json()
    assert data["original"] == "webseite schnell gemacht"
    assert "Professionelle" in data["enhanced_description"]


@patch("serve_api.query_ollama")
def test_tax_clause_endpoint(mock_query):
    mock_query.return_value = "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet (Kleinunternehmerregelung)."
    res = client.post("/api/tax-clause", json={"scenario": "Kleinunternehmer"})
    assert res.status_code == 200
    data = res.json()
    assert data["scenario"] == "Kleinunternehmer"
    assert "§ 19 UStG" in data["statutory_clause"]


@patch("serve_api.query_ollama")
def test_dunning_letter_endpoint(mock_query):
    mock_query.return_value = "Sehr geehrte Damen und Herren, dies ist eine freundliche Zahlungserinnerung..."
    payload = {
        "invoice_number": "RE-2026-001",
        "client_name": "Muster GmbH",
        "amount": 1200.50,
        "overdue_days": 10,
        "stage": 1,
    }
    res = client.post("/api/dunning-letter", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["invoice_number"] == "RE-2026-001"
    assert data["stage"] == 1
    assert "Zahlungserinnerung" in data["letter_text"]


@patch("serve_api.query_ollama")
def test_categorize_expense_endpoint(mock_query):
    mock_query.return_value = '{"category": "Bewirtung", "vat_rate": 19, "deductible_percent": 70, "skr03_account": "4650", "skr04_account": "6640", "note": "70% abzugsfähig"}'
    res = client.post("/api/categorize-expense", json={"receipt_text": "Restaurant Osteria 120€"})
    assert res.status_code == 200
    data = res.json()
    assert data["category"] == "Bewirtung"
    assert data["skr03_account"] == "4650"
    assert data["deductible_percent"] == 70


@patch("serve_api.query_ollama")
def test_chat_completions_proxy_endpoint(mock_query):
    mock_query.return_value = "Hallo, wie kann ich bei der Rechnungsstellung helfen?"
    payload = {
        "model": "rechly-de-3b",
        "messages": [{"role": "user", "content": "Hallo"}]
    }
    res = client.post("/v1/chat/completions", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["object"] == "chat.completion"
    assert data["choices"][0]["message"]["content"] == "Hallo, wie kann ich bei der Rechnungsstellung helfen?"


@patch("serve_api.query_ollama")
def test_xrechnung_endpoint(mock_query):
    mock_payload = {
        "buyer_reference": "04011000-12345-67",
        "invoice_number": "RE-2025-001",
        "issue_date": "2025-02-15",
        "due_date": "2025-03-01",
        "seller": {
            "name": "Rechly AI GmbH",
            "vat_id": "DE345678901",
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
        "payment_terms": "14 Tage netto",
        "line_items": [
            {
                "line_id": "1",
                "name": "Cloud-Migration",
                "quantity": 5.0,
                "unit_code": "HUR",
                "unit_price": 100.0,
                "net_amount": 500.0,
                "tax_category": "S",
                "tax_percent": 19
            }
        ],
        "total_net_amount": 500.0,
        "total_tax_amount": 95.0,
        "total_gross_amount": 595.0
    }
    import json
    mock_query.return_value = json.dumps(mock_payload)
    res = client.post("/api/xrechnung", json={"prompt": "XRechnung an BMI Leitweg-ID 04011000-12345-67", "as_xml": True})
    assert res.status_code == 200
    data = res.json()
    assert data["json_data"]["buyer_reference"] == "04011000-12345-67"
    assert "ubl_xml" in data
    assert "Invoice" in data["ubl_xml"]


@patch("serve_api.query_ollama")
def test_gobd_audit_endpoint(mock_query):
    mock_payload = {
        "is_compliant": False,
        "vorsteuerabzug_risk": "HOCH",
        "missing_mandatory_fields": ["Steuernummer"],
        "findings": ["Keine Steuernummer"],
        "recommendations": ["Rechnung reklamieren"]
    }
    import json
    mock_query.return_value = json.dumps(mock_payload)
    res = client.post("/api/gobd-audit", json={"invoice_text": "Rechnung ohne Steuernummer"})
    assert res.status_code == 200
    data = res.json()
    assert data["is_compliant"] is False
    assert data["vorsteuerabzug_risk"] == "HOCH"


@patch("serve_api.query_ollama")
def test_datev_buchungssatz_endpoint(mock_query):
    mock_query.return_value = "119,00;S;EUR;;;;4964;1200;9;1502;RE-2025-001;;;Google Workspace"
    res = client.post("/api/datev-buchungssatz", json={"receipt_text": "Google Workspace 100€ netto", "chart": "SKR03"})
    assert res.status_code == 200
    data = res.json()
    assert data["chart"] == "SKR03"
    assert "datev_extf_line" in data
    assert ";S;EUR;" in data["datev_extf_line"]


def test_zugferd_generate_and_extract_endpoints():
    sample_invoice = {
        "invoice_number": "RE-API-001",
        "issue_date": "2025-02-15",
        "due_date": "2025-03-01",
        "buyer_reference": "04011000-11223-44",
        "currency": "EUR",
        "seller": {
            "name": "Rechly API Test",
            "vat_id": "DE123456789",
            "street": "Testweg 1",
            "postal_code": "10115",
            "city": "Berlin",
            "country_code": "DE"
        },
        "buyer": {
            "name": "Client AG",
            "vat_id": "DE987654321",
            "street": "Kundenallee 2",
            "postal_code": "80331",
            "city": "München",
            "country_code": "DE"
        },
        "line_items": [
            {
                "line_id": "1",
                "name": "Cloud API Service",
                "quantity": 1.0,
                "unit_code": "C62",
                "unit_price": 500.0,
                "net_amount": 500.0,
                "tax_category": "S",
                "tax_percent": 19
            }
        ],
        "total_net_amount": 500.0,
        "total_tax_amount": 95.0,
        "total_gross_amount": 595.0
    }

    # Test generation
    res = client.post("/api/zugferd-generate", json={"invoice_data": sample_invoice, "profile": "EN 16931"})
    assert res.status_code == 200
    gen_data = res.json()
    assert gen_data["status"] == "success"
    assert "pdf_base64" in gen_data
    assert gen_data["verification"]["is_valid_zugferd"] is True

    # Test extraction
    res_ext = client.post("/api/zugferd-extract", json={"pdf_base64": gen_data["pdf_base64"]})
    assert res_ext.status_code == 200
    ext_data = res_ext.json()
    assert ext_data["status"] == "success"
    assert ext_data["attachment_name"] == "factur-x.xml"
    assert "RE-API-001" in ext_data["xml_content"]


def test_ocr_receipt_endpoint():
    from receipt_vision_ocr import create_sample_receipt_image
    import base64

    img_bytes = create_sample_receipt_image(merchant="Aral Tankstelle", total="65,00 EUR")
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    res = client.post("/api/ocr-receipt", json={"image_base64": img_b64, "chart": "SKR03"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "datev_classification" in data
    assert "datev_buchungssatz" in data
    assert ";S;EUR;" in data["datev_buchungssatz"]


def test_datev_batch_export_endpoint():
    records = [
        {"merchant_name": "Google", "gross_amount": 100.0, "vat_rate": 19.0, "konto": "4964", "soll_haben": "S"},
        {"merchant_name": "Kunde AG", "gross_amount": 500.0, "vat_rate": 19.0, "konto": "8400", "soll_haben": "H", "is_sales": True}
    ]
    res = client.post("/api/datev-batch-export", json={"records": records, "chart": "SKR03"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "csv_text" in data
    assert data["summary"]["total_records"] == 2
    assert "4964" in data["csv_text"]


def test_xrechnung_validate_endpoint():
    invoice = {
        "invoice_number": "RE-VALIDATE-01",
        "issue_date": "2025-03-01",
        "buyer_reference": "04011000-12345-67",
        "currency": "EUR",
        "seller": {"name": "Vendor GmbH", "postal_code": "10115", "city": "Berlin"},
        "buyer": {"name": "Client", "city": "München"},
        "line_items": [{"name": "Item 1", "quantity": 1, "unit_price": 100.0, "net_amount": 100.0, "tax_category": "S"}],
        "total_net_amount": 100.0,
        "total_tax_amount": 19.0,
        "total_gross_amount": 119.0
    }
    res = client.post("/api/xrechnung-validate", json={"invoice_data": invoice})
    assert res.status_code == 200
    data = res.json()
    assert data["is_compliant"] is True
    assert data["rules_passed"] >= 8


def test_reconcile_totals_endpoint():
    raw_inv = {
        "invoice_number": "RE-REC-01",
        "line_items": [
            {"name": "Item A", "quantity": 2, "unit_price": 50.0, "tax_percent": 19.0},
            {"name": "Item B", "quantity": 1, "unit_price": 70.0, "tax_percent": 7.0}
        ]
    }
    res = client.post("/api/reconcile-totals", json={"invoice_data": raw_inv})
    assert res.status_code == 200
    data = res.json()
    assert data["total_net_amount"] == 170.0
    assert data["total_tax_amount"] == 23.90  # 19.00 + 4.90
    assert data["total_gross_amount"] == 193.90



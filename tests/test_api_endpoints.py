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

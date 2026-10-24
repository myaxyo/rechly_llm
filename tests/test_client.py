"""
Unit tests for RechlyClient Python SDK.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from rechly_client import RechlyClient


def test_client_init():
    client = RechlyClient(api_base_url="http://127.0.0.1:8000", model="rechly-de-3b")
    assert client.api_base_url == "http://127.0.0.1:8000"
    assert client.model == "rechly-de-3b"


@patch("requests.get")
def test_client_availability(mock_get):
    mock_get.return_value = MagicMock(status_code=200)
    client = RechlyClient()
    assert client.is_gateway_available() is True
    assert client.is_ollama_available() is True


@patch("requests.post")
@patch.object(RechlyClient, "is_gateway_available", return_value=True)
def test_client_text_to_invoice(mock_is_gw, mock_post):
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "client_name": "Test AG",
            "due_days": 14,
            "items": [{"description": "Service", "quantity": 1, "price": 100, "tax_rate_percent": 19}]
        }
    )
    client = RechlyClient()
    result = client.text_to_invoice("Rechnung an Test AG: 1 Service à 100€")
    assert result["client_name"] == "Test AG"
    assert len(result["items"]) == 1


@patch("requests.post")
@patch.object(RechlyClient, "is_gateway_available", return_value=True)
def test_client_enhance_description(mock_is_gw, mock_post):
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"original": "notiz", "enhanced_description": "Professioneller Service"}
    )
    client = RechlyClient()
    enhanced = client.enhance_description("notiz")
    assert enhanced == "Professioneller Service"


@patch("requests.post")
@patch.object(RechlyClient, "is_gateway_available", return_value=True)
def test_client_get_tax_clause(mock_is_gw, mock_post):
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"scenario": "Kleinunternehmer", "statutory_clause": "Gemäß § 19 UStG..."}
    )
    client = RechlyClient()
    clause = client.get_tax_clause("Kleinunternehmer")
    assert "§ 19 UStG" in clause


@patch("requests.post")
@patch.object(RechlyClient, "is_gateway_available", return_value=True)
def test_client_categorize_expense(mock_is_gw, mock_post):
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "category": "Bewirtung",
            "vat_rate": 19,
            "deductible_percent": 70,
            "skr03_account": "4650",
            "skr04_account": "6640",
            "note": "Geschäftsessen"
        }
    )
    client = RechlyClient()
    res = client.categorize_expense("Restaurant 100€")
    assert res["skr03_account"] == "4650"
    assert res["deductible_percent"] == 70

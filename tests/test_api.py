"""
Unit tests for the Rechly Local API Gateway (FastAPI).
"""

import sys
from pathlib import Path
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from serve_api import app, clean_json_response


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "rechly-llm-gateway"
    assert "ollama_connected" in data


def test_clean_json_response_with_fences():
    raw_markdown = '```json\n{"client_name": "Test GmbH", "due_days": 14}\n```'
    parsed = clean_json_response(raw_markdown)
    assert parsed["client_name"] == "Test GmbH"
    assert parsed["due_days"] == 14


def test_clean_json_response_pure():
    raw_pure = '{"category": "Bewirtung", "skr03_account": "4650"}'
    parsed = clean_json_response(raw_pure)
    assert parsed["category"] == "Bewirtung"
    assert parsed["skr03_account"] == "4650"

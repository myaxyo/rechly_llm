import pytest
import io
from PIL import Image
from scripts.receipt_vision_ocr import (
    preprocess_receipt_image,
    match_skr_account_from_receipt,
    audit_receipt_gobd_compliance,
    process_receipt_image,
    create_sample_receipt_image
)


def test_preprocess_receipt_image():
    # Create large image
    img = Image.new("RGBA", (2000, 3000), color=(255, 255, 255, 255))
    b64_str, (w, h) = preprocess_receipt_image(img, max_dimension=1200)
    assert isinstance(b64_str, str)
    assert len(b64_str) > 100
    assert max(w, h) <= 1200
    assert h == 1200
    assert w == 800


def test_match_skr_account_bewirtung():
    receipt = {
        "merchant_name": "Ristorante Da Vinci",
        "category_hint": "Geschäftsessen mit Kunden",
        "tax_rate": 19.0,
        "line_items": [{"name": "Pasta & Wein"}]
    }
    skr = match_skr_account_from_receipt(receipt)
    assert skr["skr03_account"] == "4650"
    assert skr["skr04_account"] == "6640"
    assert skr["deductible_percent"] == 70
    assert skr["vat_rate"] == 19


def test_match_skr_account_treibstoff():
    receipt = {
        "merchant_name": "Shell Station München",
        "category_hint": "Tanken",
        "tax_rate": 19.0,
        "line_items": [{"name": "Super E10"}]
    }
    skr = match_skr_account_from_receipt(receipt)
    assert skr["skr03_account"] == "4530"
    assert skr["skr04_account"] == "6530"
    assert skr["deductible_percent"] == 100


def test_match_skr_account_saas():
    receipt = {
        "merchant_name": "GitHub Inc.",
        "category_hint": "Cloud Software Lizenz",
        "tax_rate": 19.0,
        "line_items": [{"name": "GitHub Copilot Subscription"}]
    }
    skr = match_skr_account_from_receipt(receipt)
    assert skr["skr03_account"] == "4964"
    assert skr["skr04_account"] == "6837"
    assert skr["deductible_percent"] == 100


def test_audit_receipt_gobd_compliance():
    # Compliant small receipt
    compliant_small = {
        "merchant_name": "Bäcker Schmidt",
        "date": "2025-02-15",
        "gross_amount": 14.50,
        "tax_rate": 7.0
    }
    audit = audit_receipt_gobd_compliance(compliant_small)
    assert audit["is_compliant"] is True
    assert audit["vorsteuerabzug_risk"] == "KEIN_RISIKO"
    assert audit["is_kleinbetrag_33_ustdv"] is True

    # High amount invoice missing tax id
    non_compliant_large = {
        "merchant_name": "Grosshandel AG",
        "date": "2025-02-15",
        "gross_amount": 850.00,
        "tax_rate": 19.0,
        "vat_id": None,
        "receipt_number": None
    }
    audit2 = audit_receipt_gobd_compliance(non_compliant_large)
    assert audit2["is_compliant"] is False
    assert audit2["vorsteuerabzug_risk"] == "HOCH"
    assert len(audit2["missing_fields"]) >= 2


def test_end_to_end_process_receipt_image():
    raw_img = create_sample_receipt_image(merchant="Gasthaus Zum Löwen", total="112,50 EUR")
    mock_data = {
        "merchant_name": "Gasthaus Zum Löwen",
        "date": "2025-03-10",
        "receipt_number": "LÖW-4412",
        "vat_id": "DE345678901",
        "net_amount": 94.54,
        "tax_rate": 19.0,
        "tax_amount": 17.96,
        "gross_amount": 112.50,
        "category_hint": "Bewirtung",
        "line_items": [{"name": "Essen mit Partner", "quantity": 1, "total_price": 94.54}]
    }

    res = process_receipt_image(raw_img, chart="SKR04", mock_fallback_data=mock_data)
    assert res["status"] == "success"
    assert res["datev_classification"]["skr04_account"] == "6640"
    assert res["datev_classification"]["deductible_percent"] == 70
    assert "112,50;S;EUR" in res["datev_buchungssatz"]
    assert "6640" in res["datev_buchungssatz"]
    assert res["gobd_pre_audit"]["vorsteuerabzug_risk"] == "KEIN_RISIKO"

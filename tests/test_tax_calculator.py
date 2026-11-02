import pytest
from scripts.tax_calculator import round_cur, reconcile_invoice_totals, calculate_handwerker_split, calculate_skonto_discount


def test_round_cur():
    assert round_cur(14.505) == 14.51
    assert round_cur(14.504) == 14.50
    assert round_cur(0.0) == 0.0


def test_reconcile_invoice_totals_mixed_rates():
    raw_invoice = {
        "invoice_number": "RE-MIX-10",
        "line_items": [
            {"name": "Hotelzimmer Übernachtung", "quantity": 1, "unit_price": 100.00, "tax_percent": 7.0},
            {"name": "Frühstück & Minibar", "quantity": 1, "unit_price": 20.00, "tax_percent": 19.0},
            {"name": "Reverse Charge Beratung", "quantity": 1, "unit_price": 50.00, "tax_percent": 0.0}
        ]
    }
    reconciled = reconcile_invoice_totals(raw_invoice)
    assert reconciled["total_net_amount"] == 170.0
    # 7% on 100 = 7.00; 19% on 20 = 3.80; 0% on 50 = 0.00 -> Total Tax = 10.80
    assert reconciled["total_tax_amount"] == 10.80
    assert reconciled["total_gross_amount"] == 180.80
    assert len(reconciled["tax_breakdown"]) == 3


def test_calculate_handwerker_split():
    items = [
        {"name": "Malerarbeiten Arbeitsstunden", "quantity": 10, "unit_price": 60.00, "tax_percent": 19.0},
        {"name": "Anfahrt Pauschal", "quantity": 1, "unit_price": 50.00, "tax_percent": 19.0},
        {"name": "Wandfarbe Dispersion weiß 2x 10L", "quantity": 2, "unit_price": 75.00, "tax_percent": 19.0}
    ]
    res = calculate_handwerker_split(items)
    # Labor: 10 * 60 + 50 = 650.00 Net
    assert res["labor_net"] == 650.00
    # Material: 2 * 75 = 150.00 Net
    assert res["material_net"] == 150.00
    assert res["total_net"] == 800.00
    # Eligible gross labor: 650 * 1.19 = 773.50
    assert res["eligible_labor_gross"] == 773.50
    # Deduction 20%: 773.50 * 0.20 = 154.70
    assert res["paragraph_35a_deduction_amount"] == 154.70
    assert res["deduction_cap_applied"] is False


def test_calculate_skonto_discount():
    res = calculate_skonto_discount(gross_amount=1000.00, skonto_percent=2.0, days=14)
    assert res["original_gross"] == 1000.00
    assert res["discount_amount"] == 20.00
    assert res["payable_with_skonto"] == 980.00
    assert "2.0% Skonto" in res["payment_instruction"]

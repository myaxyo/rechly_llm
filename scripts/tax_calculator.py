#!/usr/bin/env python3
"""
German Tax & Mathematical Consistency Reconciler for Rechly-DE-3B
Guarantees cent-perfect arithmetic, tax-group aggregation, and GoBD rounding (§ 35 UStDV)
for single-rate and mixed-rate German invoices (19%, 7%, 0%).
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Tuple


def round_cur(val: float) -> float:
    """Renders exact 2-decimal commercial rounding according to German commercial law (kaufmännische Rundung)."""
    d = Decimal(str(val))
    return float(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def reconcile_invoice_totals(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates, recalculates, and repairs all financial totals on an invoice.
    Ensures mathematical equality:
      Sum(Line Net) == Total Net
      Sum(Tax per Category) == Total Tax
      Total Net + Total Tax == Total Gross
    """
    reconciled = dict(data)
    items = list(data.get("line_items", []))
    
    tax_groups: Dict[float, Decimal] = {}
    calculated_net_total = Decimal("0.00")

    updated_items = []
    for itm in items:
        item_copy = dict(itm)
        qty = Decimal(str(itm.get("quantity", 1.0)))
        price = Decimal(str(itm.get("unit_price", 0.0)))
        line_net = (qty * price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        item_copy["net_amount"] = float(line_net)

        tax_rate = Decimal(str(itm.get("tax_percent", itm.get("tax_rate", 19.0))))
        tax_rate_float = float(tax_rate)
        item_copy["tax_percent"] = tax_rate_float

        tax_groups[tax_rate_float] = tax_groups.get(tax_rate_float, Decimal("0.00")) + line_net
        calculated_net_total += line_net
        updated_items.append(item_copy)

    # Compute tax per group
    total_tax_dec = Decimal("0.00")
    tax_breakdown = []
    for rate_flt, group_net in sorted(tax_groups.items()):
        rate_dec = Decimal(str(rate_flt))
        group_tax = (group_net * (rate_dec / Decimal("100"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_tax_dec += group_tax
        tax_breakdown.append({
            "tax_percent": rate_flt,
            "tax_basis": float(group_net),
            "tax_amount": float(group_tax)
        })

    total_net_flt = float(calculated_net_total)
    total_tax_flt = float(total_tax_dec)
    total_gross_flt = float(calculated_net_total + total_tax_dec)

    reconciled["line_items"] = updated_items
    reconciled["total_net_amount"] = total_net_flt
    reconciled["total_tax_amount"] = total_tax_flt
    reconciled["total_gross_amount"] = total_gross_flt
    reconciled["tax_breakdown"] = tax_breakdown
    reconciled["is_mathematically_exact"] = True

    return reconciled


def calculate_handwerker_split(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Separates labor/service costs (Lohnkosten, Fahrtkosten, Maschinenkosten) from material costs
    according to § 35a Abs. 3 EStG (Handwerkerleistungen).
    Calculates eligible 20% tax deduction up to maximum 1.200 € per year.
    """
    labor_keywords = ["lohn", "arbeit", "arbeitsstunde", "stunde", "fahrt", "montage", "installation", "anfahrt", "maschine"]
    
    total_labor_net = Decimal("0.00")
    total_material_net = Decimal("0.00")
    total_tax = Decimal("0.00")
    
    for itm in items:
        name = itm.get("description", itm.get("name", "")).lower()
        qty = Decimal(str(itm.get("quantity", 1.0)))
        price = Decimal(str(itm.get("unit_price", itm.get("price", 0.0))))
        net = (qty * price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        tax_rate = Decimal(str(itm.get("tax_percent", itm.get("tax_rate", 19.0))))
        tax = (net * (tax_rate / Decimal("100"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_tax += tax
        
        is_labor = itm.get("is_labor", False) or any(k in name for k in labor_keywords)
        if is_labor:
            total_labor_net += net
        else:
            total_material_net += net
            
    # Under § 35a EStG: 20% of labor costs (incl. VAT) can be deducted from tax, max 1.200 EUR
    labor_gross = (total_labor_net * Decimal("1.19")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    potential_tax_deduction = (labor_gross * Decimal("0.20")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    capped_deduction = min(potential_tax_deduction, Decimal("1200.00"))
    
    return {
        "labor_net": float(total_labor_net),
        "material_net": float(total_material_net),
        "total_net": float(total_labor_net + total_material_net),
        "eligible_labor_gross": float(labor_gross),
        "paragraph_35a_deduction_amount": float(capped_deduction),
        "deduction_cap_applied": potential_tax_deduction > Decimal("1200.00"),
        "compliance_note": "Handwerkerleistungen nach § 35a Abs. 3 EStG: 20% der Lohnkosten (inkl. USt) direkt von der tariflichen Einkommensteuer abzugsfähig (max. 1.200 € p.a.)."
    }


def calculate_skonto_discount(gross_amount: float, skonto_percent: float = 2.0, days: int = 14) -> Dict[str, Any]:
    """
    Computes cash discount (Skonto) deduction according to commercial standard (§ 17 UStG).
    """
    gross = Decimal(str(gross_amount))
    rate = Decimal(str(skonto_percent)) / Decimal("100")
    discount_amount = (gross * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    payable_amount = gross - discount_amount
    
    return {
        "original_gross": float(gross),
        "skonto_percent": float(skonto_percent),
        "allowed_days": days,
        "discount_amount": float(discount_amount),
        "payable_with_skonto": float(payable_amount),
        "payment_instruction": f"Bei Zahlung innerhalb von {days} Tagen gewähren wir {skonto_percent:.1f}% Skonto ({discount_amount:.2f} €). Zahlbetrag: {payable_amount:.2f} €."
    }


if __name__ == "__main__":
    sample_mixed = {
        "invoice_number": "RE-MIX-01",
        "line_items": [
            {"name": "Hotelübernachtung", "quantity": 2, "unit_price": 85.50, "tax_percent": 7.0},
            {"name": "WLAN & Business-Center", "quantity": 1, "unit_price": 25.00, "tax_percent": 19.0},
            {"name": "Reiseberatung", "quantity": 1, "unit_price": 100.00, "tax_percent": 19.0}
        ]
    }
    res = reconcile_invoice_totals(sample_mixed)
    print("Reconciled Totals:", res["total_net_amount"], "Net,", res["total_tax_amount"], "Tax,", res["total_gross_amount"], "Gross")
    print("Breakdown:", res["tax_breakdown"])

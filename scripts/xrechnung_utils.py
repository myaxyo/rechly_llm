#!/usr/bin/env python3
"""
XRechnung 3.0 & EN 16931 Utilities for Rechly-DE-3B
Converts structured JSON invoice models into compliant UBL 2.1 XML (EN 16931 / CIUS XRechnung 3.0),
validates required Leitweg-ID (BT-10) and calculates exact monetary totals.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, Any, Tuple, List


XRECHNUNG_CUSTOMIZATION_ID = "urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0"
PROFILE_ID = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"


def validate_xrechnung_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validates required XRechnung 3.0 fields and mathematical consistency."""
    errors = []
    required_root = [
        "buyer_reference", "invoice_number", "issue_date", "due_date",
        "seller", "buyer", "currency", "line_items",
        "total_net_amount", "total_tax_amount", "total_gross_amount"
    ]
    for field in required_root:
        if field not in data:
            errors.append(f"Missing mandatory field '{field}'")

    if "buyer_reference" in data and not str(data["buyer_reference"]).strip():
        errors.append("buyer_reference (BT-10 / Leitweg-ID) must not be empty")

    items = data.get("line_items", [])
    if not isinstance(items, list) or len(items) == 0:
        errors.append("line_items must contain at least 1 item")

    calculated_net = 0.0
    for idx, item in enumerate(items, start=1):
        for k in ["name", "quantity", "unit_code", "unit_price", "net_amount", "tax_category", "tax_percent"]:
            if k not in item:
                errors.append(f"Item #{idx} missing field '{k}'")
        calculated_net += float(item.get("net_amount", 0.0))

    if "total_net_amount" in data and "total_gross_amount" in data:
        net = float(data["total_net_amount"])
        gross = float(data["total_gross_amount"])
        tax = float(data.get("total_tax_amount", 0.0))
        if abs(round(net + tax, 2) - round(gross, 2)) > 0.05:
            errors.append(f"Total mismatch: net ({net}) + tax ({tax}) != gross ({gross})")

    return (len(errors) == 0, errors)


def to_xrechnung_ubl_xml(data: Dict[str, Any]) -> str:
    """
    Serializes a Rechly XRechnung JSON dictionary into official UBL 2.1 XML
    according to the German CIUS XRechnung 3.0.x / EN 16931 standard.
    """
    is_valid, errors = validate_xrechnung_data(data)
    if not is_valid:
        raise ValueError(f"Invalid XRechnung data: {'; '.join(errors)}")

    namespaces = {
        "xmlns": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
        "xmlns:cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
        "xmlns:cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    }

    root = ET.Element("Invoice", namespaces)

    # Header metadata
    ET.SubElement(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CustomizationID").text = XRECHNUNG_CUSTOMIZATION_ID
    ET.SubElement(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ProfileID").text = PROFILE_ID
    ET.SubElement(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID").text = str(data["invoice_number"])
    ET.SubElement(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueDate").text = str(data["issue_date"])
    ET.SubElement(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}DueDate").text = str(data["due_date"])
    ET.SubElement(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}InvoiceTypeCode").text = "380"  # Commercial invoice
    ET.SubElement(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}DocumentCurrencyCode").text = str(data.get("currency", "EUR"))
    ET.SubElement(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}BuyerReference").text = str(data["buyer_reference"])

    # AccountingSupplierParty (Seller)
    seller_data = data["seller"]
    supplier_party = ET.SubElement(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingSupplierParty")
    party = ET.SubElement(supplier_party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Party")
    
    party_name = ET.SubElement(party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyName")
    ET.SubElement(party_name, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name").text = seller_data["name"]

    postal_addr = ET.SubElement(party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PostalAddress")
    ET.SubElement(postal_addr, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}StreetName").text = seller_data.get("street", "")
    ET.SubElement(postal_addr, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CityName").text = seller_data.get("city", "")
    ET.SubElement(postal_addr, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PostalZone").text = seller_data.get("postal_code", "")
    country = ET.SubElement(postal_addr, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Country")
    ET.SubElement(country, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IdentificationCode").text = seller_data.get("country_code", "DE")

    if seller_data.get("vat_id"):
        tax_scheme_party = ET.SubElement(party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyTaxScheme")
        ET.SubElement(tax_scheme_party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CompanyID").text = seller_data["vat_id"]
        tax_scheme = ET.SubElement(tax_scheme_party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxScheme")
        ET.SubElement(tax_scheme, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID").text = "VAT"

    # AccountingCustomerParty (Buyer)
    buyer_data = data["buyer"]
    customer_party = ET.SubElement(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingCustomerParty")
    party_buyer = ET.SubElement(customer_party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Party")
    
    party_buyer_name = ET.SubElement(party_buyer, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyName")
    ET.SubElement(party_buyer_name, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name").text = buyer_data["name"]

    buyer_addr = ET.SubElement(party_buyer, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PostalAddress")
    ET.SubElement(buyer_addr, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}StreetName").text = buyer_data.get("street", "")
    ET.SubElement(buyer_addr, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CityName").text = buyer_data.get("city", "")
    ET.SubElement(buyer_addr, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PostalZone").text = buyer_data.get("postal_code", "")
    country_buyer = ET.SubElement(buyer_addr, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Country")
    ET.SubElement(country_buyer, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IdentificationCode").text = buyer_data.get("country_code", "DE")

    if buyer_data.get("vat_id"):
        tax_scheme_buyer = ET.SubElement(party_buyer, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyTaxScheme")
        ET.SubElement(tax_scheme_buyer, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CompanyID").text = buyer_data["vat_id"]
        tax_scheme = ET.SubElement(tax_scheme_buyer, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxScheme")
        ET.SubElement(tax_scheme, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID").text = "VAT"

    # PaymentTerms
    if data.get("payment_terms"):
        pmt_terms = ET.SubElement(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PaymentTerms")
        ET.SubElement(pmt_terms, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Note").text = data["payment_terms"]

    # TaxTotal
    tax_total = ET.SubElement(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxTotal")
    tax_amt_elem = ET.SubElement(tax_total, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxAmount", {"currencyID": "EUR"})
    tax_amt_elem.text = f"{float(data['total_tax_amount']):.2f}"

    # LegalMonetaryTotal
    legal_total = ET.SubElement(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}LegalMonetaryTotal")
    line_ext = ET.SubElement(legal_total, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}LineExtensionAmount", {"currencyID": "EUR"})
    line_ext.text = f"{float(data['total_net_amount']):.2f}"
    tax_excl = ET.SubElement(legal_total, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxExclusiveAmount", {"currencyID": "EUR"})
    tax_excl.text = f"{float(data['total_net_amount']):.2f}"
    tax_incl = ET.SubElement(legal_total, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxInclusiveAmount", {"currencyID": "EUR"})
    tax_incl.text = f"{float(data['total_gross_amount']):.2f}"
    payable = ET.SubElement(legal_total, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PayableAmount", {"currencyID": "EUR"})
    payable.text = f"{float(data['total_gross_amount']):.2f}"

    # InvoiceLines
    for idx, item in enumerate(data["line_items"], start=1):
        inv_line = ET.SubElement(root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}InvoiceLine")
        ET.SubElement(inv_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID").text = str(item.get("line_id", idx))
        
        invoiced_qty = ET.SubElement(inv_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}InvoicedQuantity", {
            "unitCode": item.get("unit_code", "C62")
        })
        invoiced_qty.text = f"{float(item['quantity']):.2f}"
        
        line_net = ET.SubElement(inv_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}LineExtensionAmount", {"currencyID": "EUR"})
        line_net.text = f"{float(item['net_amount']):.2f}"

        item_elem = ET.SubElement(inv_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Item")
        ET.SubElement(item_elem, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name").text = item["name"]

        tax_cat = ET.SubElement(item_elem, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}ClassifiedTaxCategory")
        ET.SubElement(tax_cat, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID").text = item.get("tax_category", "S")
        ET.SubElement(tax_cat, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Percent").text = f"{float(item.get('tax_percent', 19)):.2f}"
        tax_scheme_line = ET.SubElement(tax_cat, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxScheme")
        ET.SubElement(tax_scheme_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID").text = "VAT"

        price_elem = ET.SubElement(inv_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Price")
        price_amt = ET.SubElement(price_elem, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PriceAmount", {"currencyID": "EUR"})
        price_amt.text = f"{float(item['unit_price']):.2f}"

    rough_xml = ET.tostring(root, encoding="utf-8")
    parsed = minidom.parseString(rough_xml)
    return parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


if __name__ == "__main__":
    test_payload = {
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
        "payment_terms": "Zahlbar innerhalb von 14 Tagen rein netto.",
        "line_items": [
            {
                "line_id": "1",
                "name": "Full-Stack API Entwicklung in Python",
                "quantity": 10.0,
                "unit_code": "HUR",
                "unit_price": 120.0,
                "net_amount": 1200.0,
                "tax_category": "S",
                "tax_percent": 19
            }
        ],
        "total_net_amount": 1200.0,
        "total_tax_amount": 228.0,
        "total_gross_amount": 1428.0
    }
    xml_out = to_xrechnung_ubl_xml(test_payload)
    print("Sample XRechnung UBL 2.1 XML generated successfully:")
    print(xml_out[:600] + "...\n[TRUNCATED]")

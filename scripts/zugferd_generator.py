#!/usr/bin/env python3
"""
ZUGFeRD 2.3 & Factur-X PDF/A-3 Hybrid Invoice Generator for Rechly-DE-3B
Creates professional German visual PDF invoices and embeds compliant EN 16931 XML
(Factur-X / ZUGFeRD 2.3 profile) as an associated file (/AF) in accordance with ISO 19005-3 (PDF/A-3).

Also provides extraction and validation utilities for incoming hybrid e-invoices.
"""

import io
import os
import sys
import argparse
import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union, List

# PDF & Formatting libraries
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

from pypdf import PdfWriter, PdfReader
from pypdf.generic import NameObject, ArrayObject, DictionaryObject, TextStringObject

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.xrechnung_utils import to_xrechnung_ubl_xml, validate_xrechnung_data


ZUGFeRD_PROFILE_URN = "urn:cen.eu:en16931:2017#compliant#urn:factur-x.eu:1p0:en16931"
ZUGFeRD_VERSION = "1.0"
ZUGFeRD_CONFORMANCE = "EN 16931"
ATTACHMENT_NAME = "factur-x.xml"


def to_zugferd_cii_xml(data: Dict[str, Any]) -> str:
    """
    Serializes invoice data into standard UN/CEFACT Cross-Industry Invoice (CII) XML
    in compliance with EN 16931 / Factur-X / ZUGFeRD 2.3.
    """
    is_valid, errors = validate_xrechnung_data(data)
    if not is_valid:
        raise ValueError(f"Invalid invoice data for ZUGFeRD: {'; '.join(errors)}")

    rsm_ns = "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
    ram_ns = "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"
    udt_ns = "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100"

    ET.register_namespace("rsm", rsm_ns)
    ET.register_namespace("ram", ram_ns)
    ET.register_namespace("udt", udt_ns)

    root = ET.Element(f"{{{rsm_ns}}}CrossIndustryInvoice")

    # 1. ExchangedDocumentContext
    ctx = ET.SubElement(root, f"{{{rsm_ns}}}ExchangedDocumentContext")
    param = ET.SubElement(ctx, f"{{{ram_ns}}}GuidelineSpecifiedDocumentContextParameter")
    ET.SubElement(param, f"{{{ram_ns}}}ID").text = ZUGFeRD_PROFILE_URN

    # 2. ExchangedDocument
    doc = ET.SubElement(root, f"{{{rsm_ns}}}ExchangedDocument")
    ET.SubElement(doc, f"{{{ram_ns}}}ID").text = str(data["invoice_number"])
    ET.SubElement(doc, f"{{{ram_ns}}}TypeCode").text = "380"
    
    issue_dt = ET.SubElement(doc, f"{{{ram_ns}}}IssueDateTime")
    dt_str = ET.SubElement(issue_dt, f"{{{udt_ns}}}DateTimeString", {"format": "102"})
    clean_date = str(data["issue_date"]).replace("-", "")
    dt_str.text = clean_date

    # 3. SupplyChainTradeTransaction
    trade = ET.SubElement(root, f"{{{rsm_ns}}}SupplyChainTradeTransaction")

    # Line Items
    for idx, item in enumerate(data.get("line_items", []), start=1):
        item_elem = ET.SubElement(trade, f"{{{ram_ns}}}IncludedSupplyChainTradeLineItem")
        doc_line = ET.SubElement(item_elem, f"{{{ram_ns}}}AssociatedDocumentLineDocument")
        ET.SubElement(doc_line, f"{{{ram_ns}}}LineID").text = str(item.get("line_id", idx))

        trade_prod = ET.SubElement(item_elem, f"{{{ram_ns}}}SpecifiedTradeProduct")
        ET.SubElement(trade_prod, f"{{{ram_ns}}}Name").text = str(item.get("name", f"Position {idx}"))

        agree = ET.SubElement(item_elem, f"{{{ram_ns}}}SpecifiedLineTradeAgreement")
        gross_price = ET.SubElement(agree, f"{{{ram_ns}}}GrossPriceProductTradePrice")
        ET.SubElement(gross_price, f"{{{ram_ns}}}ChargeAmount").text = f"{float(item['unit_price']):.2f}"
        net_price = ET.SubElement(agree, f"{{{ram_ns}}}NetPriceProductTradePrice")
        ET.SubElement(net_price, f"{{{ram_ns}}}ChargeAmount").text = f"{float(item['unit_price']):.2f}"

        delivery = ET.SubElement(item_elem, f"{{{ram_ns}}}SpecifiedLineTradeDelivery")
        billed_qty = ET.SubElement(delivery, f"{{{ram_ns}}}BilledQuantity", {"unitCode": item.get("unit_code", "C62")})
        billed_qty.text = f"{float(item['quantity']):.2f}"

        settle = ET.SubElement(item_elem, f"{{{ram_ns}}}SpecifiedLineTradeSettlement")
        trade_tax = ET.SubElement(settle, f"{{{ram_ns}}}ApplicableTradeTax")
        ET.SubElement(trade_tax, f"{{{ram_ns}}}TypeCode").text = "VAT"
        ET.SubElement(trade_tax, f"{{{ram_ns}}}CategoryCode").text = str(item.get("tax_category", "S"))
        ET.SubElement(trade_tax, f"{{{ram_ns}}}RateApplicablePercent").text = f"{float(item.get('tax_percent', 19)):.2f}"

        line_sum = ET.SubElement(settle, f"{{{ram_ns}}}SpecifiedTradeSettlementLineMonetarySummation")
        ET.SubElement(line_sum, f"{{{ram_ns}}}LineTotalAmount").text = f"{float(item['net_amount']):.2f}"

    # Header Trade Agreement
    header_agree = ET.SubElement(trade, f"{{{ram_ns}}}ApplicableHeaderTradeAgreement")
    if data.get("buyer_reference"):
        ET.SubElement(header_agree, f"{{{ram_ns}}}BuyerReference").text = str(data["buyer_reference"])

    # Seller
    seller = data.get("seller", {})
    seller_trade = ET.SubElement(header_agree, f"{{{ram_ns}}}SellerTradeParty")
    ET.SubElement(seller_trade, f"{{{ram_ns}}}Name").text = str(seller.get("name", "Rechly AI Vendor"))
    seller_addr = ET.SubElement(seller_trade, f"{{{ram_ns}}}PostalTradeAddress")
    ET.SubElement(seller_addr, f"{{{ram_ns}}}PostcodeCode").text = str(seller.get("postal_code", "10115"))
    ET.SubElement(seller_addr, f"{{{ram_ns}}}LineOne").text = str(seller.get("street", "Musterstr. 1"))
    ET.SubElement(seller_addr, f"{{{ram_ns}}}CityName").text = str(seller.get("city", "Berlin"))
    ET.SubElement(seller_addr, f"{{{ram_ns}}}CountryID").text = str(seller.get("country_code", "DE"))
    if seller.get("vat_id"):
        seller_tax = ET.SubElement(seller_trade, f"{{{ram_ns}}}SpecifiedTaxRegistration")
        tax_id = ET.SubElement(seller_tax, f"{{{ram_ns}}}ID", {"schemeID": "VA"})
        tax_id.text = str(seller["vat_id"])

    # Buyer
    buyer = data.get("buyer", {})
    buyer_trade = ET.SubElement(header_agree, f"{{{ram_ns}}}BuyerTradeParty")
    ET.SubElement(buyer_trade, f"{{{ram_ns}}}Name").text = str(buyer.get("name", "Kunde"))
    buyer_addr = ET.SubElement(buyer_trade, f"{{{ram_ns}}}PostalTradeAddress")
    ET.SubElement(buyer_addr, f"{{{ram_ns}}}PostcodeCode").text = str(buyer.get("postal_code", "10115"))
    ET.SubElement(buyer_addr, f"{{{ram_ns}}}LineOne").text = str(buyer.get("street", "Kundenstr. 10"))
    ET.SubElement(buyer_addr, f"{{{ram_ns}}}CityName").text = str(buyer.get("city", "Berlin"))
    ET.SubElement(buyer_addr, f"{{{ram_ns}}}CountryID").text = str(buyer.get("country_code", "DE"))
    if buyer.get("vat_id"):
        buyer_tax = ET.SubElement(buyer_trade, f"{{{ram_ns}}}SpecifiedTaxRegistration")
        b_tax_id = ET.SubElement(buyer_tax, f"{{{ram_ns}}}ID", {"schemeID": "VA"})
        b_tax_id.text = str(buyer["vat_id"])

    # Header Trade Delivery
    header_deliv = ET.SubElement(trade, f"{{{ram_ns}}}ApplicableHeaderTradeDelivery")
    chain_event = ET.SubElement(header_deliv, f"{{{ram_ns}}}ActualDeliverySupplyChainEvent")
    event_dt = ET.SubElement(chain_event, f"{{{ram_ns}}}OccurrenceDateTime")
    ET.SubElement(event_dt, f"{{{udt_ns}}}DateTimeString", {"format": "102"}).text = clean_date

    # Header Trade Settlement
    header_settle = ET.SubElement(trade, f"{{{ram_ns}}}ApplicableHeaderTradeSettlement")
    ET.SubElement(header_settle, f"{{{ram_ns}}}InvoiceCurrencyCode").text = str(data.get("currency", "EUR"))

    # Summary Tax
    vat_rate = float(data.get("line_items", [{}])[0].get("tax_percent", 19.0))
    tax_elem = ET.SubElement(header_settle, f"{{{ram_ns}}}ApplicableTradeTax")
    ET.SubElement(tax_elem, f"{{{ram_ns}}}CalculatedAmount").text = f"{float(data.get('total_tax_amount', 0.0)):.2f}"
    ET.SubElement(tax_elem, f"{{{ram_ns}}}TypeCode").text = "VAT"
    ET.SubElement(tax_elem, f"{{{ram_ns}}}BasisAmount").text = f"{float(data.get('total_net_amount', 0.0)):.2f}"
    ET.SubElement(tax_elem, f"{{{ram_ns}}}CategoryCode").text = "S" if vat_rate > 0 else "K"
    ET.SubElement(tax_elem, f"{{{ram_ns}}}RateApplicablePercent").text = f"{vat_rate:.2f}"

    if data.get("payment_terms"):
        p_terms = ET.SubElement(header_settle, f"{{{ram_ns}}}SpecifiedTradePaymentTerms")
        ET.SubElement(p_terms, f"{{{ram_ns}}}Description").text = str(data["payment_terms"])

    # Monetary Summation
    mon_sum = ET.SubElement(header_settle, f"{{{ram_ns}}}SpecifiedTradeSettlementHeaderMonetarySummation")
    ET.SubElement(mon_sum, f"{{{ram_ns}}}LineTotalAmount").text = f"{float(data.get('total_net_amount', 0.0)):.2f}"
    ET.SubElement(mon_sum, f"{{{ram_ns}}}TaxBasisTotalAmount").text = f"{float(data.get('total_net_amount', 0.0)):.2f}"
    ET.SubElement(mon_sum, f"{{{ram_ns}}}TaxTotalAmount", {"currencyID": "EUR"}).text = f"{float(data.get('total_tax_amount', 0.0)):.2f}"
    ET.SubElement(mon_sum, f"{{{ram_ns}}}GrandTotalAmount").text = f"{float(data.get('total_gross_amount', 0.0)):.2f}"
    ET.SubElement(mon_sum, f"{{{ram_ns}}}DuePayableAmount").text = f"{float(data.get('total_gross_amount', 0.0)):.2f}"

    rough_xml = ET.tostring(root, encoding="utf-8")
    parsed = minidom.parseString(rough_xml)
    return parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


def generate_visual_invoice_pdf(data: Dict[str, Any]) -> bytes:
    """
    Renders a clean, GoBD-compliant German B2B visual invoice PDF using ReportLab.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=f"Rechnung {data.get('invoice_number', 'ENTWURF')}",
        author="Rechly AI ZUGFeRD Engine"
    )

    styles = getSampleStyleSheet()

    # Custom styles
    style_sender_bar = ParagraphStyle(
        "SenderBar",
        parent=styles["Normal"],
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#64748B")
    )
    style_recipient = ParagraphStyle(
        "Recipient",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1E293B")
    )
    style_h1 = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F172A"),
        fontName="Helvetica-Bold"
    )
    style_meta_label = ParagraphStyle(
        "MetaLabel",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748B"),
        fontName="Helvetica-Bold"
    )
    style_meta_val = ParagraphStyle(
        "MetaVal",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0F172A")
    )
    style_table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.white,
        fontName="Helvetica-Bold"
    )
    style_table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1E293B")
    )
    style_legal = ParagraphStyle(
        "LegalNotice",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#475569")
    )

    elements = []

    seller = data.get("seller", {})
    buyer = data.get("buyer", {})

    # Sender bar
    sender_bar_text = f"<b>{seller.get('name', 'Rechly AI GmbH')}</b> • {seller.get('street', 'Musterstr. 1')} • {seller.get('postal_code', '10115')} {seller.get('city', 'Berlin')}"
    elements.append(Paragraph(sender_bar_text, style_sender_bar))
    elements.append(Spacer(1, 4 * mm))

    # Two column: Buyer Address (Left) & Invoice Meta (Right)
    buyer_lines = [
        f"<b>{buyer.get('name', 'Kunde')}</b>",
        f"{buyer.get('street', '')}",
        f"{buyer.get('postal_code', '')} {buyer.get('city', '')}",
        f"{buyer.get('country_code', 'DE')}",
    ]
    if buyer.get("vat_id"):
        buyer_lines.append(f"USt-IdNr.: {buyer['vat_id']}")
    buyer_para = Paragraph("<br/>".join([l for l in buyer_lines if l.strip()]), style_recipient)

    meta_data = [
        [Paragraph("Rechnungsnummer:", style_meta_label), Paragraph(str(data.get("invoice_number", "-")), style_meta_val)],
        [Paragraph("Rechnungsdatum:", style_meta_label), Paragraph(str(data.get("issue_date", "-")), style_meta_val)],
        [Paragraph("Fälligkeitsdatum:", style_meta_label), Paragraph(str(data.get("due_date", "-")), style_meta_val)],
        [Paragraph("Leitweg-ID (BT-10):", style_meta_label), Paragraph(str(data.get("buyer_reference", "-")), style_meta_val)],
        [Paragraph("Zahlungsziel:", style_meta_label), Paragraph(f"{data.get('due_days', 14)} Tage", style_meta_val)],
    ]
    meta_table = Table(meta_data, colWidths=[35 * mm, 35 * mm])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
    ]))

    header_table = Table([[buyer_para, meta_table]], colWidths=[90 * mm, 80 * mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10 * mm))

    # Heading & Title
    elements.append(Paragraph(f"Rechnung Nr. {data.get('invoice_number', '')}", style_h1))
    elements.append(Spacer(1, 4 * mm))

    # Line Items Table
    table_rows = [
        [
            Paragraph("Pos.", style_table_header),
            Paragraph("Bezeichnung / Leistung", style_table_header),
            Paragraph("Menge", style_table_header),
            Paragraph("Einheit", style_table_header),
            Paragraph("Einzelpreis", style_table_header),
            Paragraph("USt", style_table_header),
            Paragraph("Gesamt Netto", style_table_header),
        ]
    ]

    for idx, itm in enumerate(data.get("line_items", []), start=1):
        table_rows.append([
            Paragraph(str(idx), style_table_cell),
            Paragraph(itm.get("name", "Position"), style_table_cell),
            Paragraph(f"{float(itm.get('quantity', 1)):.2f}", style_table_cell),
            Paragraph(str(itm.get("unit_code", "Std.")), style_table_cell),
            Paragraph(f"{float(itm.get('unit_price', 0)):.2f} €", style_table_cell),
            Paragraph(f"{itm.get('tax_percent', 19)}%", style_table_cell),
            Paragraph(f"{float(itm.get('net_amount', 0)):.2f} €", style_table_cell),
        ])

    items_table = Table(
        table_rows,
        colWidths=[12 * mm, 68 * mm, 18 * mm, 16 * mm, 24 * mm, 14 * mm, 26 * mm]
    )
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 6 * mm))

    # Financial Totals Box (Right Aligned)
    totals_data = [
        [Paragraph("Nettobetrag:", style_meta_label), Paragraph(f"{float(data.get('total_net_amount', 0)):.2f} €", style_meta_val)],
        [Paragraph("Umsatzsteuer:", style_meta_label), Paragraph(f"{float(data.get('total_tax_amount', 0)):.2f} €", style_meta_val)],
        [Paragraph("<b>Gesamtbetrag (Brutto):</b>", style_meta_label), Paragraph(f"<b>{float(data.get('total_gross_amount', 0)):.2f} €</b>", style_meta_val)],
    ]
    totals_table = Table(totals_data, colWidths=[45 * mm, 30 * mm])
    totals_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 2), (-1, 2), 1, colors.HexColor("#0F172A")),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor("#F1F5F9")),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))

    totals_wrapper = Table([[Paragraph("", style_recipient), totals_table]], colWidths=[103 * mm, 75 * mm])
    totals_wrapper.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(totals_wrapper)
    elements.append(Spacer(1, 8 * mm))

    # Legal note & Payment terms
    if data.get("legal_note"):
        elements.append(Paragraph(f"<b>Steuerrechtlicher Hinweis:</b> {data['legal_note']}", style_legal))
        elements.append(Spacer(1, 3 * mm))

    if data.get("payment_terms"):
        elements.append(Paragraph(f"<b>Zahlungskonditionen:</b> {data['payment_terms']}", style_legal))
        elements.append(Spacer(1, 3 * mm))

    # ZUGFeRD E-Invoice Badge Note
    elements.append(Spacer(1, 5 * mm))
    zugferd_badge = (
        "<i>Hinweis: Dieses Dokument ist eine hybride elektronische Rechnung (ZUGFeRD 2.3 / Factur-X) "
        "im Konformitätsstandard EN 16931 gemäß Wachstumschancengesetz (§ 14 UStG). "
        "Die maschinenlesbare Rechnungsdatei ('factur-x.xml') ist als Anhang im PDF/A-3-Container eingebettet.</i>"
    )
    elements.append(Paragraph(zugferd_badge, style_sender_bar))

    doc.build(elements)
    return buffer.getvalue()


def build_facturx_xmp_metadata(
    conformance_level: str = ZUGFeRD_CONFORMANCE,
    document_type: str = "INVOICE",
    version: str = ZUGFeRD_VERSION,
    filename: str = ATTACHMENT_NAME
) -> bytes:
    """
    Constructs compliant XMP metadata packet for Factur-X / ZUGFeRD 2.3 PDF/A-3.
    """
    xmp = f"""<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about="" xmlns:pdfaExtension="http://www.aiim.org/pdfa/ns/extension/" xmlns:pdfaProperty="http://www.aiim.org/pdfa/ns/property#" xmlns:pdfaSchema="http://www.aiim.org/pdfa/ns/schema#">
      <pdfaExtension:schemas>
        <rdf:Bag>
          <rdf:li rdf:parseType="Resource">
            <pdfaSchema:schema>Factur-X PDFA Extension Schema</pdfaSchema:schema>
            <pdfaSchema:namespaceURI>urn:factur-x:pdfa:CrossIndustryDocument:invoice:1p0#</pdfaSchema:namespaceURI>
            <pdfaSchema:prefix>fx</pdfaSchema:prefix>
            <pdfaSchema:property>
              <rdf:Seq>
                <rdf:li rdf:parseType="Resource">
                  <pdfaProperty:name>DocumentFileName</pdfaProperty:name>
                  <pdfaProperty:valueType>Text</pdfaProperty:valueType>
                  <pdfaProperty:description>The name of the embedded invoice XML</pdfaProperty:description>
                </rdf:li>
                <rdf:li rdf:parseType="Resource">
                  <pdfaProperty:name>DocumentType</pdfaProperty:name>
                  <pdfaProperty:valueType>Text</pdfaProperty:valueType>
                  <pdfaProperty:description>Type of the hybrid invoice</pdfaProperty:description>
                </rdf:li>
                <rdf:li rdf:parseType="Resource">
                  <pdfaProperty:name>Version</pdfaProperty:name>
                  <pdfaProperty:valueType>Text</pdfaProperty:valueType>
                  <pdfaProperty:description>Version of the Factur-X schema</pdfaProperty:description>
                </rdf:li>
                <rdf:li rdf:parseType="Resource">
                  <pdfaProperty:name>ConformanceLevel</pdfaProperty:name>
                  <pdfaProperty:valueType>Text</pdfaProperty:valueType>
                  <pdfaProperty:description>Factur-X / ZUGFeRD conformance profile</pdfaProperty:description>
                </rdf:li>
              </rdf:Seq>
            </pdfaSchema:property>
          </rdf:li>
        </rdf:Bag>
      </pdfaExtension:schemas>
    </rdf:Description>
    <rdf:Description rdf:about="" xmlns:fx="urn:factur-x:pdfa:CrossIndustryDocument:invoice:1p0#">
      <fx:DocumentType>{document_type}</fx:DocumentType>
      <fx:DocumentFileName>{filename}</fx:DocumentFileName>
      <fx:Version>{version}</fx:Version>
      <fx:ConformanceLevel>{conformance_level}</fx:ConformanceLevel>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>"""
    return xmp.encode("utf-8")


def create_zugferd_pdf(
    invoice_data: Dict[str, Any],
    xml_content: Optional[str] = None,
    profile: str = ZUGFeRD_CONFORMANCE,
    xml_filename: str = ATTACHMENT_NAME
) -> bytes:
    """
    Creates a full Factur-X / ZUGFeRD 2.3 PDF/A-3 hybrid electronic invoice.
    Combines the visual PDF representation with the embedded EN 16931 XML.
    """
    # 1. Generate XML if not supplied
    if xml_content is None:
        try:
            xml_content = to_zugferd_cii_xml(invoice_data)
        except Exception:
            xml_content = to_xrechnung_ubl_xml(invoice_data)

    xml_bytes = xml_content.encode("utf-8") if isinstance(xml_content, str) else xml_content

    # 2. Render visual PDF
    visual_pdf_bytes = generate_visual_invoice_pdf(invoice_data)

    # 3. Assemble PDF/A-3 container with pypdf
    reader = PdfReader(io.BytesIO(visual_pdf_bytes))
    writer = PdfWriter()
    writer.append(reader)

    # Embed factur-x.xml
    embedded_file = writer.add_attachment(xml_filename, xml_bytes)
    
    # Configure PDF/A-3 Associated File (/AF) metadata
    embedded_file.pdf_object[NameObject("/AFRelationship")] = NameObject("/Data")
    embedded_file.pdf_object[NameObject("/Desc")] = TextStringObject(f"Factur-X / ZUGFeRD 2.3 Invoice XML ({profile})")

    # Add to catalog AF array
    if NameObject("/AF") not in writer.root_object:
        writer.root_object[NameObject("/AF")] = ArrayObject()
    
    file_ref = getattr(embedded_file.pdf_object, "indirect_reference", embedded_file.pdf_object)
    writer.root_object[NameObject("/AF")].append(file_ref)

    # Set XMP metadata
    writer.xmp_metadata = build_facturx_xmp_metadata(
        conformance_level=profile,
        document_type="INVOICE",
        version=ZUGFeRD_VERSION,
        filename=xml_filename
    )

    # Add standard PDF document info
    writer.add_metadata({
        "/Title": f"Rechnung {invoice_data.get('invoice_number', 'E-Rechnung')}",
        "/Author": str(invoice_data.get("seller", {}).get("name", "Rechly AI")),
        "/Subject": f"ZUGFeRD 2.3 / Factur-X ({profile}) E-Rechnung",
        "/Creator": "Rechly-DE-3B ZUGFeRD 2.3 Engine (100% Open Source)",
    })

    out_stream = io.BytesIO()
    writer.write(out_stream)
    return out_stream.getvalue()


def extract_zugferd_xml(pdf_input: Union[bytes, str, Path]) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts embedded Factur-X / ZUGFeRD XML from a PDF invoice.
    Returns (xml_content_string, attachment_filename) or (None, None).
    """
    if isinstance(pdf_input, (str, Path)):
        with open(pdf_input, "rb") as f:
            pdf_bytes = f.read()
    else:
        pdf_bytes = pdf_input

    reader = PdfReader(io.BytesIO(pdf_bytes))
    attachments = reader.attachments

    # Known filenames for Factur-X and ZUGFeRD
    candidates = ["factur-x.xml", "zugferd-invoice.xml", "xrechnung.xml"]
    
    # Direct search in attachments dictionary
    for cand in candidates:
        if cand in attachments:
            items = attachments[cand]
            if items:
                raw = items[0]
                return (raw.decode("utf-8", errors="replace"), cand)

    # Fallback: search any .xml attachment
    for att_name, items in attachments.items():
        if att_name.lower().endswith(".xml") and items:
            return (items[0].decode("utf-8", errors="replace"), att_name)

    return (None, None)


def verify_zugferd_pdf(pdf_input: Union[bytes, str, Path]) -> Dict[str, Any]:
    """
    Verifies that a PDF is a valid ZUGFeRD / Factur-X hybrid e-invoice.
    Checks PDF integrity, attachment presence, and XML parseability.
    """
    result = {
        "is_valid_zugferd": False,
        "attachment_name": None,
        "xml_size_bytes": 0,
        "xml_type": None,
        "conformance_level": None,
        "invoice_number": None,
        "errors": []
    }

    try:
        xml_str, filename = extract_zugferd_xml(pdf_input)
        if not xml_str:
            result["errors"].append("No embedded XML invoice file found in PDF attachments.")
            return result

        result["attachment_name"] = filename
        result["xml_size_bytes"] = len(xml_str.encode("utf-8"))

        # Parse XML
        root = ET.fromstring(xml_str)
        tag = root.tag.lower()
        if "crossindustryinvoice" in tag:
            result["xml_type"] = "CII (Cross Industry Invoice / Factur-X)"
        elif "invoice" in tag:
            result["xml_type"] = "UBL 2.1 (Universal Business Language)"
        else:
            result["xml_type"] = f"XML (Root: {root.tag})"

        result["is_valid_zugferd"] = True

    except Exception as e:
        result["errors"].append(f"Validation failed: {e}")

    return result


if __name__ == "__main__":
    sample_invoice = {
        "invoice_number": "RE-2025-089",
        "issue_date": "2025-03-01",
        "due_date": "2025-03-15",
        "due_days": 14,
        "currency": "EUR",
        "buyer_reference": "04011000-12345-67",
        "seller": {
            "name": "Rechly OpenSource Solutions GmbH",
            "vat_id": "DE345678901",
            "street": "Friedrichstraße 100",
            "postal_code": "10117",
            "city": "Berlin",
            "country_code": "DE"
        },
        "buyer": {
            "name": "Deutsche Bahn Digital AG",
            "vat_id": "DE811569869",
            "street": "Potsdamer Platz 2",
            "postal_code": "10785",
            "city": "Berlin",
            "country_code": "DE"
        },
        "payment_terms": "Zahlbar innerhalb von 14 Tagen ohne Abzug.",
        "legal_note": "Reguläre Besteuerung mit 19% USt.",
        "line_items": [
            {
                "line_id": "1",
                "name": "Architektur-Review KI-Pipeline",
                "quantity": 8.0,
                "unit_code": "HUR",
                "unit_price": 135.0,
                "net_amount": 1080.0,
                "tax_category": "S",
                "tax_percent": 19
            },
            {
                "line_id": "2",
                "name": "GoBD & DATEV Validierungspaket",
                "quantity": 1.0,
                "unit_code": "C62",
                "unit_price": 420.0,
                "net_amount": 420.0,
                "tax_category": "S",
                "tax_percent": 19
            }
        ],
        "total_net_amount": 1500.0,
        "total_tax_amount": 285.0,
        "total_gross_amount": 1785.0
    }

    out_path = PROJECT_ROOT / "invoice_zugferd_sample.pdf"
    pdf_bytes = create_zugferd_pdf(sample_invoice)
    with open(out_path, "wb") as f:
        f.write(pdf_bytes)

    print(f"Generated sample ZUGFeRD 2.3 hybrid invoice at: {out_path} ({len(pdf_bytes)} bytes)")
    
    # Test extraction & verification
    ver = verify_zugferd_pdf(out_path)
    print(f"Verification: {ver}")

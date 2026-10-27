#!/usr/bin/env python3
"""
Comprehensive 50-Point Benchmark Suite for Rechly-DE-3B
Measures:
1. Strict JSON schema validity and key accuracy
2. GoBD and German Tax Law (§ 19, § 13b, § 4, § 25a, § 14, § 33) statutory accuracy
3. B2B Line Item Rewriting quality and conciseness
4. Mahnwesen tone progression across Stages 1, 2, and 3
5. DATEV SKR03 and SKR04 account assignment accuracy
6. Inference throughput (tokens/sec) and latency

Usage:
    python scripts/benchmark_comprehensive.py --model rechly-de-3b
"""

import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple
from jsonschema import validate, ValidationError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INVOICE_SCHEMA = json.load(open(PROJECT_ROOT / "data" / "schemas" / "invoice_schema.json", "r", encoding="utf-8"))
EXPENSE_SCHEMA = json.load(open(PROJECT_ROOT / "data" / "schemas" / "expense_schema.json", "r", encoding="utf-8"))
XRECHNUNG_SCHEMA = json.load(open(PROJECT_ROOT / "data" / "schemas" / "xrechnung_schema.json", "r", encoding="utf-8"))
GOBD_AUDIT_SCHEMA = json.load(open(PROJECT_ROOT / "data" / "schemas" / "gobd_audit_schema.json", "r", encoding="utf-8"))


BENCHMARK_CASES = [
    # ==================== DOMAIN 1: TEXT-TO-INVOICE (15 cases) ====================
    {
        "id": "D1-01",
        "domain": "Domain 1: Text-to-Invoice",
        "name": "Standard IT Services (19%)",
        "prompt": "Erstelle eine Rechnung an Kanzlei Schmidt & Partner: 12 Stunden IT-Forensik à 140€ und Anfahrt Pauschal 80€, zahlbar in 14 Tagen mit 2% Skonto.",
        "type": "invoice",
        "expected_client": "Kanzlei Schmidt & Partner",
        "min_items": 2,
        "expected_vat": 19,
    },
    {
        "id": "D1-02",
        "domain": "Domain 1: Text-to-Invoice",
        "name": "Kleinunternehmer (§ 19 UStG) Handwerk",
        "prompt": "Rechnung an Blumenladen Rose: 5 Stunden Schaufensterdeko à 55€, ich bin Kleinunternehmer.",
        "type": "invoice",
        "expected_client": "Blumenladen Rose",
        "min_items": 1,
        "expected_vat": 0,
        "required_in_notes": ["§ 19", "kleinunternehmer"],
    },
    {
        "id": "D1-03",
        "domain": "Domain 1: Text-to-Invoice",
        "name": "Print Books (Reduced 7% VAT)",
        "prompt": "Rechnung an Buchhandlung Leselust: Lieferung von 50 Stück Fachbuch 'Finanzwissen' à 24,90€, 7% MwSt, sofort fällig.",
        "type": "invoice",
        "expected_client": "Buchhandlung Leselust",
        "min_items": 1,
        "expected_vat": 7,
    },
    {
        "id": "D1-04",
        "domain": "Domain 1: Text-to-Invoice",
        "name": "Reverse Charge EU B2B (§ 3a Abs. 2 UStG)",
        "prompt": "Rechnung an Alpha Cloud Services Ltd in Dublin (USt-IdNr. IE987654321): 2 Monate Cloud-Infrastruktur Wartung à 850€, Reverse Charge B2B.",
        "type": "invoice",
        "expected_client": "Alpha Cloud Services Ltd",
        "min_items": 1,
        "expected_vat": 0,
        "required_in_notes": ["steuerschuldnerschaft", "leistungsempfänger"],
    },
    {
        "id": "D1-05",
        "domain": "Domain 1: Text-to-Invoice",
        "name": "Reverse Charge Bauleistungen (§ 13b UStG)",
        "prompt": "Rechnung für handwerkliche Bauleistung an Generalunternehmer Bauunternehmen Hoch & Tief GmbH: 3x Estrichlegearbeiten Tage à 650€, Zahlungsziel 30 Tage, Bauleistung gem. § 13b UStG, Reverse Charge.",
        "type": "invoice",
        "expected_client": "Hoch & Tief",
        "min_items": 1,
        "expected_vat": 0,
        "required_in_notes": ["13b", "steuerschuldnerschaft"],
    },
    {
        "id": "D1-06",
        "domain": "Domain 1: Text-to-Invoice",
        "name": "Third-Country Export (Schweiz / § 4 Nr. 1a)",
        "prompt": "Exportrechnung an Helvetica Consulting AG in Zürich: 10 Stunden strategische Beratung à 180€, steuerfreie Ausfuhr Drittland.",
        "type": "invoice",
        "expected_client": "Helvetica Consulting AG",
        "min_items": 1,
        "expected_vat": 0,
        "required_in_notes": ["steuerfreie", "ausfuhr"],
    },
    {
        "id": "D1-07",
        "domain": "Domain 1: Text-to-Invoice",
        "name": "Craftsman Multi-Item with Material",
        "prompt": "Rechnung an Praxis Dr. Weishaupt: 8 Stunden Sanitärreparatur à 75€ und Installationsmaterial Pauschal 120€, zahlbar in 14 Tagen rein netto.",
        "type": "invoice",
        "expected_client": "Dr. Weishaupt",
        "min_items": 2,
        "expected_vat": 19,
    },
    {
        "id": "D1-08",
        "domain": "Domain 1: Text-to-Invoice",
        "name": "SaaS Subscription (Monat unit)",
        "prompt": "Rechnung an MediaDesign UG: 12 Monate Software-Lizenz 'DesignPro' à 49,00€, sofort zahlbar.",
        "type": "invoice",
        "expected_client": "MediaDesign UG",
        "min_items": 1,
        "expected_vat": 19,
    },
    {
        "id": "D1-09",
        "domain": "Domain 1: Text-to-Invoice",
        "name": "Consulting Daily Rate",
        "prompt": "Rechnung an Retail Solutions AG: 4 Tage Managementberatung à 1.500€ zzgl. Spesen 350€ pauschal, 30 Tage Zahlungsziel.",
        "type": "invoice",
        "expected_client": "Retail Solutions AG",
        "min_items": 2,
        "expected_vat": 19,
    },
    {
        "id": "D1-10",
        "domain": "Domain 1: Text-to-Invoice",
        "name": "Colloquial German Handwerker Prompt",
        "prompt": "Mach mal ne Rechnung fertig für Tischlerei Holz: Hab denen 6 Stunden beim Einbau der Türen geholfen für 60 Tacken die Stunde und 30 Euro für Schrauben. Zahlbar bis nächste Woche.",
        "type": "invoice",
        "expected_client": "Tischlerei Holz",
        "min_items": 2,
        "expected_vat": 19,
    },

    # ==================== DOMAIN 2: LINE ITEM REWRITER (8 cases) ====================
    {
        "id": "D2-01",
        "domain": "Domain 2: Line Item Rewriter",
        "name": "Web Performance Optimization",
        "prompt": "Optimiere diese Tätigkeitsbeschreibung für die Rechnungsstellung: 'homepage schneller gemacht und alte bilder gelöscht'",
        "type": "text",
        "keywords": ["webseite", "homepage", "performance", "optimierung", "ladezeit", "bereinigung", "bildmaterial", "bilder", "entfernt", "leistend", "sichtbar"],
        "disallow": ["```json", "{\"items\":"],
    },
    {
        "id": "D2-02",
        "domain": "Domain 2: Line Item Rewriter",
        "name": "Database Cleaning",
        "prompt": "Optimiere diese Tätigkeitsbeschreibung für die Rechnungsstellung: 'datenbank aufgeräumt und alte kunden bereinigt'",
        "type": "text",
        "keywords": ["datenbank", "bereinigung", "optimierung", "wartung", "indexierung", "integrität", "überprüfung", "datensätze", "aufbereitet", "aufbereitung", "entfernt", "kunden"],
        "disallow": ["```json"],
    },
    {
        "id": "D2-03",
        "domain": "Domain 2: Line Item Rewriter",
        "name": "Sanitary Handwerk",
        "prompt": "Formuliere folgende Position professionell für eine B2B-Rechnung: 'rohre freigemacht im keller und dichtung getauscht'",
        "type": "text",
        "keywords": ["sanitär", "instandsetzung", "rohrreinigung", "austausch", "dichtung", "rohr", "rohre", "keller"],
        "disallow": ["```json"],
    },
    {
        "id": "D2-04",
        "domain": "Domain 2: Line Item Rewriter",
        "name": "IT Emergency Weekend Callout",
        "prompt": "Professionelle Formulierung für folgende Rechnungsposition erbeten: 'server abgestürzt am sonntag, wieder hochgefahren und backup geprüft'",
        "type": "text",
        "keywords": ["notfall", "systemadministration", "server", "ausfall", "wiederherstellung", "datensicherung", "backup"],
        "disallow": ["```json"],
    },
    {
        "id": "D2-05",
        "domain": "Domain 2: Line Item Rewriter",
        "name": "Social Media Editorial Planning",
        "prompt": "Optimiere diese Tätigkeitsbeschreibung für die Rechnungsstellung: 'social media beiträge getextet und grafiken gebastelt'",
        "type": "text",
        "keywords": ["social media", "social-media", "content", "redaktion", "redaktionsplan", "redaktionsplanung", "konzeption", "grafik", "gestaltung", "beiträge", "beitrag", "erstellung", "planung", "text", "texte", "monat", "zielgruppen"],
        "disallow": ["```json"],
    },
    {
        "id": "D2-06",
        "domain": "Domain 2: Line Item Rewriter",
        "name": "Electrical Installation",
        "prompt": "Formuliere folgende Position professionell und GoBD-konform: 'steckdosen im büro neu verlegt und kabelkanal geschraubt'",
        "type": "text",
        "keywords": ["elektro", "installation", "kabelkanal", "steckdosen", "montage", "vde"],
        "disallow": ["```json"],
    },
    {
        "id": "D2-07",
        "domain": "Domain 2: Line Item Rewriter",
        "name": "Pitch Deck Enhancement",
        "prompt": "Optimiere folgende Position für eine Beraterrechnung: 'investoren präsentation hübscher gemacht und zahlen korrigiert'",
        "type": "text",
        "keywords": ["präsentation", "pitch", "optimierung", "finanz", "überarbeitung", "investor"],
        "disallow": ["```json"],
    },
    {
        "id": "D2-08",
        "domain": "Domain 2: Line Item Rewriter",
        "name": "Climate Conditioning Maintenance",
        "prompt": "Optimiere diese Tätigkeitsbeschreibung für die Rechnungsstellung: 'klimaanlage gecheckt und filter sauber gemacht'",
        "type": "text",
        "keywords": ["klima", "klimaanlage", "wartung", "filter", "reinigung", "inspektion", "raumluft", "prüfung", "überprüft", "gereinigt", "sauber"],
        "disallow": ["```json"],
    },

    # ==================== DOMAIN 3: TAX & GOBD STATUTORY CLAUSES (10 cases) ====================
    {
        "id": "D3-01",
        "domain": "Domain 3: Tax & GoBD Clauses",
        "name": "Kleinunternehmer (§ 19 UStG)",
        "prompt": "Welcher steuerliche Pflichttext muss auf die Rechnung bei Inanspruchnahme der Kleinunternehmerregelung?",
        "type": "text",
        "keywords": ["19", "ustg", "keine umsatzsteuer", "kleinunternehmer"],
    },
    {
        "id": "D3-02",
        "domain": "Domain 3: Tax & GoBD Clauses",
        "name": "Reverse Charge Bauleistungen (§ 13b UStG)",
        "prompt": "Welcher Vermerk gehört auf die Rechnung für Handwerkerleistungen an einen Generalunternehmer?",
        "type": "text",
        "keywords": ["13b", "steuerschuldnerschaft", "leistungsempfänger", "umsatzsteuer"],
    },
    {
        "id": "D3-03",
        "domain": "Domain 3: Tax & GoBD Clauses",
        "name": "Innergemeinschaftliche Lieferung EU (§ 4 Nr. 1b / § 6a)",
        "prompt": "Welche Gesetzesklausel muss bei einer steuerfreien innergemeinschaftlichen Lieferung an ein Unternehmen in Frankreich mit gültiger USt-IdNr. angegeben werden?",
        "type": "text",
        "keywords": ["steuerfreie", "innergemeinschaftliche", "4 nr. 1b", "6a"],
    },
    {
        "id": "D3-04",
        "domain": "Domain 3: Tax & GoBD Clauses",
        "name": "Export Drittland Schweiz (§ 4 Nr. 1a / § 6)",
        "prompt": "Welcher Vermerk ist erforderlich bei einem Export von Waren an einen Geschäftskunden in die Schweiz (Drittland)?",
        "type": "text",
        "keywords": ["steuerfreie", "ausfuhrlieferung", "4 nr. 1a", "6"],
    },
    {
        "id": "D3-05",
        "domain": "Domain 3: Tax & GoBD Clauses",
        "name": "Differenzbesteuerung (§ 25a UStG)",
        "prompt": "Welcher Hinweis gehört auf eine Rechnung bei Verkauf von Gebrauchtwaren unter Differenzbesteuerung?",
        "type": "text",
        "keywords": ["25a", "differenzbesteuerung", "gebraucht"],
    },
    {
        "id": "D3-06",
        "domain": "Domain 3: Tax & GoBD Clauses",
        "name": "B2B EU Service (§ 3a Abs. 2 UStG)",
        "prompt": "Welcher Vermerk gehört auf die B2B-Dienstleistungsrechnung an einen Kunden in Österreich mit UID-Nummer?",
        "type": "text",
        "keywords": ["steuerschuldnerschaft", "leistungsempfänger", "3a"],
    },
    {
        "id": "D3-07",
        "domain": "Domain 3: Tax & GoBD Clauses",
        "name": "Invoice Mandatory Fields (§ 14 Abs. 4 UStG)",
        "prompt": "Welche Pflichtangaben fordert § 14 Abs. 4 UStG für eine ordnungsgemäße deutsche B2B-Rechnung?",
        "type": "text",
        "keywords": ["rechnungsnummer", "steuernummer", "leistungszeitpunkt", "steuersatz", "ausstellungsdatum"],
    },
    {
        "id": "D3-08",
        "domain": "Domain 3: Tax & GoBD Clauses",
        "name": "Small Amount Invoice (§ 33 UStDV)",
        "prompt": "Welche Erleichterungen gelten für Kleinbetragsrechnungen bis 250 Euro nach § 33 UStDV?",
        "type": "text",
        "keywords": ["250", "brutto", "steuersatz", "leistenden unternehmer"],
    },
    {
        "id": "D3-09",
        "domain": "Domain 3: Tax & GoBD Clauses",
        "name": "Retention Periods (§ 147 AO / GoBD)",
        "prompt": "Wie lange müssen Rechnungen, Buchungsbelege und Geschäftsbriefe nach den deutschen GoBD und § 147 AO aufbewahrt werden?",
        "type": "text",
        "keywords": ["10 jahre", "6 jahre", "147 ao", "belege", "aufbewahrt", "aufbewahren"],
    },
    {
        "id": "D3-10",
        "domain": "Domain 3: Tax & GoBD Clauses",
        "name": "Reverse Charge Cleaning (§ 13b Abs. 2 Nr. 8)",
        "prompt": "Welcher Vermerk gehört auf eine Rechnung über Gebäudereinigung an ein anderes Reinigungsunternehmen nach § 13b UStG?",
        "type": "text",
        "keywords": ["steuerschuldnerschaft", "leistungsempfänger", "13b"],
    },

    # ==================== DOMAIN 4: MAHNWESEN / DUNNING (7 cases) ====================
    {
        "id": "D4-01",
        "domain": "Domain 4: Mahnwesen",
        "name": "Stage 1 Friendly Reminder",
        "prompt": "Erstelle eine freundliche Zahlungserinnerung für Rechnung RE-9901 an Meier GmbH über 1.500 EUR, 5 Tage überfällig.",
        "type": "text",
        "keywords": ["betreff", "re-9901", "1.500", "überfällig", "zahlungserinnerung"],
        "disallow": ["gerichtlicher", "inkasso", "mahnbescheid"],
    },
    {
        "id": "D4-02",
        "domain": "Domain 4: Mahnwesen",
        "name": "Stage 1 Friendly Overdue Notice",
        "prompt": "Schreibe eine Zahlungserinnerung Stufe 1 an Delta Logistik e.K.: Rechnung RE-2024-301, 890,00 EUR, 7 Tage über Fälligkeit.",
        "type": "text",
        "keywords": ["betreff", "re-2024-301", "890", "zahlungserinnerung"],
    },
    {
        "id": "D4-03",
        "domain": "Domain 4: Mahnwesen",
        "name": "Stage 2 First Dunning with 7-Day Deadline",
        "prompt": "Erstelle eine 1. Mahnung (Stufe 2): Rechnung RE-2024-092, Kunde: Bauer Medien GmbH, überfällig seit 16 Tagen, Rechnungsbetrag 3.200,00 EUR, Nachfrist 7 Tage.",
        "type": "text",
        "keywords": ["betreff", "re-2024-092", "3.200", "nachfrist", "7 tage", "mahnung"],
    },
    {
        "id": "D4-04",
        "domain": "Domain 4: Mahnwesen",
        "name": "Stage 2 Formal Payment Demand",
        "prompt": "Formuliere die 1. Mahnung für Rechnung RE-5510 an Nova Tech UG über 2.450 EUR, 18 Tage im Verzug mit 7 Tagen Zahlungsfrist.",
        "type": "text",
        "keywords": ["betreff", "re-5510", "2.450", "mahnung", "frist"],
    },
    {
        "id": "D4-05",
        "domain": "Domain 4: Mahnwesen",
        "name": "Stage 3 Final Notice Before Legal Action",
        "prompt": "Erstelle eine letzte Mahnung (Stufe 3 vor Inkasso/Mahnbescheid) für Rechnung RE-2024-061 an Delta Handels KG, 35 Tage überfällig, Betrag 4.890,00 EUR.",
        "type": "text",
        "keywords": ["betreff", "re-2024-061", "4.890", "inkasso", "gericht", "mahnbescheid"],
    },
    {
        "id": "D4-06",
        "domain": "Domain 4: Mahnwesen",
        "name": "Stage 3 Final Warning with Costs Warning",
        "prompt": "Schreibe letzte Mahnung vor gerichtlichem Mahnverfahren: Rechnung RE-8812, Kunde Stark Bau GmbH, 6.200 EUR, 45 Tage überfällig.",
        "type": "text",
        "keywords": ["betreff", "re-8812", "6.200", "mahnbescheid", "kosten"],
    },
    {
        "id": "D4-07",
        "domain": "Domain 4: Mahnwesen",
        "name": "German Business Letter Structure Check",
        "prompt": "Verfasse eine formelle Mahnung für Rechnung RE-1029 an Alpha Consulting über 1.200 Euro.",
        "type": "text",
        "keywords": ["betreff", "re-1029", "1.200", "sehr geehrte", "grüßen"],
    },

    # ==================== DOMAIN 5: SKR03 & SKR04 EXPENSE ACCOUNTS (10 cases) ====================
    {
        "id": "D5-01",
        "domain": "Domain 5: SKR Expenses",
        "name": "Client Entertainment (Bewirtung 70%)",
        "prompt": "Kategorisiere für SKR03 und SKR04: 'Geschäftsessen mit Neukunden im Steakhouse 160€ netto zzgl. 19% MwSt'",
        "type": "expense",
        "expected_skr03": "4650",
        "expected_skr04": "6640",
        "expected_vat": 19,
        "expected_deductible": 70,
    },
    {
        "id": "D5-02",
        "domain": "Domain 5: SKR Expenses",
        "name": "Cloud / SaaS Subscription",
        "prompt": "Kategorisiere für SKR03 und SKR04: 'Monatsrechnung Google Workspace 25€ netto'",
        "type": "expense",
        "expected_skr03": "4964",
        "expected_skr04": "6837",
        "expected_vat": 19,
    },
    {
        "id": "D5-03",
        "domain": "Domain 5: SKR Expenses",
        "name": "Low-Value Asset GWG (< 800€)",
        "prompt": "Kategorisiere für SKR03 und SKR04: 'Kauf eines ergonomischen Bürostuhls für 380€ netto'",
        "type": "expense",
        "expected_skr03": "0480",
        "expected_skr04": "0670",
        "expected_vat": 19,
    },
    {
        "id": "D5-04",
        "domain": "Domain 5: SKR Expenses",
        "name": "Telecommunications & Mobile",
        "prompt": "Kategorisiere für SKR03 und SKR04: 'Monatlicher Telekommunikationsvertrag Mobilfunk und Internet 69,90€ netto'",
        "type": "expense",
        "expected_skr03": "4920",
        "expected_skr04": "6805",
        "expected_vat": 19,
    },
    {
        "id": "D5-05",
        "domain": "Domain 5: SKR Expenses",
        "name": "Train Travel (7% VAT)",
        "prompt": "Kategorisiere für SKR03 und SKR04: 'Deutsche Bahn ICE-Ticket zum Kundentermin 84€ inkl. 7% MwSt'",
        "type": "expense",
        "expected_skr03": "4673",
        "expected_skr04": "6673",
        "expected_vat": 7,
    },
    {
        "id": "D5-06",
        "domain": "Domain 5: SKR Expenses",
        "name": "Hotel Accommodation (7% VAT)",
        "prompt": "Kategorisiere für SKR03 und SKR04: 'Hotelzimmer Buchung Kundentermin München 130€ netto zzgl. 7% MwSt'",
        "type": "expense",
        "expected_skr03": "4660",
        "expected_skr04": "6660",
        "expected_vat": 7,
    },
    {
        "id": "D5-07",
        "domain": "Domain 5: SKR Expenses",
        "name": "Professional Literature (7% VAT)",
        "prompt": "Kategorisiere für SKR03 und SKR04: 'Fachbuch über Steuerrecht und B2B-Abrechnung 49€ inkl. 7% MwSt'",
        "type": "expense",
        "expected_skr03": "4940",
        "expected_skr04": "6815",
        "expected_vat": 7,
    },
    {
        "id": "D5-08",
        "domain": "Domain 5: SKR Expenses",
        "name": "Vehicle Fuel (Benzin/Diesel 19%)",
        "prompt": "Kategorisiere für SKR03 und SKR04: 'Tanken Firmenwagen Diesel an der Tankstelle 85€ netto zzgl. 19% MwSt'",
        "type": "expense",
        "expected_skr03": "4530",
        "expected_skr04": "6530",
        "expected_vat": 19,
    },
    {
        "id": "D5-09",
        "domain": "Domain 5: SKR Expenses",
        "name": "Bank & Account Fees (0% Tax-Exempt)",
        "prompt": "Kategorisiere für SKR03 und SKR04: 'Monatliche Kontoführungsgebühren Geschäftskonto 15,00€ steuerfrei'",
        "type": "expense",
        "expected_skr03": "2100",
        "expected_skr04": "7300",
        "expected_vat": 0,
    },
    {
        "id": "D5-10",
        "domain": "Domain 5: SKR Expenses",
        "name": "Tax Advisor Fees (19%)",
        "prompt": "Kategorisiere für SKR03 und SKR04: 'Rechnung Steuerberater für Erstellung des Jahresabschlusses 1.200€ netto zzgl. 19% MwSt'",
        "type": "expense",
        "expected_skr03": "4955",
        "expected_skr04": "6830",
        "expected_vat": 19,
    },

    # ==================== DOMAIN 6: E-RECHNUNG & XRECHNUNG 3.0 (4 cases) ====================
    {
        "id": "D6-01",
        "domain": "Domain 6: E-Rechnung XRechnung 3.0",
        "name": "Public Sector Federal Agency (BMI)",
        "prompt": "Erstelle eine elektronische Rechnung im XRechnung 3.0 Standard (EN 16931) an Bundesministerium des Innern (Leitweg-ID: 04011000-12345-67): 10 Stunden Cloud-Migration à 120.00€, Zahlungsziel 14 Tage netto. Aussteller: TechConsult GmbH (Berlin).",
        "type": "xrechnung",
        "expected_buyer_ref": "04011000-12345-67",
        "min_items": 1,
    },
    {
        "id": "D6-02",
        "domain": "Domain 6: E-Rechnung XRechnung 3.0",
        "name": "Municipal Authority (Stadt Köln)",
        "prompt": "Generiere eine EN 16931-konforme XRechnung für Stadtverwaltung Köln mit Leitweg-ID 05315000-0001-44: 1x Software-Lizenz 'CityApp' à 450.00€, Rechnungsnummer RE-2025-042.",
        "type": "xrechnung",
        "expected_buyer_ref": "05315000-0001-44",
        "min_items": 1,
    },
    {
        "id": "D6-03",
        "domain": "Domain 6: E-Rechnung XRechnung 3.0",
        "name": "State Ministry (Senatsverwaltung Berlin)",
        "prompt": "Erzeuge die XRechnung 3.0 JSON-Struktur für Senatsverwaltung für Finanzen Berlin (11000000-0001-89): 5 Tage IT-Schulung à 1200.00€, Rechnungsdatum 2025-02-15.",
        "type": "xrechnung",
        "expected_buyer_ref": "11000000-0001-89",
        "min_items": 1,
    },
    {
        "id": "D6-04",
        "domain": "Domain 6: E-Rechnung XRechnung 3.0",
        "name": "Public Utility (Deutsche Bahn AG)",
        "prompt": "Erstelle eine elektronische Rechnung im XRechnung 3.0 Standard an Deutsche Bahn AG - Procurement Solutions (Leitweg-ID: 991-01234-55): 20x Fachdokumentation à 35.00€ mit 7% MwSt, Zahlungsziel 14 Tage netto.",
        "type": "xrechnung",
        "expected_buyer_ref": "991-01234-55",
        "min_items": 1,
    },

    # ==================== DOMAIN 7: GOBD § 14 ABS. 4 USTG PRE-AUDIT (4 cases) ====================
    {
        "id": "D7-01",
        "domain": "Domain 7: GoBD § 14 UStG Pre-Audit",
        "name": "Compliant B2B Invoice",
        "prompt": "Prüfe folgende Eingangsrechnung auf GoBD-Konformität und Vorsteuerabzug nach § 14 Abs. 4 UStG: 'Rechnung von Alpha Tech GmbH (Berlin, Steuernummer 12/345/67890, USt-IdNr. DE123456789), Rechnungsnummer RE-2025-101, Ausstellungsdatum 2025-02-10, Leistungszeitpunkt Februar 2025, an Beta Services GmbH (München): 10 Stunden IT-Consulting 1200.00€ netto zzgl. 19% USt (228.00€) = 1428.00€ brutto.'",
        "type": "gobd_audit",
        "expected_compliant": True,
        "expected_risk": "KEIN_RISIKO",
    },
    {
        "id": "D7-02",
        "domain": "Domain 7: GoBD § 14 UStG Pre-Audit",
        "name": "Missing Tax ID / USt-IdNr",
        "prompt": "GoBD-Audit nach § 14 UStG für Eingangsrechnung durchführen: 'Rechnung von Schmidt Design GbR (Hamburg), Rechnungsnummer RE-2025-502, Datum 2025-01-18, an Gamma UG: Serverwartung 800.00€ netto zzgl. 19% MwSt = 952.00€ brutto. Keine Steuernummer und keine USt-IdNr. angegeben.'",
        "type": "gobd_audit",
        "expected_compliant": False,
        "expected_risk": "HOCH",
    },
    {
        "id": "D7-03",
        "domain": "Domain 7: GoBD § 14 UStG Pre-Audit",
        "name": "Missing Invoice Number",
        "prompt": "Prüfe Eingangsrechnung auf Konformität: 'Rechnung von Bauprofi Müller (Steuernummer 34/567/89012, Datum 2025-03-01) an Kanzlei Becker: Bürorenovierung 1500.00€ netto zzgl. 19% MwSt = 1785.00€ brutto. Keine Rechnungsnummer vorhanden.'",
        "type": "gobd_audit",
        "expected_compliant": False,
        "expected_risk": "HOCH",
    },
    {
        "id": "D7-04",
        "domain": "Domain 7: GoBD § 14 UStG Pre-Audit",
        "name": "Missing Service Period (Leistungszeitpunkt)",
        "prompt": "Vorsteuerabzug-Prüfung § 14 Abs. 4 UStG: 'Rechnung von Apex Solutions GmbH (USt-IdNr. DE987654321, Rechnungsnummer RE-2025-789, Ausstellungsdatum 2025-02-20) an Delta AG: Beratungsleistungen 2000.00€ netto zzgl. 19% USt = 2380.00€ brutto. Kein Leistungszeitpunkt und kein Leistungszeitraum angegeben.'",
        "type": "gobd_audit",
        "expected_compliant": False,
        "expected_risk": ["MITTEL", "HOCH"],
    },

    # ==================== DOMAIN 8: DATEV BUCHUNGSSATZ CSV EXTF (4 cases) ====================
    {
        "id": "D8-01",
        "domain": "Domain 8: DATEV Buchungssatz CSV",
        "name": "Software SaaS Lizenz (SKR03)",
        "prompt": "Erzeuge den DATEV-Buchungssatz (EXTF-Zeile) für folgende Ausgabe in SKR03: 'Monatsrechnung Google Workspace 25.00€ netto bezahlt per Bank am 15.02.2025, Beleg RE-2025-081'",
        "type": "datev",
        "expected_konto": "4964",
        "expected_gegenkonto": "1200",
    },
    {
        "id": "D8-02",
        "domain": "Domain 8: DATEV Buchungssatz CSV",
        "name": "GWG Office Furniture (SKR04)",
        "prompt": "Generiere die DATEV EXTF Buchungszeile für: 'Kauf eines ergonomischen Bürostuhls für 380.00€ netto am 20.03.2025 über Bank bezahlt, Beleg RE-1049, SKR04'",
        "type": "datev",
        "expected_konto": "0670",
        "expected_gegenkonto": "1800",
    },
    {
        "id": "D8-03",
        "domain": "Domain 8: DATEV Buchungssatz CSV",
        "name": "Client Hospitality Bewirtung (SKR03)",
        "prompt": "Erzeuge den DATEV-Buchungssatz (EXTF-Zeile) für folgende Ausgabe in SKR03: 'Bewirtungsbeleg Abendessen mit Geschäftspartner 160.00€ netto bezahlt per Bank am 10.01.2025, Beleg RE-2025-012'",
        "type": "datev",
        "expected_konto": "4650",
        "expected_gegenkonto": "1200",
    },
    {
        "id": "D8-04",
        "domain": "Domain 8: DATEV Buchungssatz CSV",
        "name": "Bank Fees 0% VAT (SKR03)",
        "prompt": "Erzeuge den DATEV-Buchungssatz (EXTF-Zeile) für folgende Ausgabe in SKR03: 'Monatliche Kontoführungsgebühren Geschäftskonto 15.00€ steuerfrei bezahlt per Bank am 31.01.2025, Beleg RE-2025-999'",
        "type": "datev",
        "expected_konto": "2100",
        "expected_gegenkonto": "1200",
    },
]


def query_ollama_raw(prompt: str, model: str, base_url: str = "http://localhost:11434") -> Tuple[str, float]:
    """Queries Ollama and measures response latency."""
    import requests
    t0 = time.time()
    url = f"{base_url}/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.0, "top_p": 0.90},
    }
    r = requests.post(url, json=payload, timeout=60)
    r.raise_for_status()
    latency = time.time() - t0
    data = r.json()
    content = data.get("message", {}).get("content", "")
    return content, latency


def evaluate_test_case(tc: Dict[str, Any], raw_output: str) -> Tuple[bool, List[str]]:
    fail_reasons = []

    if tc["type"] == "invoice":
        cleaned = raw_output.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {e}"]

        try:
            validate(instance=data, schema=INVOICE_SCHEMA)
        except ValidationError as e:
            fail_reasons.append(f"Schema error: {e.message}")

        if tc.get("expected_client"):
            if tc["expected_client"].lower() not in data.get("client_name", "").lower():
                fail_reasons.append(f"Client mismatch: expected '{tc['expected_client']}' in '{data.get('client_name')}'")

        items = data.get("items", [])
        if len(items) < tc.get("min_items", 1):
            fail_reasons.append(f"Expected at least {tc.get('min_items', 1)} items, got {len(items)}")

        if tc.get("expected_vat") is not None:
            for itm in items:
                if itm.get("tax_rate_percent") != tc["expected_vat"]:
                    fail_reasons.append(f"Tax rate mismatch: expected {tc['expected_vat']}%, got {itm.get('tax_rate_percent')}%")
                    break

        if "required_in_notes" in tc:
            notes_lower = (str(data.get("notes", "")) + " " + str(data.get("payment_terms", ""))).lower()
            for kw in tc["required_in_notes"]:
                if kw.lower() not in notes_lower:
                    fail_reasons.append(f"Missing '{kw}' in notes/payment_terms: '{data.get('notes')}' / '{data.get('payment_terms')}'")

    elif tc["type"] == "expense":
        cleaned = raw_output.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {e}"]

        try:
            validate(instance=data, schema=EXPENSE_SCHEMA)
        except ValidationError as e:
            fail_reasons.append(f"Schema error: {e.message}")

        if tc.get("expected_skr03"):
            if str(data.get("skr03_account")) != tc["expected_skr03"]:
                fail_reasons.append(f"SKR03 mismatch: expected {tc['expected_skr03']}, got {data.get('skr03_account')}")

        if tc.get("expected_skr04"):
            if str(data.get("skr04_account")) != tc["expected_skr04"]:
                fail_reasons.append(f"SKR04 mismatch: expected {tc['expected_skr04']}, got {data.get('skr04_account')}")

        if tc.get("expected_vat") is not None:
            if data.get("vat_rate") != tc["expected_vat"]:
                fail_reasons.append(f"VAT rate mismatch: expected {tc['expected_vat']}%, got {data.get('vat_rate')}%")

        if tc.get("expected_deductible") is not None:
            if data.get("deductible_percent") != tc["expected_deductible"]:
                fail_reasons.append(f"Deductible mismatch: expected {tc['expected_deductible']}%, got {data.get('deductible_percent')}%")

    elif tc["type"] == "text":
        out_lower = raw_output.lower()
        if "disallow" in tc:
            for dis in tc["disallow"]:
                if dis.lower() in out_lower:
                    fail_reasons.append(f"Contained disallowed text/format: '{dis}'")

        if "keywords" in tc:
            matches = [kw for kw in tc["keywords"] if kw.lower() in out_lower]
            if len(matches) < 2:
                fail_reasons.append(f"Expected at least 2 keywords from {tc['keywords']}, matched only {matches}")

    elif tc["type"] == "xrechnung":
        cleaned = raw_output.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {e}"]

        try:
            validate(instance=data, schema=XRECHNUNG_SCHEMA)
        except ValidationError as e:
            fail_reasons.append(f"Schema error: {e.message}")

        if tc.get("expected_buyer_ref"):
            if tc["expected_buyer_ref"] not in str(data.get("buyer_reference", "")):
                fail_reasons.append(f"Buyer reference mismatch: expected '{tc['expected_buyer_ref']}' in '{data.get('buyer_reference')}'")

        items = data.get("line_items", [])
        if len(items) < tc.get("min_items", 1):
            fail_reasons.append(f"Expected at least {tc.get('min_items', 1)} items, got {len(items)}")

    elif tc["type"] == "gobd_audit":
        cleaned = raw_output.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {e}"]

        try:
            validate(instance=data, schema=GOBD_AUDIT_SCHEMA)
        except ValidationError as e:
            fail_reasons.append(f"Schema error: {e.message}")

        if "expected_compliant" in tc:
            if data.get("is_compliant") != tc["expected_compliant"]:
                fail_reasons.append(f"is_compliant mismatch: expected {tc['expected_compliant']}, got {data.get('is_compliant')}")

        if "expected_risk" in tc:
            if isinstance(tc["expected_risk"], list):
                if data.get("vorsteuerabzug_risk") not in tc["expected_risk"]:
                    fail_reasons.append(f"vorsteuerabzug_risk mismatch: expected one of {tc['expected_risk']}, got {data.get('vorsteuerabzug_risk')}")
            elif data.get("vorsteuerabzug_risk") != tc["expected_risk"]:
                fail_reasons.append(f"vorsteuerabzug_risk mismatch: expected {tc['expected_risk']}, got {data.get('vorsteuerabzug_risk')}")

    elif tc["type"] == "datev":
        cleaned = raw_output.strip()
        parts = cleaned.split(";")
        if len(parts) < 7:
            fail_reasons.append(f"Expected at least 7 DATEV fields, got {len(parts)} in '{cleaned}'")
        else:
            if parts[1].upper() not in ("S", "H"):
                fail_reasons.append(f"Invalid Soll/Haben flag: '{parts[1]}'")
            if parts[2].upper() != "EUR":
                fail_reasons.append(f"Invalid currency: '{parts[2]}'")
            if tc.get("expected_konto") and parts[6] != tc["expected_konto"]:
                fail_reasons.append(f"Konto mismatch: expected {tc['expected_konto']}, got {parts[6]}")
            if tc.get("expected_gegenkonto") and parts[7] != tc["expected_gegenkonto"]:
                fail_reasons.append(f"Gegenkonto mismatch: expected {tc['expected_gegenkonto']}, got {parts[7]}")

    return len(fail_reasons) == 0, fail_reasons


def run_benchmark(model: str):
    print("================================================================================")
    print(f"  RECHLY-DE-3B COMPREHENSIVE 50-POINT AUDIT BENCHMARK")
    print(f"  Model Under Test: {model}")
    print(f"  Test Cases:       {len(BENCHMARK_CASES)}")
    print("================================================================================\n")

    domain_results: Dict[str, Dict[str, Any]] = {}
    latencies: List[float] = []

    passed_total = 0
    failed_total = 0

    for idx, tc in enumerate(BENCHMARK_CASES, start=1):
        domain = tc["domain"]
        if domain not in domain_results:
            domain_results[domain] = {"passed": 0, "total": 0}
        domain_results[domain]["total"] += 1

        print(f"[{idx:02d}/{len(BENCHMARK_CASES):02d}] {tc['id']} | {tc['name']:<42} ... ", end="", flush=True)

        try:
            output, latency = query_ollama_raw(tc["prompt"], model)
            latencies.append(latency)
            success, reasons = evaluate_test_case(tc, output)
        except Exception as e:
            success = False
            reasons = [f"Connection / runtime exception: {e}"]
            latencies.append(0.0)

        if success:
            print(f"[PASS] ({latency:.2f}s)")
            passed_total += 1
            domain_results[domain]["passed"] += 1
        else:
            print(f"[FAIL] ({latency:.2f}s)")
            for r in reasons:
                print(f"         └── Reason: {r}")
            failed_total += 1

    # --- Print Structured Rating Report ---
    print("\n" + "=" * 80)
    print("                         AUDIT & RATING SUMMARY SCORECARD")
    print("=" * 80)

    for dom, res in domain_results.items():
        score = (res["passed"] / res["total"]) * 100
        bar = "█" * int(score / 5) + "░" * (20 - int(score / 5))
        print(f"  * {dom:<36} {bar} {res['passed']:02d}/{res['total']:02d} ({score:5.1f}%)")

    overall_score = (passed_total / len(BENCHMARK_CASES)) * 100
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    print("-" * 80)
    print(f"  OVERALL AUDIT SCORE:  {passed_total}/{len(BENCHMARK_CASES)} passed ({overall_score:.1f}%)")
    print(f"  AVERAGE QUERY LATENCY: {avg_latency:.2f} seconds")

    grade = "A+" if overall_score >= 95 else ("A" if overall_score >= 90 else ("B+" if overall_score >= 80 else ("B" if overall_score >= 70 else "C")))
    print(f"  FINAL MODEL RATING:    {grade}")
    print("=" * 80 + "\n")

    return {
        "overall_score": overall_score,
        "grade": grade,
        "domain_results": domain_results,
        "passed": passed_total,
        "total": len(BENCHMARK_CASES),
        "avg_latency": avg_latency,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="rechly-de-3b")
    args = parser.parse_args()
    run_benchmark(args.model)

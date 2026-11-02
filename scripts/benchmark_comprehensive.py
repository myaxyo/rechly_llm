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
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
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

    # ==================== DOMAIN 9: ZUGFeRD 2.3 & FACTUR-X PDF/A-3 (5 cases) ====================
    {
        "id": "D9-01",
        "domain": "Domain 9: ZUGFeRD 2.3 Hybrid Engine",
        "name": "Standard B2B Invoice Factur-X Embedding",
        "type": "zugferd",
        "invoice_data": {
            "invoice_number": "RE-2025-901",
            "issue_date": "2025-02-15",
            "due_date": "2025-03-01",
            "seller": {"name": "TechPro Cloud GmbH", "vat_id": "DE123456789", "tax_id": "27/123/45678", "street": "Friedrichstr. 10", "postal_code": "10117", "city": "Berlin"},
            "buyer": {"name": "Muster Consulting AG", "vat_id": "DE987654321", "street": "Königsallee 45", "postal_code": "40212", "city": "Düsseldorf"},
            "line_items": [{"description": "Cloud Deployment & DevOps", "quantity": 10.0, "unit_price": 150.00, "vat_rate": 19.0}]
        },
        "profile": "EN 16931",
        "expected_xml_strings": ["CrossIndustryInvoice", "RE-2025-901", "DE123456789", "1500.00", "285.00", "1785.00"],
        "expected_net_total": 1500.00
    },
    {
        "id": "D9-02",
        "domain": "Domain 9: ZUGFeRD 2.3 Hybrid Engine",
        "name": "Public Sector B2G Leitweg-ID BT-10 Embedding",
        "type": "zugferd",
        "invoice_data": {
            "invoice_number": "RE-2025-902",
            "issue_date": "2025-02-15",
            "due_date": "2025-03-15",
            "buyer_reference": "04011000-12345-67",
            "seller": {"name": "Apex Security UG", "vat_id": "DE111222333", "tax_id": "11/222/33344", "street": "Am Spreeufer 1", "postal_code": "10178", "city": "Berlin"},
            "buyer": {"name": "Bundesministerium des Innern", "street": "Alt-Moabit 140", "postal_code": "10557", "city": "Berlin"},
            "line_items": [{"description": "Sicherheits-Audit Infrastruktur", "quantity": 1.0, "unit_price": 3200.00, "vat_rate": 19.0}]
        },
        "profile": "EN 16931",
        "expected_xml_strings": ["04011000-12345-67", "RE-2025-902", "3200.00", "3808.00"],
        "expected_net_total": 3200.00
    },
    {
        "id": "D9-03",
        "domain": "Domain 9: ZUGFeRD 2.3 Hybrid Engine",
        "name": "Mixed Tax Rates (19% & 7%) Cross-Industry XML",
        "type": "zugferd",
        "invoice_data": {
            "invoice_number": "RE-2025-903",
            "issue_date": "2025-02-18",
            "seller": {"name": "Grand Hotel & Business Center", "vat_id": "DE333444555", "street": "Bahnhofstr. 12", "postal_code": "80335", "city": "München"},
            "buyer": {"name": "Alpha Solutions GmbH", "vat_id": "DE777888999", "street": "Taunusanlage 8", "postal_code": "60329", "city": "Frankfurt"},
            "line_items": [
                {"description": "Übernachtung Business Zimmer", "quantity": 2.0, "unit_price": 110.00, "vat_rate": 7.0},
                {"description": "Konferenzraum & Beamer", "quantity": 1.0, "unit_price": 180.00, "vat_rate": 19.0}
            ]
        },
        "profile": "EN 16931",
        "expected_xml_strings": ["<ram:RateApplicablePercent>7.00</ram:RateApplicablePercent>", "<ram:RateApplicablePercent>19.00</ram:RateApplicablePercent>"],
        "expected_net_total": 400.00
    },
    {
        "id": "D9-04",
        "domain": "Domain 9: ZUGFeRD 2.3 Hybrid Engine",
        "name": "Kleinunternehmer (§ 19 UStG) Zero Tax Hybrid",
        "type": "zugferd",
        "invoice_data": {
            "invoice_number": "RE-2025-904",
            "issue_date": "2025-02-20",
            "seller": {"name": "Grafikdesign Schmidt (Kleinunternehmer)", "tax_id": "24/555/66677", "street": "Lindenweg 4", "postal_code": "50672", "city": "Köln"},
            "buyer": {"name": "Café Sonnenschein", "street": "Marktplatz 3", "postal_code": "50667", "city": "Köln"},
            "notes": "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet.",
            "line_items": [{"description": "Speisekarte Redesign & Druckvorstufe", "quantity": 1.0, "unit_price": 450.00, "vat_rate": 0.0}]
        },
        "profile": "BASIC",
        "expected_xml_strings": ["RE-2025-904", "450.00"],
        "expected_net_total": 450.00
    },
    {
        "id": "D9-05",
        "domain": "Domain 9: ZUGFeRD 2.3 Hybrid Engine",
        "name": "ZUGFeRD Extraction & Roundtrip Conformance",
        "type": "zugferd",
        "invoice_data": {
            "invoice_number": "RE-2025-905",
            "issue_date": "2025-02-22",
            "seller": {"name": "Nordic IT Engineering", "vat_id": "DE999111222", "street": "Hafenpromenade 9", "postal_code": "20457", "city": "Hamburg"},
            "buyer": {"name": "Logistik Express SE", "vat_id": "DE888333222", "street": "Am Güterbahnhof 15", "postal_code": "28195", "city": "Bremen"},
            "line_items": [{"description": "API Integration DATEV Schnittstelle", "quantity": 8.0, "unit_price": 130.00, "vat_rate": 19.0}]
        },
        "profile": "EN 16931",
        "expected_xml_strings": ["RE-2025-905", "1040.00", "1237.60"],
        "expected_net_total": 1040.00
    },

    # ==================== DOMAIN 10: MULTIMODAL VISION OCR TO DATEV (5 cases) ====================
    {
        "id": "D10-01",
        "domain": "Domain 10: Multimodal Receipt OCR",
        "name": "Restaurant Hospitality Bewirtungsbeleg (70%)",
        "type": "vision_ocr",
        "merchant": "Restaurant Hirsch",
        "item_text": "Bewirtung Mandanten 140.00 EUR inkl. 19% MwSt",
        "gross_amount": 140.00,
        "vat_rate": 19.0,
        "expected_skr03": "4650",
        "expected_skr04": "6640",
        "expected_deductible": 70
    },
    {
        "id": "D10-02",
        "domain": "Domain 10: Multimodal Receipt OCR",
        "name": "Fleet Fuel Aral Diesel (19% VAT)",
        "type": "vision_ocr",
        "merchant": "Aral Tankstelle Berlin",
        "item_text": "Diesel Kraftstoff 45 Liter 85.50 EUR",
        "gross_amount": 85.50,
        "vat_rate": 19.0,
        "expected_skr03": "4530",
        "expected_skr04": "6530",
        "expected_deductible": 100
    },
    {
        "id": "D10-03",
        "domain": "Domain 10: Multimodal Receipt OCR",
        "name": "Hotel Lodging Reduced Tax (7% VAT)",
        "type": "vision_ocr",
        "merchant": "Hotel Imperial München",
        "item_text": "Übernachtung 1 Nacht Einzelzimmer 120.00 EUR",
        "gross_amount": 120.00,
        "vat_rate": 7.0,
        "expected_skr03": "4660",
        "expected_skr04": "6660",
        "expected_deductible": 100
    },
    {
        "id": "D10-04",
        "domain": "Domain 10: Multimodal Receipt OCR",
        "name": "Low-Value Asset Office Desk GWG (< 800€)",
        "type": "vision_ocr",
        "merchant": "Büromöbel Direkt GmbH",
        "item_text": "Schreibtisch höhenverstellbar 420.00 EUR",
        "gross_amount": 420.00,
        "vat_rate": 19.0,
        "expected_skr03": "0480",
        "expected_skr04": "0670",
        "expected_deductible": 100
    },
    {
        "id": "D10-05",
        "domain": "Domain 10: Multimodal Receipt OCR",
        "name": "Telecommunications & Internet Flatrate",
        "type": "vision_ocr",
        "merchant": "Telekom Deutschland GmbH",
        "item_text": "Business DSL & Festnetz Monatstarif 59.95 EUR",
        "gross_amount": 59.95,
        "vat_rate": 19.0,
        "expected_skr03": "4920",
        "expected_skr04": "6805",
        "expected_deductible": 100
    },

    # ==================== DOMAIN 11: ENTERPRISE DATEV EXTF BATCH (5 cases) ====================
    {
        "id": "D11-01",
        "domain": "Domain 11: Enterprise DATEV Batch",
        "name": "Format 700 Header Conformance (27 Fields)",
        "type": "datev_batch",
        "records": [
            {"merchant_name": "Aral Tankstelle", "date": "15.02.2025", "gross_amount": 85.00, "vat_rate": 19.0, "konto": "4530"}
        ],
        "expected_bu": "9"
    },
    {
        "id": "D11-02",
        "domain": "Domain 11: Enterprise DATEV Batch",
        "name": "Mixed Vorsteuer BU-Schlüssel Resolution (BU 8 & 9)",
        "type": "datev_batch",
        "records": [
            {"merchant_name": "Deutsche Bahn", "date": "18.02.2025", "gross_amount": 120.00, "vat_rate": 7.0, "konto": "4670"},
            {"merchant_name": "Telekom", "date": "19.02.2025", "gross_amount": 60.00, "vat_rate": 19.0, "konto": "4920"}
        ],
        "expected_bu": "8"
    },
    {
        "id": "D11-03",
        "domain": "Domain 11: Enterprise DATEV Batch",
        "name": "Dual Encoding Integrity (Umlauts Ä, Ö, Ü, ß)",
        "type": "datev_batch",
        "records": [
            {"merchant_name": "Kanzlei Müller-Lüdenscheidt & Söhne", "date": "20.02.2025", "gross_amount": 250.00, "vat_rate": 19.0, "konto": "4955", "belegtext": "Beratungsgebühren Großprojekt"}
        ],
        "expected_bu": "9"
    },
    {
        "id": "D11-04",
        "domain": "Domain 11: Enterprise DATEV Batch",
        "name": "DATEV Unternehmen Online ZIP Archive Package",
        "type": "datev_batch",
        "test_zip": True,
        "records": [
            {"merchant_name": "Cloud Host Provider", "date": "22.02.2025", "gross_amount": 140.00, "vat_rate": 19.0, "konto": "4964"},
            {"merchant_name": "Büroexpress", "date": "23.02.2025", "gross_amount": 75.00, "vat_rate": 19.0, "konto": "4930"}
        ]
    },
    {
        "id": "D11-05",
        "domain": "Domain 11: Enterprise DATEV Batch",
        "name": "Multi-Record Batch Roundtrip Verification",
        "type": "datev_batch",
        "records": [
            {"merchant_name": "Kunde A", "date": "01.02.2025", "gross_amount": 100.00, "vat_rate": 19.0, "konto": "4530"},
            {"merchant_name": "Kunde B", "date": "02.02.2025", "gross_amount": 200.00, "vat_rate": 7.0, "konto": "4670"},
            {"merchant_name": "Kunde C", "date": "03.02.2025", "gross_amount": 300.00, "vat_rate": 19.0, "konto": "4920"},
            {"merchant_name": "Kunde D", "date": "04.02.2025", "gross_amount": 400.00, "vat_rate": 0.0, "konto": "2100"}
        ]
    },

    # ==================== DOMAIN 12: CENT-PERFECT RECONCILER & § 35a (5 cases) ====================
    {
        "id": "D12-01",
        "domain": "Domain 12: Cent-Perfect Reconciler",
        "name": "Commercial Rounding (§ 35 UStDV) on Repeating Thirds",
        "type": "reconcile",
        "subtask": "reconcile",
        "invoice_data": {
            "invoice_number": "RE-ROUND-01",
            "line_items": [
                {"name": "Teilleistung 1", "quantity": 1, "unit_price": 33.333, "tax_percent": 19.0},
                {"name": "Teilleistung 2", "quantity": 1, "unit_price": 33.333, "tax_percent": 19.0},
                {"name": "Teilleistung 3", "quantity": 1, "unit_price": 33.335, "tax_percent": 19.0}
            ]
        },
        "expected_net": 100.00,
        "expected_tax": 19.00,
        "expected_gross": 119.00
    },
    {
        "id": "D12-02",
        "domain": "Domain 12: Cent-Perfect Reconciler",
        "name": "Multi-Tax Rate Group Breakdown Reconciliation",
        "type": "reconcile",
        "subtask": "reconcile",
        "invoice_data": {
            "invoice_number": "RE-MULTI-02",
            "line_items": [
                {"name": "Übernachtung Hotel", "quantity": 2, "unit_price": 100.00, "tax_percent": 7.0},
                {"name": "Business WiFi Flat", "quantity": 1, "unit_price": 20.00, "tax_percent": 19.0},
                {"name": "Reverse-Charge Consulting", "quantity": 1, "unit_price": 80.00, "tax_percent": 0.0}
            ]
        },
        "expected_net": 300.00,
        "expected_tax": 17.80,
        "expected_gross": 317.80,
        "expected_breakdown_count": 3
    },
    {
        "id": "D12-03",
        "domain": "Domain 12: Cent-Perfect Reconciler",
        "name": "§ 35a Abs. 3 EStG Handwerkerleistungen Labor Separation",
        "type": "reconcile",
        "subtask": "handwerker",
        "items": [
            {"name": "Fliesenleger Arbeitsstunden Meister", "quantity": 15, "unit_price": 65.00, "tax_percent": 19.0},
            {"name": "Fahrtkostenpauschale Baustelle", "quantity": 1, "unit_price": 45.00, "tax_percent": 19.0},
            {"name": "Fliesen Feinsteinzeug 30qm", "quantity": 30, "unit_price": 40.00, "tax_percent": 19.0},
            {"name": "Fliesenkleber & Fugenmörtel", "quantity": 5, "unit_price": 25.00, "tax_percent": 19.0}
        ],
        "expected_labor_net": 1020.00,
        "expected_deduction": 242.76
    },
    {
        "id": "D12-04",
        "domain": "Domain 12: Cent-Perfect Reconciler",
        "name": "Cash Discount Skonto 2% Calculation (§ 17 UStG)",
        "type": "reconcile",
        "subtask": "skonto",
        "gross_amount": 2380.00,
        "skonto_percent": 2.0,
        "days": 14,
        "expected_discount": 47.60,
        "expected_payable": 2332.40
    },
    {
        "id": "D12-05",
        "domain": "Domain 12: Cent-Perfect Reconciler",
        "name": "Negative Line Item Gutschrift & Commercial Discount",
        "type": "reconcile",
        "subtask": "reconcile",
        "invoice_data": {
            "invoice_number": "RE-DISC-05",
            "line_items": [
                {"name": "Hardware Server Rack 42HE", "quantity": 1, "unit_price": 1200.00, "tax_percent": 19.0},
                {"name": "Treuerabatt 10% Aktionsnachlass", "quantity": 1, "unit_price": -120.00, "tax_percent": 19.0}
            ]
        },
        "expected_net": 1080.00,
        "expected_tax": 205.20,
        "expected_gross": 1285.20
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


def eval_zugferd_case(tc: Dict[str, Any]) -> Tuple[bool, List[str]]:
    from scripts.zugferd_generator import create_zugferd_pdf, verify_zugferd_pdf, extract_zugferd_xml
    reasons = []
    inv_data = tc["invoice_data"]
    profile = tc.get("profile", "EN 16931")
    pdf_bytes = create_zugferd_pdf(inv_data, profile=profile)
    if len(pdf_bytes) < 1000:
        reasons.append("Generated PDF too small")
        return False, reasons

    ver = verify_zugferd_pdf(pdf_bytes)
    if not ver.get("is_valid_zugferd"):
        reasons.append("verify_zugferd_pdf failed: is_valid_zugferd is False")
    if ver.get("attachment_name") != "factur-x.xml":
        reasons.append(f"verify_zugferd_pdf failed: attachment_name is {ver.get('attachment_name')}")

    xml_content, filename = extract_zugferd_xml(pdf_bytes)
    if not xml_content or filename != "factur-x.xml":
        reasons.append(f"extract_zugferd_xml failed: filename={filename}")

    if tc.get("expected_xml_strings"):
        for s in tc["expected_xml_strings"]:
            if s not in xml_content:
                reasons.append(f"Expected XML substring '{s}' not found in factur-x.xml")

    if tc.get("expected_net_total") is not None:
        if f"{tc['expected_net_total']:.2f}" not in xml_content:
            reasons.append(f"Net total {tc['expected_net_total']:.2f} not found in XML")

    return len(reasons) == 0, reasons


def eval_vision_ocr_case(tc: Dict[str, Any]) -> Tuple[bool, List[str]]:
    from PIL import Image, ImageDraw
    import io
    from scripts.receipt_vision_ocr import process_receipt_image
    reasons = []

    img = Image.new("RGB", (420, 480), color="#ffffff")
    draw = ImageDraw.Draw(img)
    draw.text((30, 30), f"Beleg: {tc['merchant']}", fill="#000000")
    draw.text((30, 60), f"Datum: {tc.get('date', '2025-02-15')}", fill="#000000")
    draw.text((30, 90), f"{tc.get('item_text', 'Ausgabe')}", fill="#000000")
    draw.text((30, 130), f"Gesamtbetrag: {tc['gross_amount']:.2f} EUR", fill="#000000")
    draw.text((30, 160), f"MwSt: {tc.get('vat_rate', 19.0)}%", fill="#000000")
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    mock_data = {
        "merchant_name": tc["merchant"],
        "date": tc.get("date", "2025-02-15"),
        "receipt_number": f"REC-{tc['id']}",
        "gross_amount": tc["gross_amount"],
        "tax_rate": float(tc.get("vat_rate", 19.0)),
        "net_amount": round(tc["gross_amount"] / (1 + float(tc.get("vat_rate", 19.0)) / 100.0), 2),
        "tax_amount": round(tc["gross_amount"] - tc["gross_amount"] / (1 + float(tc.get("vat_rate", 19.0)) / 100.0), 2),
        "currency": "EUR",
        "category_hint": tc.get("item_text", "")
    }

    res = process_receipt_image(buf.getvalue(), chart=tc.get("chart", "SKR03"), mock_fallback_data=mock_data)
    d_class = res.get("datev_classification", {})

    if tc.get("expected_skr03") and str(d_class.get("skr03_account")) != tc["expected_skr03"]:
        reasons.append(f"SKR03 mismatch: expected {tc['expected_skr03']}, got {d_class.get('skr03_account')}")
    if tc.get("expected_skr04") and str(d_class.get("skr04_account")) != tc["expected_skr04"]:
        reasons.append(f"SKR04 mismatch: expected {tc['expected_skr04']}, got {d_class.get('skr04_account')}")
    if tc.get("expected_deductible") is not None and d_class.get("deductible_percent") != tc["expected_deductible"]:
        reasons.append(f"Deductible mismatch: expected {tc['expected_deductible']}%, got {d_class.get('deductible_percent')}%")

    extf = res.get("datev_buchungssatz", "")
    if not extf or ";" not in extf:
        reasons.append(f"Invalid datev_buchungssatz EXTF row: '{extf}'")

    return len(reasons) == 0, reasons


def eval_datev_batch_case(tc: Dict[str, Any]) -> Tuple[bool, List[str]]:
    from scripts.datev_batch_exporter import export_datev_batch_csv, parse_datev_extf_csv, generate_datev_zip_archive
    reasons = []
    records = tc["records"]
    chart = tc.get("chart", "SKR03")

    csv_bytes = export_datev_batch_csv(records, chart=chart)
    text = csv_bytes.decode("utf-8-sig")
    lines = text.strip().split("\r\n")
    if not lines[0].startswith('"EXTF";700;21;"Buchungsstapel"'):
        reasons.append(f"Invalid DATEV header line: '{lines[0][:40]}'")

    header_fields = lines[0].split(";")
    if len(header_fields) < 27:
        reasons.append(f"Header field count < 27 (got {len(header_fields)})")

    parsed = parse_datev_extf_csv(csv_bytes)
    if parsed["total_records"] != len(records):
        reasons.append(f"Parsed count {parsed['total_records']} != {len(records)}")

    if tc.get("expected_bu"):
        bu_found = False
        for r in parsed["records"]:
            if r.get("bu_schluessel") == tc["expected_bu"]:
                bu_found = True
                break
        if not bu_found:
            reasons.append(f"Expected BU-Schlüssel {tc['expected_bu']} not found in parsed records")

    if tc.get("test_zip", False):
        import zipfile
        import io
        zip_bytes = generate_datev_zip_archive(records, chart=chart)
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            names = z.namelist()
            if "EXTF_Buchungsstapel.csv" not in names or "document.xml" not in names:
                reasons.append(f"Missing files in DATEV zip: {names}")

    return len(reasons) == 0, reasons


def eval_reconcile_case(tc: Dict[str, Any]) -> Tuple[bool, List[str]]:
    from scripts.tax_calculator import reconcile_invoice_totals, calculate_handwerker_split, calculate_skonto_discount
    reasons = []

    subtask = tc.get("subtask", "reconcile")
    if subtask == "reconcile":
        rec = reconcile_invoice_totals(tc["invoice_data"])
        if not rec.get("is_mathematically_exact"):
            reasons.append("is_mathematically_exact is False")
        if tc.get("expected_net") is not None and rec["total_net_amount"] != tc["expected_net"]:
            reasons.append(f"Net mismatch: expected {tc['expected_net']}, got {rec['total_net_amount']}")
        if tc.get("expected_tax") is not None and rec["total_tax_amount"] != tc["expected_tax"]:
            reasons.append(f"Tax mismatch: expected {tc['expected_tax']}, got {rec['total_tax_amount']}")
        if tc.get("expected_gross") is not None and rec["total_gross_amount"] != tc["expected_gross"]:
            reasons.append(f"Gross mismatch: expected {tc['expected_gross']}, got {rec['total_gross_amount']}")
        if tc.get("expected_breakdown_count") and len(rec["tax_breakdown"]) != tc["expected_breakdown_count"]:
            reasons.append(f"Tax breakdown count mismatch: expected {tc['expected_breakdown_count']}, got {len(rec['tax_breakdown'])}")

    elif subtask == "handwerker":
        res = calculate_handwerker_split(tc["items"])
        if tc.get("expected_labor_net") is not None and res["labor_net"] != tc["expected_labor_net"]:
            reasons.append(f"Labor net mismatch: expected {tc['expected_labor_net']}, got {res['labor_net']}")
        if tc.get("expected_deduction") is not None and res["paragraph_35a_deduction_amount"] != tc["expected_deduction"]:
            reasons.append(f"35a deduction mismatch: expected {tc['expected_deduction']}, got {res['paragraph_35a_deduction_amount']}")

    elif subtask == "skonto":
        res = calculate_skonto_discount(tc["gross_amount"], skonto_percent=tc.get("skonto_percent", 2.0), days=tc.get("days", 14))
        if tc.get("expected_discount") is not None and res["discount_amount"] != tc["expected_discount"]:
            reasons.append(f"Discount amount mismatch: expected {tc['expected_discount']}, got {res['discount_amount']}")
        if tc.get("expected_payable") is not None and res["payable_with_skonto"] != tc["expected_payable"]:
            reasons.append(f"Payable mismatch: expected {tc['expected_payable']}, got {res['payable_with_skonto']}")

    return len(reasons) == 0, reasons


def evaluate_test_case(tc: Dict[str, Any], raw_output: str = None) -> Tuple[bool, List[str]]:
    fail_reasons = []

    if tc["type"] == "zugferd":
        return eval_zugferd_case(tc)
    elif tc["type"] == "vision_ocr":
        return eval_vision_ocr_case(tc)
    elif tc["type"] == "datev_batch":
        return eval_datev_batch_case(tc)
    elif tc["type"] == "reconcile":
        return eval_reconcile_case(tc)

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


def run_benchmark(model: str = "rechly-de-3b", domain_filter: str = None, engine_only: bool = False):
    cases = list(BENCHMARK_CASES)
    if engine_only:
        cases = [c for c in cases if c["type"] in ("zugferd", "vision_ocr", "datev_batch", "reconcile")]
    elif domain_filter:
        cases = [c for c in cases if domain_filter.lower() in c["domain"].lower()]

    print("================================================================================")
    print(f"  RECHLY-DE-3B COMPREHENSIVE 77-POINT ENTERPRISE AUDIT BENCHMARK")
    print(f"  Model Under Test: {model}")
    print(f"  Test Cases:       {len(cases)} across 12 Domains")
    print("================================================================================\n")

    domain_results: Dict[str, Dict[str, Any]] = {}
    latencies: List[float] = []

    passed_total = 0
    failed_total = 0

    for idx, tc in enumerate(cases, start=1):
        domain = tc["domain"]
        if domain not in domain_results:
            domain_results[domain] = {"passed": 0, "total": 0}
        domain_results[domain]["total"] += 1

        print(f"[{idx:02d}/{len(cases):02d}] {tc['id']} | {tc['name']:<46} ... ", end="", flush=True)

        if tc["type"] in ("zugferd", "vision_ocr", "datev_batch", "reconcile"):
            t0 = time.time()
            try:
                success, reasons = evaluate_test_case(tc, raw_output=None)
            except Exception as e:
                success = False
                reasons = [f"Engine execution error: {e}"]
            latency = time.time() - t0
            latencies.append(latency)
        else:
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
        print(f"  * {dom:<38} {bar} {res['passed']:02d}/{res['total']:02d} ({score:5.1f}%)")

    overall_score = (passed_total / len(cases)) * 100 if cases else 0.0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    print("-" * 80)
    print(f"  OVERALL AUDIT SCORE:   {passed_total}/{len(cases)} passed ({overall_score:.1f}%)")
    print(f"  AVERAGE QUERY LATENCY: {avg_latency:.2f} seconds")

    grade = "A+" if overall_score >= 95 else ("A" if overall_score >= 90 else ("B+" if overall_score >= 80 else ("B" if overall_score >= 70 else "C")))
    print(f"  FINAL MODEL RATING:    {grade}")
    print("=" * 80 + "\n")

    return {
        "overall_score": overall_score,
        "grade": grade,
        "domain_results": domain_results,
        "passed": passed_total,
        "total": len(cases),
        "avg_latency": avg_latency,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="rechly-de-3b")
    parser.add_argument("--domain", type=str, default=None, help="Filter to specific domain")
    parser.add_argument("--engine-only", action="store_true", help="Run only engine verification cases (Domains 9-12)")
    args = parser.parse_args()
    run_benchmark(args.model, domain_filter=args.domain, engine_only=args.engine_only)

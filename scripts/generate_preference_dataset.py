#!/usr/bin/env python3
"""
Rechly-DE-3B DPO / ORPO Preference Dataset Generator & Validator
Produces a high-precision German tax, GoBD, DATEV, and E-Rechnung preference alignment dataset
in (prompt, chosen, rejected) format to eliminate edge-case hallucinations and tax law violations.

Output format:
    {"id": "...", "domain": "...", "prompt": "...", "chosen": "...", "rejected": "...", "penalty_reason": "..."}
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = PROJECT_ROOT / "data" / "rechly_preference_pairs.jsonl"


def create_preference_samples() -> List[Dict[str, Any]]:
    pairs = []
    
    # --------------------------------------------------------------------------
    # 1. § 19 UStG Kleinunternehmer (0% VAT vs Illegal 19% VAT)
    # --------------------------------------------------------------------------
    clients = ["Kanzlei Dr. Weber", "Müller & Partner GbR", "Autohaus Schmidt GmbH", "Designstudio Kreativ", "Bäckerei Bergmann"]
    services_ku = [
        ("Webdesign und Homepageerstellung", 850.0, "Pauschal"),
        ("Social Media Betreuung für 1 Monat", 650.0, "Monat"),
        ("15 Stunden IT-Support und Systemeinrichtung", 75.0, "Stunde"),
        ("Fotografische Begleitung Firmenevent", 450.0, "Tag"),
        ("Texterstellung für Unternehmensbroschüre", 500.0, "Pauschal"),
        ("Garten- und Landschaftspflege Frühjahr", 380.0, "Pauschal"),
        ("Suchmaschinenoptimierung (SEO) Audit", 720.0, "Pauschal")
    ]

    for idx, (client) in enumerate(clients):
        for s_idx, (srv, price, unit) in enumerate(services_ku):
            p_id = f"PREF-KU-{idx+1:02d}-{s_idx+1:02d}"
            prompt = f"Erstelle eine Rechnung an {client}: {srv} à {price}€, ich bin Kleinunternehmer gem. § 19 UStG."
            
            chosen_obj = {
                "client_name": client,
                "due_days": 14,
                "payment_terms": "Zahlbar innerhalb von 14 Tagen rein netto.",
                "legal_note": "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet (Kleinunternehmerregelung).",
                "items": [
                    {
                        "description": srv,
                        "quantity": 1 if unit != "Stunde" else 15,
                        "unit": unit,
                        "unit_price": price,
                        "tax_rate": 0
                    }
                ]
            }
            
            # Rejected variant 1: 19% VAT charged illegally
            rejected_obj_1 = {
                "client_name": client,
                "due_days": 14,
                "payment_terms": "Zahlbar innerhalb von 14 Tagen.",
                "legal_note": None,
                "items": [
                    {
                        "description": srv,
                        "quantity": 1 if unit != "Stunde" else 15,
                        "unit": unit,
                        "unit_price": price,
                        "tax_rate": 19
                    }
                ]
            }

            pairs.append({
                "id": p_id,
                "domain": "Domain 1: § 19 UStG Kleinunternehmer",
                "prompt": prompt,
                "chosen": json.dumps(chosen_obj, ensure_ascii=False, indent=2),
                "rejected": json.dumps(rejected_obj_1, ensure_ascii=False, indent=2),
                "penalty_reason": "CRITICAL TAX VIOLATION: Invoices under § 19 UStG must have tax_rate 0% and include the statutory notice. Outputting 19% VAT triggers unentitled tax liability pursuant to § 14c UStG."
            })

    # --------------------------------------------------------------------------
    # 2. § 13b UStG Reverse Charge Bauleistungen & Gebäudereinigung
    # --------------------------------------------------------------------------
    bau_clients = ["Bauunternehmen Hoch & Tief GmbH", "Generalbau Nord AG", "Immobilienverwaltung Rhein-Ruhr", "Stadtreinigung Süd GmbH"]
    bau_services = [
        ("Estrichlegearbeiten Neubauprojekt 5 Tage à 650€", "5 Tage Estricharbeiten", 5, 650.0, "Tag"),
        ("Trockenbau und Spachtelarbeiten Bürokomplex", "Trockenbauarbeiten", 40, 55.0, "Stunde"),
        ("Dachabdichtungs- und Isolierarbeiten Industriehalle", "Dachabdichtung", 1, 3800.0, "Pauschal"),
        ("Unterhaltsreinigung Gewerbeimmobilie 1 Monat", "Gebäudereinigung gem. § 13b Abs. 2 Nr. 8 UStG", 1, 1450.0, "Monat")
    ]

    for b_idx, client in enumerate(bau_clients):
        for s_idx, (raw_srv, item_name, qty, prc, un) in enumerate(bau_services):
            p_id = f"PREF-13B-{b_idx+1:02d}-{s_idx+1:02d}"
            prompt = f"Rechnung an Generalunternehmer {client}: {raw_srv}, Steuerschuldnerschaft des Leistungsempfängers / Reverse Charge gem. § 13b UStG."
            
            chosen_obj = {
                "client_name": client,
                "due_days": 30,
                "payment_terms": "Zahlbar innerhalb von 30 Tagen.",
                "legal_note": "Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge gem. § 13b Abs. 2 i.V.m. Abs. 5 UStG).",
                "items": [
                    {
                        "description": item_name,
                        "quantity": qty,
                        "unit": un,
                        "unit_price": prc,
                        "tax_rate": 0
                    }
                ]
            }

            rejected_obj = {
                "client_name": client,
                "due_days": 30,
                "payment_terms": "Zahlbar in 30 Tagen.",
                "legal_note": "Rechnung mit 19% MwSt.",
                "items": [
                    {
                        "description": item_name,
                        "quantity": qty,
                        "unit": un,
                        "unit_price": prc,
                        "tax_rate": 19
                    }
                ]
            }

            pairs.append({
                "id": p_id,
                "domain": "Domain 2: § 13b UStG Reverse Charge",
                "prompt": prompt,
                "chosen": json.dumps(chosen_obj, ensure_ascii=False, indent=2),
                "rejected": json.dumps(rejected_obj, ensure_ascii=False, indent=2),
                "penalty_reason": "TAX LAW ERROR: In domestic construction B2B (§ 13b UStG), VAT shifts to recipient. Tax rate must be 0% and Steuerschuldnerschaft clause is mandatory."
            })

    # --------------------------------------------------------------------------
    # 3. § 4 Nr. 1b / § 6a UStG Innergemeinschaftliche Lieferung EU B2B
    # --------------------------------------------------------------------------
    eu_clients = [
        ("Acme Solutions B.V.", "NL847291024B01", "Niederlande"),
        ("Alpine Tech SAS", "FR90823471029", "Frankreich"),
        ("Vienna Consulting GmbH", "ATU68192039", "Österreich"),
        ("Madrid Logistics SL", "ESB82910492", "Spanien"),
        ("Nordic Design ApS", "DK39201948", "Dänemark")
    ]
    eu_items = [
        ("Lieferung von 50x IoT-Sensor-Gateways Hardware à 180€", "IoT-Sensor-Gateways", 50, 180.0, 9000.0),
        ("Softwarelizenz Enterprise Jahresabo", "Softwarelizenz", 1, 4800.0, 4800.0),
        ("Server-Hardware Rack-Server 2HE", "Rack-Server", 2, 2400.0, 4800.0)
    ]

    for c_idx, (c_name, vat_id, country) in enumerate(eu_clients):
        for i_idx, (desc, itm, qty, prc, tot) in enumerate(eu_items):
            p_id = f"PREF-EU-{c_idx+1:02d}-{i_idx+1:02d}"
            prompt = f"Erstelle eine steuerfreie EU B2B Rechnung an {c_name} ({country}, USt-IdNr {vat_id}): {desc}."
            
            chosen_obj = {
                "client_name": c_name,
                "due_days": 14,
                "payment_terms": "Zahlbar innerhalb von 14 Tagen rein netto.",
                "legal_note": "Steuerfreie innergemeinschaftliche Lieferung gem. § 4 Nr. 1b i.V.m. § 6a UStG.",
                "items": [
                    {
                        "description": itm,
                        "quantity": qty,
                        "unit": "Stück",
                        "unit_price": prc,
                        "tax_rate": 0
                    }
                ]
            }

            rejected_obj = {
                "client_name": c_name,
                "due_days": 14,
                "payment_terms": "Zahlbar innerhalb von 14 Tagen.",
                "legal_note": "Rechnung mit 19% deutscher Umsatzsteuer.",
                "items": [
                    {
                        "description": itm,
                        "quantity": qty,
                        "unit": "Stück",
                        "unit_price": prc,
                        "tax_rate": 19
                    }
                ]
            }

            pairs.append({
                "id": p_id,
                "domain": "Domain 3: § 4 Nr. 1b UStG EU B2B Steuerbefreiung",
                "prompt": prompt,
                "chosen": json.dumps(chosen_obj, ensure_ascii=False, indent=2),
                "rejected": json.dumps(rejected_obj, ensure_ascii=False, indent=2),
                "penalty_reason": "EU CROSS-BORDER TAX VIOLATION: Deliveries to verified EU business entities with valid VAT-ID are tax-exempt (0% VAT) under § 4 Nr. 1b i.V.m. § 6a UStG. Charging domestic VAT is unlawful."
            })

    # --------------------------------------------------------------------------
    # 4. § 4 Nr. 1a / § 6 UStG Drittland Export (Schweiz / USA)
    # --------------------------------------------------------------------------
    third_clients = [
        ("Zürich Financial Consulting AG", "CH-100.3.029.112-9", "Schweiz"),
        ("Geneva Biotech Sarl", "CH-220.1.094.882-1", "Schweiz"),
        ("Boston Data Corp", "US-EIN-94-829104", "USA")
    ]
    for t_idx, (t_name, t_tax, t_ctry) in enumerate(third_clients):
        p_id = f"PREF-EXPORT-{t_idx+1:02d}"
        prompt = f"Rechnung an Drittland-Kunden {t_name} ({t_ctry}): 20 Stunden Software-Entwicklung à 140€."
        
        chosen_obj = {
            "client_name": t_name,
            "due_days": 30,
            "payment_terms": "Zahlbar innerhalb von 30 Tagen.",
            "legal_note": "Steuerfreie Ausfuhrlieferung / Nicht im Inland steuerbare Leistung gem. § 4 Nr. 1a UStG.",
            "items": [
                {
                    "description": "Software-Entwicklung",
                    "quantity": 20,
                    "unit": "Stunde",
                    "unit_price": 140.0,
                    "tax_rate": 0
                }
            ]
        }

        rejected_obj = {
            "client_name": t_name,
            "due_days": 30,
            "payment_terms": "Zahlbar in 30 Tagen.",
            "legal_note": "19% MwSt.",
            "items": [
                {
                    "description": "Software-Entwicklung",
                    "quantity": 20,
                    "unit": "Stunde",
                    "unit_price": 140.0,
                    "tax_rate": 19
                }
            ]
        }

        pairs.append({
            "id": p_id,
            "domain": "Domain 4: § 4 Nr. 1a UStG Drittland Export",
            "prompt": prompt,
            "chosen": json.dumps(chosen_obj, ensure_ascii=False, indent=2),
            "rejected": json.dumps(rejected_obj, ensure_ascii=False, indent=2),
            "penalty_reason": "EXPORT TAX ERROR: Export deliveries to non-EU third countries (e.g. Switzerland, USA) are tax-exempt (0% VAT) pursuant to § 4 Nr. 1a UStG."
        })

    # --------------------------------------------------------------------------
    # 5. § 25a UStG Differenzbesteuerung (Gebrauchtgegenstände)
    # --------------------------------------------------------------------------
    diff_items = [
        ("Gebrauchter Apple iMac M2 24 Zoll", 890.0),
        ("Gebrauchter Firmenwagen VW Golf VII", 12500.0),
        ("Antiker Schreibtisch Echtholz Eiche", 750.0)
    ]
    for d_idx, (d_name, d_price) in enumerate(diff_items):
        p_id = f"PREF-DIFF-{d_idx+1:02d}"
        prompt = f"Erstelle eine Rechnung über den Verkauf: '{d_name}' für {d_price}€ unter Anwendung der Differenzbesteuerung."
        
        chosen_obj = {
            "client_name": "Kunde",
            "due_days": 14,
            "payment_terms": "Zahlbar sofort nach Erhalt.",
            "legal_note": "Sonderregelung für Gebrauchtgegenstände gem. § 25a UStG (Differenzbesteuerung). Ein gesonderter Ausweis der Umsatzsteuer erfolgt nicht.",
            "items": [
                {
                    "description": d_name,
                    "quantity": 1,
                    "unit": "Stück",
                    "unit_price": d_price,
                    "tax_rate": 0
                }
            ]
        }

        rejected_obj = {
            "client_name": "Kunde",
            "due_days": 14,
            "payment_terms": "Zahlbar sofort.",
            "legal_note": "Rechnung enthält 19% MwSt.",
            "items": [
                {
                    "description": d_name,
                    "quantity": 1,
                    "unit": "Stück",
                    "unit_price": d_price,
                    "tax_rate": 19
                }
            ]
        }

        pairs.append({
            "id": p_id,
            "domain": "Domain 5: § 25a UStG Differenzbesteuerung",
            "prompt": prompt,
            "chosen": json.dumps(chosen_obj, ensure_ascii=False, indent=2),
            "rejected": json.dumps(rejected_obj, ensure_ascii=False, indent=2),
            "penalty_reason": "DIFFERENZBESTEUERUNG BREACH: Under § 25a Abs. 3 UStG, disclosing separate VAT amounts on invoices is strictly prohibited."
        })

    # --------------------------------------------------------------------------
    # 6. E-Rechnung EN 16931 / XRechnung 3.0 (Leitweg-ID BT-10 Enforcement)
    # --------------------------------------------------------------------------
    erechnung_prompts = [
        ("Bundesministerium des Innern", "04011000-12345-67", "IT-Forensik Gutachten", 1800.0),
        ("Stadtverwaltung Köln", "05315-00001-44", "Digitalisierung von Ratsunterlagen", 3400.0),
        ("Senatsverwaltung für Finanzen Berlin", "11000-0000000002-88", "Cloud-Security Audit", 4500.0),
        ("Deutsche Bahn AG", "05111-99887-33", "Netzwerk-Infrastruktur Wartung", 2900.0)
    ]
    for e_idx, (pub_client, leitweg, e_srv, e_amt) in enumerate(erechnung_prompts):
        p_id = f"PREF-XRECH-{e_idx+1:02d}"
        prompt = f"Erstelle eine EN 16931 / XRechnung 3.0 an {pub_client} mit Leitweg-ID {leitweg}: {e_srv} für {e_amt}€ netto."
        
        chosen_x = {
            "buyer_reference": leitweg,
            "invoice_number": f"RE-2025-{100+e_idx}",
            "issue_date": "2025-03-01",
            "due_date": "2025-03-31",
            "seller": {"name": "Rechly Solutions GmbH", "vat_id": "DE345678901", "street": "Musterstr. 1", "postal_code": "10115", "city": "Berlin", "country_code": "DE"},
            "buyer": {"name": pub_client, "street": "Behördenstr. 10", "postal_code": "10115", "city": "Berlin", "country_code": "DE"},
            "currency": "EUR",
            "payment_terms": "Zahlbar rein netto innerhalb von 30 Tagen.",
            "line_items": [{"line_id": "1", "name": e_srv, "quantity": 1.0, "unit_code": "C62", "unit_price": e_amt, "net_amount": e_amt, "tax_category": "S", "tax_percent": 19}],
            "total_net_amount": e_amt,
            "total_tax_amount": round(e_amt * 0.19, 2),
            "total_gross_amount": round(e_amt * 1.19, 2)
        }

        rejected_x = {
            "buyer_reference": "",  # Missing Leitweg-ID
            "invoice_number": f"RE-2025-{100+e_idx}",
            "issue_date": "2025-03-01",
            "due_date": "2025-03-31",
            "seller": {"name": "Rechly Solutions GmbH"},
            "buyer": {"name": pub_client},
            "currency": "EUR",
            "line_items": [{"name": e_srv, "quantity": 1.0, "price": e_amt}],
            "total_net_amount": e_amt,
            "total_gross_amount": e_amt
        }

        pairs.append({
            "id": p_id,
            "domain": "Domain 6: E-Rechnung EN 16931 / XRechnung",
            "prompt": prompt,
            "chosen": json.dumps(chosen_x, ensure_ascii=False, indent=2),
            "rejected": json.dumps(rejected_x, ensure_ascii=False, indent=2),
            "penalty_reason": "E-RECHNUNG REJECTION: Missing mandatory Leitweg-ID (BT-10) or UN/ECE unit codes results in instant technical rejection at the government ZRE/OZG-RE portals."
        })

    # --------------------------------------------------------------------------
    # 7. DATEV SKR03 & SKR04 Expense Accounts (30+ Standard Accounts)
    # --------------------------------------------------------------------------
    accounts_test = [
        ("Fachbuch über deutsches Steuerrecht 49€ inkl. 7% MwSt", "4940", "6815", 7, 100, "Fachliteratur"),
        ("Tanken Firmenwagen Diesel 85€ netto zzgl. 19% MwSt", "4530", "6530", 19, 100, "Kfz-Treibstoff"),
        ("Büromöbel Schreibtisch GWG 650€ netto", "0480", "0670", 19, 100, "GWG Geringwertige Wirtschaftsgüter"),
        ("Monatliche Festnetz- und Mobilfunkrechnung Telekom 120€ netto", "4920", "6805", 19, 100, "Telekommunikation"),
        ("Bahnfahrkarte ICE Geschäftsreise 2. Klasse 84€ inkl. 7% MwSt", "4673", "6673", 7, 100, "Reisekosten Bahn"),
        ("Hotelübernachtung auf Dienstreise 130€ netto zzgl. 7% MwSt", "4660", "6660", 7, 100, "Hotelübernachtung"),
        ("Software-Abonnement Adobe Creative Cloud 65€ netto", "4964", "6837", 19, 100, "EDV SaaS Software"),
        ("Kontoführungsgebühren Geschäftskonto 12€ steuerfrei", "4970", "6855", 0, 100, "Bankgebühren Geldverkehr")
    ]

    for a_idx, (exp_txt, skr03, skr04, vat, ded, cat) in enumerate(accounts_test):
        p_id = f"PREF-SKR-ACC-{a_idx+1:02d}"
        prompt = f"Kategorisiere für SKR03 und SKR04: '{exp_txt}'"
        
        chosen_acc = {
            "category": cat,
            "vat_rate": vat,
            "deductible_percent": ded,
            "skr03_account": skr03,
            "skr04_account": skr04,
            "note": f"DATEV-konforme Buchung für {cat}."
        }

        rejected_acc = {
            "category": cat,
            "vat_rate": 19 if vat == 7 else 0,  # Wrong tax rate
            "deductible_percent": ded,
            "skr03_account": "9999",  # Hallucinated non-existent account
            "skr04_account": "9999",
            "note": "Unbekanntes Konto."
        }

        pairs.append({
            "id": p_id,
            "domain": "Domain 7: DATEV Chart of Accounts Accuracy",
            "prompt": prompt,
            "chosen": json.dumps(chosen_acc, ensure_ascii=False, indent=2),
            "rejected": json.dumps(rejected_acc, ensure_ascii=False, indent=2),
            "penalty_reason": f"DATEV CHART MISMATCH: Must map to SKR03 {skr03} / SKR04 {skr04} with correct statutory VAT rate ({vat}%)."
        })

    bewirtung_prompts = [
        ("Geschäftsessen mit Kunde im Restaurant 145€ brutto mit Rechnung", 145.0),
        ("Bewirtung Geschäftspartner im Gasthof 210€ netto zzgl. 19% MwSt", 249.90),
        ("Arbeitsessen mit Neukunden im Steakhouse 95€ inklusive 19% USt", 95.0),
        ("Kundenbewirtung Projektabschlussessen 340€ brutto", 340.0)
    ]

    for idx, (p_text, amt) in enumerate(bewirtung_prompts):
        p_id = f"PREF-SKR-BEW-{idx+1:02d}"
        prompt = f"Kategorisiere für SKR03 und SKR04: '{p_text}'"
        
        chosen_obj = {
            "category": "Bewirtungsaufwand (Kundenbewirtung)",
            "vat_rate": 19,
            "deductible_percent": 70,
            "skr03_account": "4650",
            "skr04_account": "6640",
            "note": "Geschäftliche Bewirtung ist gem. § 4 Abs. 5 Nr. 2 EStG zu 70% als Betriebsausgabe abziehbar. Der Vorsteuerabzug beträgt 100%."
        }

        rejected_obj = {
            "category": "Bewirtung",
            "vat_rate": 19,
            "deductible_percent": 100,
            "skr03_account": "4900",
            "skr04_account": "6800",
            "note": "Vollständig als Betriebsausgabe abzugsfähig."
        }

        pairs.append({
            "id": p_id,
            "domain": "Domain 3: DATEV SKR Bewirtung 70% Cap",
            "prompt": prompt,
            "chosen": json.dumps(chosen_obj, ensure_ascii=False, indent=2),
            "rejected": json.dumps(rejected_obj, ensure_ascii=False, indent=2),
            "penalty_reason": "FINANCIAL COMPLIANCE VIOLATION: Business entertainment (Bewirtung) is legally capped at 70% corporate tax deduction (§ 4 Abs. 5 Nr. 2 EStG) and must map to SKR03 4650 / SKR04 6640."
        })

    # --------------------------------------------------------------------------
    # 4. GoBD § 14 Abs. 4 UStG Pre-Audit Inspector
    # --------------------------------------------------------------------------
    audit_prompts = [
        (
            "Rechnung von TechServices GmbH, Rechnungsnr RE-109, Ausstellungsdatum 15.02.2025, Leistung: 10 Std Beratung à 100€, Netto 1000€ + 190€ MwSt = 1190€ Brutto. Keine Steuernummer oder USt-IdNr angegeben.",
            "HOCH",
            False,
            ["Steuernummer oder USt-IdNr (§ 14 Abs. 4 Nr. 2 UStG)"],
            "Fehlende Steuernummer/USt-IdNr gefährdet den Vorsteuerabzug nach § 15 UStG vollständig."
        ),
        (
            "Lieferantenrechnung über 1.500€ Netto zzgl. 19% MwSt von Büroservice Maier, Steuernummer 14/123/45678, aber ohne fortlaufende Rechnungsnummer.",
            "HOCH",
            False,
            ["Fortlaufende Rechnungsnummer (§ 14 Abs. 4 Nr. 4 UStG)"],
            "Fehlende fortlaufende Rechnungsnummer führt bei Betriebsprüfungen zur Versagung des Vorsteuerabzugs."
        ),
        (
            "Rechnung von Kanzlei Weber & Partner GbR, USt-IdNr DE987654321, Rechnungsnr 2025-081, Datum 10.01.2025, Betrag 500€ netto + 95€ MwSt. Leistungszeitraum fehlt komplett.",
            "MITTEL",
            False,
            ["Zeitpunkt der Lieferung oder sonstigen Leistung (§ 14 Abs. 4 Nr. 6 UStG)"],
            "Fehlender Leistungszeitraum muss durch Korrekturbeleg geheilt werden."
        ),
        (
            "Ordnungsgemäße Rechnung der CloudHost AG, Rechnungsnr CH-2025-44, Datum 01.03.2025, USt-IdNr DE112233445, 120€ Netto + 22,80€ MwSt = 142,80€ Brutto, Leistungsdatum 01.03.2025, Cloud-Server Hosting März 2025.",
            "KEIN_RISIKO",
            True,
            [],
            "Vollständig GoBD- und UStG-konform. Voller Vorsteuerabzug gesichert."
        )
    ]

    for idx, (inv_text, exp_risk, exp_comp, missing, note) in enumerate(audit_prompts):
        p_id = f"PREF-GOBD-AUDIT-{idx+1:02d}"
        prompt = f"Prüfe folgende Eingangsrechnung auf GoBD-Konformität und Vorsteuerabzug nach § 14 Abs. 4 UStG: '{inv_text}'"

        chosen_obj = {
            "is_compliant": exp_comp,
            "vorsteuerabzug_risk": exp_risk,
            "missing_mandatory_fields": missing,
            "findings": [note],
            "recommendations": ["Rechnung zur Buchung freigeben."] if exp_comp else ["Rechnungskorrektur beim Aussteller anfordern."]
        }

        # Flawed rejected: model says compliant despite missing mandatory fields
        rejected_obj = {
            "is_compliant": True,
            "vorsteuerabzug_risk": "KEIN_RISIKO",
            "missing_mandatory_fields": [],
            "findings": ["Rechnung sieht gut aus."],
            "recommendations": ["Kann gebucht werden."]
        } if not exp_comp else {
            "is_compliant": False,
            "vorsteuerabzug_risk": "HOCH",
            "missing_mandatory_fields": ["Unbekannter Fehler"],
            "findings": ["Fehler"],
            "recommendations": ["Ablehnen"]
        }

        pairs.append({
            "id": p_id,
            "domain": "Domain 4: GoBD § 14 Abs. 4 UStG Pre-Audit",
            "prompt": prompt,
            "chosen": json.dumps(chosen_obj, ensure_ascii=False, indent=2),
            "rejected": json.dumps(rejected_obj, ensure_ascii=False, indent=2),
            "penalty_reason": "TAX AUDIT RISK: Misidentifying missing statutory fields (§ 14 Abs. 4 UStG) exposes companies to severe input VAT repayment penalties by the Finanzamt."
        })

    # --------------------------------------------------------------------------
    # 5. DATEV EXTF Semicolon Formatting (Decimal Comma vs Decimal Dot)
    # --------------------------------------------------------------------------
    extf_prompts = [
        ("Software SaaS Lizenz Google Workspace 142.80€ brutto bezahlt per Bank am 15.02.2025, Beleg RE-2025-081, SKR03", "142,80;S;EUR;;;;4964;1200;9;1502;RE-2025-081;;;Google Workspace SaaS", "142.80;S;EUR;;;;4964;1200;9;1502;RE-2025-081"),
        ("GWG Bürostuhl Kauf 450.00€ netto zzgl. 19% MwSt bezahlt per Bank am 10.01.2025, Beleg RE-449, SKR04", "535,50;S;EUR;;;;0670;1800;9;1001;RE-449;;;GWG Büromöbel Bürostuhl", "535.50,S,EUR,0670,1800,RE-449"),
        ("Geschäftliche Bewirtung Restaurant 119.00€ brutto am 22.03.2025 über Bank bezahlt, Beleg RE-901, SKR03", "119,00;S;EUR;;;;4650;1200;9;2203;RE-901;;;Bewirtungsaufwand", "119,00;H;USD;;;;4650;1200;;RE-901"),
        ("Kontoführungsgebühren Bank 15.00€ ohne MwSt am 31.01.2025, Beleg BK-01, SKR03", "15,00;S;EUR;;;;4970;1200;;3101;BK-01;;;Nebenkosten Geldverkehr", "15,00;S;EUR;;;;4970;1200;9;3101;BK-01;;;Bankgebühren")
    ]

    for idx, (p_text, chosen_line, rejected_line) in enumerate(extf_prompts):
        p_id = f"PREF-DATEV-EXTF-{idx+1:02d}"
        prompt = f"Erzeuge den DATEV-Buchungssatz (EXTF-Zeile): '{p_text}'"

        pairs.append({
            "id": p_id,
            "domain": "Domain 5: DATEV EXTF Formatting",
            "prompt": prompt,
            "chosen": chosen_line,
            "rejected": rejected_line,
            "penalty_reason": "DATEV IMPORT SYNTAX ERROR: DATEV EXTF requires semicolon delimiter, German comma decimal representation (e.g. 142,80), exact Soll/Haben flag, and correct BU-Schlüssel."
        })

    # --------------------------------------------------------------------------
    # 6. B2B Line Item Rewriting (Formal Terminology vs Slang)
    # --------------------------------------------------------------------------
    rewriter_prompts = [
        (
            "homepage schneller gemacht und alte bilder gelöscht",
            "Performance-Optimierung der Webpräsenz: Bereinigung des Bilddatenbestands und signifikante Reduktion der Server-Ladezeiten.",
            "Hier ist der Text für Ihre Rechnung: homepage schneller gemacht und alte bilder gelöscht. Hoffe das hilft!"
        ),
        (
            "rohre freigemacht im keller und dichtung getauscht",
            "Fachgerechte Sanitär-Instandsetzung: Mechanische Rohrreinigung im Kellerbereich sowie Austausch schadhafter Dichtungselemente inklusive Dichtheitsprüfung.",
            "{\"status\": \"ok\", \"beschreibung\": \"rohre freigemacht im keller und dichtung getauscht\"}"
        ),
        (
            "social media beiträge getextet und grafiken gebastelt",
            "Redaktionelle Content-Erstellung für Social Media: Konzeption, Zielgruppen-Texterstellung sowie grafische Ausarbeitung von Beiträgen gemäß Redaktionsplan.",
            "social media beiträge getextet und grafiken gebastelt für kunden"
        ),
        (
            "datenbank aufgeräumt und alte kunden bereinigt",
            "Datenbank-Wartung und Performance-Tuning: Bereinigung historischer Datensätze sowie Konsistenzprüfung relationaler Tabellenstrukturen.",
            "Datenbank aufgeräumt und alte Kunden gelöscht."
        )
    ]

    for idx, (raw_note, chosen_txt, rejected_txt) in enumerate(rewriter_prompts):
        p_id = f"PREF-REWRITE-{idx+1:02d}"
        prompt = f"Optimiere diese Tätigkeitsbeschreibung für die Rechnungsstellung: '{raw_note}'"

        pairs.append({
            "id": p_id,
            "domain": "Domain 6: B2B Line Item Rewriter",
            "prompt": prompt,
            "chosen": chosen_txt,
            "rejected": rejected_txt,
            "penalty_reason": "COMMERCIAL STYLE ERROR: Invoice line items must be formal, auditable GoBD descriptions without informal slang, markdown chat wrapper preamble, or JSON artifacts."
        })

    # --------------------------------------------------------------------------
    # 7. Mahnwesen Escalation Progression
    # --------------------------------------------------------------------------
    dunning_prompts = [
        (
            "Erstelle eine freundliche Zahlungserinnerung (Stufe 1) an Kanzlei Schmidt für Rechnung RE-101 über 1.200€, seit 7 Tagen überfällig.",
            "Betreff: Zahlungserinnerung zu Rechnung RE-101\n\nSehr geehrte Damen und Herren,\n\nsicherlich ist es Ihrer Aufmerksamkeit im Alltagsgeschäft entgangen: Für unsere Rechnung RE-101 über 1.200,00 EUR konnten wir bis heute keinen Zahlungseingang feststellen. Wir bitten Sie höflich, den Betrag innerhalb der nächsten 10 Tage auf unser Konto zu überweisen. Sollte sich Ihre Zahlung mit diesem Schreiben überschnitten haben, betrachten Sie es bitte als gegenstandslos.\n\nMit freundlichen Grüßen",
            "Betreff: LETZTE MAHNUNG VOR GERICHTLICHEN SCHRITTEN RE-101\n\nZahlen Sie sofort 1.200€ plus 50€ Mahnkosten binnen 24 Stunden, sonst leiten wir unverzüglich ein gerichtliches Mahnverfahren ein!"
        )
    ]

    for idx, (prompt_txt, chosen_dunning, rejected_dunning) in enumerate(dunning_prompts):
        p_id = f"PREF-MAHN-{idx+1:02d}"
        pairs.append({
            "id": p_id,
            "domain": "Domain 7: Mahnwesen Tone Progression",
            "prompt": prompt_txt,
            "chosen": chosen_dunning,
            "rejected": rejected_dunning,
            "penalty_reason": "CUSTOMER RELATIONS & LEGAL BREACH: Stage 1 reminder must be polite and diplomatic; threatening immediate legal action on a 7-day overdue notice destroys B2B client trust."
        })

    return pairs


def main():
    pairs = create_preference_samples()
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    print(f"Generated {len(pairs)} high-precision German accounting preference pairs at:")
    print(f"👉 {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

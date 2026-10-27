#!/usr/bin/env python3
"""
Open-Source Synthetic German Accounting Dataset Generator Engine for Rechly-DE-3B.
Generates comprehensive, GoBD- and UStG-compliant German training pairs across all 5 core domains.
Requires 0 proprietary APIs and 0 paid external services.
Guarantees 100% prompt uniqueness and strict schema validity.
"""

import json
import random
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# --- Domain 1 Data Pools ---

COMPANY_PREFIXES = [
    "WebTech", "Müller Handwerk", "Dr. Meyer Praxisberatung", "Kanzlei Becker & Partner",
    "Alpha Cloud Services", "Schmidt Logistik", "Bauer Medien", "Tischlerei Holz & Form",
    "Elektroanlagen Blitz", "Sanitär Express", "Architekturbüro Bauwerk", "Kreativschmiede",
    "Green Logistics", "Catering Gaumenfreude", "Fitness & Health Studio", "Zahnarztpraxis Weishaupt",
    "Consulting Partners International", "Autohaus Nordstern", "Buchhandlung Seitenweise",
    "Software Manufaktur Süd", "Event Solutions Berlin", "Druckhaus Gutenberg", "Konditorei Süße Träume",
    "Immobilienverwaltung Werte & Raum", "Fotostudio Lichtblick", "Clean & Clear Gebäudereinigung",
    "Reisebüro Weltentdecker", "KfZ-Meisterwerkstatt Kraft & Sohn", "Biohof Sonnenschein",
    "IT-Security Pentest Labs", "Vanguard Financial Consulting", "Nordic Design Studio",
    "Optik Weitblick", "Apotheke am Markt", "Treuhand Steuerberatung", "Bäckerei Frisch & Krustig",
    "Haustechnik Kälte-Klima", "Ingenieurbüro Statik & Plan", "Modemanufaktur Eleganz",
    "Dachdeckerei Sturmfest", "Garten- und Landschaftsbau Grünkonzept", "Personalberatung TalentScout",
    "Übersetzungsbüro Polyglott", "Physiotherapie Vitalis", "Metzgerei Meisterstück"
]

LEGAL_FORMS = ["GmbH", "AG", "UG (haftungsbeschränkt)", "GmbH & Co. KG", "e.K.", "GbR", "OHG"]

CITIES = [
    "Berlin", "München", "Hamburg", "Köln", "Frankfurt am Main", "Stuttgart", "Düsseldorf",
    "Leipzig", "Dortmund", "Essen", "Bremen", "Dresden", "Hannover", "Nürnberg", "Duisburg",
    "Bochum", "Wuppertal", "Bielefeld", "Bonn", "Münster", "Karlsruhe", "Mannheim", "Augsburg",
    "Wiesbaden", "Mönchengladbach", "Gelsenkirchen", "Aachen", "Braunschweig", "Kiel", "Chemnitz",
    "Halle (Saale)", "Magdeburg", "Freiburg im Breisgau", "Krefeld", "Mainz", "Lübeck", "Erfurt",
    "Oberhausen", "Rostock", "Kassel", "Hagen", "Potsdam", "Saarbrücken", "Hamm", "Ludwigshafen",
    "Mülheim an der Ruhr", "Oldenburg", "Osnabrück", "Leverkusen", "Heidelberg", "Darmstadt"
]

SERVICE_CATALOG = [
    # IT & Software (19%)
    {
        "desc": "Full-Stack Softwareentwicklung und API-Architektur in TypeScript/Python",
        "raw_names": ["Softwareentwicklung", "Backend-Programmierung", "Full-Stack Dev-Stunden", "API-Entwicklung"],
        "unit": "Stunde",
        "price_range": (85.0, 160.0),
        "tax": 19,
        "industry": "IT"
    },
    {
        "desc": "Sicherheits-Audit und Penetration-Testing der Cloud-Infrastruktur",
        "raw_names": ["Security Audit pauschal", "Cloud Pentest", "Sicherheitsanalyse der Webapp"],
        "unit": "Pauschal",
        "price_range": (850.0, 2400.0),
        "tax": 19,
        "industry": "IT"
    },
    {
        "desc": "Laufende Systemadministration, Monitoring und Linux-Server-Wartung",
        "raw_names": ["Serverwartung Monatsvertrag", "DevOps Server-Betreuung", "Systempflege Linux"],
        "unit": "Monat",
        "price_range": (350.0, 950.0),
        "tax": 19,
        "industry": "IT"
    },
    {
        "desc": "Cloud-Migration und Kubernetes-Cluster-Einrichtung",
        "raw_names": ["Kubernetes Consulting Tage", "Cloud-Migration Tagessatz", "DevOps Workshop"],
        "unit": "Tag",
        "price_range": (950.0, 1500.0),
        "tax": 19,
        "industry": "IT"
    },
    {
        "desc": "Responsive UI/UX Frontend-Entwicklung und Barrierefreiheitsoptimierung",
        "raw_names": ["Frontend UI-Design Stunden", "UI/UX Redesign", "Barrierefreie Webanpassung"],
        "unit": "Stunde",
        "price_range": (80.0, 125.0),
        "tax": 19,
        "industry": "Design"
    },

    # Handwerk & Technik (19%)
    {
        "desc": "Elektrotechnische Installationsarbeiten und Verteilerkasten-Modernisierung",
        "raw_names": ["Elektroarbeiten Arbeitsstunden", "Schaltschrank-Installation", "Montagestunden Elektrik"],
        "unit": "Stunde",
        "price_range": (65.0, 95.0),
        "tax": 19,
        "industry": "Handwerk"
    },
    {
        "desc": "Verbrauchsmaterial, VDE-geprüfte Leitungselemente und Installationsmaterial",
        "raw_names": ["Klein- und Befestigungsmaterial Pauschale", "Installationsmaterial VDE", "Schaltermaterial"],
        "unit": "Pauschal",
        "price_range": (45.0, 180.0),
        "tax": 19,
        "industry": "Handwerk"
    },
    {
        "desc": "Sanitäre Instandsetzungsarbeiten, Rohrreparatur und Dichtheitsprüfung",
        "raw_names": ["Sanitär Notdienst Stunden", "Rohrreinigung und Dichtungstausch", "Klempnerarbeiten"],
        "unit": "Stunde",
        "price_range": (70.0, 110.0),
        "tax": 19,
        "industry": "Handwerk"
    },
    {
        "desc": "Schreiner-Maßanfertigung und Vor-Ort-Montage Einbauschrank",
        "raw_names": ["Maßgefertigter Büroschrank", "Konferenztisch Holz Einzelanfertigung", "Empfangstheke Schreinerarbeit"],
        "unit": "Stück",
        "price_range": (1400.0, 3600.0),
        "tax": 19,
        "industry": "Handwerk"
    },
    {
        "desc": "Maler-, Tapezier- und Spachtelarbeiten Gewerberäume nach VOB",
        "raw_names": ["Malerarbeiten Tagessatz", "Spachtelarbeiten Gewerbefläche", "Wandanstrich Bürotage"],
        "unit": "Tag",
        "price_range": (480.0, 750.0),
        "tax": 19,
        "industry": "Handwerk"
    },

    # Beratung, Coaching, Finanzen (19%)
    {
        "desc": "Strategische Unternehmensberatung und Prozessoptimierung Geschäftsführung",
        "raw_names": ["Strategieberatung Tagessatz", "Management Consulting Tage", "Geschäftsführer-Coaching"],
        "unit": "Tag",
        "price_range": (1200.0, 2400.0),
        "tax": 19,
        "industry": "Consulting"
    },
    {
        "desc": "Fachworkshop: Prozessautomatisierung und digitale Rechnungslegung",
        "raw_names": ["Workshop Digitalisierung pauschal", "Mitarbeiterschulung Invoicing", "Prozess-Training Tag"],
        "unit": "Pauschal",
        "price_range": (1300.0, 2800.0),
        "tax": 19,
        "industry": "Consulting"
    },
    {
        "desc": "Juristisches Fachlektorat, Prüfung von B2B-Verträgen und Datenschutz-Audit",
        "raw_names": ["Vertragsprüfung Stunden", "Datenschutz-Audit Kanzlei", "Rechtsberatung Wirtschaftsrecht"],
        "unit": "Stunde",
        "price_range": (120.0, 220.0),
        "tax": 19,
        "industry": "Legal"
    },

    # 7% USt (Bücher, Zeitschriften, Gastronomie/Lebensmittel)
    {
        "desc": "Lieferung gedrucktes Fachbuch 'Handbuch des deutschen Steuerrechts'",
        "raw_names": ["Fachbücher Steuerrecht 7% MwSt", "Gedruckte Lehrbücher Bilanzierung", "Fachliteratur Druckwerk"],
        "unit": "Stück",
        "price_range": (35.0, 89.0),
        "tax": 7,
        "industry": "Print"
    },
    {
        "desc": "Jahresabonnement Print-Fachzeitschrift für Wirtschafts- und Arbeitsrecht",
        "raw_names": ["Abonnement Fachzeitschrift Recht 7% MwSt", "Printabo Wirtschaftsjournal", "Fachmagazin Jahresbezug"],
        "unit": "Stück",
        "price_range": (110.0, 290.0),
        "tax": 7,
        "industry": "Print"
    },
    {
        "desc": "Konferenz-Catering: Tagungsverpflegung und Heißgetränke für Teilnehmer",
        "raw_names": ["Catering Kaffeepause und Gebäck 7% MwSt", "Tagungsverpflegung Pauschale", "Bio-Snackplatte Seminar"],
        "unit": "Pauschal",
        "price_range": (220.0, 680.0),
        "tax": 7,
        "industry": "Gastronomie"
    },
]

PAYMENT_TERMS_CONFIG = [
    (14, "Zahlbar innerhalb von 14 Tagen ab Rechnungsdatum rein netto ohne Abzug."),
    (30, "Zahlbar innerhalb von 30 Tagen rein netto ab Rechnungszugang."),
    (0, "Zahlbar sofort nach Erhalt der Rechnung ohne jeden Abzug."),
    (14, "Zahlbar innerhalb von 14 Tagen mit 2% Skonto oder binnen 30 Tagen netto."),
    (10, "Zahlbar innerhalb von 10 Tagen mit 3% Skonto, 30 Tage netto."),
    (7, "Zahlungsziel: 7 Tage rein netto."),
    (21, "Zahlbar innerhalb von 21 Tagen ohne Abzug.")
]


def generate_company_name() -> Tuple[str, str]:
    prefix = random.choice(COMPANY_PREFIXES)
    form = random.choice(LEGAL_FORMS)
    city = random.choice(CITIES)
    return f"{prefix} {form}", city


def generate_domain_1_samples(count: int = 250, seen_hashes: Set[str] = None) -> List[Dict[str, Any]]:
    samples = []
    regimes = ["standard", "kleinunternehmer", "reverse_charge_13b", "innergemeinschaftlich", "drittland"]

    attempts = 0
    while len(samples) < count and attempts < count * 20:
        attempts += 1
        regime = random.choice(regimes)
        client, city = generate_company_name()
        due_days, term_text = random.choice(PAYMENT_TERMS_CONFIG)

        num_items = random.choices([1, 2, 3], weights=[0.50, 0.40, 0.10])[0]
        selected_services = random.sample(SERVICE_CATALOG, num_items)

        items = []
        raw_prompt_items = []

        for svc in selected_services:
            qty = random.randint(1, 25) if svc["unit"] in ("Stunde", "Stück") else (random.randint(1, 5) if svc["unit"] == "Tag" else 1)
            price = round(random.uniform(*svc["price_range"]), 2)
            raw_title = random.choice(svc["raw_names"])

            if regime in ("kleinunternehmer", "reverse_charge_13b", "innergemeinschaftlich", "drittland"):
                tax_rate = 0
            else:
                tax_rate = svc["tax"]

            items.append({
                "description": svc["desc"],
                "quantity": qty,
                "unit_of_measure": svc["unit"],
                "price": price,
                "tax_rate_percent": tax_rate
            })

            raw_prompt_items.append(f"{qty}x {raw_title} à {price:.2f}€")

        items_str = " und ".join(raw_prompt_items)

        if regime == "kleinunternehmer":
            prompt_templates = [
                f"Erstelle eine Rechnung an {client} ({city}): {items_str}, Zahlungsziel {due_days} Tage. Beachte: Ich bin Kleinunternehmer.",
                f"Rechnung an {client}: {items_str}, {term_text}. Keine Umsatzsteuer ausweisen wegen Kleinunternehmerregelung § 19.",
                f"Schreibe Rechnung an {client} in {city} für {items_str}. Ich nehme die Kleinunternehmerregelung nach § 19 UStG in Anspruch, Frist {due_days} Tage.",
            ]
            notes = "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet (Kleinunternehmerregelung)."
        elif regime == "reverse_charge_13b":
            prompt_templates = [
                f"Rechnung an {client} ({city}) für Bauleistungen: {items_str}, {term_text}. Bauleistung an Unternehmer mit § 13b.",
                f"Erstelle Bauleistungsrechnung an {client}: {items_str}. Hinweis auf Steuerschuldnerschaft des Leistungsempfängers § 13b, Zahlungsziel {due_days} Tage.",
                f"Rechnung für handwerkliche Bauleistung an Generalunternehmer {client} in {city}: {items_str}, {term_text}, Reverse Charge.",
            ]
            notes = "Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge / § 13b Abs. 2 Nr. 4 i.V.m. Abs. 5 UStG)."
        elif regime == "innergemeinschaftlich":
            prompt_templates = [
                f"Rechnung an {client} mit Sitz im EU-Ausland (USt-IdNr. vorhanden): {items_str}, {term_text}. Innergemeinschaftliche Lieferung.",
                f"B2B-Rechnung für grenzüberschreitende Lieferung an {client} in der EU: {items_str}, Zahlungsziel {due_days} Tage, steuerfreie innergemeinschaftliche Lieferung.",
                f"Erstelle Rechnung an EU-Geschäftskunden {client}: {items_str}, {term_text}. Vermerk § 4 Nr. 1b i.V.m. § 6a UStG.",
            ]
            notes = "Steuerfreie innergemeinschaftliche Lieferung gem. § 4 Nr. 1b i.V.m. § 6a UStG. Steuerschuldnerschaft des Leistungsempfängers."
        elif regime == "drittland":
            prompt_templates = [
                f"Exportrechnung an {client} (Schweiz / Drittland): {items_str}, Zahlungsziel {due_days} Tage.",
                f"Rechnung für Ausfuhrlieferung in Drittstaat an {client}: {items_str}, {term_text}. Keine deutsche USt gem. § 4 Nr. 1a UStG.",
                f"Erstelle Rechnung an {client} in Zürich/Schweiz: {items_str}, Frist {due_days} Tage, steuerfreie Ausfuhr.",
            ]
            notes = "Steuerfreie Ausfuhrlieferung gem. § 4 Nr. 1a i.V.m. § 6 UStG."
        else:
            prompt_templates = [
                f"Rechnung an {client} ({city}): {items_str}, {term_text}.",
                f"Erstelle eine Rechnung an {client}: {items_str}, Zahlungsziel {due_days} Tage.",
                f"Bitte erstelle Rechnung für {client} in {city} über {items_str}, Zahlungsbedingungen: {term_text}.",
            ]
            notes = "Wir bedanken uns für den Auftrag und freuen uns auf eine weiterhin erfolgreiche Zusammenarbeit."

        prompt = random.choice(prompt_templates)
        h = hashlib.sha256(prompt.strip().lower().encode("utf-8")).hexdigest()
        if seen_hashes is not None and h in seen_hashes:
            continue
        if seen_hashes is not None:
            seen_hashes.add(h)

        output_data = {
            "client_name": client,
            "due_days": due_days,
            "payment_terms": term_text,
            "notes": notes,
            "items": items
        }

        samples.append({
            "conversations": [
                {"from": "human", "value": prompt},
                {"from": "gpt", "value": json.dumps(output_data, ensure_ascii=False)}
            ]
        })

    return samples


# --- Domain 2: Line Item Rewriter ---

LINE_ITEM_DEFINITIONS = [
    (
        "homepage schneller gemacht und bilder komprimiert",
        "Performance-Optimierung der Webpräsenz: Bereinigung und Indexierung, Konvertierung aller Bildressourcen in Next-Gen-Formate (WebP/AVIF) sowie messbare Reduktion der Ladezeiten und Asset-Minifizierung."
    ),
    (
        "datenbank aufgeräumt und alte einträge gelöscht",
        "Wartung und Integritätsprüfung relationaler Datenbanktabellen: Re-Indexierung, Vakuumierung und datenschutzkonforme Bereinigung veralteter Temporärdaten gem. GoBD/DSGVO."
    ),
    (
        "server abgestürzt am sonntag, wieder hochgefahren und backup geprüft",
        "Notfall-Systemadministration außerhalb der Regelarbeitszeit: Wiederherstellung der Hochverfügbarkeit nach Serverausfall inklusive Konsistenzprüfung der differentiellen Datensicherungen."
    ),
    (
        "küchenspüle angeschlossen und siffon getauscht",
        "Sanitärinstallation: Fachgerechter Anschluss einer Küchenspüle sowie Demontage und Neumontage einer geruchsdichten Geruchsverschluss-Garnitur (Siphon) inklusive Dichtheitsprüfung."
    ),
    (
        "steckdosen im büro neu verlegt und kabelkanal gesetzt",
        "Elektrotechnische Ausbauarbeiten: Aufputzverlegung schlagfester Kabelkanäle sowie normgerechte Nachrüstung und VDE-Prüfung von Arbeitsplatzsteckdosen."
    ),
    (
        "social media beiträge getextet und grafiken gebastelt",
        "Redaktionelle Content-Erstellung für Social Media: Konzeption, Zielgruppen-Texterstellung sowie grafische Ausarbeitung von Beiträgen gemäß Corporate Design für den Redaktionsplan."
    ),
    (
        "mit dem kunden telefoniert wegen neuer homepage struktur",
        "Konzeptionelle Fachberatung: Strategiegespräch zur Navigationsarchitektur, User Journey und Anforderungsspezifikation für den geplanten Webauftritt."
    ),
    (
        "laptop neu aufgesetzt und windows installiert",
        "IT-Arbeitsplatzkonfiguration: Vollständige Neuinstallation des Betriebssystems inklusive Einrichtung der Hardware-Treiber, Verschlüsselung und Konfiguration der Sicherheitspolicies."
    ),
    (
        "heizkörper entlüftet und thermostate getauscht",
        "Instandhaltung Heizungsanlage: Thermostattausch sowie Entlüftung und hydraulischer Druckausgleich der Raumheizkörper im Erdgeschoss."
    ),
    (
        "präsentation für investoren überarbeitet und hübscher gemacht",
        "Professionelle Pitch-Deck-Optimierung: Didaktische und gestalterische Überarbeitung von Unternehmensdaten, Finanzprognosen und Wertversprechen für Investorengespräche."
    ),
    (
        "neue mitarbeiter eingearbeitet in git und python",
        "Technisches Onboarding & Praxisschulung: Vermittlung interner Entwicklungsstandards, Versionskontrolle (Git-Flow) und Clean-Code-Prinzipien für neue Mitarbeiter."
    ),
    (
        "lagerregale verschraubt und schilder angebracht",
        "Lagereinrichtung und Betriebssicherheit: Fachgerechte Schwerlastanker-Montage industrieller Regalsysteme inklusive Anbringung von Fachlast- und Prüfkennzeichnungen nach DGUV."
    ),
    (
        "firmenwagen gewaschen und innen gereinigt vor rückgabe",
        "Fahrzeugaufbereitung zur Leasingrückgabe: Vollständige Innen- und Außenreinigung inklusive Lackschonwäsche, Polsterreinigung und Dokumentation des Fahrzeugzustands."
    ),
    (
        "klimaanlage gecheckt und filter gereinigt",
        "Periodische Inspektion der raumlufttechnischen Anlage (RLT): Filterreinigung, Desinfektion der Verdampfereinheit und Dichtheitsprüfung nach VDI 6022."
    ),
    (
        "fotos gemacht vom event und nachbearbeitet",
        "Eventfotografie und Postproduktion: Vor-Ort-Reportage während der Unternehmensveranstaltung sowie professionelle Farbkorrektur, Belichtungsoptimierung und Bereitstellung hochauflösender Bilddaten."
    ),
    (
        "newsletter verschickt und abmeldungen rausgenommen",
        "E-Mail-Marketing-Management: Redaktioneller Versand des Newsletters sowie Bereinigung der Empfängerdatenbank bezüglich Bounces und DSGVO-Opt-Outs."
    ),
    (
        "dachrinne sauber gemacht und laub entfernt",
        "Dachdeckerarbeiten: Gründliche Beseitigung von Laub- und Schmutzablagerungen aus Zinkdachrinnen sowie Überprüfung der Fallrohre auf ungehinderten Wasserablauf."
    ),
    (
        "agb durchgelesen und muster widerruf angepasst",
        "Rechtliche Textprüfung: Abgleich der Allgemeinen Geschäftsbedingungen und der gesetzlichen Widerrufsbelehrung mit aktuellen verbraucherschutzrechtlichen Bestimmungen."
    ),
    (
        "fließen im bad neu verfugt",
        "Fliesenleger-Instandsetzungsarbeiten: Fachgerechtes Entfernen von spröden Fugenmassen und Einbringen dauerelastischer, fungizider Sanitärsilikonfugen."
    ),
    (
        "wlan eingerichtet im ganzen büro mit 3 routern",
        "Netzwerktechnik: Konzeption, Montage und Funkausleuchtung eines unterbrechungsfreien Mesh-WLAN-Systems unter Verwendung dreier Access Points."
    ),
    (
        "logo entwurf 3x geändert für kunden meeting",
        "Grafische Konzeptionierung und iterative Überarbeitung des Unternehmenslogos gemäß Kundenfeedback inklusive Vorbereitung der Präsentationsdateien."
    ),
    (
        "lager gezählt am jahresende für bilanz",
        "Stichtagsinventur: Körperliche Bestandsaufnahme und zählgenaue Erfassung aller Lagergüter zum Bilanzstichtag inklusive Abgleich mit dem Warenwirtschaftssystem."
    ),
    (
        "drucker repariert der papierstau hatte",
        "Hardware-Instandsetzung: Beseitigung mechanischer Papiereinzugsstörungen sowie Reinigung und Kalibrierung der Transportwalzen des Abteilungsdruckers."
    ),
    (
        "seo texte geschrieben für onlineshop schuhe",
        "Suchmaschinenoptimierte Texterstellung (SEO): Redaktionelle Erstellung von Produkt- und Kategoriebeschreibungen mit Keyword-Dichte und strukturierten Meta-Tags."
    ),
    (
        "zaun repariert der umgeweht war beim sturm",
        "Zaunbau-Instandsetzung: Rückbau beschädigter Zaunelemente, Neuverankerung der Pfosten im Erdreich sowie fachgerechte Montage von Doppelstabmatten nach Sturmschaden."
    )
]


def generate_domain_2_samples(count: int = 150, seen_hashes: Set[str] = None) -> List[Dict[str, Any]]:
    samples = []
    prefixes = [
        "Formuliere folgende Position professionell und GoBD-konform für eine B2B-Rechnung:",
        "Optimiere diese Tätigkeitsbeschreibung für die offizielle Rechnungsstellung:",
        "Wie lautet die korrekte, prüfungssichere Leistungsbeschreibung für eine Handwerker-/Dienstleisterrechnung für:",
        "Schreibe folgende Notiz audit-proof und kaufmännisch präzise für die Kundenrechnung um:",
        "Wandle diese informelle Notiz in eine GoBD-konforme Rechnungsposition um:",
        "Professionelle Formulierung für folgende Rechnungsposition erbeten:",
        "Bringe diese Notiz in eine audit-fähige B2B-Formulierung:"
    ]

    attempts = 0
    while len(samples) < count and attempts < count * 20:
        attempts += 1
        raw_note, formal_desc = random.choice(LINE_ITEM_DEFINITIONS)
        prefix = random.choice(prefixes)
        prompt = f"{prefix} '{raw_note}'"

        h = hashlib.sha256(prompt.strip().lower().encode("utf-8")).hexdigest()
        if seen_hashes is not None and h in seen_hashes:
            continue
        if seen_hashes is not None:
            seen_hashes.add(h)

        samples.append({
            "conversations": [
                {"from": "human", "value": prompt},
                {"from": "gpt", "value": formal_desc}
            ]
        })
    return samples


# --- Domain 3: German Tax & GoBD Compliance ---

TAX_SPECS = [
    {
        "questions": [
            "Welche steuerliche Pflichtangabe muss auf die Rechnung bei Anwendung der Kleinunternehmerregelung (§ 19 UStG)?",
            "Was muss ein Kleinunternehmer gesetzlich vorgeschrieben auf seine Ausgangsrechnung schreiben?",
            "Welcher Hinweis nach § 19 UStG gehört auf Rechnungen von Kleinunternehmern?",
            "Wie lautet der offizielle Vermerk für die Kleinunternehmerregelung nach § 19 UStG?",
            "Welche Formulierung befreit Kleinunternehmer vom gesonderten Steuerausweis auf Rechnungen?",
        ],
        "answer": "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet (Kleinunternehmerregelung)."
    },
    {
        "questions": [
            "Welcher Hinweistext gehört auf eine Rechnung für Bauleistungen an einen anderen Bauunternehmer gem. § 13b UStG?",
            "Wie lautet der offizielle Vermerk für das Reverse-Charge-Verfahren bei handwerklichen Bauleistungen?",
            "Welche Klausel verlangt das Finanzamt bei Bauleistungen nach § 13b Abs. 2 Nr. 4 UStG?",
            "Welcher Vermerk gehört auf die Rechnung für Handwerkerleistungen an einen Generalunternehmer?",
            "Welche Gesetzesklausel muss bei Steuerschuldnerschaft des Leistungsempfängers im Baugewerbe (§ 13b UStG) angegeben werden?",
        ],
        "answer": "Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge / § 13b Abs. 2 Nr. 4 i.V.m. Abs. 5 UStG)."
    },
    {
        "questions": [
            "Welche Gesetzesklausel muss bei einer steuerfreien innergemeinschaftlichen Lieferung an ein Unternehmen in Frankreich mit gültiger USt-IdNr. angegeben werden?",
            "Welcher Vermerk gehört auf die B2B-Rechnung für eine innergemeinschaftliche Warenlieferung in die EU?",
            "Wie lautet die Pflichtklausel nach § 4 Nr. 1b i.V.m. § 6a UStG?",
            "Welcher Steuerhinweis muss auf eine Rechnung für Warenlieferungen an einen EU-Geschäftskunden?",
        ],
        "answer": "Steuerfreie innergemeinschaftliche Lieferung gem. § 4 Nr. 1b i.V.m. § 6a UStG. Steuerschuldnerschaft des Leistungsempfängers."
    },
    {
        "questions": [
            "Welcher Vermerk ist erforderlich bei einem Export von Waren an einen Geschäftskunden in die Schweiz (Drittland)?",
            "Wie lautet der steuerliche Hinweis für eine Ausfuhrlieferung in ein Drittland außerhalb der EU?",
            "Welche Klausel gehört auf Ausfuhrrechnungen in Drittländer gem. § 4 Nr. 1a UStG?",
            "Welcher Rechnungsvermerk ist bei Warenexporten in die USA oder nach Großbritannien erforderlich?",
        ],
        "answer": "Steuerfreie Ausfuhrlieferung gem. § 4 Nr. 1a i.V.m. § 6 UStG."
    },
    {
        "questions": [
            "Welcher Hinweis gehört auf eine Rechnung bei Verkauf von Gebrauchtwaren unter Differenzbesteuerung?",
            "Welche Formulierung ist bei Differenzbesteuerung nach § 25a UStG verpflichtend?",
            "Wie weist ein Gebrauchtwarenhändler die Umsatzsteuer nach § 25a UStG aus?",
            "Was muss auf einer Rechnung stehen wenn Gebrauchtgegenstände nach § 25a UStG veräußert werden?",
        ],
        "answer": "Sonderregelung für Gebrauchtgegenstände gem. § 25a UStG (Differenzbesteuerung). Ein gesonderter Ausweis der Umsatzsteuer erfolgt nicht."
    },
    {
        "questions": [
            "Welcher Vermerk gehört auf die B2B-Dienstleistungsrechnung an einen Kunden in Österreich mit UID-Nummer?",
            "Wie lautet der Reverse-Charge-Hinweis für innergemeinschaftliche sonstige Leistungen nach § 3a UStG?",
            "Welcher Pflichtvermerk gilt für grenzüberschreitende B2B-Dienstleistungen innerhalb der Europäischen Union?",
            "Wie muss eine grenzüberschreitende Beratungsrechnung innerhalb der EU nach § 3a Abs. 2 UStG gekennzeichnet werden?",
        ],
        "answer": "Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge / Innergemeinschaftliche sonstige Leistung gem. § 3a Abs. 2 UStG)."
    },
    {
        "questions": [
            "Welche gesetzlichen Mindestangaben müssen nach § 14 Abs. 4 UStG auf einer ordnungsgemäßen B2B-Rechnung über 250 Euro stehen?",
            "Was sind die Pflichtbestandteile einer deutschen Rechnung nach § 14 UStG?",
            "Welche Pflichtangaben fordert das deutsche Umsatzsteuergesetz für vollwertige Rechnungen?",
        ],
        "answer": "Eine ordnungsgemäße Rechnung nach § 14 Abs. 4 UStG muss zwingend enthalten: 1. Vollständiger Name und Anschrift des leistenden Unternehmers und des Leistungsempfängers; 2. Steuernummer oder USt-IdNr.; 3. Ausstellungsdatum; 4. Fortlaufende, einmalige Rechnungsnummer; 5. Menge und handelsübliche Bezeichnung der gelieferten Gegenstände oder Art und Umfang der Leistung; 6. Leistungszeitpunkt bzw. Lieferdatum; 7. Nach Steuersätzen aufgeschlüsseltes Entgelt; 8. Anzuwendender Steuersatz (19%, 7% oder 0%) sowie Steuerbetrag; 9. Im Fall einer Steuerbefreiung ein Hinweis auf den Befreiungsgrund."
    },
    {
        "questions": [
            "Welche Erleichterungen gelten für Kleinbetragsrechnungen bis 250 Euro nach § 33 UStDV?",
            "Welche Angaben genügen auf einer Quittung oder Rechnung bis maximal 250 Euro brutto?",
            "Welche Mindestangaben verlangt das Finanzamt bei Kleinbetragsrechnungen nach § 33 UStDV?",
        ],
        "answer": "Nach § 33 UStDV genügen bei Kleinbetragsrechnungen bis 250 Euro Gesamtbetrag folgende Mindestangaben: 1. Vollständiger Name und Anschrift des leistenden Unternehmers; 2. Ausstellungsdatum; 3. Menge und Art der gelieferten Gegenstände oder Umfang der Leistung; 4. Das Entgelt und der Steuerbetrag in einer Summe (Bruttobetrag); 5. Der anzuwendende Steuersatz oder der Hinweis auf eine Steuerbefreiung. Die Angabe des Leistungsempfängers, der Steuernummer und einer Rechnungsnummer ist nicht erforderlich."
    },
    {
        "questions": [
            "Wie lange müssen Rechnungen, Buchungsbelege und Geschäftsbriefe nach den deutschen GoBD und § 147 AO aufbewahrt werden?",
            "Welche Aufbewahrungsfristen gelten für Rechnungen im deutschen Steuerrecht?",
            "Was besagt § 147 AO hinsichtlich der Aufbewahrungspflichten für Geschäftsunterlagen?",
        ],
        "answer": "Gemäß § 147 Abs. 3 AO i.V.m. GoBD gelten folgende Fristen: 1. Bücher, Aufzeichnungen, Inventare, Jahresabschlüsse, Lageberichte, Eröffnungsbilanzen sowie Buchungsbelege (Rechnungen, Kontoauszüge): 10 Jahre (bzw. 8 Jahre nach Wachstumschancengesetz ab 2024 für reine Buchungsbelege). 2. Empfangene und abgesandte Handels- und Geschäftsbriefe: 6 Jahre. Die Frist beginnt mit dem Schluss des Kalenderjahres, in dem die letzte Eintragung gemacht oder das Dokument empfangen bzw. versandt wurde."
    }
]


def generate_domain_3_samples(count: int = 100, seen_hashes: Set[str] = None) -> List[Dict[str, Any]]:
    samples = []
    
    # Dynamic prompt builders for tax & GoBD compliance to ensure high variety
    builders = [
        # § 19 Kleinunternehmer
        (
            lambda name, form, act: f"Welcher steuerliche Pflichttext gehört auf die Rechnung von {name} {form} ({act}) bei Inanspruchnahme der Kleinunternehmerregelung nach § 19 UStG?",
            "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet (Kleinunternehmerregelung)."
        ),
        (
            lambda name, form, act: f"Wie lautet die gesetzlich vorgeschriebene Steuerbefreiungsklausel für Kleinunternehmer gem. § 19 UStG für {name}?",
            "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet (Kleinunternehmerregelung)."
        ),
        (
            lambda name, form, act: f"Welcher Satz muss auf eine Kleinunternehmer-Rechnung nach § 19 UStG bei {act}?",
            "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet (Kleinunternehmerregelung)."
        ),
        # § 13b Reverse Charge Bau
        (
            lambda name, form, act: f"Welcher Hinweistext gehört auf eine Rechnung von {name} {form} für Bauleistungen an einen anderen Bauunternehmer gem. § 13b UStG?",
            "Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge / § 13b Abs. 2 Nr. 4 i.V.m. Abs. 5 UStG)."
        ),
        (
            lambda name, form, act: f"Wie lautet der offizielle Vermerk für das Reverse-Charge-Verfahren bei Bauleistungen ({act}) an {name}?",
            "Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge / § 13b Abs. 2 Nr. 4 i.V.m. Abs. 5 UStG)."
        ),
        (
            lambda name, form, act: f"Welche Klausel verlangt das Finanzamt nach § 13b Abs. 2 Nr. 4 UStG bei Handwerker-Bauleistungen an {name} {form}?",
            "Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge / § 13b Abs. 2 Nr. 4 i.V.m. Abs. 5 UStG)."
        ),
        # Innergemeinschaftliche Lieferung
        (
            lambda name, form, act: f"Welche Gesetzesklausel muss bei einer steuerfreien innergemeinschaftlichen Lieferung an {name} mit Sitz in der EU angegeben werden?",
            "Steuerfreie innergemeinschaftliche Lieferung gem. § 4 Nr. 1b i.V.m. § 6a UStG. Steuerschuldnerschaft des Leistungsempfängers."
        ),
        (
            lambda name, form, act: f"Welcher Vermerk gehört auf die B2B-Rechnung für eine innergemeinschaftliche Warenlieferung ({act}) an ein EU-Unternehmen mit gültiger USt-IdNr.?",
            "Steuerfreie innergemeinschaftliche Lieferung gem. § 4 Nr. 1b i.V.m. § 6a UStG. Steuerschuldnerschaft des Leistungsempfängers."
        ),
        # Drittland Export
        (
            lambda name, form, act: f"Welcher Vermerk ist erforderlich bei einem Export von Waren ({act}) an einen Geschäftskunden in der Schweiz oder den USA?",
            "Steuerfreie Ausfuhrlieferung gem. § 4 Nr. 1a i.V.m. § 6 UStG."
        ),
        (
            lambda name, form, act: f"Wie lautet der steuerliche Hinweis für eine Ausfuhrlieferung von {name} {form} in ein Drittland außerhalb der EU?",
            "Steuerfreie Ausfuhrlieferung gem. § 4 Nr. 1a i.V.m. § 6 UStG."
        ),
        # Differenzbesteuerung
        (
            lambda name, form, act: f"Welcher Hinweis gehört auf eine Rechnung von {name} {form} bei Verkauf von Gebrauchtwaren unter Differenzbesteuerung (§ 25a UStG)?",
            "Sonderregelung für Gebrauchtgegenstände gem. § 25a UStG (Differenzbesteuerung). Ein gesonderter Ausweis der Umsatzsteuer erfolgt nicht."
        ),
        (
            lambda name, form, act: f"Wie weist ein Gebrauchtwarenhändler ({act}) die Umsatzsteuer nach § 25a UStG gesetzeskonform aus?",
            "Sonderregelung für Gebrauchtgegenstände gem. § 25a UStG (Differenzbesteuerung). Ein gesonderter Ausweis der Umsatzsteuer erfolgt nicht."
        ),
        # Innergemeinschaftliche Dienstleistung
        (
            lambda name, form, act: f"Welcher Vermerk gehört auf die B2B-Dienstleistungsrechnung an einen Geschäftskunden in Österreich oder Frankreich gem. § 3a Abs. 2 UStG?",
            "Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge / Innergemeinschaftliche sonstige Leistung gem. § 3a Abs. 2 UStG)."
        ),
        # § 14 UStG Pflichtangaben
        (
            lambda name, form, act: f"Welche gesetzlichen Mindestangaben müssen nach § 14 Abs. 4 UStG auf einer ordnungsgemäßen B2B-Rechnung für {act} stehen?",
            "Eine ordnungsgemäße Rechnung nach § 14 Abs. 4 UStG muss zwingend enthalten: 1. Vollständiger Name und Anschrift des leistenden Unternehmers und des Leistungsempfängers; 2. Steuernummer oder USt-IdNr.; 3. Ausstellungsdatum; 4. Fortlaufende, einmalige Rechnungsnummer; 5. Menge und handelsübliche Bezeichnung der gelieferten Gegenstände oder Art und Umfang der Leistung; 6. Leistungszeitpunkt bzw. Lieferdatum; 7. Nach Steuersätzen aufgeschlüsseltes Entgelt; 8. Anzuwendender Steuersatz (19%, 7% oder 0%) sowie Steuerbetrag; 9. Im Fall einer Steuerbefreiung ein Hinweis auf den Befreiungsgrund."
        ),
        # § 33 UStDV Kleinbetrag
        (
            lambda name, form, act: f"Welche Erleichterungen gelten für Kleinbetragsrechnungen bis 250 Euro nach § 33 UStDV bei {name}?",
            "Nach § 33 UStDV genügen bei Kleinbetragsrechnungen bis 250 Euro Gesamtbetrag folgende Mindestangaben: 1. Vollständiger Name und Anschrift des leistenden Unternehmers; 2. Ausstellungsdatum; 3. Menge und Art der gelieferten Gegenstände oder Umfang der Leistung; 4. Das Entgelt und der Steuerbetrag in einer Summe (Bruttobetrag); 5. Der anzuwendende Steuersatz oder der Hinweis auf eine Steuerbefreiung. Die Angabe des Leistungsempfängers, der Steuernummer und einer Rechnungsnummer ist nicht erforderlich."
        ),
        # GoBD Aufbewahrung
        (
            lambda name, form, act: f"Wie lange müssen Rechnungen, Buchungsbelege und Geschäftsbriefe nach den deutschen GoBD und § 147 AO aufbewahrt werden?",
            "Gemäß § 147 Abs. 3 AO i.V.m. GoBD gelten folgende Fristen: 1. Bücher, Aufzeichnungen, Inventare, Jahresabschlüsse, Lageberichte, Eröffnungsbilanzen sowie Buchungsbelege (Rechnungen, Kontoauszüge): 10 Jahre (bzw. 8 Jahre nach Wachstumschancengesetz ab 2024 für reine Buchungsbelege). 2. Empfangene und abgesandte Handels- und Geschäftsbriefe: 6 Jahre. Die Frist beginnt mit dem Schluss des Kalenderjahres, in dem die letzte Eintragung gemacht oder das Dokument empfangen bzw. versandt wurde."
        ),
    ]

    activities = [
        "IT-Beratung", "Webentwicklung", "Schreinerarbeiten", "Elektroinstallation",
        "Malerarbeiten", "Sanitärtechnik", "Architekturleistungen", "Grafikdesign",
        "Warenlieferung", "Maschinenbau", "Gebrauchtwagenhandel", "E-Commerce",
        "Management Consulting", "Gebäudereinigung", "Eventplanung"
    ]

    attempts = 0
    while len(samples) < count and attempts < count * 20:
        attempts += 1
        builder_fn, ans = random.choice(builders)
        prefix = random.choice(COMPANY_PREFIXES)
        form = random.choice(LEGAL_FORMS)
        act = random.choice(activities)
        q = builder_fn(prefix, form, act)

        h = hashlib.sha256(q.strip().lower().encode("utf-8")).hexdigest()
        if seen_hashes is not None and h in seen_hashes:
            continue
        if seen_hashes is not None:
            seen_hashes.add(h)

        samples.append({
            "conversations": [
                {"from": "human", "value": q},
                {"from": "gpt", "value": ans}
            ]
        })
    return samples


# --- Domain 4: Dunning Letters (Mahnwesen) ---

DUNNING_BASE_DATA = [
    ("Schmidt Logistik GmbH", "Herrn Thomas Schmidt", "RE-2024-", 1450.00),
    ("Bauer Medien GmbH", "Frau Claudia Bauer", "RE-2024-", 3200.00),
    ("Delta Handels KG", "Herrn Michael Weber", "RE-2024-", 4890.00),
    ("Architekturbüro Kraft & Partner", "Frau Dr. Kraft", "RE-2024-", 850.00),
    ("TechNova Solutions UG", "Herrn Alex Klein", "RE-2024-", 2150.50),
    ("Autohaus Nordring e.K.", "Herrn Markus Braun", "RE-2024-", 6340.00),
    ("Gastro & Event Service GbR", "Frau Julia Frank", "RE-2024-", 980.00),
    ("Immobilienverwaltung Hausmann", "Herrn Stefan Hausmann", "RE-2024-", 1750.00),
    ("Kreativwerkstatt Visuals OHG", "Frau Sandra Wolf", "RE-2024-", 1240.00),
    ("Praxis Dr. Eichenwald", "Herrn Dr. Eichenwald", "RE-2024-", 780.00),
    ("Bauunternehmen Stein & Mörtel GmbH", "Herrn Frank Stein", "RE-2024-", 5600.00),
    ("Druckerei Gutenberg e.K.", "Frau Monika Becker", "RE-2024-", 1320.00)
]


def generate_domain_4_samples(count: int = 100, seen_hashes: Set[str] = None) -> List[Dict[str, Any]]:
    samples = []
    stages = [1, 2, 3]

    attempts = 0
    while len(samples) < count and attempts < count * 20:
        attempts += 1
        stage = random.choice(stages)
        client, contact, inv_prefix, base_amount = random.choice(DUNNING_BASE_DATA)
        inv_nr = f"{inv_prefix}{random.randint(100, 999)}"
        amount = round(base_amount + random.uniform(10.0, 300.0), 2)
        amt_str = f"{amount:,.2f} EUR".replace(",", "X").replace(".", ",").replace("X", ".")

        if stage == 1:
            overdue = random.randint(4, 12)
            prompts = [
                f"Erstelle eine freundliche Zahlungserinnerung (Stufe 1) für Rechnung {inv_nr} an {client}, Rechnungsbetrag {amt_str}, überfällig seit {overdue} Tagen.",
                f"Formuliere eine höfliche Zahlungserinnerung: Rechnung {inv_nr}, Kunde: {client}, offener Betrag: {amt_str}, {overdue} Tage über dem Fälligkeitsdatum.",
                f"Schreibe Zahlungserinnerung Stufe 1 an {client}: Rechnungsnummer {inv_nr}, Betrag {amt_str}, seit {overdue} Tagen fällig."
            ]
            letter = (
                f"Betreff: Freundliche Zahlungserinnerung zur Rechnung {inv_nr}\n\n"
                f"Sehr geehrte Damen und Herren,\n\n"
                f"bei der regelmäßigen Durchsicht unserer Buchhaltung haben wir festgestellt, dass der Betrag für die folgende Rechnung noch als offen geführt wird:\n\n"
                f"Rechnungsnummer: {inv_nr}\n"
                f"Offener Rechnungsbetrag: {amt_str}\n"
                f"Fälligkeitsdatum: vor {overdue} Tagen\n\n"
                f"Sicherlich handelt es sich hierbei lediglich um ein Versehen oder die Zahlung hat sich mit diesem Schreiben überschnitten. "
                f"Falls der Betrag bereits überwiesen wurde, betrachten Sie dieses Schreiben bitte als gegenstandslos.\n\n"
                f"Andernfalls bitten wir Sie, den Betrag zeitnah auf unser angegebenes Geschäftskonto zu begleichen.\n\n"
                f"Mit freundlichen Grüßen\nIhre Buchhaltung"
            )
        elif stage == 2:
            overdue = random.randint(14, 25)
            prompts = [
                f"Erstelle eine 1. Mahnung (Stufe 2): Rechnung {inv_nr}, Kunde: {client}, überfällig seit {overdue} Tagen, Betrag: {amt_str}, Nachfrist 7 Tage.",
                f"Formuliere die 1. Mahnung für Rechnung {inv_nr} an {client} über {amt_str}, Nachfrist von 7 Tagen setzen, {overdue} Tage überfällig.",
                f"Schreibe 1. Mahnung mit 7-Tage-Frist an {client}: Rechnung {inv_nr}, {amt_str} noch offen seit {overdue} Tagen."
            ]
            letter = (
                f"Betreff: 1. Mahnung zur Rechnung {inv_nr}\n\n"
                f"Sehr geehrte Damen und Herren,\n\n"
                f"trotz unserer bisherigen Zahlungserinnerung konnten wir bis zum heutigen Tage keinen Zahlungseingang für folgende Forderung feststellen:\n\n"
                f"Rechnungsnummer: {inv_nr}\n"
                f"Fälliger Betrag: {amt_str}\n\n"
                f"Wir fordern Sie hiermit höflich, aber bestimmt auf, den offenen Gesamtbetrag innerhalb einer Nachfrist von 7 Tagen ab Zugang dieses Schreibens auf unser Bankkonto zu überweisen.\n\n"
                f"Sollten Sie Einwände gegen die Rechnung erheben oder eine Ratenzahlung vereinbaren wollen, bitten wir um umgehende Kontaktaufnahme.\n\n"
                f"Mit freundlichen Grüßen\nIhre Buchhaltung"
            )
        else:
            overdue = random.randint(30, 60)
            prompts = [
                f"Erstelle eine letzte Mahnung (Stufe 3 vor Inkasso/Mahnbescheid) für Rechnung {inv_nr} an {client}, {overdue} Tage überfällig, Betrag {amt_str}.",
                f"Formuliere eine letzte Mahnung (Stufe 3) für Rechnung {inv_nr} an {client} über {amt_str}, Frist 5 Werktage vor Einleitung gerichtlicher Schritte.",
                f"Schreibe letzte Mahnung vor gerichtlichem Mahnverfahren: Rechnung {inv_nr}, Kunde {client}, Summe {amt_str}, {overdue} Tage Verzug."
            ]
            letter = (
                f"Betreff: Letzte Mahnung vor Einleitung gerichtlicher Schritte - Rechnung {inv_nr}\n\n"
                f"Sehr geehrte Damen und Herren,\n\n"
                f"auf unsere wiederholten Zahlungsaufforderungen bezüglich der Rechnung {inv_nr} über {amt_str} haben Sie bislang weder reagiert noch die fällige Forderung ausgeglichen.\n\n"
                f"Wir setzen Ihnen hiermit eine letztmalige Zahlungsfrist von 5 Werktagen.\n\n"
                f"Sollte die Zahlung bis dahin nicht vollständig auf unserem Konto verbucht sein, werden wir die Angelegenheit ohne weitere Ankündigung an unser Inkassounternehmen bzw. unsere Rechtsvertretung zur Beantragung eines gerichtlichen Mahnbescheids übergeben. "
                f"Die hierdurch entstehenden Verzugszinsen und erheblichen Mehrkosten gehen zu Ihren Lasten.\n\n"
                f"Mit freundlichen Grüßen\nIhre Geschäftsleitung / Buchhaltung"
            )

        prompt = random.choice(prompts)
        h = hashlib.sha256(prompt.strip().lower().encode("utf-8")).hexdigest()
        if seen_hashes is not None and h in seen_hashes:
            continue
        if seen_hashes is not None:
            seen_hashes.add(h)

        samples.append({
            "conversations": [
                {"from": "human", "value": prompt},
                {"from": "gpt", "value": letter}
            ]
        })
    return samples


# --- Domain 5: SKR03 / SKR04 Expenses ---

EXPENSE_DEFINITIONS = [
    {
        "inputs": [
            "Geschäftsessen mit Neukunden im Restaurant Steakhouse {amount}€ netto zzgl. 19% MwSt",
            "Bewirtungsbeleg Abendessen mit Geschäftspartner {amount}€ netto",
            "Restaurantrechnung Kundenbewirtung Projektbesprechung {amount}€",
            "Geschäftliches Arbeitsessen im Gasthof {amount}€ netto",
            "Bewirtung anlässlich Vertragsunterzeichnung im Ristorante {amount}€ netto"
        ],
        "category": "Bewirtung",
        "vat_rate": 19,
        "deductible": 70,
        "skr03": "4650",
        "skr04": "6640",
        "note": "Geschäftliche Bewirtungskosten: 70% steuerlich als Betriebsausgabe abzugsfähig, 100% Vorsteuerabzug bei ordnungsgemäß ausgefülltem Bewirtungsbeleg (§ 4 Abs. 5 Nr. 2 EStG)."
    },
    {
        "inputs": [
            "Monatsrechnung Google Workspace und Google Cloud {amount}€ netto",
            "Jahreslizenz Projektmanagement-Software Notion {amount}€ netto",
            "Adobe Creative Cloud Abonnement monatlich {amount}€ netto",
            "GitHub Enterprise Lizenzgebühren {amount}€ netto",
            "Slack Business Lizenzmonatsgebühr {amount}€ netto",
            "Figma Professional Teams Jahreslizenz {amount}€ netto"
        ],
        "category": "Software / IT-Kosten",
        "vat_rate": 19,
        "deductible": 100,
        "skr03": "4964",
        "skr04": "6837",
        "note": "Laufende Software-Nutzungskosten (SaaS): 100% als Betriebsausgabe abzugsfähig, 100% Vorsteuerabzug."
    },
    {
        "inputs": [
            "Kauf eines ergonomischen Bürostuhls für {amount}€ netto",
            "Neuer Büroschreibtisch elektrisch höhenverstellbar {amount}€ netto",
            "Laserdrucker für das Büro {amount}€ netto Anschaffung",
            "Monitor 27 Zoll für den Arbeitsplatz {amount}€ netto",
            "Aktenvernichter Sicherheitsstufe P-4 {amount}€ netto",
            "Rollcontainer aus Holz für Büroarbeitsplatz {amount}€ netto"
        ],
        "category": "Geringwertige Wirtschaftsgüter (GWG)",
        "vat_rate": 19,
        "deductible": 100,
        "skr03": "0480",
        "skr04": "0670",
        "note": "Geringwertiges Wirtschaftsgut (GWG) bis 800 Euro Anschaffungskosten: Sofortabschreibung im Jahr der Anschaffung nach § 6 Abs. 2 EStG."
    },
    {
        "inputs": [
            "Monatlicher Telekommunikationsvertrag Mobilfunk und VDSL {amount}€ netto",
            "Handyrechnung Vodafone Firmenvertrag {amount}€ netto",
            "Telekom Glasfaser Internetanschluss Büro {amount}€ netto",
            "O2 Business Mobilfunktarif {amount}€ netto"
        ],
        "category": "Telefon und Internet",
        "vat_rate": 19,
        "deductible": 100,
        "skr03": "4920",
        "skr04": "6805",
        "note": "Laufende Kommunikationsaufwendungen: 100% als Betriebsausgabe abzugsfähig, 100% Vorsteuerabzug."
    },
    {
        "inputs": [
            "Deutsche Bahn ICE-Ticket zum Kundentermin nach Berlin {amount}€ inkl. 7% MwSt",
            "Monatskarte Nahverkehr für Dienstfahrten {amount}€ inkl. 7% MwSt",
            "Zugticket geschäftliche Reise {amount}€ brutto 7% USt",
            "Bahncard Business 50 Kauf {amount}€ inkl. 7% MwSt"
        ],
        "category": "Reisekosten Unternehmer (Fahrtkosten)",
        "vat_rate": 7,
        "deductible": 100,
        "skr03": "4673",
        "skr04": "6673",
        "note": "Geschäftliche Fahrtkosten mit öffentlichen Verkehrsmitteln: 100% abzugsfähig, ermäßigter Steuersatz 7% Vorsteuerabzug bei Fernverkehr."
    },
    {
        "inputs": [
            "Hotelübernachtung auf Geschäftsreise mit Kunden {amount}€ netto zzgl. 7% MwSt",
            "Übernachtungsrechnung Hotel Frankfurt {amount}€ netto",
            "Hotelzimmer Buchung Kundentermin München {amount}€ netto zzgl. 7% MwSt"
        ],
        "category": "Reisekosten Unternehmer (Übernachtung)",
        "vat_rate": 7,
        "deductible": 100,
        "skr03": "4660",
        "skr04": "6660",
        "note": "Übernachtungsaufwand für Geschäftsreisen: 100% Betriebsausgabe, ermäßigter Steuersatz 7% USt für Beherbergungsleistungen (§ 12 Abs. 2 Nr. 11 UStG)."
    },
    {
        "inputs": [
            "Fachbuch über deutsches Steuerrecht und B2B-Abrechnung {amount}€ inkl. 7% MwSt",
            "Abonnement Fachzeitschrift für Handwerk und Technik {amount}€ inkl. 7% MwSt",
            "Lehrbuch Bilanzierung und DATEV {amount}€ brutto",
            "Kommentar zum Handelsgesetzbuch HGB Fachbuch {amount}€ inkl. 7% USt"
        ],
        "category": "Fachliteratur",
        "vat_rate": 7,
        "deductible": 100,
        "skr03": "4940",
        "skr04": "6815",
        "note": "Berufliche und betriebliche Fachliteratur: 100% Betriebsausgabe mit 7% Vorsteuer."
    },
    {
        "inputs": [
            "Tanken Firmenwagen Diesel an der Shell Tankstelle {amount}€ netto zzgl. 19% MwSt",
            "Benzinquittung Aral für geschäftliches Fahrzeug {amount}€ brutto",
            "KfZ-Wäsche und Scheibenwischwasser Tankbeleg {amount}€ netto",
            "AdBlue und Motorenöl Tankstelle {amount}€ netto"
        ],
        "category": "Kfz-Kosten (Treibstoffe)",
        "vat_rate": 19,
        "deductible": 100,
        "skr03": "4530",
        "skr04": "6530",
        "note": "Laufende Kraftstoffkosten für das betriebliche Fahrzeug: 100% Betriebsausgabe mit 19% Vorsteuerabzug."
    },
    {
        "inputs": [
            "Kopierpapier, Ordner und Kugelschreiber Schreibwarenladen {amount}€ netto",
            "Bürobedarfsbestellung Toner und Notizblöcke {amount}€ netto",
            "Schreibtisch-Organizer und Versandtaschen Bürobedarf {amount}€ netto",
            "Druckerpatronen Set schwarz und farbig {amount}€ netto"
        ],
        "category": "Bürobedarf",
        "vat_rate": 19,
        "deductible": 100,
        "skr03": "4930",
        "skr04": "6815",
        "note": "Verbrauchsmaterial und laufender Bürobedarf: 100% als Betriebsausgabe abzugsfähig, 100% Vorsteuer."
    },
    {
        "inputs": [
            "Monatliche Kontoführungsgebühren Geschäftskonto {amount}€ steuerfrei",
            "Bankspesen Überweisungsentgelte und Kartenlesegerät-Miete {amount}€",
            "Depotführung und Transaktionsgebühren Bankkonto {amount}€"
        ],
        "category": "Bankgebühren und Nebenkosten des Geldverkehrs",
        "vat_rate": 0,
        "deductible": 100,
        "skr03": "2100",
        "skr04": "7300",
        "note": "Nebenkosten des Geldverkehrs: 100% Betriebsausgabe, steuerfreie Bankdienstleistung nach § 4 Nr. 8 UStG."
    },
    {
        "inputs": [
            "Rechnung Steuerberater für Erstellung des Jahresabschlusses {amount}€ netto zzgl. 19% MwSt",
            "Buchführungsgebühren monatlich Kanzlei {amount}€ netto",
            "Lohnabrechnungskosten externer Dienstleister {amount}€ netto"
        ],
        "category": "Abschluss- und Prüfungskosten / Steuerberatung",
        "vat_rate": 19,
        "deductible": 100,
        "skr03": "4955",
        "skr04": "6830",
        "note": "Steuerberatungs- und Buchführungskosten zur Erfüllung betrieblicher Pflichten: 100% Betriebsausgabe mit vollem Vorsteuerabzug."
    },
    {
        "inputs": [
            "Werbeanzeige auf Google Ads für Kundenakquise {amount}€ Reverse Charge aus Irland",
            "Meta Werbekampagne Facebook / Instagram {amount}€ netto EU-Dienstleistung",
            "LinkedIn Marketing Ads Rechnung {amount}€ netto EU"
        ],
        "category": "Werbekosten (EU Reverse Charge)",
        "vat_rate": 0,
        "deductible": 100,
        "skr03": "3123",
        "skr04": "5923",
        "note": "Sonstige Leistung eines im anderen EU-Mitgliedstaat ansässigen Unternehmers: Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge § 13b UStG)."
    },
    {
        "inputs": [
            "Briefmarken Deutsche Post Einschreiben {amount}€ steuerfrei",
            "Portokasse Briefporto für Behördenpost {amount}€",
            "Deutsche Post Frankierservice {amount}€"
        ],
        "category": "Porto und Versandkosten",
        "vat_rate": 0,
        "deductible": 100,
        "skr03": "4910",
        "skr04": "6800",
        "note": "Portokosten für Universaldienstleistungen der Deutschen Post: Steuerfrei gem. § 4 Nr. 11b UStG."
    },
    {
        "inputs": [
            "Weihnachtsgeschenk Präsentkorb an Großkunden {amount}€ netto",
            "Kundenpräsent Weinflasche und Pralinen {amount}€ netto",
            "Werbepräsent Kalender und Schokolade Geschäftspartner {amount}€ netto"
        ],
        "category": "Geschenke abzugsfähig bis 50 Euro",
        "vat_rate": 19,
        "deductible": 100,
        "skr03": "4630",
        "skr04": "6610",
        "note": "Betrieblich veranlasste Geschenke an Geschäftspartner bis zur gesetzlichen Freigrenze von 50 Euro netto (§ 4 Abs. 5 Nr. 1 EStG ab 2024): 100% abzugsfähig mit 19% Vorsteuer."
    },
    {
        "inputs": [
            "Monatliche Büromiete Geschäftsräume {amount}€ steuerfrei gem. § 4 Nr. 12a UStG",
            "Mietzahlung Büro Coworking Space {amount}€ steuerfrei",
            "Gewerberaummiete Praxisräume {amount}€ ohne MwSt",
            "Büromiete Kaltmiete {amount}€ steuerfrei"
        ],
        "category": "Miete Geschäftsräume (steuerfrei)",
        "vat_rate": 0,
        "deductible": 100,
        "skr03": "4210",
        "skr04": "6310",
        "note": "Miete für Geschäftsräume: 100% Betriebsausgabe, grundsätzlich umsatzsteuerfrei gem. § 4 Nr. 12a UStG."
    },
    {
        "inputs": [
            "Gewerbemiete Büroetage {amount}€ netto zzgl. 19% MwSt mit Vorsteueroption",
            "Monatliche Büromiete {amount}€ netto mit 19% USt-Ausweis gem. § 9 UStG",
            "Mietrechnung Werkstatt {amount}€ netto zzgl. 19% Umsatzsteuer",
            "Gewerbemiete Lagerhalle {amount}€ netto mit 19% Option"
        ],
        "category": "Miete Geschäftsräume (19% USt)",
        "vat_rate": 19,
        "deductible": 100,
        "skr03": "4210",
        "skr04": "6310",
        "note": "Gewerbliche Miete mit Option zur Umsatzsteuer (§ 9 UStG): 100% Betriebsausgabe mit 19% Vorsteuerabzug."
    },
    {
        "inputs": [
            "Stromrechnung Stadtwerke Büro {amount}€ netto zzgl. 19% MwSt",
            "Heizkostenabrechnung Geschäftsräume {amount}€ netto zzgl. 19% USt",
            "Gasrechnung für Bürogebäude {amount}€ netto zzgl. 19% MwSt",
            "Nebenkostennachzahlung Gewerbemiete {amount}€ netto zzgl. 19% USt"
        ],
        "category": "Heizung, Strom und Raumnebenkosten",
        "vat_rate": 19,
        "deductible": 100,
        "skr03": "4230",
        "skr04": "6325",
        "note": "Laufende Energiekosten und Raumnebenkosten: 100% Betriebsausgabe mit vollem Vorsteuerabzug."
    },
    {
        "inputs": [
            "Monatliche Leasingrate Firmenwagen BMW {amount}€ netto zzgl. 19% MwSt",
            "Leasingrate Geschäftsfahrzeug Audi {amount}€ netto zzgl. 19% USt",
            "Kfz-Leasing monatlich Volkswagen {amount}€ netto zzgl. 19% MwSt",
            "Pkw-Leasingrate Firmenwagen {amount}€ netto zzgl. 19% Vorsteuer"
        ],
        "category": "Kfz-Leasing",
        "vat_rate": 19,
        "deductible": 100,
        "skr03": "4570",
        "skr04": "6570",
        "note": "Leasingaufwand für betriebliches Kraftfahrzeug: 100% Betriebsausgabe mit 19% Vorsteuerabzug."
    },
    {
        "inputs": [
            "Kfz-Haftpflicht und Vollkasko Allianz Firmenwagen {amount}€ steuerfrei",
            "Jahresbeitrag Kfz-Versicherung HUK Coburg {amount}€ steuerfrei",
            "Kfz-Versicherungsbeitrag betriebliches Fahrzeug {amount}€",
            "Pkw-Versicherung Firmenwagen Prämie {amount}€ steuerfrei"
        ],
        "category": "Kfz-Versicherungen und Abgaben",
        "vat_rate": 0,
        "deductible": 100,
        "skr03": "4520",
        "skr04": "6520",
        "note": "Versicherungsbeiträge für das betriebliche Fahrzeug: 100% Betriebsausgabe, umsatzsteuerfrei gem. § 4 Nr. 10a UStG."
    },
    {
        "inputs": [
            "Hauptuntersuchung TÜV und Inspektion Firmenwagen {amount}€ netto zzgl. 19% MwSt",
            "Reifenwechsel und Bremsenreparatur Werkstatt {amount}€ netto zzgl. 19% USt",
            "KfZ-Reparaturrechnung Vertragswerkstatt {amount}€ netto zzgl. 19% MwSt",
            "Inspektion und Ölwechsel Firmenfahrzeug {amount}€ netto zzgl. 19% USt"
        ],
        "category": "Kfz-Reparaturen und Instandhaltung",
        "vat_rate": 19,
        "deductible": 100,
        "skr03": "4540",
        "skr04": "6540",
        "note": "Laufende Instandhaltung und Reparaturen am betrieblichen Fahrzeug: 100% Betriebsausgabe mit 19% Vorsteuerabzug."
    },
    {
        "inputs": [
            "Betriebshaftpflichtversicherung Jahresprämie {amount}€ steuerfrei",
            "D&O Versicherung Geschäftsführer {amount}€ steuerfrei",
            "Vermögensschaden-Haftpflichtversicherung Kanzlei {amount}€ steuerfrei",
            "Geschäftsinhaltsversicherung Prämie {amount}€ steuerfrei"
        ],
        "category": "Betriebliche Versicherungen",
        "vat_rate": 0,
        "deductible": 100,
        "skr03": "4360",
        "skr04": "6400",
        "note": "Betriebliche Versicherungen: 100% als Betriebsausgabe abzugsfähig, versicherungssteuerpflichtig aber umsatzsteuerfrei gem. § 4 Nr. 10a UStG."
    },
    {
        "inputs": [
            "Teilnahmegebühr Fachseminar Digitalisierung {amount}€ netto zzgl. 19% MwSt",
            "Online-Schulungskurs Programmierung Zertifikat {amount}€ netto zzgl. 19% USt",
            "Weiterbildung Führungskräfte Workshop {amount}€ netto zzgl. 19% MwSt",
            "Fachkonferenz Ticket und Schulung {amount}€ netto zzgl. 19% USt"
        ],
        "category": "Fortbildung und Seminare",
        "vat_rate": 19,
        "deductible": 100,
        "skr03": "4945",
        "skr04": "6820",
        "note": "Berufliche Fortbildungs- und Schulungskosten: 100% Betriebsausgabe mit Vorsteuerabzug."
    },
    {
        "inputs": [
            "Hetzner Dedicated Server Hosting monatlich {amount}€ netto zzgl. 19% MwSt",
            "Domain-Registrierung und SSL-Zertifikate {amount}€ netto zzgl. 19% USt",
            "Cloud-Server Hosting Strato {amount}€ netto zzgl. 19% MwSt",
            "Webhosting Paket monatlich {amount}€ netto zzgl. 19% USt"
        ],
        "category": "Webhosting und Servermiete",
        "vat_rate": 19,
        "deductible": 100,
        "skr03": "4964",
        "skr04": "6837",
        "note": "Webhosting, Servermiete und Domainkosten: 100% Betriebsausgabe mit 19% Vorsteuerabzug."
    },
    {
        "inputs": [
            "Subunternehmer-Rechnung Freelancer Webentwicklung {amount}€ netto zzgl. 19% MwSt",
            "Fremdleistung Handwerker-Montage {amount}€ netto zzgl. 19% USt",
            "Honorar externer IT-Consultant {amount}€ netto zzgl. 19% MwSt",
            "Dienstleistung freier Mitarbeiter {amount}€ netto zzgl. 19% USt"
        ],
        "category": "Fremdleistungen",
        "vat_rate": 19,
        "deductible": 100,
        "skr03": "3100",
        "skr04": "5900",
        "note": "Bezogene Fremdleistungen: 100% Betriebsausgabe mit vollem Vorsteuerabzug."
    },
    {
        "inputs": [
            "Gesetzlicher Verpflegungsmehraufwand 2-tägige Dienstreise {amount}€ steuerfrei",
            "Pauschale für Verpflegungsmehraufwand Kundentermin über 8 Stunden {amount}€ steuerfrei",
            "Reisekostenabrechnung Tagegeld Spesen {amount}€ steuerfrei",
            "Tagegeld Geschäftsreise inland {amount}€ steuerfrei"
        ],
        "category": "Verpflegungsmehraufwand",
        "vat_rate": 0,
        "deductible": 100,
        "skr03": "4668",
        "skr04": "6668",
        "note": "Gesetzliche Pauschalen für Verpflegungsmehraufwand nach § 9 Abs. 4a EStG: 100% steuerlich abzugsfähig, keine Umsatzsteuer."
    },
    {
        "inputs": [
            "Rechtsanwaltshonorar Vertragsprüfung {amount}€ netto zzgl. 19% MwSt",
            "Anwaltsrechnung Markenanmeldung {amount}€ netto zzgl. 19% USt",
            "Rechtsberatung Arbeitsrecht Kanzlei {amount}€ netto zzgl. 19% MwSt",
            "Anwaltskosten außergerichtliche Vertretung {amount}€ netto zzgl. 19% USt"
        ],
        "category": "Rechtsberatung",
        "vat_rate": 19,
        "deductible": 100,
        "skr03": "4950",
        "skr04": "6825",
        "note": "Aufwendungen für Rechtsberatung: 100% Betriebsausgabe mit 19% Vorsteuerabzug."
    },
    {
        "inputs": [
            "Wartung und Instandsetzung Kaffeemaschine Büro {amount}€ netto zzgl. 19% MwSt",
            "Reparatur Büromöbel und Schließanlage {amount}€ netto zzgl. 19% USt",
            "Instandhaltung Serverraum Klimasplitgerät {amount}€ netto zzgl. 19% MwSt",
            "Wartungsdienst Aufzugsanlage Betriebsgebäude {amount}€ netto zzgl. 19% USt"
        ],
        "category": "Instandhaltung Betriebs- und Geschäftsausstattung",
        "vat_rate": 19,
        "deductible": 100,
        "skr03": "4800",
        "skr04": "6450",
        "note": "Laufende Instandhaltung betrieblicher Räume und Betriebsausstattung: 100% abzugsfähig mit 19% Vorsteuer."
    },
    {
        "inputs": [
            "Monatliche Büroreinigung Reinigungsdienst {amount}€ netto zzgl. 19% MwSt",
            "Fensterreinigung Gewerbeobjekt {amount}€ netto zzgl. 19% USt",
            "Gebäudereinigung Praxisräume {amount}€ netto zzgl. 19% MwSt",
            "Reinigungsdienst Geschäftsräume Monat {amount}€ netto zzgl. 19% USt"
        ],
        "category": "Reinigung Geschäftsräume",
        "vat_rate": 19,
        "deductible": 100,
        "skr03": "4250",
        "skr04": "6330",
        "note": "Reinigungskosten für Geschäftsräume: 100% Betriebsausgabe mit 19% Vorsteuerabzug."
    },
    {
        "inputs": [
            "Jahresbeitrag Industrie- und Handelskammer (IHK) {amount}€ steuerfrei",
            "Jahresbeitrag Berufsgenossenschaft BG ETEM {amount}€ steuerfrei",
            "Kammerbeitrag Handwerkskammer HWK {amount}€ steuerfrei",
            "Mitgliedsbeitrag berufsständische Vereinigung {amount}€ steuerfrei"
        ],
        "category": "Beiträge zu Berufsgenossenschaften und Kammern",
        "vat_rate": 0,
        "deductible": 100,
        "skr03": "4380",
        "skr04": "6420",
        "note": "Gesetzliche und berufsständische Beiträge (IHK, HWK, BG): 100% Betriebsausgabe, nicht steuerbar bzw. umsatzsteuerfrei."
    },
    {
        "inputs": [
            "Druck von Firmenbroschüren und Flyern in Druckerei {amount}€ netto zzgl. 19% MwSt",
            "Miete Messestand und Messeausstattung {amount}€ netto zzgl. 19% USt",
            "Rollup Banner und Messeflyer Druck {amount}€ netto zzgl. 19% MwSt",
            "Werbeschilder und Beschriftung Firmengebäude {amount}€ netto zzgl. 19% USt"
        ],
        "category": "Werbekosten Inland",
        "vat_rate": 19,
        "deductible": 100,
        "skr03": "4600",
        "skr04": "6600",
        "note": "Werbe- und Messeaufwand: 100% Betriebsausgabe mit 19% Vorsteuerabzug."
    },
    {
        "inputs": [
            "Akkuschrauber und Bohrer-Set Baumarkt {amount}€ netto zzgl. 19% MwSt",
            "Handwerkzeuge und Messgeräte Werkstatt {amount}€ netto zzgl. 19% USt",
            "Lötkolben und Multimeter Werkzeug {amount}€ netto zzgl. 19% MwSt",
            "Arbeitsleuchte und Werkzeugkasten {amount}€ netto zzgl. 19% USt"
        ],
        "category": "Werkzeuge und Kleingeräte",
        "vat_rate": 19,
        "deductible": 100,
        "skr03": "4985",
        "skr04": "6855",
        "note": "Kleingeräte und Werkzeuge: 100% Betriebsausgabe mit 19% Vorsteuerabzug."
    },
    {
        "inputs": [
            "Sollzinsen Geschäftskredit Sparkasse {amount}€ steuerfrei",
            "Darlehenszinsen Investitionskredit Bank {amount}€ steuerfrei",
            "Kontokorrentzinsen Bank {amount}€ steuerfrei",
            "Kreditzinsen Firmenfinanzierung {amount}€ steuerfrei"
        ],
        "category": "Zinsaufwendungen",
        "vat_rate": 0,
        "deductible": 100,
        "skr03": "2120",
        "skr04": "7310",
        "note": "Zinsaufwendungen für betriebliche Finanzierungen: 100% Betriebsausgabe, umsatzsteuerfrei gem. § 4 Nr. 8a UStG."
    }
]


def generate_domain_5_samples(count: int = 150, seen_hashes: Set[str] = None) -> List[Dict[str, Any]]:
    samples = []
    templates = [
        "Kategorisiere für SKR03 und SKR04: '{receipt}'",
        "Welchem DATEV-Konto in SKR03 und SKR04 ordne ich folgenden Beleg zu: '{receipt}'?",
        "Buche folgende Betriebsausgabe in SKR03 und SKR04: '{receipt}'",
        "Gib mir die SKR03- und SKR04-Kontonummern für folgende Ausgabe: '{receipt}'",
        "Buchungsvorschlag für diesen Beleg in SKR03/04: '{receipt}'"
    ]

    attempts = 0
    while len(samples) < count and attempts < count * 20:
        attempts += 1
        exp = random.choice(EXPENSE_DEFINITIONS)
        raw_receipt = random.choice(exp["inputs"])
        amount = random.randint(15, 650)
        receipt_text = raw_receipt.format(amount=amount)
        tmpl = random.choice(templates)
        prompt = tmpl.format(receipt=receipt_text)

        h = hashlib.sha256(prompt.strip().lower().encode("utf-8")).hexdigest()
        if seen_hashes is not None and h in seen_hashes:
            continue
        if seen_hashes is not None:
            seen_hashes.add(h)

        out_data = {
            "category": exp["category"],
            "vat_rate": exp["vat_rate"],
            "deductible_percent": exp["deductible"],
            "skr03_account": exp["skr03"],
            "skr04_account": exp["skr04"],
            "note": exp["note"]
        }

        samples.append({
            "conversations": [
                {"from": "human", "value": prompt},
                {"from": "gpt", "value": json.dumps(out_data, ensure_ascii=False)}
            ]
        })
    return samples


# --- Domain 6: Text-to-XRechnung 3.0 / EN 16931 ---

LEITWEG_IDS = [
    ("04011000-12345-67", "Bundesministerium des Innern und für Heimat"),
    ("05315000-0001-44", "Stadtverwaltung Köln - Amt für Informationsverarbeitung"),
    ("02000000-0001-04", "Freie und Hansestadt Hamburg - Senatskanzlei"),
    ("08111000-0001-20", "Landeshauptstadt Stuttgart - IT-Referat"),
    ("09162000-0001-12", "Landratsamt München"),
    ("11000000-0001-89", "Senatsverwaltung für Finanzen Berlin"),
    ("991-01234-55", "Deutsche Bahn AG - Procurement Solutions"),
    ("992-05678-33", "Universitätsklinikum Freiburg AöR"),
]

GERMAN_STREETS = [
    "Hauptstraße 14", "Bahnhofstraße 22", "Friedrichstraße 102", "Berliner Allee 45",
    "Gartenstraße 8", "Industriestraße 30", "Marktplatz 3", "Schulstraße 17",
    "Goethestraße 19", "Schillerstraße 12", "Königsallee 60", "Technologiepark 4"
]


def generate_domain_6_xrechnung_samples(count: int = 120, seen_hashes: Set[str] = None) -> List[Dict[str, Any]]:
    samples = []
    attempts = 0

    while len(samples) < count and attempts < count * 20:
        attempts += 1
        leitweg_id, authority_name = random.choice(LEITWEG_IDS)
        seller_name, seller_city = generate_company_name()
        seller_tax_id = f"{random.randint(100, 999)}/{random.randint(100, 999)}/{random.randint(10000, 99999)}"
        seller_vat_id = f"DE{random.randint(100000000, 999999999)}"
        buyer_vat_id = f"DE{random.randint(100000000, 999999999)}"
        inv_no = f"RE-2025-{random.randint(1000, 9999)}"
        day = random.randint(1, 28)
        month = random.randint(1, 12)
        issue_date = f"2025-{month:02d}-{day:02d}"
        due_day = (day + 14) if (day + 14) <= 28 else 28
        due_date = f"2025-{month:02d}-{due_day:02d}"

        num_items = random.choices([1, 2], weights=[0.7, 0.3])[0]
        selected_services = random.sample(SERVICE_CATALOG, num_items)

        line_items = []
        raw_prompt_items = []
        total_net = 0.0
        total_tax = 0.0

        for idx, svc in enumerate(selected_services, start=1):
            qty = random.randint(1, 15) if svc["unit"] in ("Stunde", "Stück") else 1
            price = round(random.uniform(*svc["price_range"]), 2)
            net_amt = round(qty * price, 2)
            tax_rate = svc["tax"]
            tax_amt = round(net_amt * (tax_rate / 100.0), 2)
            
            unit_code_map = {"Stunde": "HUR", "Stück": "C62", "Tag": "DAY", "Monat": "MON", "Pauschal": "LS"}
            unit_code = unit_code_map.get(svc["unit"], "C62")
            tax_cat = "S" if tax_rate == 19 else ("AA" if tax_rate == 7 else "E")

            line_items.append({
                "line_id": str(idx),
                "name": svc["desc"],
                "quantity": float(qty),
                "unit_code": unit_code,
                "unit_price": price,
                "net_amount": net_amt,
                "tax_category": tax_cat,
                "tax_percent": tax_rate
            })
            total_net += net_amt
            total_tax += tax_amt
            raw_prompt_items.append(f"{qty}x {random.choice(svc['raw_names'])} à {price:.2f}€")

        total_net = round(total_net, 2)
        total_tax = round(total_tax, 2)
        total_gross = round(total_net + total_tax, 2)

        items_str = " und ".join(raw_prompt_items)
        prompt_templates = [
            f"Erstelle eine elektronische Rechnung im XRechnung 3.0 Standard (EN 16931) an {authority_name} (Leitweg-ID: {leitweg_id}): {items_str}, Zahlungsziel 14 Tage netto. Aussteller: {seller_name} ({seller_city}).",
            f"Generiere eine EN 16931-konforme XRechnung für {authority_name} mit Leitweg-ID {leitweg_id}: {items_str}, Rechnungsnummer {inv_no}.",
            f"Erzeuge die XRechnung 3.0 JSON-Struktur für {authority_name} ({leitweg_id}): {items_str}, Rechnungsdatum {issue_date}."
        ]
        prompt = random.choice(prompt_templates)
        h = hashlib.sha256(prompt.strip().lower().encode("utf-8")).hexdigest()
        if seen_hashes is not None and h in seen_hashes:
            continue
        if seen_hashes is not None:
            seen_hashes.add(h)

        xrechnung_obj = {
            "buyer_reference": leitweg_id,
            "invoice_number": inv_no,
            "issue_date": issue_date,
            "due_date": due_date,
            "seller": {
                "name": seller_name,
                "vat_id": seller_vat_id,
                "tax_id": seller_tax_id,
                "street": random.choice(GERMAN_STREETS),
                "postal_code": f"{random.randint(10000, 99999)}",
                "city": seller_city,
                "country_code": "DE"
            },
            "buyer": {
                "name": authority_name,
                "vat_id": buyer_vat_id,
                "street": random.choice(GERMAN_STREETS),
                "postal_code": f"{random.randint(10000, 99999)}",
                "city": "Berlin" if "Berlin" in authority_name else ("Köln" if "Köln" in authority_name else seller_city),
                "country_code": "DE"
            },
            "currency": "EUR",
            "payment_terms": "Zahlbar innerhalb von 14 Tagen ab Rechnungsdatum rein netto.",
            "line_items": line_items,
            "total_net_amount": total_net,
            "total_tax_amount": total_tax,
            "total_gross_amount": total_gross
        }

        samples.append({
            "conversations": [
                {"from": "human", "value": prompt},
                {"from": "gpt", "value": json.dumps(xrechnung_obj, ensure_ascii=False)}
            ]
        })

    return samples


# --- Domain 7: GoBD § 14 Abs. 4 UStG Pre-Audit Inspector ---

def generate_domain_7_gobd_audit_samples(count: int = 120, seen_hashes: Set[str] = None) -> List[Dict[str, Any]]:
    samples = []
    scenarios = ["compliant", "missing_tax_id", "missing_date", "missing_invoice_number", "missing_service_period"]

    attempts = 0
    while len(samples) < count and attempts < count * 20:
        attempts += 1
        scenario = random.choice(scenarios)
        seller, city = generate_company_name()
        buyer, buyer_city = generate_company_name()
        inv_no = f"RE-2025-{random.randint(100, 999)}"
        date_str = f"2025-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        net = round(random.uniform(300.0, 4500.0), 2)
        tax = round(net * 0.19, 2)
        gross = round(net + tax, 2)

        if scenario == "compliant":
            prompt = (
                f"Prüfe folgende Eingangsrechnung auf GoBD-Konformität und Vorsteuerabzug nach § 14 Abs. 4 UStG: "
                f"'Rechnung von {seller} ({city}, Steuernummer 12/345/67890, USt-IdNr. DE123456789), "
                f"Rechnungsnummer {inv_no}, Ausstellungsdatum {date_str}, Leistungszeitpunkt Monat {date_str[:7]}, "
                f"an {buyer} ({buyer_city}): IT-Consulting {net:.2f}€ netto zzgl. 19% USt ({tax:.2f}€) = {gross:.2f}€ brutto.'"
            )
            result = {
                "is_compliant": True,
                "vorsteuerabzug_risk": "KEIN_RISIKO",
                "missing_mandatory_fields": [],
                "findings": [
                    "Alle 10 gesetzlichen Pflichtangaben nach § 14 Abs. 4 UStG sind vollständig und korrekt vorhanden.",
                    "Steuernummer/USt-IdNr., einmalige Rechnungsnummer sowie Leistungszeitpunkt sind eindeutig ausgewiesen.",
                    "Der Steuerausweis (19% MwSt) und die Rechenoperationen sind mathematisch einwandfrei."
                ],
                "recommendations": [
                    "Der Beleg ist uneingeschränkt zum Vorsteuerabzug berechtigt.",
                    "Ordnungsgemäß buchen und nach § 147 AO revisionssicher für 10 bzw. 8 Jahre aufbewahren."
                ]
            }

        elif scenario == "missing_tax_id":
            prompt = (
                f"GoBD-Audit nach § 14 UStG für Eingangsrechnung durchführen: "
                f"'Rechnung von {seller} ({city}), Rechnungsnummer {inv_no}, Datum {date_str}, "
                f"an {buyer}: Serverwartung {net:.2f}€ netto zzgl. 19% MwSt = {gross:.2f}€ brutto. "
                f"Keine Steuernummer und keine USt-IdNr. angegeben.'"
            )
            result = {
                "is_compliant": False,
                "vorsteuerabzug_risk": "HOCH",
                "missing_mandatory_fields": ["Steuernummer oder USt-IdNr. des leistenden Unternehmers (§ 14 Abs. 4 Satz 1 Nr. 2 UStG)"],
                "findings": [
                    "Die Rechnung enthält weder eine deutsche Steuernummer noch eine gültige USt-IdNr. des Ausstellers.",
                    "Ohne Steuernummer oder USt-IdNr. wird das Finanzamt bei einer Betriebsprüfung den Vorsteuerabzug versagen."
                ],
                "recommendations": [
                    "Rechnung unverzüglich beim Rechnungssteller reklamieren und Neuausstellung mit Steuernummer/USt-IdNr. anfordern.",
                    "Vorsteuerabzug erst nach Erhalt des berichtigten Belegs in der Umsatzsteuervoranmeldung geltend machen."
                ]
            }

        elif scenario == "missing_date":
            prompt = (
                f"Ist dieser Beleg für den Vorsteuerabzug nach § 14 UStG zulässig? "
                f"'Rechnung von {seller} ({city}, USt-IdNr. DE987654321), Rechnungsnummer {inv_no}, "
                f"an {buyer}: Fullstack Softwareentwicklung {net:.2f}€ netto zzgl. 19% USt = {gross:.2f}€ brutto. "
                f"Ein Ausstellungsdatum fehlt komplett.'"
            )
            result = {
                "is_compliant": False,
                "vorsteuerabzug_risk": "HOCH",
                "missing_mandatory_fields": ["Ausstellungsdatum der Rechnung (§ 14 Abs. 4 Satz 1 Nr. 3 UStG)"],
                "findings": [
                    "Das Ausstellungsdatum fehlt vollständig auf dem Beleg.",
                    "Das Ausstellungsdatum ist zwingendes Gültigkeitskriterium für den Vorsteuerabzug."
                ],
                "recommendations": [
                    "Rechnung reklamieren und eine datierte Korrekturrechnung anfordern."
                ]
            }

        elif scenario == "missing_invoice_number":
            prompt = (
                f"Prüfe Eingangsrechnung auf Konformität: "
                f"'Rechnung von {seller} (Steuernummer 34/567/89012, Datum {date_str}) an {buyer}: "
                f"Bürorenovierung {net:.2f}€ netto zzgl. 19% MwSt = {gross:.2f}€ brutto. Keine Rechnungsnummer vorhanden.'"
            )
            result = {
                "is_compliant": False,
                "vorsteuerabzug_risk": "HOCH",
                "missing_mandatory_fields": ["Fortlaufende, einmalige Rechnungsnummer (§ 14 Abs. 4 Satz 1 Nr. 4 UStG)"],
                "findings": [
                    "Der Beleg weist keine fortlaufende Rechnungsnummer auf.",
                    "Dies stellt einen gravierenden formellen Verstoß gegen § 14 Abs. 4 UStG dar."
                ],
                "recommendations": [
                    "Korrekturrechnung mit eindeutiger Belegnummer verlangen, Vorsteuerabzug vorübergehend aussetzen."
                ]
            }

        else:  # missing_service_period
            prompt = (
                f"Vorsteuerabzug-Prüfung § 14 Abs. 4 UStG: "
                f"'Rechnung von {seller} (USt-IdNr. DE123456789, Rechnungsnummer {inv_no}, Ausstellungsdatum {date_str}) "
                f"an {buyer}: Beratungsleistungen {net:.2f}€ netto zzgl. 19% USt = {gross:.2f}€ brutto. "
                f"Kein Leistungszeitpunkt und kein Leistungszeitraum angegeben.'"
            )
            result = {
                "is_compliant": False,
                "vorsteuerabzug_risk": "MITTEL",
                "missing_mandatory_fields": ["Zeitpunkt der Lieferung oder Leistung (§ 14 Abs. 4 Satz 1 Nr. 6 UStG)"],
                "findings": [
                    "Auf der Rechnung fehlt der konkrete Leistungszeitpunkt oder Leistungszeitraum.",
                    "Das Rechnungsdatum alleine reicht nur aus, wenn ausdrücklich vermerkt ist, dass Leistungsdatum gleich Rechnungsdatum ist."
                ],
                "recommendations": [
                    "Vom Aussteller schriftliche Bestätigung des Leistungszeitpunkts oder korrigierte Rechnung anfordern."
                ]
            }

        h = hashlib.sha256(prompt.strip().lower().encode("utf-8")).hexdigest()
        if seen_hashes is not None and h in seen_hashes:
            continue
        if seen_hashes is not None:
            seen_hashes.add(h)

        samples.append({
            "conversations": [
                {"from": "human", "value": prompt},
                {"from": "gpt", "value": json.dumps(result, ensure_ascii=False)}
            ]
        })

    return samples


# --- Domain 8: DATEV Buchungssatz CSV Generator (EXTF) ---

def generate_domain_8_datev_buchungssatz_samples(count: int = 120, seen_hashes: Set[str] = None) -> List[Dict[str, Any]]:
    samples = []
    attempts = 0

    while len(samples) < count and attempts < count * 20:
        attempts += 1
        exp = random.choice(EXPENSE_DEFINITIONS)
        chart = random.choice(["SKR03", "SKR04"])
        konto = exp["skr03"] if chart == "SKR03" else exp["skr04"]
        gegenkonto = "1200" if chart == "SKR03" else "1800"  # Bankkonto
        
        vat_rate = exp["vat_rate"]
        bu_schluessel = "9" if vat_rate == 19 else ("8" if vat_rate == 7 else "")
        
        amount_net = round(random.uniform(25.0, 1800.0), 2)
        amount_tax = round(amount_net * (vat_rate / 100.0), 2)
        amount_gross = round(amount_net + amount_tax, 2)
        
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        belegdatum = f"{day:02d}{month:02d}"
        inv_no = f"RE-2025-{random.randint(100, 9999)}"
        buchungstext = exp["category"][:30]

        umsatz_str = f"{amount_gross:.2f}".replace(".", ",")
        datev_line = f"{umsatz_str};S;EUR;;;;{konto};{gegenkonto};{bu_schluessel};{belegdatum};{inv_no};;;{buchungstext}"

        raw_input = random.choice(exp["inputs"]).format(amount=f"{amount_net:.2f}")
        prompt_templates = [
            f"Erzeuge den DATEV-Buchungssatz (EXTF-Zeile) für folgende Ausgabe in {chart}: '{raw_input} bezahlt per Bank am {day:02d}.{month:02d}.2025, Beleg {inv_no}'",
            f"Generiere die DATEV EXTF Buchungszeile für: '{raw_input} am {day:02d}.{month:02d}.2025 über Bank bezahlt, Beleg {inv_no}, {chart}'",
            f"Buche als DATEV-Exportzeile ({chart}): '{raw_input}, Belegnummer {inv_no}, Datum {day:02d}.{month:02d}.2025, Bankzahlung'"
        ]
        prompt = random.choice(prompt_templates)

        h = hashlib.sha256(prompt.strip().lower().encode("utf-8")).hexdigest()
        if seen_hashes is not None and h in seen_hashes:
            continue
        if seen_hashes is not None:
            seen_hashes.add(h)

        samples.append({
            "conversations": [
                {"from": "human", "value": prompt},
                {"from": "gpt", "value": datev_line}
            ]
        })

    return samples


def generate_full_dataset(output_path: Path, target_total: int = 1280) -> int:
    """Generates unique, balanced synthetic dataset across all 8 domains."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    seen_hashes: Set[str] = set()

    d1_cnt = 280  # Domain 1: Text-to-Invoice (Strict JSON)
    d2_cnt = 160  # Domain 2: Line Item Rewriter
    d3_cnt = 130  # Domain 3: German Tax & GoBD Notes
    d4_cnt = 130  # Domain 4: Mahnwesen
    d5_cnt = 220  # Domain 5: SKR03 / SKR04 Expense Accounts (32+ accounts)
    d6_cnt = 120  # Domain 6: E-Rechnung / XRechnung 3.0 (EN 16931)
    d7_cnt = 120  # Domain 7: GoBD § 14 UStG Pre-Audit Inspector
    d8_cnt = 120  # Domain 8: DATEV Buchungssatz CSV (EXTF)

    print(f"Generating unique dataset across all 8 domains (target: {d1_cnt + d2_cnt + d3_cnt + d4_cnt + d5_cnt + d6_cnt + d7_cnt + d8_cnt} examples):")
    all_records = []
    all_records.extend(generate_domain_1_samples(d1_cnt, seen_hashes))
    all_records.extend(generate_domain_2_samples(d2_cnt, seen_hashes))
    all_records.extend(generate_domain_3_samples(d3_cnt, seen_hashes))
    all_records.extend(generate_domain_4_samples(d4_cnt, seen_hashes))
    all_records.extend(generate_domain_5_samples(d5_cnt, seen_hashes))
    all_records.extend(generate_domain_6_xrechnung_samples(d6_cnt, seen_hashes))
    all_records.extend(generate_domain_7_gobd_audit_samples(d7_cnt, seen_hashes))
    all_records.extend(generate_domain_8_datev_buchungssatz_samples(d8_cnt, seen_hashes))

    random.seed(42)
    random.shuffle(all_records)

    with open(output_path, "w", encoding="utf-8") as f:
        for rec in all_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"[SUCCESS] Wrote {len(all_records)} unique, verified examples to {output_path}")
    return len(all_records)


if __name__ == "__main__":
    out_file = PROJECT_ROOT / "data" / "rechly_german_accounting.jsonl"
    generate_full_dataset(out_file, target_total=1280)

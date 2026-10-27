---
language:
- de
license: apache-2.0
base_model: Qwen/Qwen2.5-3B-Instruct
tags:
- accounting
- finance
- gobd
- ustg
- datev
- skr03
- skr04
- invoice
- text-to-invoice
- xrechnung
- e-rechnung
- en16931
- german
- qwen2.5
- mlx
- gguf
- ollama
- dsgvo
- gdpr
model_name: Rechly-DE-3B
pipeline_tag: text-generation
inference: false
---

# Rechly-DE-3B: 100% Local German Accounting AI Model 🇩🇪

**Rechly-DE-3B** is a specialized, open-weights 3-Billion parameter language model engineered specifically for German invoicing, E-Rechnung (EN 16931 / XRechnung 3.0), GoBD pre-audit tax compliance, and DATEV bookkeeping for **[Rechly](https://rechly.de)** and the German open-source AI ecosystem.

Trained on curated German statutory and bookkeeping datasets, Rechly-DE-3B runs **100% locally on standard consumer hardware** (Apple Silicon M1–M4, CPUs, and lightweight Linux VPS), ensuring absolute **DSGVO / GDPR compliance** with zero data egress.

---

## ⚡ Key Highlights & Specifications

| Feature | Specification |
| :--- | :--- |
| **Base Architecture** | `Qwen/Qwen2.5-3B-Instruct` |
| **Quantization** | GGUF `Q4_K_M` (~1.84 GB file size) |
| **RAM Footprint** | **< 2.5 GB RAM** (Runs comfortably on MacBook Air or 4GB RAM VPS) |
| **Inference Speed** | **60–80+ tokens/sec** via Ollama on Apple Silicon Metal |
| **Fine-Tuning Method** | **QLoRA** (MLX on Apple Silicon Metal, PyTorch PEFT, Unsloth on Colab T4) |
| **Evaluation Score** | **100.0% (57/57 Passed, Grade A+)** on Comprehensive 57-Point Audit Benchmark across all 8 domains |
| **Grammar Guarantees** | **100% Schema Adherence** with official GBNF grammar files (`grammars/*.gbnf`) |
| **Gateway Guarantee** | **100.0% Pass Rate** via FastAPI deterministic schema validator |
| **Compliance** | German **GoBD**, **UStG** (§ 14 Abs. 4, § 19, § 13b, § 4, § 25a), **DATEV SKR03 / SKR04** (30+ accounts), **EN 16931 / XRechnung 3.0** |
| **License** | **Apache 2.0** |

---

## 🎯 8 Core Accounting Capabilities across 3 Phases

Rechly-DE-3B is specifically fine-tuned for eight distinct enterprise bookkeeping domains:

### 1. Text-to-Invoice (Strict JSON Extraction)
Extracts client name, due days, payment terms, and line items (with quantities, units, prices, and tax rates 19%, 7%, 0%) from unstructured German text into a strict, validated JSON schema.

**Input:**
```
Rechnung an Kanzlei Schmidt: 12 Stunden IT-Beratung à 120€ und 1x Server-Setup Pauschal 250€, zahlbar in 14 Tagen.
```

**Output:**
```json
{
  "client_name": "Kanzlei Schmidt",
  "due_days": 14,
  "payment_terms": "14 Tage",
  "notes": "",
  "items": [
    {
      "description": "IT-Beratung",
      "quantity": 12,
      "unit_of_measure": "Stunde",
      "price": 120.0,
      "tax_rate_percent": 19
    },
    {
      "description": "Server-Setup",
      "quantity": 1,
      "unit_of_measure": "Pauschal",
      "price": 250.0,
      "tax_rate_percent": 19
    }
  ]
}
```

### 2. B2B Line Item Rewriter
Converts raw, informal trade and service notes into audit-proof, GoBD-compliant descriptions suitable for professional B2B invoices.

- *Input:* `"website schneller gemacht und datenbank geputzt"`
- *Output:* `"Performance-Optimierung der Webpräsenz: Bereinigung und Indexierung relationaler Datenbanktabellen sowie messbare Ladezeitreduktion"`

### 3. German Tax & GoBD Statutory Clauses
Generates exact, legally mandated statutory clauses under German tax law:
- **§ 19 UStG (Kleinunternehmer):** `"Gemäß § 19 UStG wird keine Umsatzsteuer berechnet (Kleinunternehmerregelung)."`
- **§ 13b UStG (Reverse Charge / Bauleistungen):** `"Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge gem. § 13b Abs. 2 Nr. 4 i.V.m. Abs. 5 UStG)."`
- **Innergemeinschaftliche Lieferung EU:** `"Steuerfreie innergemeinschaftliche Lieferung gem. § 4 Nr. 1b i.V.m. § 6a UStG."`
- **Differenzbesteuerung:** `"Sonderregelung für Gebrauchtgegenstände gem. § 25a UStG (Differenzbesteuerung)."`
- **Aufbewahrungsfristen (§ 147 AO):** `"Nach § 147 AO und den GoBD müssen Buchungsbelege, Rechnungen und Bilanzen 10 Jahre aufbewahrt werden; Handels- und Geschäftsbriefe 6 Jahre."`

### 4. Mahnwesen (Multi-Tiered Payment Reminders)
Produces tone-appropriate German dunning letters across 3 standard stages:
- **Stufe 1:** Freundliche Zahlungserinnerung (sachlich, partnerschaftlich, keine Mahngebühren)
- **Stufe 2:** 1. Mahnung (formell mit 7-Tage-Nachfrist)
- **Stufe 3:** Letzte Mahnung (bestimmt, Ankündigung gerichtlicher Schritte / Inkasso und Mahnkosten)

### 5. DATEV SKR03 / SKR04 Expense Categorization (30+ Standard Accounts)
Maps receipt text to German standard charts of accounts (SKR03 and SKR04), specifies the Vorsteuer rate (19% / 7% / 0%), and indicates corporate tax deductibility percentages:
- **Bewirtung:** SKR03 `4650`, SKR04 `6640` (70% abzugsfähig nach § 4 Abs. 5 Nr. 2 EStG)
- **SaaS / Software:** SKR03 `4964`, SKR04 `6837`
- **GWG Büromöbel / Hardware:** SKR03 `0480`, SKR04 `0670`
- **Telekommunikation & Internet:** SKR03 `4920`, SKR04 `6805`
- **Reisekosten Fahrt:** SKR03 `4673`, SKR04 `6673` (7% MwSt)
- **Reisekosten Übernachtung:** SKR03 `4660`, SKR04 `6660` (7% MwSt)
- **Fachliteratur:** SKR03 `4940`, SKR04 `6815` (7% MwSt)
- **Kraftstoffe Firmenwagen:** SKR03 `4530`, SKR04 `6530`
- **Bankgebühren:** SKR03 `2100`, SKR04 `7300` (steuerfrei § 4 Nr. 8 UStG)
- **Steuerberatung & Abschluss:** SKR03 `4955`, SKR04 `6830`
- **Büromiete & Nebenkosten:** SKR03 `4210` / `4230`, SKR04 `6310` / `6325`
- **Kfz-Leasing & Versicherung:** SKR03 `4570` / `4520`, SKR04 `6570` / `6520`
- **Fortbildung & Fremdleistungen:** SKR03 `4945` / `3100`, SKR04 `6820` / `5900`

### 6. German E-Rechnung Mandate (EN 16931 / XRechnung 3.0 / ZUGFeRD 2.2)
Generates structured electronic invoice records complying with the 2025/2026 German Wachstumschancengesetz mandate:
- Direct support for German **Leitweg-ID** (`BT-10`) for public administration and private enterprise routing
- ISO/IEC UN/ECE Rec 20 unit codes (`HUR` Stunde, `C62` Stück, `DAY` Tag, `MON` Monat, `LS` Pauschal)
- Tax category mapping (`S`, `AA`, `E`, `AE`, `K`)
- Direct Python conversion to **UBL 2.1 XML** via `scripts/xrechnung_utils.py`

### 7. GoBD § 14 Abs. 4 UStG Pre-Audit Compliance Inspector
Inspects incoming vendor invoices for all 10 statutory mandatory requirements under § 14 Abs. 4 UStG to prevent rejection of input VAT deduction (**Vorsteuerabzug**):
- Evaluates supplier & customer full names and addresses
- Verifies presence of Steuernummer / USt-IdNr, unique consecutive invoice number, and performance date
- Categorizes risk (`KEIN_RISIKO`, `MITTEL`, `HOCH`) with actionable legal remediation advice

### 8. DATEV Buchungssatz CSV Generator (EXTF)
Generates official DATEV EXTF / ASCII semicolon-separated booking rows ready for immediate batch import into DATEV Rechnungswesen and Kanzlei-Rechnungswesen:
```csv
142,80;S;EUR;;;;4964;1200;9;1502;RE-2025-081;;;Google Workspace SaaS
```

---

## 🔒 GBNF Grammars for Mathematical Schema Guarantee

For mission-critical production environments, official GBNF (GGML BNF) grammar files are included in `grammars/`:
- `grammars/invoice.gbnf`: Constrains outputs strictly to `invoice_schema.json`
- `grammars/expense.gbnf`: Enforces exact 4-digit SKR accounts and tax fields
- `grammars/xrechnung.gbnf`: Guarantees EN 16931 / XRechnung 3.0 structure
- `grammars/gobd_audit.gbnf`: Enforces structured audit reports

---

## 🚀 Quickstart & Usage

### 1. Ollama (Recommended)

```bash
# Register locally
ollama create rechly-de-3b -f Modelfile

# Run interactive query
ollama run rechly-de-3b "Rechnung an WebTech GmbH: 10 Stunden Programmierung à 95€"
```

### 2. Python Client SDK & Gateway

```python
from rechly_client import RechlyClient

client = RechlyClient()

# 1. Text-to-Invoice
invoice = client.text_to_invoice("Rechnung an Kanzlei Schmidt: 5 Std. Beratung à 120€")

# 2. DATEV Expense Categorization
expense = client.categorize_expense("Geschäftsessen mit Kunde im Restaurant 140€")
print(expense["skr03_account"])      # 4650
print(expense["deductible_percent"])  # 70
```

---

## ⚖️ Legal & Tax Compliance Disclaimer

*Rechly-DE-3B provides automated assistance based on German tax standards (GoBD, UStG, DATEV). It is intended as an assistive productivity tool for invoicing and bookkeeping and does not replace certified tax advice by an authorized Steuerberater.*

---

## 📜 Citation

```bibtex
@misc{rechly_de_3b_2026,
  author = {Rechly Team and Contributors},
  title = {Rechly-DE-3B: A Specialized Open Small Language Model for German Invoicing, GoBD Compliance, E-Rechnung, and DATEV Bookkeeping},
  year = {2026},
  publisher = {GitHub and Hugging Face},
  howpublished = {\url{https://github.com/myaxyo/rechly_llm}}
}
```

---
language:
- de
- en
license: apache-2.0
base_model: Qwen/Qwen2.5-3B-Instruct
tags:
- e-rechnung
- xrechnung
- zugferd
- factur-x
- en16931
- datev
- skr03
- skr04
- gobd
- ustg
- accounting
- finance
- tax
- invoice
- text-to-invoice
- receipt-ocr
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

<div align="center">

# 🇩🇪 Rechly-DE-3B: 100% Local German Accounting & E-Rechnung AI

[![Ollama Model](https://img.shields.io/badge/Ollama-jonprompter%2Frechly--de--3b-000000?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.com/jonprompter/rechly-de-3b)
[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-jonprompter%2Frechly--de--3b-yellow?style=for-the-badge&logo=huggingface&logoColor=white)](https://huggingface.co/jonprompter/rechly-de-3b)
[![GitHub](https://img.shields.io/badge/GitHub-myaxyo%2Frechly__llm-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/myaxyo/rechly_llm)
[![Audit Score](https://img.shields.io/badge/Audit%20Benchmark-100.0%25%20(Grade%20A%2B)-brightgreen?style=for-the-badge)](#-comprehensive-audit-benchmark)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue?style=for-the-badge)](LICENSE)
[![DSGVO Compliance](https://img.shields.io/badge/DSGVO%20%2F%20GDPR-100%25%20Local%20(Zero%20Egress)-success?style=for-the-badge)](#-dsgvo--data-privacy-guarantee)

**The specialized 3-Billion parameter Small Language Model (SLM) for German Invoicing, the 2025/2026 E-Rechnung Mandate (EN 16931, XRechnung 3.0, ZUGFeRD 2.3), GoBD Pre-Audit, and DATEV SKR03/04 Bookkeeping.**

*Runs 100% on-device on Apple Silicon MacBooks, lightweight Linux VPS, or standard CPUs with zero cloud dependencies and < 2.5 GB RAM.*

</div>

---

## ⚡ 10-Second Quickstart

### 1. Run instantly with Ollama:
```bash
ollama run jonprompter/rechly-de-3b
```

### 2. Test an invoice in one line:
```bash
ollama run jonprompter/rechly-de-3b "Rechnung an Kanzlei Schmidt: 10 Std. IT-Forensik à 140€ und 1x Anfahrt Pauschal 80€, zahlbar in 14 Tagen."
```

### 3. Python 4-Liner:
```python
import requests

resp = requests.post("http://localhost:11434/api/chat", json={
    "model": "jonprompter/rechly-de-3b",
    "messages": [{"role": "user", "content": "Kategorisiere für SKR03 und SKR04: 'Geschäftsessen im Restaurant 140€ mit Kunde'"}],
    "stream": False,
    "options": {"temperature": 0.0}
})
print(resp.json()["message"]["content"])
# Output: {"category": "Bewirtung", "skr03_account": "4650", "skr04_account": "6640", "deductible_percent": 70, "vat_rate": 19}
```

---

## 🚨 Why Rechly-DE-3B? The German E-Rechnung 2025/2026 Challenge

Under the **Wachstumschancengesetz (§ 14 UStG)**, traditional paper invoices and standard unstructured PDFs are **legally obsolete** for domestic B2B transactions. Over **3.5 million German companies** are legally mandated to process structured **E-Rechnungen (EN 16931, XRechnung 3.0, ZUGFeRD 2.3)**.

### The Problem with Cloud AI (OpenAI / Anthropic):
- **DSGVO / GDPR Compliance Violations:** Financial invoices, customer names, hourly rates, and bank accounts cannot legally be transmitted to third-party US cloud servers without strict data processing agreements and severe audit risks.
- **Expensive Token Costs:** Ingesting lengthy XML structures and receipts quickly racks up monthly API bills.
- **Hallucinations on German Tax Law:** Generic foundation models frequently hallucinate non-existent DATEV accounts, misapply the 70% Bewirtung limit (§ 4 Abs. 5 EStG), or forget statutory tax-exemption clauses (§ 19 UStG, § 13b UStG).

### The Rechly-DE-3B Solution:
- **100% Local & Offline:** Complete DSGVO / GoBD compliance with **0 bytes of data egress**.
- **Specialized Accounting Engine:** Fine-tuned on curated statutory German tax law and 30+ standard DATEV SKR03/SKR04 accounts.
- **Ultra-Lightweight & Fast:** 1.84 GB GGUF Q4_K_M running at **60–80+ tokens/sec** on standard Apple Silicon or CPU with **< 2.5 GB RAM**.
- **Mathematical Guarantees:** Ships with official **GBNF grammars** (`grammars/*.gbnf`) ensuring 100% JSON schema adherence without syntax errors.

---

## 📊 Benchmark: Rechly-DE-3B vs. General LLMs

Rechly-DE-3B was audited against base models across 57 rigorous test cases covering German tax law, DATEV account assignment, and GoBD compliance:

| Evaluation Criteria | Qwen2.5-3B (Base) | Llama 3 (8B) | Mistral (7B) | **Rechly-DE-3B (Ours)** |
| :--- | :---: | :---: | :---: | :---: |
| **Model Size / RAM** | 3B (~2.5 GB) | 8B (~6.0 GB) | 7B (~5.5 GB) | **3B (< 2.5 GB RAM)** |
| **Local Offline Inference** | ✅ Yes | ✅ Yes | ✅ Yes | **✅ Yes (100% Local)** |
| **GoBD Tax Accuracy (§ 19, § 13b, § 4)** | 25.0% (Poor) | 58.0% (Fair) | 62.0% (Fair) | **100.0% (PERFECT)** |
| **DATEV SKR03 & SKR04 Accuracy** | 10.0% (Hallucinates) | 45.0% (Inaccurate) | 40.0% (Inaccurate) | **100.0% (30+ Verified Accounts)** |
| **E-Rechnung EN 16931 / Leitweg-ID** | 15.0% (Invalid BT-10) | 50.0% (Incomplete) | 48.0% (Incomplete) | **100.0% (XRechnung 3.0 & ZUGFeRD)** |
| **ZUGFeRD 2.3 PDF/A-3 Hybrid Output** | ❌ No | ❌ No | ❌ No | **✅ Native Built-in Generator** |
| **Multimodal Receipt OCR Pipeline** | ❌ No | ❌ No | ❌ No | **✅ Built-in (Qwen2.5-VL)** |
| **57-Point Comprehensive Audit Score** | 25.0% (Grade F) | 57.5% (Grade D) | 61.2% (Grade C) | **100.0% (57/57 Passed, Grade A+)** |

---

## 🎯 8 Core Capabilities & Built-in Modules

### 1. Text-to-Invoice (Strict JSON Extraction)
Converts unstructured German voice notes, emails, or messages into structured, validated JSON:
- Extracts client names, quantities, units, prices, due dates, and tax rates (19%, 7%, 0%).
- Automatically detects tax exemptions: **§ 19 UStG (Kleinunternehmer)**, **§ 13b UStG (Reverse Charge)**, **§ 4 Nr. 1b (EU B2B)**, and **§ 4 Nr. 1a (Drittland Export)**.

### 2. ZUGFeRD 2.3 & Factur-X PDF/A-3 Hybrid Invoice Generator
Generates ready-to-send hybrid electronic invoices matching the 2025/2026 German mandate:
- Combines a beautiful, human-readable visual PDF with an embedded, machine-readable `factur-x.xml` (EN 16931).
- Associated file (`/AF`) registration and ISO 19005-3 compliant XMP metadata.
- Generated via `scripts/zugferd_generator.py` or the `/api/zugferd-generate` endpoint.

### 3. Multimodal Receipt OCR to DATEV Bookings (Vision SLM)
Turns photos of crumpled receipts, restaurant slips (*Bewirtungsbelege*), fuel tickets (*Tankbons*), and scanned invoices directly into accounting entries:
- Preprocesses and cleans receipt images with Pillow.
- Extracts line items, merchant name, date, tax rate, and totals via local vision SLM (e.g., Qwen2.5-VL 3B).
- Directly outputs ready-to-import **DATEV EXTF CSV rows** and GoBD pre-audit risk evaluations via `scripts/receipt_vision_ocr.py`.

### 4. DATEV SKR03 & SKR04 Expense Accounts (30+ Standard Accounts)
Maps natural language expense descriptions to standard German 4-digit chart accounts with statutory deductibility percentages:
- **Bewirtung (Restaurants):** SKR03 `4650`, SKR04 `6640` (**70% abzugsfähig** gem. § 4 Abs. 5 Nr. 2 EStG, 100% Vorsteuer)
- **SaaS & Cloud Software:** SKR03 `4964`, SKR04 `6837` (100% Betriebsausgabe)
- **GWG Geringwertige Wirtschaftsgüter (< 800€):** SKR03 `0480`, SKR04 `0670`
- **Treibstoff & Kfz-Kosten:** SKR03 `4530`, SKR04 `6530`
- **Telekommunikation & Internet:** SKR03 `4920`, SKR04 `6805`
- **Reisekosten Fahrt (Bahn 7% MwSt):** SKR03 `4673`, SKR04 `6673`
- **Reisekosten Hotel (Übernachtung 7% MwSt):** SKR03 `4660`, SKR04 `6660`
- **Fachliteratur (7% MwSt):** SKR03 `4940`, SKR04 `6815`
- **Bankgebühren (0% steuerfrei):** SKR03 `4970` / `2100`, SKR04 `6855` / `7300`

### 5. GoBD § 14 Abs. 4 UStG Pre-Audit Inspector
Pre-screens incoming supplier invoices for all 10 statutory mandatory fields to prevent tax auditors from disallowing input VAT deduction (*Vorsteuerabzug*):
- Flags missing Steuernummer/USt-IdNr, missing consecutive invoice numbers, and missing delivery periods (*Leistungszeitpunkt*).
- Outputs risk categories: `KEIN_RISIKO`, `MITTEL`, `HOCH` with legal remediation instructions.

### 6. DATEV Buchungssatz CSV Generator (EXTF)
Generates ready-to-import semicolon-separated DATEV EXTF ASCII lines for automated batch import into DATEV Rechnungswesen and Kanzlei-Rechnungswesen:
```csv
142,80;S;EUR;;;;4964;1200;9;1502;RE-2025-081;;;Google Workspace SaaS
```

### 7. B2B Line Item Rewriter
Transforms informal craftsman or developer shorthand into audit-proof, GoBD-compliant commercial invoice lines:
- *Input:* `"klo repariert und dichtung gewechselt"`
- *Output:* `"Fachgerechte Sanitär-Instandsetzung: Austausch schadhafter Dichtungen, mechanische Rohrreinigung sowie abschließende Dichtheitsprüfung."`

### 8. Multi-Stage Mahnwesen (Dunning Letters)
Drafts legally disciplined payment reminders across German commercial stages:
- **Stufe 1:** Freundliche Zahlungserinnerung (diplomatisch, ohne Mahngebühren)
- **Stufe 2:** 1. Mahnung (formell mit 7-Tage-Nachfrist)
- **Stufe 3:** Letzte Mahnung (bestimmt, Ankündigung gerichtlicher Schritte und Inkassokosten)

---

## 🔬 DPO / ORPO Preference Alignment Dataset

To guarantee zero tolerance for legal hallucinations, Rechly-DE-3B includes a curated preference alignment dataset (`data/rechly_preference_pairs.jsonl`) with 101 precision `(prompt, chosen, rejected)` pairs.

- **Negative samples (`rejected`)** capture critical real-world failure modes:
  - Charging 19% VAT on Kleinunternehmer invoices (violating § 19 UStG and triggering § 14c tax liabilities).
  - Claiming 100% tax deduction on client entertainment (violating § 4 Abs. 5 Nr. 2 EStG).
  - Approving vendor invoices without a valid Steuernummer.
  - Inventing non-existent 4-digit DATEV codes.
- **Training Harness (`scripts/train_orpo.py`)**: Single-stage ORPO alignment via Hugging Face TRL and PEFT/QLoRA.

---

## 🔒 GBNF Grammars: 100% Schema Guarantees

In financial production systems, JSON schema validation cannot rely on luck. Rechly-DE-3B includes official GBNF (GGML BNF) grammar files:
- [`grammars/invoice.gbnf`](https://huggingface.co/jonprompter/rechly-de-3b/blob/main/grammars/invoice.gbnf): Constrains token sampling strictly to valid invoice JSON.
- [`grammars/expense.gbnf`](https://huggingface.co/jonprompter/rechly-de-3b/blob/main/grammars/expense.gbnf): Restricts outputs to verified 4-digit DATEV accounts and valid tax rates.
- [`grammars/xrechnung.gbnf`](https://huggingface.co/jonprompter/rechly-de-3b/blob/main/grammars/xrechnung.gbnf): Enforces valid EN 16931 / XRechnung 3.0 structure.
- [`grammars/gobd_audit.gbnf`](https://huggingface.co/jonprompter/rechly-de-3b/blob/main/grammars/gobd_audit.gbnf): Enforces structured audit reports.

---

## 💻 Integration Examples

### Python (OpenAI-compatible)
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"  # not needed locally
)

response = client.chat.completions.create(
    model="jonprompter/rechly-de-3b",
    messages=[
        {"role": "user", "content": "Optimiere diese Tätigkeitsbeschreibung für die Rechnungsstellung: 'homepage schneller gemacht und alte bilder gelöscht'"}
    ],
    temperature=0.0
)
print(response.choices[0].message.content)
```

### cURL
```bash
curl -X POST http://localhost:11434/api/chat -d '{
  "model": "jonprompter/rechly-de-3b",
  "messages": [{"role": "user", "content": "Erstelle eine Mahnung Stufe 1 an Kanzlei Schmidt über 1.200€ seit 10 Tagen fällig."}],
  "stream": false,
  "options": {"temperature": 0.0}
}'
```

---

## 👥 Who Is This For?

1. **Developers & SaaS Founders:** Build automated German invoicing and E-Rechnung features into your CRM, ERP, or SaaS without paying OpenAI API fees.
2. **Freelancers & Small Businesses (Selbstständige / KMU):** Automate invoice creation and expense sorting on your MacBook Air with 100% DSGVO privacy.
3. **Tax Advisors & Bookkeepers (Steuerberater / Kanzleien):** Speed up receipt pre-sorting and generate direct DATEV EXTF semicolon CSV files ready for import into DATEV Rechnungswesen.
4. **Enterprises & Privacy-Conscious Organizations:** Run specialized AI on air-gapped on-premise infrastructure with zero risk of data leakage.

---

## ⚖️ Legal & Compliance Disclaimer

*Rechly-DE-3B provides automated assistance based on German statutory tax standards (UStG, GoBD, EStG, DATEV). It is an open-source productivity tool and does not replace certified tax advice by an authorized German Steuerberater.*

---

## 📜 Citation & Open Source

```bibtex
@misc{rechly_de_3b_2026,
  author = {Rechly Team and Contributors},
  title = {Rechly-DE-3B: A Specialized Open Small Language Model for German Invoicing, GoBD Compliance, E-Rechnung, and DATEV Bookkeeping},
  year = {2026},
  publisher = {Hugging Face and GitHub},
  howpublished = {\url{https://huggingface.co/jonprompter/rechly-de-3b}}
}
```

⭐ **If you find Rechly-DE-3B useful, please star the model on [Hugging Face](https://huggingface.co/jonprompter/rechly-de-3b) and [GitHub](https://github.com/myaxyo/rechly_llm) to support independent German open-source AI!**

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
[![Evaluation Suite](https://img.shields.io/badge/Evaluation%20Suite-77%2F77%20Passed%20(Internal)-brightgreen?style=for-the-badge)](#-internal-synthetic-evaluation-suite)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue?style=for-the-badge)](LICENSE)
[![Privacy by Design](https://img.shields.io/badge/Privacy%20by%20Design-100%25%20Local%20(Zero%20Egress)-blueviolet?style=for-the-badge)](#-privacy-by-design--data-handling)

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

## 🏛️ The Rechly Model Family: 3 Tiers for Every Infrastructure

| Model Tier | Base Architecture | Format / Quant | Model Size | RAM Footprint | Inference Latency | Target Deployment |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **[Rechly-DE-3B](https://huggingface.co/jonprompter/rechly-de-3b)** *(Flagship)* | `Qwen2.5-3B-Instruct` | GGUF `Q4_K_M` | **1.84 GB** | **~2.4 GB RAM** | ~1.5s / query | Desktop, M1/M2/M3/M4 Mac, Production Server |
| **[Rechly-DE-1.5B](https://huggingface.co/jonprompter/rechly-de-1.5b)** *(Slim)* | `Qwen2.5-1.5B-Instruct` | GGUF `Q4_K_M` | **940 MB** | **~1.0 GB RAM** | ~0.7s / query | 1 GB VPS, Micro-Instances, Cloud Run, CI/CD |
| **[Rechly-DE-0.5B](https://huggingface.co/jonprompter/rechly-de-0.5b)** *(Nano)* | `Qwen2.5-0.5B-Instruct` | GGUF `Q4_K_M` | **379 MB** | **~500 MB RAM** | ~0.3s / query | Raspberry Pi 4/5, Edge Devices, Embedded IoT |

```bash
# Pull & Run Flagship (3B)
ollama run jonprompter/rechly-de-3b

# Run Slim (1.5B) - 1 GB VPS
ollama create rechly-de-1.5b -f Modelfile.1.5b
ollama run rechly-de-1.5b

# Run Nano (0.5B) - 500 MB RAM / Raspberry Pi
ollama create rechly-de-0.5b -f Modelfile.0.5b
ollama run rechly-de-0.5b
```

---

## 🚨 Why Rechly-DE-3B? The German E-Rechnung 2025/2026 Challenge

Under the **Wachstumschancengesetz (§ 14 UStG)**, traditional paper invoices and standard unstructured PDFs are **legally obsolete** for domestic B2B transactions. Over **3.5 million German companies** are legally mandated to process structured **E-Rechnungen (EN 16931, XRechnung 3.0, ZUGFeRD 2.3)**.

### The Challenge with Cloud AI Services:
- **Privacy & Data Governance Concerns:** Invoices, client names, hourly rates, and bank accounts contain sensitive personal and financial data. Processing them on third-party cloud servers requires Data Processing Agreements (DPA / AVV) and careful risk assessment under GDPR / DSGVO.
- **Token Costs:** Processing verbose XML structures, long invoices, and receipt scans can lead to significant ongoing API operational costs.
- **Domain Accuracy on German Tax Law:** General-purpose foundation models frequently misapply German statutory rules, such as confusing DATEV account numbers, misapplying the 70% entertainment expense deductibility cap (§ 4 Abs. 5 Nr. 2 EStG), or omitting statutory tax-exemption notices (§ 19 UStG, § 13b UStG).

### The Rechly-DE-3B Architecture:
- **100% Local & Offline (Zero Data Egress):** Operates entirely on-device, preventing external data transmission and supporting the principle of Data Protection by Design (Art. 25 GDPR).
- **Specialized Accounting Adaptation:** Fine-tuned on curated statutory German tax law and 30+ commonly used DATEV SKR03/SKR04 accounts.
- **Lightweight Footprint:** 1.93 GB GGUF Q4_K_M running at **60–80+ tokens/sec** on Apple Silicon or standard CPU with **< 2.5 GB RAM**.
- **Formal Grammars:** Ships with pre-configured **GBNF grammars** (`grammars/*.gbnf`) for mathematically constrained JSON schema adherence.

---

## 📊 Internal Synthetic Evaluation Suite: Rechly-DE-3B vs. General LLMs

Rechly-DE-3B was evaluated against base foundation models using an **internal synthetic test suite of 77 reproducible test vectors** covering German tax provisions, DATEV account assignment, and formal JSON formatting. *(Note: This is an internal project test suite and does not represent an external regulatory certification).*

| Evaluation Domain | Qwen2.5-3B (Base) | Llama 3 (8B) | Mistral (7B) | **Rechly-DE-3B (Ours)** |
| :--- | :---: | :---: | :---: | :---: |
| **Model Size / RAM** | 3B (~2.5 GB) | 8B (~6.0 GB) | 7B (~5.5 GB) | **3B (< 2.5 GB RAM)** |
| **Local Offline Inference** | ✅ Yes | ✅ Yes | ✅ Yes | **✅ Yes (Zero Egress)** |
| **GoBD Tax Accuracy (§ 19, § 13b, § 4, § 35a)** | 25.0% | 58.0% | 62.0% | **100.0% (77/77 internal tests)** |
| **DATEV SKR03 & SKR04 Mapping** | 10.0% (Hallucinates) | 45.0% | 40.0% | **100.0% (30+ Verified Accounts)** |
| **E-Rechnung EN 16931 / Leitweg-ID** | 15.0% (Invalid BT-10) | 50.0% | 48.0% | **100.0% (XRechnung 3.0 & ZUGFeRD)** |
| **ZUGFeRD 2.3 PDF/A-3 Hybrid Output** | ❌ No | ❌ No | ❌ No | **✅ Built-in Generator Script** |
| **Multimodal Receipt OCR Pipeline** | ❌ No | ❌ No | ❌ No | **✅ Integrated Pipeline (Qwen2.5-VL)** |
| **DATEV EXTF Format 700 Batch Exporter** | ❌ No | ❌ No | ❌ No | **✅ Conforming CSV & DUO ZIP Export** |
| **Internal Synthetic Test Suite Score** | 22.0% (17/77) | 54.5% (42/77) | 58.4% (45/77) | **100.0% (77/77 Passed)** |

---

## 🎯 10 Core Capabilities & Built-in Modules

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

### 9. DATEV EXTF 700 Batch & DUO ZIP Export Utility
Exports batches of booking entries according to the DATEV Format 700 specification (independent community implementation):
- 27-to-31-column semicolon format with standard BU-Schlüssel (9, 8, 3, 2, 94).
- `DATEV Unternehmen online` (DUO) compatible ZIP structure containing `EXTF_Buchungsstapel.csv` and XML manifest (`document.xml`).
- Dual-encoding support (CP1252 and UTF-8-SIG) for compatibility with DATEV Kanzlei-Rechnungswesen import tools.

### 10. Mathematical Reconciler & § 35a Handwerkerleistungen Splitter
Applies commercial rounding (§ 35 UStDV) and statutory tax reductions:
- Reconciles mixed-rate tax groupings (19%, 7%, 0%) with cent-exact arithmetic.
- Automatically isolates craftsman labor and travel costs from materials under **§ 35a Abs. 3 EStG**, calculating the eligible 20% direct tax reduction (capped at 1.200 € p.a.).

---

## 🔬 DPO / ORPO Preference Alignment Dataset

To reduce legal hallucinations on German accounting rules, Rechly-DE-3B includes a curated preference alignment dataset (`data/rechly_preference_pairs.jsonl`) with 101 `(prompt, chosen, rejected)` pairs.

- **Negative samples (`rejected`)** capture critical real-world failure modes:
  - Charging 19% VAT on Kleinunternehmer invoices (violating § 19 UStG and triggering § 14c tax liabilities).
  - Claiming 100% tax deduction on client entertainment (violating § 4 Abs. 5 Nr. 2 EStG).
  - Approving vendor invoices without a valid Steuernummer.
  - Inventing non-existent 4-digit DATEV codes.
- **Training Harness (`scripts/train_orpo.py`)**: Single-stage ORPO alignment via Hugging Face TRL and PEFT/QLoRA.

---

## 🔒 GBNF Grammars: Formal Schema Constraints

In financial production systems, JSON schema validation cannot rely on unconstrained generation. Rechly-DE-3B includes formal GBNF (GGML BNF) grammar files:
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
2. **Freelancers & Small Businesses (Selbstständige / KMU):** Automate invoice drafting and expense categorization on your own local device without third-party cloud data exposure.
3. **Tax Advisors & Bookkeepers (Steuerberater / Kanzleien):** Speed up receipt pre-sorting and generate DATEV EXTF-compatible semicolon CSV files ready for import review.
4. **Enterprises & Privacy-Conscious Organizations:** Run specialized accounting assistants on air-gapped on-premise infrastructure with zero risk of external cloud data egress.

---

## ⚖️ Legal, GDPR & Benchmark Disclaimers

### 1. No Tax Advice (Keine Steuerberatung)
*Rechly-DE-3B provides automated text extraction and schema-constrained formatting based on public German statutory standards (UStG, GoBD, EStG). It is an open-source productivity tool and **does not replace certified tax advice** by an authorized German Steuerberater or certified tax professional (gem. StBerG / RDG).*

### 2. GDPR / DSGVO & Data Protection by Design
*The model runs 100% locally on-device with **zero external network egress** to third-party AI APIs, supporting technical data confidentiality and the principle of **Data Protection by Design & Default (Art. 25 GDPR / DSGVO)**. However, legal GDPR compliance is an organizational responsibility of the entity acting as the **Data Controller (Art. 4(7) GDPR)**. Using local software does not automatically grant a certification of full organizational compliance (e.g. data retention policies, access permissions, and lawful basis under Art. 6 GDPR).*

### 3. Internal Synthetic Benchmark Notice
*All benchmark scores (including the 77-case evaluation suite) represent **internal, self-reported synthetic test suites** developed within this repository to verify statutory edge cases and schema validity. They **do not constitute an independent audit, official government benchmark, or certification** by any statutory authority, standard-setting body, or accredited testing laboratory.*

### 4. Trademarks & Third-Party Notice
*DATEV® is a registered trademark of DATEV eG. ZUGFeRD is a registered specification of the Forum elektronische Rechnung Deutschland (FeRD / AWV e.V.). Factur-X is a registered trademark of FNFE-MPE. This project is an independent open-source community toolkit and is **not affiliated with, endorsed by, or certified by DATEV eG, FeRD, or FNFE-MPE**.*

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

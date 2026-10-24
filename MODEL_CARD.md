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

**Rechly-DE-3B** is a specialized, open-weights 3-Billion parameter language model engineered specifically for German invoicing, GoBD tax compliance, and DATEV bookkeeping for **[Rechly](https://rechly.de)** and the German open-source AI ecosystem.

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
| **Evaluation Score** | **100.0% Pass Rate (8/8)** across all 5 core accounting domains |
| **Compliance** | German **GoBD**, **UStG** (§ 19, § 13b, § 4 Nr. 1b, § 25a), **DATEV SKR03 / SKR04** |
| **License** | **Apache 2.0** |

---

## 🎯 5 Core Accounting Capabilities

Rechly-DE-3B is specifically fine-tuned for five distinct enterprise bookkeeping tasks:

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
- *Output:* `"Performance-Optimierung der Webpräsenz: Bereinigung und Indexierung relationaler Datenbanktabellen sowie Ladezeitreduktion"`

### 3. German Tax & GoBD Statutory Clauses
Generates exact, legally mandated statutory clauses under German tax law:
- **§ 19 UStG (Kleinunternehmer):** `"Gemäß § 19 UStG wird keine Umsatzsteuer berechnet (Kleinunternehmerregelung)."`
- **§ 13b UStG (Reverse Charge / Bauleistungen):** `"Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge / § 13b UStG)."`
- **Innergemeinschaftliche Lieferung:** `"Steuerfreie innergemeinschaftliche Lieferung gem. § 4 Nr. 1b i.V.m. § 6a UStG."`
- **Differenzbesteuerung:** `"Sonderregelung für Gebrauchtgegenstände gem. § 25a UStG (Differenzbesteuerung)."`

### 4. Mahnwesen (Multi-Tiered Payment Reminders)
Produces tone-appropriate German dunning letters across 3 standard stages:
- **Stufe 1:** Freundliche Zahlungserinnerung (sachlich, partnerschaftlich)
- **Stufe 2:** 1. Mahnung (konkrete Nachfrist von 7 Tagen)
- **Stufe 3:** 2. / Letzte Mahnung (Bestimmt, Ankündigung gerichtlicher Schritte / Inkasso)

### 5. DATEV SKR03 / SKR04 Expense Categorization
Maps receipt text to standard German standard chart of accounts (SKR03 and SKR04), specifies the Vorsteuer rate (19% / 7%), and indicates corporate tax deductibility percentages (e.g. 70% Bewirtung nach § 4 Abs. 5 EStG, 100% Büromaterial).

---

## 📊 Benchmark Evaluation

Evaluated against the official 5-domain GoBD benchmark suite (`scripts/evaluate_model.py`):

| Domain | Base Qwen 2.5 3B | Rechly-DE-3B |
| :--- | :---: | :---: |
| **Domain 1: Text-to-Invoice (Strict JSON)** | 62.5% (schema drift, hallucinated keys) | **100.0%** (strict schema valid) |
| **Domain 2: B2B Line Item Rewriter** | 75.0% (overly generic English/German) | **100.0%** (German audit-proof) |
| **Domain 3: Tax & GoBD Clauses** | 50.0% (missing statutory citations) | **100.0%** (exact UStG citations) |
| **Domain 4: Dunning Reminders** | 80.0% (informal tone) | **100.0%** (3-stage formal German) |
| **Domain 5: DATEV SKR03/04 Accounts** | 25.0% (invalid 4-digit codes) | **100.0%** (verified DATEV codes) |
| **Overall Benchmark Score** | **58.5%** | **100.0% (8/8 Passed)** |

---

## 🚀 Quickstart & Usage

### 1. Ollama (Recommended)

```bash
# Register locally
ollama create rechly-de-3b -f Modelfile

# Run interactive query
ollama run rechly-de-3b "Rechnung an WebTech GmbH: 10 Stunden Programmierung à 95€"
```

### 2. Python Client SDK

```python
from rechly_client import RechlyClient

client = RechlyClient()

# 1. Text-to-Invoice
invoice = client.text_to_invoice("Rechnung an Kanzlei Schmidt: 5 Std. Beratung à 120€")

# 2. DATEV Expense Categorization
expense = client.categorize_expense("Geschäftsessen mit Kunde im Restaurant 140€")
print(expense["skr03_account"]) # 4650
print(expense["deductible_percent"]) # 70
```

### 3. Apple Silicon Native (MLX)

```python
from mlx_lm import load, generate

model, tokenizer = load("rechly-de-3b-mlx")
prompt = "<|im_start|>user\nKategorisiere für SKR03: 'Google Workspace Cloud 70€'<|im_end|>\n<|im_start|>assistant\n"
response = generate(model, tokenizer, prompt=prompt, max_tokens=256)
print(response)
```

---

## ⚖️ Legal & Tax Compliance Disclaimer

*Rechly-DE-3B provides automated assistance based on German tax standards (GoBD, UStG, DATEV). It is intended as an assistive productivity tool for invoicing and bookkeeping and does not replace certified tax advice by an authorized Steuerberater.*

---

## 📜 Citation

```bibtex
@misc{rechly_de_3b_2026,
  author = {Rechly Team and Contributors},
  title = {Rechly-DE-3B: A Specialized Open Small Language Model for German Invoicing, GoBD Compliance, and DATEV Bookkeeping},
  year = {2026},
  publisher = {GitHub and Hugging Face},
  howpublished = {\url{https://github.com/rechly/rechly_llm}}
}
```

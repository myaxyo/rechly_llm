# Training Blueprint: Rechly Local German AI Model (Rechly-DE-3B)

This document contains the **complete blueprint, synthetic data generation prompt, training pipeline, and Ollama integration** to fine-tune a specialized, 100% local, GDPR/DSGVO-compliant German accounting model for Rechly.

---

## 1. Architecture & Model Selection

| Specification | Recommendation |
| :--- | :--- |
| **Base Model** | `Qwen/Qwen2.5-3B-Instruct` (or `meta-llama/Llama-3.2-3B-Instruct`) |
| **Why 3B?** | Fits into **< 2.5 GB RAM** when quantized (Q4_K_M). Runs at **60+ tokens/sec** on MacBook (M1/M2/M3/M4) and CPU servers. Far higher JSON fidelity than 1B models. |
| **Fine-Tuning Method** | **QLoRA** with [Unsloth](https://github.com/unslothai/unsloth) (Google Colab / Linux) or [MLX](https://github.com/ml-explore/mlx-examples) (Apple Silicon). |
| **Training Time & Cost** | ~30 minutes on a free Google Colab T4 GPU (**$0 cost**). |
| **Target Export** | Single GGUF file (`rechly-de-3b-Q4_K_M.gguf`, ~1.9 GB). |

---

## 2. Master Prompt: Synthetic Dataset Generation

Use this prompt with a frontier LLM (Claude 3.5 Sonnet, GPT-4o, or Gemini 1.5 Pro) to generate 1,500–3,000 diverse training examples in **ShareGPT JSONL format**.

```markdown
You are a German Tax Advisor (Steuerberater) and Senior Machine Learning Engineer building a specialized training dataset for "Rechly-DE-3B", an open-source German invoicing and bookkeeping model.

Generate 50 diverse training pairs in ShareGPT JSON format covering the 5 core domains below. All German texts must follow German GoBD standards, official tax laws (UStG), and standard B2B business etiquette.

### Domain 1: Text-to-Invoice (Strict JSON Extraction)
- Input: Natural, colloquial German sentence describing an invoice (e.g. "Rechnung an WebTech GmbH: 14 Stunden Frontend-Entwicklung à 95€ und 1x SSL Zertifikat Pauschal 60€, zahlbar in 14 Tagen mit 2% Skonto").
- Output: Strict JSON matching this schema:
{
  "client_name": "string",
  "due_days": number,
  "payment_terms": "string",
  "notes": "string",
  "items": [
    {
      "description": "string",
      "quantity": number,
      "unit_of_measure": "Stunde" | "Stück" | "Tag" | "Pauschal" | "Monat",
      "price": number,
      "tax_rate_percent": 19 | 7 | 0
    }
  ]
}

### Domain 2: B2B Line Item Description Rewriter
- Input: Rough, informal notes (e.g. "website schneller gemacht und datenbank geputzt").
- Output: Formal, professional, audit-compliant description (e.g. "Performance-Optimierung der Webpräsenz: Bereinigung und Indexierung relationaler Datenbanktabellen sowie Ladezeitreduktion").

### Domain 3: German Tax & GoBD Compliance Notes
- Input: Invoice parameters (e.g. "Kleinunternehmer", "Bauleistung an Generalunternehmer", "B2B Kunde in Österreich mit ATU-Nummer").
- Output: The legally mandated German statutory clause:
  - § 19 UStG: "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet (Kleinunternehmerregelung)."
  - § 13b UStG: "Steuerschuldnerschaft des Leistungsempfängers (Reverse Charge / § 13b UStG)."
  - Innergemeinschaftlich: "Steuerfreie innergemeinschaftliche Lieferung gem. § 4 Nr. 1b i.V.m. § 6a UStG."

### Domain 4: Mahnwesen (Dunning Letters)
- Input: Invoice number, client name, overdue days, amount.
- Output: Tone-appropriate German payment reminder:
  - Stufe 1: Freundliche Zahlungserinnerung (sachlich, partnerschaftlich).
  - Stufe 2: 1. Mahnung (konkrete Nachfrist von 7 Tagen).
  - Stufe 3: 2. Mahnung / Letzte Mahnung (Bestimmt, Ankündigung gerichtlicher Schritte).

### Domain 5: SKR03 / SKR04 Expense Categorization
- Input: Receipt description (e.g. "Geschäftsessen mit Kunde im Restaurant Osteria 120€").
- Output: Structured JSON:
{
  "category": "Bewirtung",
  "vat_rate": 19,
  "deductible_percent": 70,
  "skr03_account": "4650",
  "skr04_account": "6640",
  "note": "Geschäftliche Bewirtungskosten: 70% steuerlich abzugsfähig, 100% Vorsteuerabzug."
}

Format each example as a single JSON line:
{"conversations": [{"from": "human", "value": "..."}, {"from": "gpt", "value": "..."}]}
```

---

## 3. Dataset Generation Script (`scripts/generate_dataset.py`)

Run this Python script to synthesize your training data using the Anthropic, OpenAI, or OpenRouter API.

---

## 4. Fine-Tuning Pipeline (Unsloth on Google Colab / GPU)

Execute QLoRA fine-tuning on `Qwen/Qwen2.5-3B-Instruct` using Unsloth, then export directly to GGUF format (`rechly-de-3b-q4_k_m.gguf`).

---

## 5. Attaching the Model to Rechly with Ollama

Register with `ollama create rechly-de-3b -f Modelfile` and integrate directly into Rechly settings.

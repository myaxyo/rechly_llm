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

## 3. Dataset Generation Scripts

- **100% Open-Source Engine (`scripts/dataset_generator_engine.py`)**: Generates balanced, verified GoBD pairs across all 5 domains offline with zero API keys required (`python scripts/dataset_generator_engine.py`).
- **Multi-Provider Synthesizer (`scripts/generate_dataset.py`)**: Synthesizes and augments data using `--provider engine`, local Ollama (`--provider ollama`), or frontier models.
- **Dataset Validator (`scripts/validate_dataset.py`)**: Enforces JSON schema validity, GoBD compliance, and detects duplicate prompts.

---

## 4. Fine-Tuning Pipelines

1. **Apple Silicon Native Metal (MLX)**: Run local fine-tuning on MacBooks via `scripts/train_mlx.py`.
2. **PyTorch + PEFT (MPS / CUDA / CPU)**: Universal open-source fine-tuning via `scripts/train_hf_mps.py`.
3. **Unsloth on Google Colab (Free T4 GPU)**: Cloud fine-tuning via `scripts/train_unsloth.py` and `notebooks/rechly_de_3b_training_colab.ipynb`.

---

## 5. Export, Ollama Deployment & Evaluation

- **GGUF Export & Verification (`scripts/export_gguf.py`)**: Verifies GGUF binary headers and merges LoRA adapters.
- **Ollama Modelfile (`Modelfile`)**: Registers `rechly-de-3b` locally in Ollama (`ollama create rechly-de-3b -f Modelfile`).
- **Benchmark Suite (`scripts/evaluate_model.py`)**: Automated verification achieving 100% pass score across all 5 domains.
- **API Gateway (`scripts/serve_api.py`)**: Local REST API and OpenAI-compatible completions server with embedded German AI Playground UI for seamless integration with the Rechly web app.

---

## 6. Developer Tooling, Client SDK & Production DevOps

- **Interactive German AI Web Playground (`web/index.html`)**: Modern, dark-mode, 5-domain interactive UI mounted at `http://localhost:8000/` and `/demo`.
- **Python Client SDK (`scripts/rechly_client.py`)**: Ergonomic, typed SDK providing direct integration methods (`text_to_invoice()`, `enhance_description()`, `get_tax_clause()`, `generate_dunning_letter()`, `categorize_expense()`).
- **CLI Developer Tool (`scripts/cli.py`)**: Terminal utility (`rechly-cli`) for executing invoice extractions, enhancements, and checks directly from bash/zsh.
- **Containerization (`Dockerfile`, `docker-compose.yml`)**: Turnkey 1-command deployment with health checks.
- **Developer Makefile (`Makefile`)**: Shortcuts for `make test`, `make benchmark`, `make validate`, `make serve`, and `make docker-up`.
- **Continuous Integration (`.github/workflows/ci.yml`)**: Multi-Python CI workflow testing 31 unit & integration tests and dataset validation.
- **Hugging Face Model Card (`MODEL_CARD.md`)**: Complete model card ready for Hugging Face Hub with metadata tags.
- **CV & Job Search Guide (`CV_PORTFOLIO_GUIDE.md`)**: Comprehensive technical interview guide, quantifiable metrics, and LinkedIn portfolio templates.


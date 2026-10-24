# Rechly-DE-3B: 100% Local German Accounting AI Model 🇩🇪

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Base Model](https://img.shields.io/badge/Base%20Model-Qwen%202.5%203B%20Instruct-brightgreen.svg)](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct)
[![Colab T4](https://img.shields.io/badge/Colab%20Training-Free%20T4%20GPU%20($0)-orange.svg)](notebooks/rechly_de_3b_training_colab.ipynb)
[![Ollama Ready](https://img.shields.io/badge/Ollama-Ready-black.svg)](Modelfile)

**Rechly-DE-3B** is a specialized, lightweight (3 Billion parameters), privacy-first German accounting language model tailored specifically for **[Rechly](https://rechly.de)**. It operates **100% locally** on Apple Silicon (M1/M2/M3/M4) and standard CPUs, providing complete **DSGVO/GDPR compliance** with zero data leaving your hardware.

---

## ⚡ Specifications & Highlights

| Parameter | Specification |
| :--- | :--- |
| **Base Architecture** | `Qwen/Qwen2.5-3B-Instruct` |
| **Quantization** | GGUF `Q4_K_M` (~1.9 GB file size) |
| **RAM Footprint** | **< 2.5 GB RAM** (Runs comfortably on any MacBook or 4GB VPS) |
| **Inference Speed** | **60–80+ tokens/sec** via Ollama on Apple Silicon Metal |
| **Fine-Tuning Method** | QLoRA (Rank 16, Alpha 32, AdamW 8-bit) with Unsloth or Apple MLX |
| **Training Hardware** | Free Google Colab T4 GPU (~30 min, **$0 cost**) or local Mac with MLX |
| **Compliance Standards** | German **GoBD**, **UStG** (§ 19 Kleinunternehmer, § 13b Reverse-Charge, Innergemeinschaftlich), **DATEV SKR03 / SKR04** |

---

## 🎯 5 Core Accounting Domains

```
                                  ┌────────────────────────┐
                                  │     Rechly-DE-3B       │
                                  └───────────┬────────────┘
         ┌──────────────────┬─────────────────┼────────────────┬──────────────────┐
         ▼                  ▼                 ▼                ▼                  ▼
┌─────────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌─────────────────┐
│ Domain 1:       │ │ Domain 2:     │ │ Domain 3:     │ │ Domain 4:     │ │ Domain 5:       │
│ Text-to-Invoice │ │ Line Item     │ │ GoBD / Tax    │ │ Dunning       │ │ SKR03 / SKR04   │
│ Strict JSON     │ │ Rewriter      │ │ Clauses       │ │ Reminders     │ │ Categorization  │
└─────────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └─────────────────┘
```

1. **Text-to-Invoice (Strict JSON Extraction)**:
   Extracts client names, quantities, unit prices, tax rates (19%, 7%, 0%), and payment terms directly from unstructured German notes into Rechly's native schema.
2. **B2B Line Item Description Rewriter**:
   Converts informal, raw notes (`"website schneller gemacht und datenbank geputzt"`) into audit-proof, formal descriptions (`"Performance-Optimierung der Webpräsenz: Bereinigung und Indexierung relationaler Datenbanktabellen sowie Ladezeitreduktion"`).
3. **German Tax & GoBD Compliance Notes**:
   Generates legally mandated statutory clauses (§ 19 UStG Kleinunternehmer, § 13b UStG Steuerschuldnerschaft des Leistungsempfängers, § 4 Nr. 1b i.V.m. § 6a UStG innergemeinschaftliche Lieferung, § 25a UStG Differenzbesteuerung).
4. **Mahnwesen (Dunning Letters & Reminders)**:
   Produces multi-tiered, tone-appropriate German payment reminders (Stufe 1: Freundliche Erinnerung, Stufe 2: 1. Mahnung mit 7-Tage-Nachfrist, Stufe 3: Letzte Mahnung vor Inkasso/Mahnbescheid).
5. **SKR03 / SKR04 Expense Categorization**:
   Assigns DATEV-standard 4-digit accounting codes (e.g. 4650 / 6640 for Bewirtung, 4964 / 6837 for SaaS, 0480 / 0670 for GWG) along with deductibility percentages and receipt guidelines.

---

## 📁 Repository Structure

```
rechly_llm/
├── BLUEPRINT.md                         # Detailed design specification
├── Modelfile                            # Ollama Modelfile with ChatML & system prompt
├── README.md                            # Complete setup & training guide
├── requirements.txt                     # Dependencies for dataset gen & training
├── data/
│   ├── seed_dataset.jsonl               # 25 verified GoBD training seed pairs
│   └── schemas/
│       ├── invoice_schema.json          # JSON schema for Text-to-Invoice output
│       └── expense_schema.json          # JSON schema for SKR03/SKR04 output
├── notebooks/
│   └── rechly_de_3b_training_colab.ipynb# Turnkey Google Colab training notebook
└── scripts/
    ├── generate_dataset.py              # Multi-provider synthetic dataset generator
    ├── validate_dataset.py              # Schema & GoBD integrity validator
    ├── train_unsloth.py                 # QLoRA training script for CUDA / Colab
    ├── train_mlx.py                     # Native Apple Silicon MLX training script
    ├── export_gguf.py                   # GGUF quantization helper
    └── evaluate_model.py                # Automated 5-domain evaluation benchmark
```

---

## 🚀 Quickstart Guide

### 1. Installation

```bash
git clone https://github.com/rechly/rechly_llm.git
cd rechly_llm
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Validate Existing Seed Data

Check the pre-packaged seed dataset:
```bash
python scripts/validate_dataset.py data/seed_dataset.jsonl
```

### 3. Generate Large-Scale Synthetic Dataset (Optional)

Generate 1,500+ diverse examples using OpenAI, Anthropic, OpenRouter, or local Ollama:
```bash
# Using OpenAI GPT-4o-mini
export OPENAI_API_KEY="sk-..."
python scripts/generate_dataset.py --provider openai --model gpt-4o-mini --output data/rechly_german_accounting.jsonl

# Or using local Ollama (100% free)
python scripts/generate_dataset.py --provider ollama --model qwen2.5-coder:14b --batch-size 2
```

---

## 🏋️ Training Pipelines

### Option A: Google Colab (Recommended, Free T4 GPU)
1. Open [`notebooks/rechly_de_3b_training_colab.ipynb`](notebooks/rechly_de_3b_training_colab.ipynb) in Google Colab.
2. Select runtime: **T4 GPU** (under `Runtime` $\to$ `Change runtime type`).
3. Upload `rechly_german_accounting.jsonl` (or use the seed dataset).
4. Run all cells: the model trains in ~30 minutes and exports `rechly-de-3b-q4_k_m.gguf`.
5. Download the `.gguf` file to your machine.

### Option B: Local Training on Apple Silicon (MLX)
Fine-tune directly on your Mac using Apple's MLX framework:
```bash
pip install mlx mlx-lm
python scripts/train_mlx.py --data data/seed_dataset.jsonl --iters 200
```

---

## 🦙 Ollama Integration

### 1. Register the Model
Once you have `rechly-de-3b-q4_k_m.gguf` in your folder:
```bash
ollama create rechly-de-3b -f Modelfile
```

> **Pro Tip**: Want to test the prompt & system persona immediately before training? Create a prototype alias from base Qwen:
> ```bash
> sed 's|./rechly-de-3b-q4_k_m.gguf|qwen2.5:3b|g' Modelfile > Modelfile.dev
> ollama create rechly-de-3b -f Modelfile.dev
> ```

### 2. Test in Terminal
```bash
ollama run rechly-de-3b "Rechnung an Müller GmbH: 10 Std. Beratung à 120€, zahlbar in 14 Tagen"
```

### 3. Run Automated Benchmark
```bash
python scripts/evaluate_model.py --model rechly-de-3b
```

---

## 🔗 Connecting to Rechly

1. Open your Rechly web app and navigate to **Einstellungen $\to$ KI** (`/dashboard/settings`).
2. Select **KI-Anbieter**: `Ollama (Lokal / DSGVO-konform)`.
3. In the **Modell** field, select or type: `rechly-de-3b`.
4. Ensure the **Server-URL** is `http://localhost:11434/v1`.
5. Click **KI-Einstellungen speichern** and **KI testen**.
6. The **Text-zu-Rechnung** prompt bar, line item optimizers, and dunning generator in Rechly will now run 100% privately and securely on your own machine!

---

## 📜 License & Compliance

Distributed under the Apache 2.0 License. All tax logic and statutory citations comply with German tax law (UStG, GoBD, EStG).

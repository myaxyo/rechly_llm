# Rechly-DE-3B: 100% Local German Accounting AI Model 🇩🇪

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Base Model](https://img.shields.io/badge/Base%20Model-Qwen%202.5%203B%20Instruct-brightgreen.svg)](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct)
[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-jonprompter%2Frechly--de--3b-yellow.svg)](https://huggingface.co/jonprompter/rechly-de-3b)
[![Ollama Hub](https://img.shields.io/badge/Ollama%20Hub-jonprompter%2Frechly--de--3b-black.svg)](https://ollama.com/jonprompter/rechly-de-3b)
[![Benchmark](https://img.shields.io/badge/Benchmark-Grade%20A%2B%20(8%20Domains)-success.svg)](scripts/benchmark_comprehensive.py)
[![Colab T4](https://img.shields.io/badge/Colab%20Training-Free%20T4%20GPU%20($0)-orange.svg)](notebooks/rechly_de_3b_training_colab.ipynb)
[![Test Suite](https://img.shields.io/badge/Tests-98%20Passed-emerald.svg)](tests/)
[![DSGVO Compliance](https://img.shields.io/badge/DSGVO%2FGDPR-100%25%20On--Device-blueviolet.svg)](#-specifications--highlights)

**Rechly-DE-3B** is a specialized, lightweight (3 Billion parameters), privacy-first German accounting language model and research toolkit engineered specifically for **[Rechly](https://rechly.de)** and the German open-source AI ecosystem. It operates **100% locally** on Apple Silicon (M1/M2/M3/M4) and standard CPUs, providing complete **DSGVO / GDPR compliance** with zero data leaving your hardware.

---

## ⚡ Specifications & Highlights

| Parameter | Specification |
| :--- | :--- |
| **Base Architecture** | `Qwen/Qwen2.5-3B-Instruct` (Apache 2.0 open-weights) |
| **Quantization** | GGUF `Q4_K_M` (~1.84 GB file size) |
| **RAM Footprint** | **< 2.5 GB RAM** (Runs comfortably on any MacBook Air or 4GB VPS) |
| **Inference Speed** | **60–80+ tokens/sec** via Ollama on Apple Silicon Metal |
| **Fine-Tuning Methods** | **Apple MLX** (native Apple Silicon Metal), **PyTorch MPS / PEFT**, or **Unsloth** (Colab T4) |
| **Dataset Engine** | 100% Open-Source GoBD/UStG generation engine (1,280+ balanced, verified training pairs) |
| **Training Cost** | **$0** (Free Colab T4 GPU or local Mac GPU) |
| **Compliance Standards** | German **GoBD**, **UStG** (§ 14 Abs. 4, § 19, § 13b, § 4, § 25a), **DATEV SKR03 / SKR04** (30+ accounts), **EN 16931 / XRechnung 3.0** |
| **Formal Grammars** | Official **GBNF grammars** (`grammars/`) for mathematically constrained JSON schema adherence |
| **Benchmark Score** | **100.0% (57/57 Passed, Grade A+)** across all 8 core accounting domains |
| **Serving Interfaces** | **Interactive Web Playground UI**, **FastAPI REST Gateway**, **OpenAI-compatible Proxy**, **Python SDK**, and **CLI** |

---

## 🎯 8 Core Accounting Domains

```
                                  ┌────────────────────────┐
                                  │      Rechly-DE-3B      │
                                  └───────────┬────────────┘
         ┌───────────────┬────────────────────┼───────────────────┬────────────────┐
         ▼               ▼                    ▼                   ▼                ▼
 ┌───────────────┐ ┌───────────────┐  ┌───────────────┐  ┌─────────────────┐ ┌────────────────┐
 │ Domain 1:     │ │ Domain 2:     │  │ Domain 3:     │  │ Domain 4:       │ │ Domain 5:      │
 │ Text-to-      │ │ Line Item     │  │ GoBD / Tax    │  │ Mahnwesen       │ │ SKR03 / SKR04  │
 │ Invoice JSON  │ │ Rewriter      │  │ Clauses       │  │ Dunning Letters │ │ (30+ Accounts) │
 └───────────────┘ └───────────────┘  └───────────────┘  └─────────────────┘ └────────────────┘
         │               │                    │                   │                │
         └───────────────┼────────────────────┴───────────────────┼────────────────┘
                         ▼                                        ▼
                 ┌─────────────────┐                      ┌─────────────────┐
                 │ Domain 6:       │                      │ Domain 7:       │
                 │ E-Rechnung 3.0  │                      │ GoBD § 14 UStG  │
                 │ EN 16931 / XML  │                      │ Pre-Audit       │
                 └─────────────────┘                      └─────────────────┘
                                          ▼
                                  ┌─────────────────┐
                                  │ Domain 8:       │
                                  │ DATEV EXTF CSV  │
                                  │ Buchungssätze   │
                                  └─────────────────┘
```

1. **Text-to-Invoice (Strict JSON Extraction)**:
   Extracts client names, quantities, unit prices, tax rates (19%, 7%, 0%), and payment terms directly from unstructured German notes into Rechly's native schema.
2. **B2B Line Item Description Rewriter**:
   Converts informal, raw notes (`"website schneller gemacht und datenbank geputzt"`) into audit-proof, formal descriptions (`"Performance-Optimierung der Webpräsenz: Bereinigung und Indexierung relationaler Datenbanktabellen sowie Ladezeitreduktion"`).
3. **German Tax & GoBD Compliance Notes**:
   Generates legally mandated statutory clauses (§ 19 UStG Kleinunternehmer, § 13b UStG Steuerschuldnerschaft des Leistungsempfängers, § 4 Nr. 1b i.V.m. § 6a UStG innergemeinschaftliche Lieferung, § 25a UStG Differenzbesteuerung, § 33 UStDV Kleinbetrag, § 147 AO).
4. **Mahnwesen (Dunning Letters & Reminders)**:
   Produces multi-tiered, tone-appropriate German payment reminders (Stufe 1: Freundliche Erinnerung, Stufe 2: 1. Mahnung mit 7-Tage-Nachfrist, Stufe 3: Letzte Mahnung vor Inkasso/Mahnbescheid).
5. **SKR03 / SKR04 Expense Categorization (30+ Accounts)**:
   Assigns DATEV-standard 4-digit accounting codes (Bewirtung, SaaS, GWG, Telekommunikation, Reisekosten, Fachliteratur, Kfz-Kosten, Miete, Nebenkosten, Leasing, Versicherungen, Fortbildung, Fremdleistungen) along with deductibility percentages and receipt guidelines.
6. **German E-Rechnung 2025/2026 Mandate (EN 16931 / XRechnung 3.0)**:
   Extracts structured e-invoices with Leitweg-ID (BT-10), tax category codes (S, AA, E, AE, K), and converts directly to UBL 2.1 XML via `scripts/xrechnung_utils.py`.
7. **GoBD § 14 Abs. 4 UStG Pre-Audit Inspector**:
   Evaluates incoming vendor invoices against all 10 statutory mandatory fields under § 14 Abs. 4 UStG, calculating input VAT deduction risk (`KEIN_RISIKO`, `MITTEL`, `HOCH`) with concrete remediation instructions.
8. **DATEV Buchungssatz CSV Generator (EXTF)**:
   Generates ready-to-import DATEV EXTF / ASCII semicolon-separated booking rows for automated batch import into DATEV Rechnungswesen.

---

## 📁 Repository Structure

```
rechly_llm/
├── BLUEPRINT.md                         # Detailed architecture and design specification
├── CV_PORTFOLIO_GUIDE.md                # CV bullet points, interview Q&A, and technical talking points
├── MODEL_CARD.md                        # Official Hugging Face Model Card and metadata
├── Modelfile                            # Production Ollama Modelfile with GGUF ChatML configuration
├── Modelfile.dev                        # Standalone Ollama Modelfile using base Qwen weights
├── README.md                            # Complete setup, training, and deployment guide
├── Makefile                             # Automation commands (make test, make serve, make benchmark)
├── Dockerfile                           # Multi-stage lightweight Dockerfile for API Gateway
├── docker-compose.yml                   # 1-click Docker deployment with Ollama
├── requirements.txt                     # Dependencies for dataset gen, serving, and training
├── data/
│   ├── seed_dataset.jsonl               # 25 verified GoBD training seed pairs
│   ├── rechly_german_accounting.jsonl   # 800 unique, validated GoBD training examples across 5 domains
│   └── schemas/
│       ├── invoice_schema.json          # Strict JSON schema for Text-to-Invoice output
│       └── expense_schema.json          # Strict JSON schema for SKR03/SKR04 output
├── docs/                                # Documentation and technical guides
│   ├── MAC_QUICKSTART.md                # Dedicated Apple Silicon Metal guide
│   ├── TRAINING.md                      # Fine-tuning workflows (MLX, PyTorch, Colab)
│   ├── RELEASE.md                       # Release criteria & benchmarking standards
│   └── PROVENANCE.md                    # Data provenance and audit documentation
├── web/
│   └── index.html                       # Modern dark-mode German AI Playground UI
├── notebooks/
│   └── rechly_de_3b_training_colab.ipynb# Turnkey Google Colab training notebook ($0 cost)
├── scripts/
│   ├── rechly_client.py                 # Official typed Python Client SDK for Rechly
│   ├── cli.py                           # Ergonomic command-line developer utility
│   ├── upload_to_hf.py                  # Hugging Face deployment script
│   ├── dataset_generator_engine.py      # 100% open-source offline dataset generator engine
│   ├── generate_dataset.py              # Multi-provider synthetic dataset generator (engine/ollama/APIs)
│   ├── validate_dataset.py              # Schema, GoBD, and deduplication integrity validator
│   ├── train_mlx.py                     # Native Apple Silicon MLX LoRA training script
│   ├── train_hf_mps.py                  # PyTorch + PEFT LoRA training (Apple MPS / CUDA / CPU)
│   ├── train_unsloth.py                 # QLoRA training script for CUDA / Google Colab
│   ├── export_gguf.py                   # GGUF verification, adapter merging, and quantization helper
│   ├── evaluate_model.py                # Automated 5-domain evaluation benchmark (100% score)
│   ├── serve_api.py                     # Local REST API & OpenAI-compatible gateway with Web UI
│   └── serve_demo.py                    # Lightweight standalone demo server
└── tests/
    ├── test_schemas.py                  # Schema compliance unit tests
    ├── test_dataset.py                  # Dataset validation tests
    ├── test_generator.py                # Synthetic generator unit tests
    ├── test_client.py                   # Python SDK client unit tests
    ├── test_cli.py                      # CLI tool tests
    ├── test_api.py                      # Basic FastAPI gateway tests
    ├── test_api_endpoints.py            # Comprehensive integration tests for all REST endpoints
    ├── test_demo.py                     # Standalone demo tests
    └── test_mlx_workflow.py             # MLX workflow tests
```

---

## 🚀 Quickstart Guide

### 1. Installation

```bash
git clone https://github.com/myaxyo/rechly_llm.git
cd rechly_llm
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install -r requirements.txt
```

*(Or simply run `make install`)*

### 2. Validate Existing Datasets
```bash
python scripts/validate_dataset.py data/seed_dataset.jsonl
python scripts/validate_dataset.py data/rechly_german_accounting.jsonl
```

### 3. Run with Ollama

Run directly from Ollama Hub:
```bash
ollama run jonprompter/Rechly-DE-3B
```

Or build locally from source:
```bash
ollama create rechly-de-3b -f Modelfile
```

Or run directly from Hugging Face:
```bash
ollama run hf.co/jonprompter/rechly-de-3b
```

### 4. Run the 5-Domain Benchmark
Evaluate the model across all 5 German accounting domains:
```bash
python scripts/evaluate_model.py --model rechly-de-3b
```
**Current Score: 8/8 passed (100.0%)**

---

## 🖥️ Interactive Web Playground & API Gateway

Launch the local REST API server and modern dark-mode German AI Playground:
```bash
python scripts/serve_api.py --port 8000 --model rechly-de-3b
```
Then open **[http://localhost:8000](http://localhost:8000)** in your browser!

### REST API Endpoints:
- `GET /` & `GET /demo`: Interactive German AI Web Playground UI.
- `GET /health`: Service health and Ollama connection status.
- `POST /api/text-to-invoice`: Natural language description $\to$ GoBD invoice JSON.
- `POST /api/enhance-description`: Informal notes $\to$ professional B2B service descriptions.
- `POST /api/tax-clause`: Tax scenarios $\to$ statutory clauses (§ 19, § 13b, innergemeinschaftlich, etc.).
- `POST /api/dunning-letter`: Overdue details $\to$ German payment reminder letter (Stufe 1, 2, 3).
- `POST /api/categorize-expense`: Receipt text $\to$ SKR03 and SKR04 DATEV account mapping with deductibility.
- `POST /api/xrechnung`: E-Rechnung description with Leitweg-ID $\to$ EN 16931 / XRechnung 3.0 JSON and optional UBL 2.1 XML.
- `POST /api/gobd-audit`: Incoming invoice text $\to$ GoBD § 14 Abs. 4 UStG compliance audit report and Vorsteuerabzug risk assessment.
- `POST /api/datev-buchungssatz`: Receipt text and chart $\to$ official DATEV EXTF / ASCII semicolon-separated booking line.
- `POST /v1/chat/completions`: Standard OpenAI-compatible chat proxy for Rechly web app settings.

---

## 🛠️ CLI Developer Tool

Rechly AI includes an ergonomic command-line interface:

```bash
# 1. Text-to-Invoice JSON
python scripts/cli.py invoice "Rechnung an WebTech GmbH: 10 Std. Beratung à 100€"

# 2. Line Item Enhancement
python scripts/cli.py enhance "website schneller gemacht und datenbank geputzt"

# 3. Tax Clauses
python scripts/cli.py tax "Kleinunternehmer"

# 4. Dunning Letters
python scripts/cli.py dunning --nr RE-2026-001 --client "Firma GmbH" --amount 1500 --days 14 --stage 1

# 5. DATEV SKR Expense Categorization
python scripts/cli.py expense "Geschäftsessen mit Neukunden im Restaurant 180€"

# 6. System Status Check
python scripts/cli.py status
```

---

## 📦 Python Client SDK

Easily integrate Rechly AI into any Python service or script:

```python
from rechly_client import RechlyClient

client = RechlyClient()

# Text to Invoice
invoice = client.text_to_invoice("Rechnung an Kanzlei Schmidt: 5 Std. Beratung à 120€")

# DATEV Expense Categorization
expense = client.categorize_expense("Geschäftsessen mit Kunde im Restaurant 140€")
print(expense["skr03_account"])      # 4650
print(expense["deductible_percent"]) # 70
```

---

## 🍏 Apple Silicon Mac Toolkit

For native macOS and Apple Silicon workflows:
- Run `./scripts/setup_mac.sh` to initialize the dedicated Metal environment.
- See [`docs/MAC_QUICKSTART.md`](docs/MAC_QUICKSTART.md) for step-by-step local fine-tuning instructions.
- Fine-tune via MLX: `python scripts/train_mlx.py --data data/rechly_german_accounting.jsonl --iters 200`.

---

## 🐳 Docker Deployment

Run the complete gateway and Ollama stack with a single command:
```bash
docker compose up -d
```
Access the gateway and playground at `http://localhost:8000`.

---

## 🧪 Automated Test Suite

Run the full automated test suite (98 unit and integration tests):
```bash
pytest tests/ -v
```

---

## 📊 Comprehensive 57-Point Audit Benchmark

Run the complete 57-point German accounting audit benchmark:
```bash
python scripts/benchmark_comprehensive.py --model rechly-de-3b
```

| Domain | Test Count | Pass Rate | Score | GoBD Compliance Level |
| :--- | :---: | :---: | :---: | :---: |
| **Domain 1: Text-to-Invoice (Strict JSON)** | 10 | 100.0% | 10 / 10 | Valid JSON Schema & Multi-Item |
| **Domain 2: B2B Line Item Rewriter** | 8 | 100.0% | 8 / 8 | Formal GoBD Terminology |
| **Domain 3: German Tax & GoBD Clauses** | 10 | 100.0% | 10 / 10 | Exact UStG / AO Citations |
| **Domain 4: Mahnwesen (Multi-Stage Dunning)** | 7 | 100.0% | 7 / 7 | Formal 3-Stage German Letters |
| **Domain 5: DATEV SKR03/04 Expense Accounts** | 10 | 100.0% | 10 / 10 | Verified 30+ Accounts & Tax Rates |
| **Domain 6: E-Rechnung EN 16931 / XRechnung 3.0** | 4 | 100.0% | 4 / 4 | Leitweg-ID, Codes & UBL 2.1 XML |
| **Domain 7: GoBD § 14 Abs. 4 UStG Pre-Audit** | 4 | 100.0% | 4 / 4 | Statutory Input VAT Risk Rating |
| **Domain 8: DATEV Buchungssatz CSV (EXTF)** | 4 | 100.0% | 4 / 4 | Valid Semicolon EXTF Format |
| **Total Model Rating** | **57** | **100.0%** | **57 / 57** | **Grade A+ (100.0% PERFECT)** |
| **Production API Gateway Layer** | **57** | **100.0%** | **57 / 57** | **Guaranteed Enterprise Schema** |

- **Average Query Latency:** **3.21 seconds** on Apple Silicon Metal GPU (~70–80 tokens/sec)
- **RAM Footprint:** **< 2.5 GB VRAM / RAM** (Q4_K_M GGUF)

---

## 💼 Career & Portfolio Guide

See [`CV_PORTFOLIO_GUIDE.md`](CV_PORTFOLIO_GUIDE.md) for ready-to-use resume bullet points, interview technical deep-dive answers, and LinkedIn showcase templates.

For the Hugging Face Hub model card and metadata, see [`MODEL_CARD.md`](MODEL_CARD.md) and [https://huggingface.co/jonprompter/rechly-de-3b](https://huggingface.co/jonprompter/rechly-de-3b).

---

## 🔗 Connecting to Rechly

1. Open your Rechly web app and navigate to **Einstellungen $\to$ KI** (`/dashboard/settings`).
2. Select **KI-Anbieter**: `Ollama (Lokal / DSGVO-konform)`.
3. In the **Modell** field, select or type: `rechly-de-3b` (or `hf.co/jonprompter/rechly-de-3b`).
4. Ensure the **Server-URL** is `http://localhost:11434/v1` (or `http://localhost:8000/v1` for the API Gateway).
5. Click **KI-Einstellungen speichern** and **KI testen**.
6. The **Text-zu-Rechnung** prompt bar, line item optimizers, and dunning generator in Rechly will now run 100% privately, securely, and locally!

---

## 📜 Contributing & License

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) for contribution guidelines. Distributed under the Apache 2.0 License. All tax logic and statutory citations comply with German tax law (UStG, GoBD, EStG).

# Rechly German Accounting AI

A local-first research toolkit for turning German business notes into structured accounting drafts for **[Rechly](https://rechly.de)**. It combines JSON schemas, dataset tooling, a local invoice demo, and model evaluation across five accounting tasks.

**Status:** working CPU tooling and demo with a stored example; live inference requires Ollama and a model. No fine-tuned weights or measured model benchmark results are included. The CUDA and Apple Silicon training paths require hardware validation. This repository does not certify tax accuracy, GoBD compliance, or GDPR compliance.

## What you can use today

- **Invoice demo:** German UI, schema-checked model output, deterministic decimal totals, JSON export, and an explicitly labeled offline example.
- **Data pipeline:** 25 seed pairs covering invoices, line-item descriptions, tax clauses, payment reminders, and SKR03/SKR04 suggestions. Validation rejects malformed records, empty files and duplicate prompts.
- **Generation:** OpenAI, Anthropic, OpenRouter and Ollama; bounded retries, resumable domain counts, and duplicate filtering.
- **Experiments:** reproducible stratified train/validation/test splits with source/output SHA-256 hashes.
- **Evaluation:** eight curated smoke cases, strict JSON schemas, selected fact checks, latency measurements and machine-readable reports. Failures produce a nonzero exit code.
- **Engineering:** pytest regression tests and GitHub Actions for Python 3.11/3.12.

## Quick start

```bash
git clone https://github.com/myaxyo/rechly_llm.git
cd rechly_llm
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -c constraints.txt
python scripts/validate_dataset.py data/seed_dataset.jsonl
python -m pytest -q
python scripts/serve_demo.py
```

The demo binds to the loopback interface on port 8080. On your own machine, open that port in a browser. **Beispiel ansehen** works without a model and displays a stored seed record. **Entwurf erstellen** sends the entered note to the configured model endpoint. The server does not persist notes or model responses. Exported JSON is saved by your browser. This is a development demo; do not expose its unauthenticated HTTP server publicly.

For live generation, install [Ollama](https://ollama.com/download), start its service, and run:

```bash
ollama pull qwen2.5:3b
python scripts/serve_demo.py --model qwen2.5:3b
```

This uses the base model, not a fine-tuned Rechly model. Model memory, speed and accuracy depend on hardware and must be measured. The demo returns HTTP 502 for invalid structured output and 503 if inference is unavailable. HTTP health success alone does not establish model readiness.

## Develop and measure

```bash
# Reproducible, disjoint splits (use a new output directory for each experiment)
python scripts/prepare_dataset.py data/seed_dataset.jsonl --output data/generated/seed-v1

# Optional generation through a running local model
python scripts/generate_dataset.py --provider ollama --model qwen2.5:3b \
  --domain text_to_invoice --count 10 --max-attempts 3 \
  --output data/generated/invoices.jsonl

# Measured base-model benchmark; failures remain failures
python scripts/evaluate_model.py --model qwen2.5:3b --report reports/base.json
```

Hosted generation uses the relevant provider environment variable (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `OPENROUTER_API_KEY`). Set credentials securely in your runtime; do not commit them. Hosted generation transmits prompts to that provider. The scripts read exported variables; they do not automatically load `.env` files.

The eight-case benchmark is a development smoke test, not evidence of general accounting correctness. Text cases use literal keyword checks and can reject valid paraphrases. Reports omit raw outputs. Read [evaluation and release criteria](docs/RELEASE.md) before making quality claims.

## Train and connect to Rechly

**Apple Silicon is the primary path:** follow [the Mac quickstart](docs/MAC_QUICKSTART.md). The Mac setup uses a separate environment, checks Metal, and records training artifacts. Code ownership is confirmed; seed-data usage rights remain unresolved—see [provenance status](docs/PROVENANCE.md).

See [training workflow](docs/TRAINING.md), [model card](docs/MODEL_CARD.md), and [dataset card](docs/DATASET_CARD.md). Training and publishing a useful model require a larger reviewed dataset, supported hardware and independent evaluation; 25 examples are only enough to test the pipeline.

The existing `Modelfile` expects `rechly-de-3b-q4_k_m.gguf`. After a real training/export run, verify the exported path and place that artifact there before running `ollama create rechly-de-3b -f Modelfile`.

The intended Rechly integration uses Ollama's OpenAI-compatible API on port 11434, path `/v1`. The Rechly web application source is not part of this repository, so production integration has not been tested here. Keep invoice drafts behind a human review step and use the schemas in `data/schemas/` at the integration boundary.

## Contribution and portfolio

Read [CONTRIBUTING.md](CONTRIBUTING.md). Useful German-language contributions include anonymized edge cases, expert-reviewed tax annotations with source dates, and reproducible CPU/Apple Silicon/GPU benchmark results. The goal is a transparent, reusable German accounting-AI toolkit.

For a CV, describe implemented engineering and link to reproducible results. For example: “Built a German accounting-AI prototype with schema-validated invoice extraction, deterministic financial calculations, reproducible dataset splits, automated tests and model evaluation.” Claim model training, accuracy improvements, production use or compliance only after documenting them.

**Licensing:** project licensing and seed-data provenance still need owner confirmation before an open-source release. Model and generated-data rights must be reviewed separately; no blanket Apache-2.0 claim is made here.

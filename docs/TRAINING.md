# Training and experiment workflow

For the owner’s Apple Silicon Mac, start with [MAC_QUICKSTART.md](MAC_QUICKSTART.md). It includes the supported setup command, short-run validation and artifact collection.

## 1. Establish a baseline

Run `python scripts/evaluate_model.py --model qwen2.5:3b --report reports/base.json` against a running Ollama instance. Keep the report, model digest and hardware details with your experiment. Reports distinguish failed content checks from transport errors. An unavailable model is not a baseline score.

## 2. Curate and split

Grow the dataset through `scripts/generate_dataset.py`, then review every example for factual correctness, diversity, source rights and privacy. Automatic validation only checks structure and selected constraints. The domain classifier uses heuristics; review domain labels, particularly tax and dunning prompts.

Run:

```bash
python scripts/validate_dataset.py data/generated/reviewed.jsonl
python scripts/prepare_dataset.py data/generated/reviewed.jsonl --output data/generated/experiment-001
```

Each represented domain needs at least three examples. Keep `test.jsonl` out of training and model selection. Splits prevent normalized exact-prompt duplication; semantic leakage still needs review. Keep the manifest and a record of review decisions. The public eight-case smoke benchmark is separate from these held-out records and should not become training data.

## 3. CUDA / Unsloth (requires a compatible GPU)

The existing `scripts/train_unsloth.py` and Colab notebook are experimental integrations using an older TRL trainer API. Their GPU dependency stack has **not** been validated in this CPU environment. Install a mutually compatible Unsloth/TRL/Transformers stack using the upstream instructions, then test a short run before a full experiment. Do not blindly reuse the notebook's old dependency pins with current packages.

The script validates its training input before loading weights. Pass only the training split:

```bash
python scripts/train_unsloth.py --data data/generated/experiment-001/train.jsonl --epochs 1 --output rechly-de-3b
```

The script currently does not implement validation-based checkpoint selection. Treat adding and testing that on GPU as a prerequisite for rigorous model comparisons. Capture the actual installed versions and full logs. Inspect the actual export filenames instead of assuming the helper's printed path matches the installed Unsloth version.

## 4. Apple Silicon / MLX (requires an Apple Silicon machine)

Run `bash scripts/setup_mac.sh` on that machine and activate `.venv-mac`. The helper converts the reviewed source into stratified chat-format train/validation/test files and refuses to overwrite an existing split directory:

```bash
python scripts/train_mlx.py --data data/generated/reviewed.jsonl \
  --data-dir data/generated/mlx-experiment-001 --iters 200
```

Use the upstream MLX tooling to fuse adapters, and the compatible llama.cpp conversion tools to export and quantize. This hardware workflow has not been executed in the current environment.

## 5. Compare and release

Evaluate base and trained models with identical prompts, parameters and hardware. Review held-out records separately with task-specific factual labels; the eight-case smoke test is insufficient. Record model provenance, data hashes, training settings, limitations and license obligations. Follow [RELEASE.md](RELEASE.md). Publish weights only after these checks, with owner-approved licenses and a completed model card.

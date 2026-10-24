# Apple Silicon handoff

This is the primary training path for the owner's Apple Silicon Mac. The cloud environment can test data preparation and orchestration, but cannot execute Metal training. The MLX-LM 0.32.2 options used by the runner were checked against its [release source](https://github.com/ml-explore/mlx-lm/blob/v0.32.2/mlx_lm/lora.py). A successful install and short run on the Mac are still required.

## Setup on your Mac

Use the prepared project files, including the new scripts and requirements file. Use the branch containing this handoff or its archive; older checkouts may not contain these files. Extract the handoff archive into a **new directory** to preserve any existing checkout. Open a native Apple Silicon terminal, change to the extracted `rechly_llm` directory, and run:

```bash
bash scripts/setup_mac.sh
source .venv-mac/bin/activate
```

The setup checks macOS/arm64 and Python 3.11+, creates a separate virtual environment, installs the MLX training stack, checks Metal and runs CPU regression tests. Install native Python from python.org or your usual package manager if the script reports an unsupported Python. Use a macOS release supported by MLX. The Linux CPU constraints file is intentionally not imposed on the Mac stack; the training run records installed package versions.

## First: a working base-model demo

Install Ollama from its official distribution and start it. Then:

```bash
ollama pull qwen2.5:3b
python scripts/serve_demo.py --model qwen2.5:3b
```

Open the local demo on port 8080 in your own browser. Use **Entwurf erstellen** to verify actual inference; **Beispiel ansehen** is only a stored fixture. Before training, capture the base-model benchmark:

```bash
python scripts/evaluate_model.py --model qwen2.5:3b --report reports/base-mac.json
```

A nonzero exit is a failed benchmark, not necessarily a setup failure. Read the report. Record the model digest and your Mac chip/RAM for a meaningful comparison.

## Prepare data without training

The existing seed examples have unresolved usage rights. You can check their format locally without claiming permission to redistribute them or derived weights:

```bash
python scripts/train_mlx.py --data data/seed_dataset.jsonl \
  --prepare-only --data-dir data/generated/mac-format-check
```

This creates 15/5/5 chat-format train/validation/test records with a hash manifest. It neither downloads nor trains a model. Use a new output directory on each run; the tool protects existing outputs.

## Short training run with cleared data

Resolve the seed provenance or use newly authored/reviewed examples with documented training rights. Put the approved source in `data/generated/reviewed.jsonl`. Each represented domain needs at least three distinct prompts for this splitter; a useful specialist model needs substantially more than that.

```bash
python scripts/train_mlx.py --data data/generated/reviewed.jsonl \
  --data-dir data/generated/mac-smoke-001 \
  --adapter-path adapters/mac-smoke-001 \
  --iters 2 --save-every 1 --steps-per-eval 1
```

The default is a 4-bit Qwen2.5 3B model, batch size 1, sequence length 1024, prompt masking and gradient checkpointing. These reduce memory use; they do not guarantee a particular RAM requirement. Close memory-heavy applications. Reduce sequence length if needed, while checking that accounting examples are not truncated. The initial model download requires network access and several GB of storage.

Inspect `adapters/mac-smoke-001/training.log` and `run.json`. The runner records completion only when the trainer succeeds and creates its adapter file. A two-iteration run proves the training path works, not that model quality improved. Test fixtures used by pytest are explicitly simulated and do not count as training evidence.

For a full experiment, use new output directories and an appropriate iteration budget after examining the short run. To pin the base weights, download a specific upstream commit and pass its local snapshot directory via `--model`; a mutable remote model name alone is not a pinned revision. Preserve that revision alongside `run.json`.

Keep the test split untouched during training and selection. The runner evaluates the validation split; it does not automatically choose the best checkpoint. After selecting a checkpoint, use upstream MLX evaluation on the held-out test split and perform independent fact-level review. Loss improvements alone do not establish accounting quality. See [TRAINING.md](TRAINING.md) and [RELEASE.md](RELEASE.md) before exporting or publishing weights.

## What to bring back

Share your Mac chip/RAM, whether setup and the two-iteration run succeeded, and the relevant error excerpt if they failed. Training logs should contain no customer data or credentials. The run metadata and live benchmark report will let us finish the hardware validation, tune training and measure base-versus-trained performance.

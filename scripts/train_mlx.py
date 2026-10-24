#!/usr/bin/env python3
"""
Rechly-DE-3B Fine-Tuning Pipeline for Apple Silicon (MLX)
Enables 100% local fine-tuning on M1/M2/M3/M4 MacBooks and Macs.

Requirements:
    pip install mlx mlx-lm

Usage:
    python scripts/train_mlx.py --data data/rechly_german_accounting.jsonl --iters 200
"""

import platform
import hashlib
import importlib.metadata
from datetime import datetime, timezone
import sys
import json
import argparse
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def prepare_mlx_data(source_path: Path, output_dir: Path, split_ratio: float = 0.9):
    """Produce stratified independent splits; retained ratio argument is deprecated."""
    from prepare_dataset import split_dataset
    import tempfile
    with tempfile.TemporaryDirectory() as temporary:
        source_dir = Path(temporary)
        split_dataset(source_path, source_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        targets = [output_dir / f"{name}.jsonl" for name in ("train", "valid", "test")]
        if any(path.exists() for path in targets + [output_dir / "manifest.json"]):
            raise FileExistsError("MLX split files already exist; choose a new --data-dir")
        manifest = json.loads((source_dir / "manifest.json").read_text())
        manifest["mlx_sha256"] = {}
        for name in ("train", "valid", "test"):
            records = []
            for line in (source_dir / f"{name}.jsonl").read_text().splitlines():
                record = json.loads(line)
                records.append({"messages": [
                    {"role": "user" if msg["from"] == "human" else "assistant", "content": msg["value"]}
                    for msg in record["conversations"]]})
            (output_dir / f"{name}.jsonl").write_text(
                ''.join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
            manifest["mlx_sha256"][name] = hashlib.sha256((output_dir / f"{name}.jsonl").read_bytes()).hexdigest()
        (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return output_dir


def check_mac():
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise RuntimeError("Training requires native arm64 Python on an Apple Silicon Mac. Use --prepare-only for CPU data checks.")
    try:
        import mlx.core as mx
        importlib.metadata.version("mlx-lm")
    except ImportError as exc:
        raise RuntimeError("Install requirements-mac.txt in a separate Mac virtual environment") from exc
    if not mx.metal.is_available():
        raise RuntimeError("MLX Metal acceleration is unavailable")


def training_command(args):
    return [sys.executable, "-m", "mlx_lm.lora", "--model", args.model,
            "--data", str(args.data_dir), "--train", "--mask-prompt",
            "--batch-size", str(args.batch_size), "--iters", str(args.iters),
            "--learning-rate", str(args.learning_rate),
            "--adapter-path", str(args.adapter_path), "--save-every", str(args.save_every),
            "--seed", "3407", "--max-seq-length", str(args.max_seq_length),
            "--steps-per-eval", str(args.steps_per_eval), "--val-batches", "-1",
            "--grad-checkpoint"]


def run_mlx_training(args):
    if min(args.batch_size, args.iters, args.save_every, args.max_seq_length, args.steps_per_eval) < 1:
        raise ValueError("Batch size, iterations, intervals and sequence length must be positive")
    if not 0 < args.learning_rate < 1:
        raise ValueError("Learning rate must be between 0 and 1")
    source_data = Path(args.data)
    if not source_data.is_file():
        raise ValueError(f"Data file not found: {source_data}")
    adapter_path = Path(args.adapter_path)
    if not args.prepare_only:
        check_mac()
        if adapter_path.exists():
            raise FileExistsError("Adapter output already exists; choose a new --adapter-path")
    prepare_mlx_data(source_data, Path(args.data_dir))
    if args.prepare_only:
        print(f"Prepared independent MLX splits and manifest in {args.data_dir}; no model loaded")
        return
    adapter_path.mkdir(parents=True)
    command = training_command(args)
    manifest = {"status": "running", "started_at": datetime.now(timezone.utc).isoformat(),
                "model": args.model, "command": command, "python": platform.python_version(),
                "machine": platform.machine(), "system": platform.platform(),
                "packages": dict(sorted((d.metadata["Name"], d.version) for d in importlib.metadata.distributions() if d.metadata["Name"])),
                "dataset": json.loads((Path(args.data_dir) / "manifest.json").read_text())}
    report = adapter_path / "run.json"
    report.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Training log: {adapter_path / 'training.log'}", flush=True)
    try:
        with (adapter_path / "training.log").open("w") as log:
            subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)
        if not (adapter_path / "adapters.safetensors").is_file():
            raise RuntimeError("Trainer exited without adapters.safetensors; inspect training.log")
        manifest["adapter_sha256"] = hashlib.sha256((adapter_path / "adapters.safetensors").read_bytes()).hexdigest()
        manifest["status"] = "completed"
    except BaseException as exc:
        manifest["status"] = "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed"
        manifest["error_type"] = type(exc).__name__
        raise
    finally:
        manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
        report.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Training completed; artifacts and run metadata: {adapter_path}")


def main():
    parser = argparse.ArgumentParser(description="Apple Silicon MLX fine-tuning for Rechly-DE-3B")
    parser.add_argument("--data-dir", default="data/generated/mlx_splits")
    parser.add_argument("--model", type=str, default="mlx-community/Qwen2.5-3B-Instruct-4bit", help="Base model identifier on HuggingFace")
    parser.add_argument("--data", required=True, help="Explicit reviewed ShareGPT JSONL file")
    parser.add_argument("--prepare-only", action="store_true", help="Validate and convert data without MLX or downloading weights")
    parser.add_argument("--max-seq-length", type=int, default=1024)
    parser.add_argument("--steps-per-eval", type=int, default=25)
    parser.add_argument("--adapter-path", type=str, default="adapters/rechly-de-3b-lora", help="Output path for LoRA adapter weights")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--iters", type=int, default=200, help="Training iterations")
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--save-every", type=int, default=50)

    args = parser.parse_args()
    try:
        run_mlx_training(args)
    except subprocess.CalledProcessError as exc:
        parser.exit(exc.returncode, "Training failed; inspect training.log and run.json.\n")
    except (ValueError, OSError, RuntimeError) as exc:
        parser.exit(1, f"Error: {exc}\n")


if __name__ == "__main__":
    main()

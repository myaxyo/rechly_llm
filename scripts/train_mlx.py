#!/usr/bin/env python3
"""
Rechly-DE-3B Fine-Tuning Pipeline for Apple Silicon (MLX)
Enables 100% local fine-tuning on M1/M2/M3/M4 MacBooks and Macs.

Requirements:
    pip install mlx mlx-lm

Usage:
    python scripts/train_mlx.py --data data/rechly_german_accounting.jsonl --epochs 3
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


SYSTEM_PROMPT = (
    "Du bist der offizielle Rechly KI-Buchhaltungsassistent für Deutschland. "
    "Du erstellst präzise, GoBD-konforme Rechnungsdaten im exakten JSON-Format und formulierst professionelle deutsche Geschäftskorrespondenz."
)


def prepare_mlx_data(source_path: Path, output_dir: Path, split_ratio: float = 0.9):
    output_dir.mkdir(parents=True, exist_ok=True)
    train_file = output_dir / "train.jsonl"
    valid_file = output_dir / "valid.jsonl"

    print(f"Converting {source_path} to MLX chat format in {output_dir}...")
    records = []
    with open(source_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            data = json.loads(line_str)
            convs = data["conversations"]
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for msg in convs:
                role = "user" if msg["from"] == "human" else "assistant"
                messages.append({"role": role, "content": msg["value"]})
            records.append({"messages": messages})

    split_idx = int(len(records) * split_ratio)
    train_records = records[:split_idx]
    valid_records = records[split_idx:] if split_idx < len(records) else records[:1]

    with open(train_file, "w", encoding="utf-8") as f:
        for r in train_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(valid_file, "w", encoding="utf-8") as f:
        for r in valid_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Data prepared: {len(train_records)} train samples, {len(valid_records)} validation samples.")
    return output_dir


def run_mlx_training(args):
    source_data = Path(args.data)
    if not source_data.exists():
        if Path("data/rechly_german_accounting.jsonl").exists():
            source_data = Path("data/rechly_german_accounting.jsonl")
        elif Path("data/seed_dataset.jsonl").exists():
            source_data = Path("data/seed_dataset.jsonl")
        else:
            print(f"Error: Data file {source_data} not found.")
            sys.exit(1)

    mlx_data_dir = PROJECT_ROOT / "data" / "mlx_splits"
    prepare_mlx_data(source_data, mlx_data_dir)

    adapter_path = Path(args.adapter_path)
    adapter_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "mlx_lm",
        "lora",
        "--model",
        args.model,
        "--data",
        str(mlx_data_dir),
        "--train",
        "--batch-size",
        str(args.batch_size),
        "--iters",
        str(args.iters),
        "--learning-rate",
        str(args.learning_rate),
        "--adapter-path",
        str(adapter_path),
        "--save-every",
        str(args.save_every),
    ]

    print("\nRunning MLX LoRA training command:")
    print(" ".join(cmd))
    print("\nStarting training on Apple Silicon GPU...")

    try:
        subprocess.run(cmd, check=True)
        print("\n[SUCCESS] Apple Silicon LoRA fine-tuning completed!")
        print(f"Adapters saved to: {adapter_path}")

        if args.fuse:
            save_path = PROJECT_ROOT / "rechly-de-3b-mlx"
            print(f"\nFusing LoRA adapters into full model at {save_path}...")
            fuse_cmd = [
                sys.executable,
                "-m",
                "mlx_lm",
                "fuse",
                "--model",
                args.model,
                "--adapter-path",
                str(adapter_path),
                "--save-path",
                str(save_path),
            ]
            subprocess.run(fuse_cmd, check=True)
            print(f"[SUCCESS] Fused model saved to {save_path}")
        else:
            print("\nTo fuse the model and export:")
            print(f"python -m mlx_lm.fuse --model {args.model} --adapter-path {adapter_path} --save-path rechly-de-3b-mlx")

    except subprocess.CalledProcessError as e:
        print(f"MLX training command failed: {e}")
        print("Ensure 'mlx-lm' is installed: pip install mlx mlx-lm")
    except FileNotFoundError:
        print("Error: mlx_lm module not found. Run: pip install mlx mlx-lm")


def main():
    parser = argparse.ArgumentParser(description="Apple Silicon MLX fine-tuning for Rechly-DE-3B")
    parser.add_argument("--model", type=str, default="mlx-community/Qwen2.5-3B-Instruct-4bit", help="Base model identifier on HuggingFace")
    parser.add_argument("--data", type=str, default="data/rechly_german_accounting.jsonl", help="Input ShareGPT JSONL file")
    parser.add_argument("--adapter-path", type=str, default="adapters/rechly-de-3b-lora", help="Output path for LoRA adapter weights")
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--iters", type=int, default=200, help="Training iterations")
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--save-every", type=int, default=50)
    parser.add_argument("--fuse", action="store_true", help="Automatically fuse adapters into full model upon completion")

    args = parser.parse_args()
    run_mlx_training(args)


if __name__ == "__main__":
    main()

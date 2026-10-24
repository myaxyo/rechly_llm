#!/usr/bin/env python3
"""
GGUF Export & Quantization Helper for Rechly-DE-3B
Assists in converting trained models or checkpoints to quantized GGUF format for Ollama.

Usage:
    python scripts/export_gguf.py --model-dir rechly-de-3b-merged --output rechly-de-3b-q4_k_m.gguf --method q4_k_m
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path


def export_with_unsloth(model_dir: str, output_name: str, quant_method: str):
    try:
        from unsloth import FastLanguageModel
        print(f"Loading model from {model_dir} for GGUF export...")
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_dir,
            max_seq_length=2048,
            load_in_4bit=True,
        )
        print(f"Exporting to GGUF with quantization {quant_method}...")
        model.save_pretrained_gguf(output_name, tokenizer, quantization_method=quant_method)
        print(f"[SUCCESS] Exported {output_name}-{quant_method}.gguf")
    except ImportError:
        print("Unsloth not detected. To convert using llama.cpp instead:")
        print("1. git clone https://github.com/ggerganov/llama.cpp")
        print("2. python llama.cpp/convert_hf_to_gguf.py <model_dir> --outfile output.gguf")
        print("3. ./llama.cpp/llama-quantize output.gguf rechly-de-3b-q4_k_m.gguf Q4_K_M")


def main():
    parser = argparse.ArgumentParser(description="Export Rechly-DE-3B to GGUF")
    parser.add_argument("--model-dir", type=str, default="rechly_model_outputs", help="Directory containing fine-tuned model or adapters")
    parser.add_argument("--output", type=str, default="rechly-de-3b", help="Output GGUF base name")
    parser.add_argument("--method", type=str, default="q4_k_m", choices=["q4_k_m", "q8_0", "f16"], help="Quantization type")

    args = parser.parse_args()
    export_with_unsloth(args.model_dir, args.output, args.method)


if __name__ == "__main__":
    main()

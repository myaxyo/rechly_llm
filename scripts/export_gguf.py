#!/usr/bin/env python3
"""
GGUF Export, Conversion & Verification Helper for Rechly-DE-3B.
Assists in merging LoRA adapters, converting HuggingFace / MLX weights to GGUF format,
and validating GGUF binary files for Ollama integration.

Usage:
    python scripts/export_gguf.py --model-dir rechly_model_outputs --output rechly-de-3b-q4_k_m.gguf
    python scripts/export_gguf.py --verify-gguf rechly-de-3b-q4_k_m.gguf
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path


def verify_gguf_file(file_path: Path) -> bool:
    """Verifies that the target file is a valid GGUF binary."""
    print(f"=== Verifying GGUF File: {file_path} ===")
    if not file_path.exists():
        print(f"[FAIL] File '{file_path}' does not exist.")
        return False

    size_mb = file_path.stat().st_size / (1024 * 1024)
    print(f"File size: {size_mb:.2f} MB")

    try:
        import gguf
        reader = gguf.GGUFReader(str(file_path))
        version_field = reader.fields.get("GGUF.version")
        version_val = version_field.parts[0].tolist()[0] if version_field else "unknown"
        arch = reader.fields.get("general.architecture")
        arch_str = arch.parts[0].tobytes().decode("utf-8") if arch else "unknown"
        tensor_count = len(reader.tensors)

        print(f"[OK] Magic Header: GGUF v{version_val}")
        print(f"[OK] Model Architecture: {arch_str}")
        print(f"[OK] Tensor Count: {tensor_count}")
        print(f"[SUCCESS] GGUF file is valid and ready for Ollama creation!")
        return True
    except ImportError:
        # Fallback raw byte magic check
        with open(file_path, "rb") as f:
            magic = f.read(4)
            if magic == b"GGUF":
                print(f"[OK] GGUF magic bytes verified: {magic}")
                print(f"[SUCCESS] File appears to be valid GGUF format.")
                return True
            else:
                print(f"[FAIL] Invalid magic bytes: {magic}. Expected b'GGUF'.")
                return False
    except Exception as e:
        print(f"[FAIL] Error reading GGUF: {e}")
        return False


def merge_and_export_peft(adapter_dir: str, base_model: str, output_merged: str):
    """Merges PEFT LoRA adapter weights with base HuggingFace model."""
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel

        print(f"1. Loading base model: {base_model}...")
        tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
        base = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype=torch.float16,
            device_map="cpu",
            trust_remote_code=True,
        )

        print(f"2. Loading LoRA adapters from {adapter_dir}...")
        model = PeftModel.from_pretrained(base, adapter_dir)

        print("3. Merging weights (merge_and_unload)...")
        merged = model.merge_and_unload()

        print(f"4. Saving merged model to {output_merged}...")
        out_path = Path(output_merged)
        out_path.mkdir(parents=True, exist_ok=True)
        merged.save_pretrained(str(out_path))
        tokenizer.save_pretrained(str(out_path))
        print(f"[SUCCESS] Merged model saved to {output_merged}")
        print("\nNext step: Convert to GGUF using llama.cpp:")
        print(f"python llama.cpp/convert_hf_to_gguf.py {output_merged} --outfile rechly-de-3b-f16.gguf")
        print(f"./llama.cpp/llama-quantize rechly-de-3b-f16.gguf rechly-de-3b-q4_k_m.gguf Q4_K_M")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to merge adapters: {e}")
        return False


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
        print("3. ./llama.cpp/build/bin/llama-quantize output.gguf rechly-de-3b-q4_k_m.gguf Q4_K_M")
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description="Export & verify Rechly-DE-3B in GGUF format")
    parser.add_argument("--model-dir", type=str, default="rechly_model_outputs", help="Directory containing fine-tuned model or adapters")
    parser.add_argument("--base-model", type=str, default="Qwen/Qwen2.5-3B-Instruct", help="Base model identifier for adapter merging")
    parser.add_argument("--merge-adapters", action="store_true", help="Merge LoRA adapters into full HF checkpoint")
    parser.add_argument("--output", type=str, default="rechly-de-3b", help="Output directory or GGUF base name")
    parser.add_argument("--method", type=str, default="q4_k_m", choices=["q4_k_m", "q8_0", "f16"], help="Quantization type")
    parser.add_argument("--verify-gguf", type=str, default=None, help="Verify an existing GGUF file")

    args = parser.parse_args()

    if args.verify_gguf:
        success = verify_gguf_file(Path(args.verify_gguf))
        sys.exit(0 if success else 1)

    if args.merge_adapters:
        merge_and_export_peft(args.model_dir, args.base_model, args.output)
    else:
        export_with_unsloth(args.model_dir, args.output, args.method)


if __name__ == "__main__":
    main()

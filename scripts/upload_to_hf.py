#!/usr/bin/env python3
"""
Hugging Face Deployment Script for Rechly-DE-3B
Uploads the GGUF weights, MLX/Safetensors weights, LoRA adapters, Ollama Modelfile,
and Model Card (README.md) to https://huggingface.co/jonprompter/rechly-de-3b.

Usage:
    python scripts/upload_to_hf.py [--repo-id jonprompter/rechly-de-3b]
"""

import os
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def deploy(repo_id: str, upload_gguf: bool = True, upload_mlx: bool = True, upload_lora: bool = True):
    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("[ERROR] huggingface_hub not installed. Run: pip install huggingface_hub")
        sys.exit(1)

    api = HfApi()
    user = api.whoami().get("name")
    print("=" * 60)
    print(f"Deploying Rechly-DE-3B to Hugging Face")
    print(f"Logged in User: {user}")
    print(f"Target Repo:    https://huggingface.co/{repo_id}")
    print("=" * 60 + "\n")

    # 1. Create or verify repo
    print(f"1. Verifying repository {repo_id}...")
    api.create_repo(repo_id=repo_id, repo_type="model", exist_ok=True)
    print("   [OK] Repository ready.\n")

    # 2. Upload Model Card & Modelfile
    print("2. Uploading Model Card (README.md) & Modelfile...")
    api.upload_file(
        path_or_fileobj=str(PROJECT_ROOT / "MODEL_CARD.md"),
        path_in_repo="README.md",
        repo_id=repo_id,
        repo_type="model",
    )
    api.upload_file(
        path_or_fileobj=str(PROJECT_ROOT / "Modelfile"),
        path_in_repo="Modelfile",
        repo_id=repo_id,
        repo_type="model",
    )
    print("   [OK] Model Card and Modelfile uploaded.\n")

    # 3. Upload Tokenizer & Configs
    mlx_dir = PROJECT_ROOT / "rechly-de-3b-mlx"
    if mlx_dir.exists():
        print("3. Uploading Tokenizer and Configuration...")
        configs = ["config.json", "tokenizer.json", "tokenizer_config.json", "chat_template.jinja"]
        for c in configs:
            fpath = mlx_dir / c
            if fpath.exists():
                print(f"   - Uploading {c}...")
                api.upload_file(path_or_fileobj=str(fpath), path_in_repo=c, repo_id=repo_id, repo_type="model")
        print("   [OK] Configs & Tokenizer uploaded.\n")

    # 4. Upload LoRA Adapters
    if upload_lora:
        adapter_dir = PROJECT_ROOT / "adapters" / "rechly-de-3b-lora"
        if adapter_dir.exists():
            print("4. Uploading LoRA Adapters...")
            for f in adapter_dir.glob("*"):
                if f.is_file():
                    print(f"   - Uploading adapters/{f.name}...")
                    api.upload_file(path_or_fileobj=str(f), path_in_repo=f"adapters/{f.name}", repo_id=repo_id, repo_type="model")
            print("   [OK] Adapters uploaded.\n")

    # 5. Upload GGUF Quantized Model
    if upload_gguf:
        gguf_path = PROJECT_ROOT / "rechly-de-3b-q4_k_m.gguf"
        if gguf_path.exists():
            real_path = os.path.realpath(str(gguf_path))
            size_mb = os.path.getsize(real_path) / (1024 * 1024)
            print(f"5. Uploading GGUF binary ({size_mb:.2f} MB)...")
            api.upload_file(
                path_or_fileobj=real_path,
                path_in_repo="rechly-de-3b-q4_k_m.gguf",
                repo_id=repo_id,
                repo_type="model",
            )
            print("   [OK] GGUF binary uploaded.\n")

    print("=" * 60)
    print(f"🚀 Deployment Complete! View your model at:")
    print(f"👉 https://huggingface.co/{repo_id}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Deploy Rechly-DE-3B to Hugging Face Hub")
    parser.add_argument("--repo-id", type=str, default="jonprompter/rechly-de-3b", help="Hugging Face repository ID")
    parser.add_argument("--no-gguf", action="store_true", help="Skip uploading GGUF weights")
    parser.add_argument("--no-lora", action="store_true", help="Skip uploading LoRA adapters")

    args = parser.parse_args()
    deploy(
        repo_id=args.repo_id,
        upload_gguf=not args.no_gguf,
        upload_lora=not args.no_lora,
    )


if __name__ == "__main__":
    main()

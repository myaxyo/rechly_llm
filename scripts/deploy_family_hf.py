#!/usr/bin/env python3
"""
Deploy the Rechly model family tiers (1.5B and 0.5B) to their dedicated Hugging Face repositories.
"""

import os
import sys
from pathlib import Path
from huggingface_hub import HfApi

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def deploy_tier(repo_id: str, card_path: str, modelfile_path: str, gguf_path: str):
    api = HfApi()
    print("=" * 60)
    print(f"Deploying {repo_id}...")
    print("=" * 60)

    # 1. Create or verify repo
    api.create_repo(repo_id=repo_id, repo_type="model", exist_ok=True)
    print(f"1. Verified repository {repo_id}")

    # 2. Upload Model Card as README.md
    print("2. Uploading Model Card...")
    api.upload_file(
        path_or_fileobj=str(PROJECT_ROOT / card_path),
        path_in_repo="README.md",
        repo_id=repo_id,
        repo_type="model"
    )

    # 3. Upload Modelfile as Modelfile
    print("3. Uploading Modelfile...")
    api.upload_file(
        path_or_fileobj=str(PROJECT_ROOT / modelfile_path),
        path_in_repo="Modelfile",
        repo_id=repo_id,
        repo_type="model"
    )

    # 4. Upload Grammars and Schemas
    print("4. Uploading Grammars & Schemas...")
    grammars_dir = PROJECT_ROOT / "grammars"
    if grammars_dir.exists():
        for gf in grammars_dir.glob("*.gbnf"):
            api.upload_file(
                path_or_fileobj=str(gf),
                path_in_repo=f"grammars/{gf.name}",
                repo_id=repo_id,
                repo_type="model"
            )

    schemas_dir = PROJECT_ROOT / "data" / "schemas"
    if schemas_dir.exists():
        for sf in schemas_dir.glob("*.json"):
            api.upload_file(
                path_or_fileobj=str(sf),
                path_in_repo=f"schemas/{sf.name}",
                repo_id=repo_id,
                repo_type="model"
            )

    # 5. Upload GGUF binary
    full_gguf = PROJECT_ROOT / gguf_path
    if full_gguf.exists():
        real_path = os.path.realpath(str(full_gguf))
        size_mb = os.path.getsize(real_path) / (1024 * 1024)
        print(f"5. Uploading GGUF binary {gguf_path} ({size_mb:.2f} MB)...")
        api.upload_file(
            path_or_fileobj=real_path,
            path_in_repo=gguf_path,
            repo_id=repo_id,
            repo_type="model"
        )
        print(f"   [OK] {gguf_path} uploaded.")

    print(f"🚀 Deployment Complete for {repo_id}!")
    print(f"👉 https://huggingface.co/{repo_id}\n")


def main():
    # Deploy 1.5B (Slim)
    deploy_tier(
        repo_id="jonprompter/rechly-de-1.5b",
        card_path="MODEL_CARD_1.5B.md",
        modelfile_path="Modelfile.1.5b",
        gguf_path="rechly-de-1.5b-q4_k_m.gguf"
    )

    # Deploy 0.5B (Nano)
    deploy_tier(
        repo_id="jonprompter/rechly-de-0.5b",
        card_path="MODEL_CARD_0.5B.md",
        modelfile_path="Modelfile.0.5b",
        gguf_path="rechly-de-0.5b-q4_k_m.gguf"
    )


if __name__ == "__main__":
    main()

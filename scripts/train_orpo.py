#!/usr/bin/env python3
"""
ORPO (Odds Ratio Preference Optimization) Training Script for Rechly-DE-3B
Aligns Qwen2.5-3B-Instruct using domain-specific German tax and accounting preference pairs
(prompt, chosen, rejected) in a single-stage optimization pass without a separate reward model.

Usage:
    python scripts/train_orpo.py --dry-run
    python scripts/train_orpo.py --model Qwen/Qwen2.5-3B-Instruct --epochs 1 --batch-size 2
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET = PROJECT_ROOT / "data" / "rechly_preference_pairs.jsonl"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "adapters" / "rechly-de-3b-orpo"


def format_chatml_preference_sample(sample: Dict[str, Any]) -> Dict[str, str]:
    """
    Formats a raw (prompt, chosen, rejected) record into ChatML format
    compatible with Qwen2.5 and standard TRL ORPO / DPO trainers.
    """
    system_prompt = (
        "Du bist Rechly-DE-3B, ein spezialisiertes deutsches KI-Modell für GoBD-Konformität, "
        "Rechnungserstellung, DATEV SKR03/SKR04 Buchungslogik und Steuerrecht."
    )
    prompt_text = (
        f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        f"<|im_start|>user\n{sample['prompt']}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )
    chosen_text = f"{sample['chosen']}<|im_end|>"
    rejected_text = f"{sample['rejected']}<|im_end|>"

    return {
        "prompt": prompt_text,
        "chosen": chosen_text,
        "rejected": rejected_text
    }


def load_preference_dataset(file_path: Path) -> List[Dict[str, str]]:
    formatted = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            formatted.append(format_chatml_preference_sample(data))
    return formatted


def run_training(
    model_id: str,
    dataset_path: Path,
    output_dir: Path,
    epochs: int = 1,
    batch_size: int = 2,
    learning_rate: float = 8e-6,
    orpo_alpha: float = 0.1,
    dry_run: bool = False
):
    print("=" * 70)
    print("          RECHLY-DE-3B ORPO PREFERENCE ALIGNMENT")
    print("=" * 70)
    print(f"Base Model:       {model_id}")
    print(f"Dataset:          {dataset_path}")
    print(f"Output Directory: {output_dir}")
    print(f"Epochs:           {epochs}")
    print(f"Batch Size:       {batch_size}")
    print(f"Learning Rate:    {learning_rate}")
    print(f"ORPO Alpha:       {orpo_alpha}")
    print(f"Dry Run Mode:     {dry_run}")
    print("=" * 70 + "\n")

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")

    dataset = load_preference_dataset(dataset_path)
    print(f"[OK] Loaded {len(dataset)} formatted ChatML preference pairs.")
    print("Sample prompt preview:\n" + dataset[0]["prompt"][:180] + "...\n")

    if dry_run:
        print("[DRY RUN] Verification successful. Pipeline configuration is valid!")
        return

    # Attempt Hugging Face TRL & PEFT imports
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import LoraConfig
        from trl import ORPOConfig, ORPOTrainer
        from datasets import Dataset
    except ImportError as e:
        print(f"[ERROR] Required deep learning dependency missing: {e}")
        print("Install via: pip install torch transformers peft trl datasets")
        sys.exit(1)

    print("1. Loading Tokenizer & Model...")
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Check device
    device_map = "auto"
    torch_dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch_dtype,
        device_map=device_map,
        trust_remote_code=True
    )

    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )

    hf_dataset = Dataset.from_list(dataset)

    orpo_args = ORPOConfig(
        output_dir=str(output_dir),
        learning_rate=learning_rate,
        lr_scheduler_type="cosine",
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=4,
        num_train_epochs=epochs,
        max_prompt_length=512,
        max_length=1024,
        orpo_alpha=orpo_alpha,
        logging_steps=5,
        save_strategy="epoch",
        fp16=False,
        bf16=torch.cuda.is_available()
    )

    print("2. Initializing ORPOTrainer...")
    trainer = ORPOTrainer(
        model=model,
        args=orpo_args,
        train_dataset=hf_dataset,
        peft_config=peft_config,
        tokenizer=tokenizer
    )

    print("3. Commencing Alignment Training...")
    trainer.train()

    print("4. Saving Aligned LoRA Checkpoint...")
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    print(f"\n[COMPLETE] Model successfully aligned and saved to: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="ORPO Preference Alignment for Rechly-DE-3B")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-3B-Instruct", help="Hugging Face model ID or path")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET, help="Path to preference jsonl file")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Output directory for adapters")
    parser.add_argument("--epochs", type=int, default=1, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=2, help="Per-device batch size")
    parser.add_argument("--lr", type=float, default=8e-6, help="Learning rate")
    parser.add_argument("--orpo-alpha", type=float, default=0.1, help="Weight for the odds ratio penalty")
    parser.add_argument("--dry-run", action="store_true", help="Validate dataset and configuration without running GPU training")

    args = parser.parse_args()
    run_training(
        model_id=args.model,
        dataset_path=args.dataset,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        orpo_alpha=args.orpo_alpha,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()

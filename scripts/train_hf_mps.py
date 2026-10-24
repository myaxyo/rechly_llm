#!/usr/bin/env python3
"""
Rechly-DE-3B Fine-Tuning Pipeline with PyTorch, PEFT (LoRA), and Hugging Face Transformers.
Supports Apple Silicon Metal (MPS), Linux CUDA, and CPU.
100% Open Source.

Usage:
    python scripts/train_hf_mps.py --data data/rechly_german_accounting.jsonl --epochs 2 --batch-size 2
"""

import os
import sys
import json
import argparse
from pathlib import Path

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    get_linear_schedule_with_warmup,
)
from peft import LoraConfig, get_peft_model, TaskType

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SYSTEM_PROMPT = (
    "Du bist der offizielle Rechly KI-Buchhaltungsassistent für Deutschland. "
    "Du erstellst präzise, GoBD-konforme Rechnungsdaten im exakten JSON-Format und formulierst professionelle deutsche Geschäftskorrespondenz."
)


class ShareGPTAccountingDataset(Dataset):
    def __init__(self, jsonl_path: Path, tokenizer, max_length: int = 1024):
        self.examples = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue
                data = json.loads(line_str)
                convs = data["conversations"]
                human_text = convs[0]["value"]
                assistant_text = convs[1]["value"]

                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": human_text},
                    {"role": "assistant", "content": assistant_text},
                ]

                # Format with ChatML template
                formatted_text = tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=False
                )

                tokenized = tokenizer(
                    formatted_text,
                    truncation=True,
                    max_length=max_length,
                    padding="max_length",
                    return_tensors="pt",
                )

                input_ids = tokenized["input_ids"].squeeze(0)
                attention_mask = tokenized["attention_mask"].squeeze(0)
                labels = input_ids.clone()
                # Ignore padding in loss
                labels[labels == tokenizer.pad_token_id] = -100

                self.examples.append({
                    "input_ids": input_ids,
                    "attention_mask": attention_mask,
                    "labels": labels,
                })

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        return self.examples[idx]


def train(args):
    # Detect best available device
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        print("[Device] Using Apple Silicon Metal Performance Shaders (MPS)")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
        print("[Device] Using NVIDIA CUDA GPU")
    else:
        device = torch.device("cpu")
        print("[Device] Using CPU")

    print("==================================================")
    print("Rechly-DE-3B Training Pipeline (PyTorch + PEFT LoRA)")
    print(f"Base Model:     {args.model}")
    print(f"Dataset:        {args.data}")
    print(f"Output Adapter: {args.output_dir}")
    print(f"Epochs:         {args.epochs}")
    print(f"Batch Size:     {args.batch_size}")
    print(f"Learning Rate:  {args.lr}")
    print(f"Max Seq Length: {args.max_length}")
    print("==================================================\n")

    # 1. Load Tokenizer
    print("1. Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 2. Load Model
    print("2. Loading base model...")
    dtype = torch.bfloat16 if device.type != "cpu" else torch.float32
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        torch_dtype=dtype,
        trust_remote_code=True,
    )
    model.to(device)

    # 3. Setup LoRA
    print("3. Applying LoRA adapters...")
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # 4. Prepare Dataset
    print(f"4. Tokenizing dataset from {args.data}...")
    dataset = ShareGPTAccountingDataset(Path(args.data), tokenizer, max_length=args.max_length)
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)
    print(f"Dataset loaded: {len(dataset)} examples ({len(dataloader)} batches per epoch).")

    # 5. Optimizer & Scheduler
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    total_steps = len(dataloader) * args.epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=int(total_steps * 0.05),
        num_training_steps=total_steps,
    )

    # 6. Training Loop
    print("\n5. Starting training loop...")
    model.train()
    step = 0
    for epoch in range(1, args.epochs + 1):
        total_loss = 0.0
        for b_idx, batch in enumerate(dataloader, start=1):
            step += 1
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            total_loss += loss.item()

            if step % args.log_interval == 0 or b_idx == len(dataloader):
                avg_loss = total_loss / b_idx
                lr_curr = scheduler.get_last_lr()[0]
                print(f"Epoch [{epoch}/{args.epochs}] | Batch [{b_idx}/{len(dataloader)}] | Loss: {loss.item():.4f} (Avg: {avg_loss:.4f}) | LR: {lr_curr:.2e}")

    # 7. Save Adapter
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n6. Saving LoRA adapter to {output_dir}...")
    model.save_pretrained(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    print(f"[SUCCESS] Fine-tuning complete! Adapters saved to {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="PyTorch + PEFT LoRA training for Rechly-DE-3B")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-3B-Instruct")
    parser.add_argument("--data", type=str, default="data/rechly_german_accounting.jsonl")
    parser.add_argument("--output-dir", type=str, default="adapters/rechly-de-3b-hf")
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--max-length", type=int, default=768)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--log-interval", type=int, default=20)

    args = parser.parse_args()
    train(args)


if __name__ == "__main__":
    main()

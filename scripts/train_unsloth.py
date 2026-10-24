#!/usr/bin/env python3
"""
Rechly-DE-3B Fine-Tuning Pipeline with Unsloth
Optimized for Google Colab (T4 / A100 GPU) and Linux CUDA machines.

Usage:
    python scripts/train_unsloth.py --data data/rechly_german_accounting.jsonl --output rechly-de-3b
"""

import os
import sys
import argparse
from pathlib import Path


def train(args):
    try:
        import torch
        from unsloth import FastLanguageModel
        from datasets import load_dataset
        from trl import SFTTrainer
        from transformers import TrainingArguments
    except ImportError:
        print("Error: Unsloth, PyTorch, or Trl not found.")
        print("Please install requirements on CUDA/Colab:")
        print('pip install --no-deps "xformers<0.0.27" "trl<0.9.0" peft accelerate bitsandbytes')
        print('pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"')
        sys.exit(1)

    print("==================================================")
    print("Rechly-DE-3B Training Pipeline (Unsloth QLoRA)")
    print(f"Base Model:     {args.base_model}")
    print(f"Dataset:        {args.data}")
    print(f"Output GGUF:    {args.output}")
    print(f"Max Seq Length: {args.max_seq_length}")
    print(f"Epochs:         {args.epochs}")
    print("==================================================\n")

    # 1. Load Base Model in 4-bit
    print("1. Loading base model in 4-bit...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.base_model,
        max_seq_length=args.max_seq_length,
        load_in_4bit=True,
    )

    # 2. Add LoRA Adapters
    print("2. Applying LoRA adapters...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=args.lora_r,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        lora_alpha=args.lora_alpha,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
    )

    # 3. Load & Format Dataset
    print(f"3. Loading dataset from {args.data}...")
    dataset = load_dataset("json", data_files=args.data, split="train")

    def formatting_prompts_func(examples):
        convs = examples["conversations"]
        texts = []
        for conv in convs:
            # Map ShareGPT to standard chat template
            formatted_conv = []
            for msg in conv:
                role = "user" if msg["from"] == "human" else "assistant"
                formatted_conv.append({"role": role, "content": msg["value"]})
            text = tokenizer.apply_chat_template(
                formatted_conv, tokenize=False, add_generation_prompt=False
            )
            texts.append(text)
        return {"text": texts}

    print("Formatting conversations with ChatML template...")
    dataset = dataset.map(formatting_prompts_func, batched=True)

    # 4. Train Model
    print("4. Starting SFTTrainer...")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
        dataset_num_proc=2,
        packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=args.batch_size,
            gradient_accumulation_steps=args.grad_accum,
            warmup_steps=10,
            num_train_epochs=args.epochs,
            learning_rate=args.learning_rate,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=10,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=3407,
            output_dir=args.checkpoints_dir,
            save_strategy="epoch",
        ),
    )

    trainer_stats = trainer.train()
    print("Training finished successfully!")
    print(f"Training Loss: {trainer_stats.training_loss:.4f}")

    # 5. Export to GGUF for Ollama
    print(f"5. Exporting quantized GGUF ({args.quant_method})...")
    model.save_pretrained_gguf(
        args.output,
        tokenizer,
        quantization_method=args.quant_method,
    )
    print(f"[SUCCESS] Exported {args.output}-{args.quant_method.lower()}.gguf")
    print(f"You can now run: ollama create rechly-de-3b -f Modelfile")


def main():
    parser = argparse.ArgumentParser(description="Fine-tune Rechly-DE-3B using Unsloth")
    parser.add_argument("--base_model", type=str, default="Qwen/Qwen2.5-3B-Instruct")
    parser.add_argument("--data", type=str, default="data/rechly_german_accounting.jsonl")
    parser.add_argument("--output", type=str, default="rechly-de-3b")
    parser.add_argument("--checkpoints_dir", type=str, default="rechly_model_outputs")
    parser.add_argument("--max_seq_length", type=int, default=2048)
    parser.add_argument("--batch_size", type=int, default=2)
    parser.add_argument("--grad_accum", type=int, default=4)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--learning_rate", type=float, default=2e-4)
    parser.add_argument("--lora_r", type=int, default=16)
    parser.add_argument("--lora_alpha", type=int, default=32)
    parser.add_argument("--quant_method", type=str, default="q4_k_m", choices=["q4_k_m", "q8_0", "f16"])

    args = parser.parse_args()
    train(args)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Synthetic Dataset Generator for Rechly-DE-3B
Generates high-quality, GoBD-compliant German accounting training data in ShareGPT format.

Supports:
- OpenAI (GPT-4o, GPT-4o-mini)
- Anthropic (Claude 3.5 Sonnet, Claude 3.5 Haiku)
- OpenRouter
- Local Ollama (e.g. qwen2.5:14b)

Usage:
    python scripts/generate_dataset.py --provider openai --model gpt-4o-mini --output data/rechly_synthetic.jsonl
    python scripts/generate_dataset.py --provider ollama --model qwen2.5-coder:14b --batch-size 2
"""

import os
import sys
import json
import time
import argparse
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Import validator
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
try:
    from validate_dataset import validate_sharegpt_record, identify_domain
except ImportError:
    validate_sharegpt_record = None

DOMAINS_SPEC = {
    "text_to_invoice": {
        "target": 500,
        "name": "Domain 1: Text-to-Invoice (Strict JSON Extraction)",
        "prompt_instructions": """
Generate unique training pairs for Domain 1: Text-to-Invoice.
Input (human): Natural, colloquial, realistic German instructions requesting an invoice. Vary the industries (IT, craftsmen/Handwerk, consulting, gastronomy, e-commerce, legal, healthcare, event management, freight/logistics). Include various payment terms (14 Tage netto, 2% Skonto, sofort fällig, 30 Tage) and VAT rates (19%, 7% for books/food, or 0% for Kleinunternehmer/Reverse-Charge).
Output (gpt): A valid JSON object matching EXACTLY this schema:
{
  "client_name": "string",
  "due_days": number,
  "payment_terms": "string",
  "notes": "string",
  "items": [
    {
      "description": "string",
      "quantity": number,
      "unit_of_measure": "Stunde" | "Stück" | "Tag" | "Pauschal" | "Monat",
      "price": number,
      "tax_rate_percent": 19 | 7 | 0
    }
  ]
}
No markdown backticks around the JSON string inside the value. The value MUST be an unescaped or escaped JSON string that can be parsed by json.loads.
"""
    },
    "line_item_enhancement": {
        "target": 300,
        "name": "Domain 2: B2B Line Item Description Rewriter",
        "prompt_instructions": """
Generate unique training pairs for Domain 2: B2B Line Item Description Rewriter.
Input (human): Rough, informal, quick notes describing a service or trade work (e.g., "datenbank aufgeräumt", "küchenspüle angeschlossen", "steuererklärung durchgeguckt", "neue firewall eingerichtet", "social media plan gemacht").
Output (gpt): A formal, professional, audit-proof, GoBD-compliant German line item description suitable for an official B2B invoice.
"""
    },
    "tax_exemption_clauses": {
        "target": 200,
        "name": "Domain 3: German Tax & GoBD Compliance Notes",
        "prompt_instructions": """
Generate unique training pairs for Domain 3: German Tax & GoBD Compliance Notes.
Input (human): Questions or scenarios regarding tax exemptions, special regimes, and mandatory German statutory clauses on invoices (e.g. Kleinunternehmerregelung § 19 UStG, Reverse Charge Bauleistungen § 13b Abs. 2 Nr. 4 UStG, Innergemeinschaftliche Lieferung § 4 Nr. 1b i.V.m. § 6a UStG, B2B EU-Dienstleistung § 3a Abs. 2 UStG, Ausfuhrlieferung Drittland § 4 Nr. 1a i.V.m. § 6 UStG, Differenzbesteuerung § 25a UStG, Reiseleistungen § 25 UStG).
Output (gpt): The exact legally mandated German statutory clause and concise explanation complying with German tax law.
"""
    },
    "dunning_reminders": {
        "target": 200,
        "name": "Domain 4: Mahnwesen (Dunning Letters & Payment Reminders)",
        "prompt_instructions": """
Generate unique training pairs for Domain 4: Mahnwesen (Dunning Letters).
Input (human): Request for a payment reminder with invoice number, client name, overdue days, amount, and reminder stage:
- Stufe 1: Freundliche Zahlungserinnerung (sachlich, partnerschaftlich, Nachfrage ob Rechnung untergegangen ist)
- Stufe 2: 1. Mahnung (Bestimmter Ton, konkrete Nachfrist von 7 Tagen)
- Stufe 3: 2. Mahnung / Letzte Mahnung (Nachdrücklich, Ankündigung gerichtlicher Schritte / Inkasso bei Fristablauf)
Output (gpt): Complete German letter or email text starting with 'Betreff: ...' followed by greeting, clear debt details, polite but firm deadline, and formal closing.
"""
    },
    "skr03_skr04_expenses": {
        "target": 300,
        "name": "Domain 5: SKR03 / SKR04 Expense Categorization",
        "prompt_instructions": """
Generate unique training pairs for Domain 5: SKR03 / SKR04 Expense Categorization.
Input (human): Description of a business receipt or expense (e.g. Bewirtungsbeleg, Tankquittung, Software-Abo, Bahnfahrkarte, Bürobedarf, Fachliteratur, GWG Büromöbel, Telefonrechnung, Beratungskosten).
Output (gpt): Strict JSON object with SKR03 and SKR04 account numbers and tax details:
{
  "category": "string",
  "vat_rate": 19 | 7 | 0,
  "deductible_percent": number,
  "skr03_account": "4-digit string",
  "skr04_account": "4-digit string",
  "note": "string explaining GoBD compliance and receipt prerequisites"
}
"""
    }
}

SYSTEM_PROMPT = """You are a German Tax Advisor (Steuerberater) and Senior Machine Learning Engineer building a specialized training dataset for "Rechly-DE-3B", an open-source German invoicing and bookkeeping model.
You generate realistic, varied, 100% GoBD and UStG compliant examples.
All examples must be output as valid JSON Lines where each line is in ShareGPT format:
{"conversations": [{"from": "human", "value": "..."}, {"from": "gpt", "value": "..."}]}
Output ONLY raw JSON lines. No markdown formatting, no code fences (no ```json)."""


def query_llm(
    provider: str,
    model: str,
    prompt: str,
    system_prompt: str = SYSTEM_PROMPT,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> str:
    """Dispatches request to specified LLM provider."""
    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"), base_url=base_url)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        return resp.choices[0].message.content or ""

    elif provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        resp = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return resp.content[0].text if resp.content else ""

    elif provider == "openrouter":
        from openai import OpenAI
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key or os.environ.get("OPENROUTER_API_KEY"),
        )
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        return resp.choices[0].message.content or ""

    elif provider == "ollama":
        import requests
        endpoint = base_url or "http://localhost:11434"
        if endpoint.endswith("/v1"):
            endpoint = endpoint[:-3]
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {"temperature": 0.7}
        }
        try:
            r = requests.post(f"{endpoint}/api/chat", json=payload, timeout=120)
            r.raise_for_status()
            data = r.json()
            return data.get("message", {}).get("content", "")
        except Exception:
            # Fallback to OpenAI SDK format
            from openai import OpenAI
            client = OpenAI(base_url=f"{endpoint}/v1", api_key="ollama")
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )
            return resp.choices[0].message.content or ""

    else:
        raise ValueError(f"Unsupported provider '{provider}'")


def count_existing_domain_samples(file_path: Path) -> Dict[str, int]:
    counts = {d: 0 for d in DOMAINS_SPEC}
    if not file_path.exists():
        return counts

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            try:
                data = json.loads(line_str)
                h_val = data["conversations"][0]["value"]
                g_val = data["conversations"][1]["value"]
                dom = identify_domain(h_val, g_val)
                # Map domain name
                for k in counts:
                    if k in dom:
                        counts[k] += 1
                        break
            except Exception:
                continue
    return counts


def run_generation(args):
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"==================================================")
    print(f"Rechly-DE-3B Synthetic Dataset Generator")
    print(f"Provider:    {args.provider}")
    print(f"Model:       {args.model}")
    print(f"Output File: {output_path}")
    print(f"==================================================\n")

    if args.provider == "engine":
        from dataset_generator_engine import generate_full_dataset
        total = args.count if args.count else 800
        count = generate_full_dataset(output_path, target_total=total)
        print(f"\n[SUCCESS] Generated {count} balanced GoBD examples with open-source engine.")
        print(f"Run `python scripts/validate_dataset.py {output_path}` to inspect.")
        return

    existing_counts = count_existing_domain_samples(output_path)
    total_existing = sum(existing_counts.values())
    if total_existing > 0:
        print(f"Found {total_existing} existing examples in {output_path}:")
        for k, v in existing_counts.items():
            print(f"  - {k}: {v}")

    target_domains = [args.domain] if args.domain else list(DOMAINS_SPEC.keys())

    for domain_key in target_domains:
        spec = DOMAINS_SPEC[domain_key]
        domain_target = args.count if args.count else spec["target"]
        current_count = existing_counts.get(domain_key, 0)
        needed = domain_target - current_count

        if needed <= 0:
            print(f"[OK] {spec['name']}: Target of {domain_target} already reached ({current_count} present).")
            continue

        print(f"\n--> Generating {needed} examples for {spec['name']}...")
        batch_size = args.batch_size

        while needed > 0:
            current_batch = min(batch_size, needed)
            prompt = f"{spec['prompt_instructions']}\n\nGenerate {current_batch} unique, high-quality pairs. Return each pair as one JSON line in ShareGPT format."

            print(f"    Requesting batch of {current_batch}...", end="", flush=True)
            try:
                raw_output = query_llm(
                    provider=args.provider,
                    model=args.model,
                    prompt=prompt,
                    base_url=args.base_url,
                )
            except Exception as e:
                print(f" [FAILED: {e}] Retrying in 5s...")
                time.sleep(5)
                continue

            valid_batch_lines = []
            for line in raw_output.splitlines():
                line = line.strip()
                if not (line.startswith("{") and line.endswith("}")):
                    continue
                try:
                    record = json.loads(line)
                    if validate_sharegpt_record:
                        valid, msg, _ = validate_sharegpt_record(record, 0)
                        if not valid:
                            continue
                    valid_batch_lines.append(json.dumps(record, ensure_ascii=False))
                except Exception:
                    continue

            if valid_batch_lines:
                with open(output_path, "a", encoding="utf-8") as f:
                    for vl in valid_batch_lines:
                        f.write(vl + "\n")
                needed -= len(valid_batch_lines)
                print(f" [Saved {len(valid_batch_lines)} valid pairs | Remaining: {max(0, needed)}]")
            else:
                print(f" [No valid JSON pairs extracted, retrying...]")

            time.sleep(1.0)

    print("\nGeneration run completed successfully!")
    print(f"Run `python scripts/validate_dataset.py {output_path}` to inspect.")


def main():
    parser = argparse.ArgumentParser(description="Synthetic dataset generator for Rechly-DE-3B")
    parser.add_argument("--provider", type=str, choices=["engine", "ollama", "openai", "anthropic", "openrouter"], default="engine", help="Provider for dataset generation (default: open-source engine)")
    parser.add_argument("--model", type=str, default="qwen2.5:3b", help="Model name (e.g. qwen2.5:3b, qwen2.5-coder:14b, gpt-4o-mini)")
    parser.add_argument("--output", type=str, default="data/rechly_german_accounting.jsonl", help="Path to output JSONL file")
    parser.add_argument("--domain", type=str, choices=list(DOMAINS_SPEC.keys()), default=None, help="Generate for a specific domain only")
    parser.add_argument("--count", type=int, default=None, help="Override target count for selected domain")
    parser.add_argument("--batch-size", type=int, default=5, help="Number of examples per prompt call")
    parser.add_argument("--base-url", type=str, default=None, help="Custom base URL for OpenAI/Ollama compatible endpoints")

    args = parser.parse_args()
    run_generation(args)


if __name__ == "__main__":
    main()

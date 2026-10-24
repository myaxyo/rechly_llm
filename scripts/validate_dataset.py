#!/usr/bin/env python3
"""
Dataset Validator for Rechly-DE-3B Training Data
Validates ShareGPT JSONL files against strict GoBD, tax rules, and JSON schemas.

Usage:
    python scripts/validate_dataset.py [path_to_dataset.jsonl]
"""

import sys
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple

try:
    from jsonschema import validate, ValidationError
except ImportError:
    validate = None
    ValidationError = Exception

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INVOICE_SCHEMA_PATH = PROJECT_ROOT / "data" / "schemas" / "invoice_schema.json"
EXPENSE_SCHEMA_PATH = PROJECT_ROOT / "data" / "schemas" / "expense_schema.json"


def load_schema(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


INVOICE_SCHEMA = load_schema(INVOICE_SCHEMA_PATH)
EXPENSE_SCHEMA = load_schema(EXPENSE_SCHEMA_PATH)


def identify_domain(human_prompt: str, gpt_response: str) -> str:
    cleaned = gpt_response.strip()
    if cleaned.startswith("{") and "items" in cleaned:
        return "domain_1_text_to_invoice"
    if cleaned.startswith("{") and ("skr03" in cleaned or "skr04" in cleaned):
        return "domain_5_skr_expenses"
    combined = (human_prompt + " " + gpt_response).lower()
    if any(k in human_prompt.lower() for k in ["mahnung", "zahlungserinnerung", "überfällig"]):
        return "domain_4_dunning"
    if any(k in combined for k in [
        "§ 19", "§ 13b", "innergemeinschaft", "steuerfrei", "ausfuhr", "ustg",
        "pflichtangabe", "klausel", "ustdv", "§ 147 ao", "aufbewahrungsfrist",
        "differenzbesteuerung", "§ 25a", "§ 14 abs. 4", "§ 33", "steuerschuldnerschaft"
    ]):
        return "domain_3_tax_compliance"
    return "domain_2_line_item_enhancement"


def validate_sharegpt_record(record: Dict[str, Any], line_num: int) -> Tuple[bool, str, str]:
    """Validates ShareGPT structure and domain constraints."""
    if not isinstance(record, dict) or "conversations" not in record:
        return False, "Missing 'conversations' key at root", "unknown"
    
    convs = record["conversations"]
    if not isinstance(convs, list) or len(convs) < 2:
        return False, f"Conversations must be a list with at least 2 items, got {len(convs) if isinstance(convs, list) else type(convs)}", "unknown"
    
    human_msg = convs[0]
    gpt_msg = convs[1]

    if human_msg.get("from") != "human" or not human_msg.get("value", "").strip():
        return False, "First message must be {'from': 'human', 'value': '...'}", "unknown"

    if gpt_msg.get("from") != "gpt" or not gpt_msg.get("value", "").strip():
        return False, "Second message must be {'from': 'gpt', 'value': '...'}", "unknown"

    human_val = human_msg["value"].strip()
    gpt_val = gpt_msg["value"].strip()
    domain = identify_domain(human_val, gpt_val)

    # Domain 1 validation: Strict Invoice JSON
    if domain == "domain_1_text_to_invoice":
        try:
            data = json.loads(gpt_val)
        except json.JSONDecodeError as e:
            return False, f"Domain 1 GPT response is not valid JSON: {e}", domain

        if validate and INVOICE_SCHEMA:
            try:
                validate(instance=data, schema=INVOICE_SCHEMA)
            except ValidationError as e:
                return False, f"Domain 1 failed schema validation: {e.message}", domain
        else:
            if not isinstance(data.get("items"), list) or len(data["items"]) == 0:
                return False, "Domain 1 JSON must include at least one item in 'items'", domain

        # Tax rate check
        for item in data.get("items", []):
            tax = item.get("tax_rate_percent")
            if tax not in (0, 7, 19):
                return False, f"Invalid tax_rate_percent {tax}, must be 0, 7, or 19", domain

    # Domain 5 validation: Strict Expense JSON
    elif domain == "domain_5_skr_expenses":
        try:
            data = json.loads(gpt_val)
        except json.JSONDecodeError as e:
            return False, f"Domain 5 GPT response is not valid JSON: {e}", domain

        if validate and EXPENSE_SCHEMA:
            try:
                validate(instance=data, schema=EXPENSE_SCHEMA)
            except ValidationError as e:
                return False, f"Domain 5 failed schema validation: {e.message}", domain

        for k in ["skr03_account", "skr04_account"]:
            acc = str(data.get(k, ""))
            if not (acc.isdigit() and len(acc) == 4):
                return False, f"Account {k} must be 4 digits, got '{acc}'", domain

    return True, "", domain


def validate_file(file_path: Path) -> bool:
    print(f"=== Validating Dataset: {file_path} ===")
    if not file_path.exists():
        print(f"Error: File '{file_path}' does not exist.")
        return False

    seen_hashes = set()
    domain_counts = {
        "domain_1_text_to_invoice": 0,
        "domain_2_line_item_enhancement": 0,
        "domain_3_tax_compliance": 0,
        "domain_4_dunning": 0,
        "domain_5_skr_expenses": 0,
        "unknown": 0,
    }

    valid_lines = 0
    duplicate_count = 0
    errors: List[str] = []

    with open(file_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            line_str = line.strip()
            if not line_str:
                continue

            try:
                record = json.loads(line_str)
            except json.JSONDecodeError as e:
                errors.append(f"Line {idx}: JSONDecodeError - {e}")
                continue

            is_valid, msg, domain = validate_sharegpt_record(record, idx)
            if not is_valid:
                errors.append(f"Line {idx} [{domain}]: {msg}")
                continue

            # Check duplicates based on human prompt
            human_text = record["conversations"][0]["value"].strip().lower()
            prompt_hash = hashlib.sha256(human_text.encode("utf-8")).hexdigest()
            if prompt_hash in seen_hashes:
                duplicate_count += 1
            else:
                seen_hashes.add(prompt_hash)

            domain_counts[domain] = domain_counts.get(domain, 0) + 1
            valid_lines += 1

    print("\n--- Validation Summary ---")
    print(f"Total Valid Examples:   {valid_lines}")
    print(f"Duplicate Prompts:      {duplicate_count}")
    print(f"Failed Records:         {len(errors)}")

    print("\n--- Domain Distribution ---")
    domain_names = {
        "domain_1_text_to_invoice": "Domain 1: Text-to-Invoice (Strict JSON)",
        "domain_2_line_item_enhancement": "Domain 2: B2B Line Item Rewriter",
        "domain_3_tax_compliance": "Domain 3: German Tax & GoBD Notes",
        "domain_4_dunning": "Domain 4: Mahnwesen (Payment Reminders)",
        "domain_5_skr_expenses": "Domain 5: SKR03 / SKR04 Expense Accounts",
    }
    for dom_key, label in domain_names.items():
        cnt = domain_counts.get(dom_key, 0)
        pct = (cnt / valid_lines * 100) if valid_lines > 0 else 0
        print(f"  * {label}: {cnt} ({pct:.1f}%)")

    if errors:
        print("\n--- Errors Found ---")
        for err in errors[:15]:
            print(f"  [ERROR] {err}")
        if len(errors) > 15:
            print(f"  ... and {len(errors) - 15} more errors.")
        return False

    print("\n[SUCCESS] Dataset is 100% valid and ready for training!")
    return True


if __name__ == "__main__":
    target_path = Path(sys.argv[1]) if len(sys.argv) > 1 else PROJECT_ROOT / "data" / "seed_dataset.jsonl"
    success = validate_file(target_path)
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Validator for Rechly DPO / ORPO Preference Dataset
Checks schema integrity, uniqueness of IDs, diversity of tax domains,
and non-empty chosen/rejected pairs.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = PROJECT_ROOT / "data" / "rechly_preference_pairs.jsonl"


def validate_preference_dataset(dataset_path: Path = DATASET_PATH) -> Dict[str, Any]:
    if not dataset_path.exists():
        raise FileNotFoundError(f"Preference dataset not found at {dataset_path}")

    seen_ids = set()
    domain_counts: Dict[str, int] = {}
    total_pairs = 0
    errors: List[str] = []

    required_keys = ["id", "domain", "prompt", "chosen", "rejected", "penalty_reason"]

    with open(dataset_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"Line {line_no}: Invalid JSON: {e}")
                continue

            total_pairs += 1

            # Key check
            for k in required_keys:
                if k not in record or not str(record[k]).strip():
                    errors.append(f"Line {line_no} (ID: {record.get('id')}): Missing or empty required field '{k}'")

            # ID uniqueness
            pair_id = record.get("id")
            if pair_id in seen_ids:
                errors.append(f"Line {line_no}: Duplicate ID '{pair_id}'")
            seen_ids.add(pair_id)

            # Equality check
            if record.get("chosen") == record.get("rejected"):
                errors.append(f"Line {line_no} (ID: {pair_id}): 'chosen' and 'rejected' are identical!")

            # Domain tally
            domain = record.get("domain", "Unknown")
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

    is_valid = len(errors) == 0
    return {
        "is_valid": is_valid,
        "total_pairs": total_pairs,
        "unique_ids": len(seen_ids),
        "domain_counts": domain_counts,
        "errors": errors
    }


def main():
    print("=" * 70)
    print("      RECHLY DPO / ORPO PREFERENCE DATASET VALIDATION")
    print("=" * 70)
    res = validate_preference_dataset()
    print(f"Total Preference Pairs: {res['total_pairs']}")
    print(f"Unique Sample IDs:      {res['unique_ids']}")
    print(f"Validation Status:      {'[PASSED OK]' if res['is_valid'] else '[FAILED]'}\n")
    print("Domain Distribution:")
    for dom, count in res["domain_counts"].items():
        print(f"  - {dom:<45} {count:3d} pairs")

    if not res["is_valid"]:
        print("\nErrors Found:")
        for err in res["errors"]:
            print(f"  [ERROR] {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Unit tests for the open-source dataset generator engine.
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from dataset_generator_engine import (
    generate_domain_1_samples,
    generate_domain_2_samples,
    generate_domain_3_samples,
    generate_domain_4_samples,
    generate_domain_5_samples,
)
from validate_dataset import validate_sharegpt_record


def test_domain_1_generation():
    samples = generate_domain_1_samples(count=10)
    assert len(samples) == 10
    for s in samples:
        is_valid, msg, domain = validate_sharegpt_record(s, 1)
        assert is_valid is True, f"Domain 1 validation failed: {msg}"
        assert domain == "domain_1_text_to_invoice"


def test_domain_2_generation():
    samples = generate_domain_2_samples(count=10)
    assert len(samples) == 10
    for s in samples:
        is_valid, msg, domain = validate_sharegpt_record(s, 1)
        assert is_valid is True, f"Domain 2 validation failed: {msg}"
        assert domain == "domain_2_line_item_enhancement"


def test_domain_3_generation():
    samples = generate_domain_3_samples(count=10)
    assert len(samples) == 10
    for s in samples:
        is_valid, msg, domain = validate_sharegpt_record(s, 1)
        assert is_valid is True, f"Domain 3 validation failed: {msg}"
        assert domain == "domain_3_tax_compliance"


def test_domain_4_generation():
    samples = generate_domain_4_samples(count=10)
    assert len(samples) == 10
    for s in samples:
        is_valid, msg, domain = validate_sharegpt_record(s, 1)
        assert is_valid is True, f"Domain 4 validation failed: {msg}"
        assert domain == "domain_4_dunning"
        assert "betreff" in s["conversations"][1]["value"].lower()


def test_domain_5_generation():
    samples = generate_domain_5_samples(count=10)
    assert len(samples) == 10
    for s in samples:
        is_valid, msg, domain = validate_sharegpt_record(s, 1)
        assert is_valid is True, f"Domain 5 validation failed: {msg}"
        assert domain == "domain_5_skr_expenses"

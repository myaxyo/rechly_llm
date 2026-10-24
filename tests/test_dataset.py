"""
Unit tests for dataset integrity and validation.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from validate_dataset import validate_file


def test_seed_dataset_valid():
    seed_file = PROJECT_ROOT / "data" / "seed_dataset.jsonl"
    assert seed_file.exists(), "seed_dataset.jsonl must exist"
    assert validate_file(seed_file) is True


def test_synthetic_dataset_valid():
    synth_file = PROJECT_ROOT / "data" / "rechly_german_accounting.jsonl"
    assert synth_file.exists(), "rechly_german_accounting.jsonl must exist"
    assert validate_file(synth_file) is True

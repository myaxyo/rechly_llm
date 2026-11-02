import pytest
from pathlib import Path
from scripts.validate_preference_dataset import validate_preference_dataset
from scripts.train_orpo import format_chatml_preference_sample, load_preference_dataset

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREF_DATASET_PATH = PROJECT_ROOT / "data" / "rechly_preference_pairs.jsonl"


def test_preference_dataset_exists():
    assert PREF_DATASET_PATH.exists()
    assert PREF_DATASET_PATH.stat().st_size > 1000


def test_validate_preference_dataset():
    res = validate_preference_dataset(PREF_DATASET_PATH)
    assert res["is_valid"] is True
    assert res["total_pairs"] >= 50
    assert res["unique_ids"] == res["total_pairs"]
    assert len(res["errors"]) == 0
    assert len(res["domain_counts"]) >= 5


def test_format_chatml_preference_sample():
    sample = {
        "id": "TEST-01",
        "domain": "Test",
        "prompt": "Test prompt",
        "chosen": "Valid chosen",
        "rejected": "Bad rejected",
        "penalty_reason": "Testing reason"
    }
    formatted = format_chatml_preference_sample(sample)
    assert "<|im_start|>user\nTest prompt<|im_end|>" in formatted["prompt"]
    assert "Valid chosen<|im_end|>" == formatted["chosen"]
    assert "Bad rejected<|im_end|>" == formatted["rejected"]


def test_load_preference_dataset():
    data = load_preference_dataset(PREF_DATASET_PATH)
    assert len(data) >= 50
    for itm in data[:5]:
        assert "prompt" in itm
        assert "chosen" in itm
        assert "rejected" in itm
        assert itm["chosen"] != itm["rejected"]

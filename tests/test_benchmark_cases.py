"""
Unit tests for the comprehensive 77-point audit benchmark suite.
Verifies test case counts, domain coverage, schema validity, and engine case execution.
"""

import pytest
from scripts.benchmark_comprehensive import BENCHMARK_CASES, evaluate_test_case


def test_benchmark_case_counts_and_domains():
    assert len(BENCHMARK_CASES) >= 75, f"Expected at least 75 benchmark cases, got {len(BENCHMARK_CASES)}"
    
    domains = set(tc["domain"] for tc in BENCHMARK_CASES)
    assert len(domains) == 12, f"Expected 12 domains, got {len(domains)}: {sorted(domains)}"

    expected_domains = [
        "Domain 1: Text-to-Invoice",
        "Domain 2: Line Item Rewriter",
        "Domain 3: Tax & GoBD Clauses",
        "Domain 4: Mahnwesen",
        "Domain 5: SKR Expenses",
        "Domain 6: E-Rechnung XRechnung 3.0",
        "Domain 7: GoBD § 14 UStG Pre-Audit",
        "Domain 8: DATEV Buchungssatz CSV",
        "Domain 9: ZUGFeRD 2.3 Hybrid Engine",
        "Domain 10: Multimodal Receipt OCR",
        "Domain 11: Enterprise DATEV Batch",
        "Domain 12: Cent-Perfect Reconciler"
    ]
    for d in expected_domains:
        assert d in domains, f"Missing domain '{d}'"


def test_engine_cases_100_percent_pass():
    engine_cases = [tc for tc in BENCHMARK_CASES if tc["type"] in ("zugferd", "vision_ocr", "datev_batch", "reconcile")]
    assert len(engine_cases) == 20, f"Expected 20 engine benchmark cases, got {len(engine_cases)}"

    for tc in engine_cases:
        success, reasons = evaluate_test_case(tc, raw_output=None)
        assert success is True, f"Benchmark case {tc['id']} ({tc['name']}) failed: {reasons}"

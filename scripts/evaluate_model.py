#!/usr/bin/env python3
"""
Evaluation Suite for Rechly-DE-3B
Tests model performance across the 5 core German accounting domains via Ollama or OpenAI-compatible endpoint.

Usage:
    python scripts/evaluate_model.py --model rechly-de-3b
    python scripts/evaluate_model.py --model qwen2.5:3b --base-url http://localhost:11434/v1
"""

import sys
import json
from json_utils import loads as strict_loads
import argparse
from typing import Dict, Any, List

TEST_CASES = [
    # Domain 1: Text-to-Invoice
    {
        "domain": "Domain 1: Text-to-Invoice",
        "prompt": "Erstelle eine Rechnung an Kanzlei Schmidt & Partner: 12 Stunden IT-Forensik à 140€ und Anfahrt Pauschal 80€, zahlbar in 14 Tagen mit 2% Skonto.",
        "type": "json_invoice",
        "expected_keys": ["client_name", "due_days", "items"],
        "expected_values": {"client_name": "Kanzlei Schmidt & Partner", "due_days": 14},
        "expected_items": [{"quantity": 12, "price": 140, "tax_rate_percent": 19},
                           {"quantity": 1, "price": 80, "tax_rate_percent": 19}],
    },
    {
        "domain": "Domain 1: Text-to-Invoice (Kleinunternehmer)",
        "prompt": "Rechnung an Blumenladen Rose: 5 Stunden Schaufensterdeko à 55€, ich bin Kleinunternehmer.",
        "type": "json_invoice",
        "expected_keys": ["client_name", "due_days", "items"],
        "expected_vat": 0,
    },

    # Domain 2: Line Item Rewriting
    {
        "domain": "Domain 2: Line Item Rewriter",
        "prompt": "Formuliere folgende Position professionell und GoBD-konform für eine Rechnung: 'homepage schneller gemacht und alte bilder gelöscht'",
        "type": "text",
        "required_keywords": ["optimierung", "webseite", "performance", "bereinigung", "ladezeit"],
    },

    # Domain 3: Tax & GoBD Compliance
    {
        "domain": "Domain 3: Tax Exemption Clause (§ 19 UStG)",
        "prompt": "Welcher steuerliche Pflichttext muss auf die Rechnung bei Inanspruchnahme der Kleinunternehmerregelung?",
        "type": "text",
        "required_keywords": ["19", "ustg", "keine umsatzsteuer", "kleinunternehmer"],
    },
    {
        "domain": "Domain 3: Reverse Charge (§ 13b UStG)",
        "prompt": "Welcher Vermerk gehört auf die Rechnung für Handwerkerleistungen an einen Generalunternehmer?",
        "type": "text",
        "required_keywords": ["13b", "steuerschuldnerschaft", "leistungsempfänger"],
    },

    # Domain 4: Mahnwesen
    {
        "domain": "Domain 4: Dunning Letter (Stufe 1)",
        "prompt": "Erstelle eine freundliche Zahlungserinnerung für Rechnung RE-9901 an Meier GmbH über 1.500 EUR, 5 Tage überfällig.",
        "type": "text",
        "required_keywords": ["betreff", "re-9901", "1.500", "überfällig", "zahlungserinnerung"],
    },

    # Domain 5: SKR03 / SKR04 Expense Categorization
    {
        "domain": "Domain 5: SKR Expense (Bewirtung)",
        "prompt": "Kategorisiere für SKR03 und SKR04: 'Geschäftsessen mit Neukunden im Steakhouse 160€ netto zzgl. 19% MwSt'",
        "type": "json_expense",
        "expected_keys": ["category", "vat_rate", "deductible_percent", "skr03_account", "skr04_account"],
        "expected_skr03": "4650",
    },
    {
        "domain": "Domain 5: SKR Expense (SaaS Software)",
        "prompt": "Kategorisiere für SKR03 und SKR04: 'Monatsrechnung Google Workspace 25€ netto'",
        "type": "json_expense",
        "expected_keys": ["category", "vat_rate", "skr03_account", "skr04_account"],
    },
]


from pathlib import Path
from datetime import datetime, timezone
import time
from jsonschema import validate, ValidationError
from validate_dataset import INVOICE_SCHEMA, EXPENSE_SCHEMA


def query_model(prompt: str, model: str, base_url: str, api_key: str = "ollama") -> str:
    from openai import OpenAI
    with OpenAI(base_url=base_url, api_key=api_key, timeout=90, max_retries=0) as client:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Du bist Rechlys deutscher Buchhaltungsassistent. Erstelle Entwürfe zur menschlichen Prüfung. Gib strukturierte Antworten ausschließlich als JSON aus."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
        )
    return resp.choices[0].message.content or ""


def score_response(tc, output):
    """Strict structural checks and explicit content heuristics, not legal review."""
    errors = []
    if tc["type"] in ("json_invoice", "json_expense"):
        try:
            data = strict_loads(output)
            schema = INVOICE_SCHEMA if tc["type"] == "json_invoice" else EXPENSE_SCHEMA
            validate(data, schema)
            if tc.get("expected_vat") is not None:
                if any(item["tax_rate_percent"] != tc["expected_vat"] for item in data["items"]):
                    errors.append("Unexpected VAT rate")
            if tc.get("expected_skr03") and data["skr03_account"] != tc["expected_skr03"]:
                errors.append("Unexpected SKR03 account")
            for key, expected in tc.get("expected_values", {}).items():
                if data.get(key) != expected:
                    errors.append(f"Unexpected {key}")
            if "expected_items" in tc and data["items"] != tc["expected_items"]:
                # Compare only explicitly annotated facts; wording is not scored.
                expected = tc["expected_items"]
                if len(data["items"]) != len(expected) or any(
                    any(actual.get(k) != v for k, v in item.items())
                    for actual, item in zip(data["items"], expected)
                ):
                    errors.append("Incorrect extracted line-item facts")
        except (ValueError, ValidationError) as exc:
            errors.append(f"Invalid structured response: {type(exc).__name__}")
    else:
        missing = [kw for kw in tc.get("required_keywords", []) if kw.casefold() not in output.casefold()]
        if missing:
            errors.append("Missing expected terms: " + ", ".join(missing))
    return errors


def evaluate(model: str, base_url: str):
    results = []
    for index, case in enumerate(TEST_CASES):
        started = time.perf_counter()
        try:
            output = query_model(case["prompt"], model, base_url)
            errors = score_response(case, output)
            status = "failed" if errors else "passed"
        except Exception as exc:
            # Avoid recording credentials, private response bodies or proxy URLs.
            errors, status = [f"Request failed: {type(exc).__name__}"], "error"
        result = {"id": index + 1, "domain": case["domain"], "status": status,
                  "latency_seconds": round(time.perf_counter() - started, 3), "errors": errors}
        results.append(result)
        print(f"[{index + 1}/{len(TEST_CASES)}] {status}: {case['domain']}")
    passed = sum(r["status"] == "passed" for r in results)
    return {"model": model, "created_at": datetime.now(timezone.utc).isoformat(),
            "benchmark_version": 1, "total": len(results), "passed": passed,
            "failed": sum(r["status"] == "failed" for r in results),
            "errors": sum(r["status"] == "error" for r in results),
            "score_percent": round(100 * passed / len(results), 2), "results": results}


def main():
    parser = argparse.ArgumentParser(description="Evaluate Rechly model; exits 1 if any case fails")
    parser.add_argument("--model", default="rechly-de-3b")
    parser.add_argument("--base-url", default="http://localhost:11434/v1")
    parser.add_argument("--report", type=Path, default=Path("reports/evaluation.json"))
    args = parser.parse_args()
    report = evaluate(args.model, args.base_url)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"{report['passed']}/{report['total']} passed; report: {args.report}")
    return 0 if report["passed"] == report["total"] else 1


if __name__ == "__main__":
    sys.exit(main())

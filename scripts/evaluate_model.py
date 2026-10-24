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
import argparse
from typing import Dict, Any, List

TEST_CASES = [
    # Domain 1: Text-to-Invoice
    {
        "domain": "Domain 1: Text-to-Invoice",
        "prompt": "Erstelle eine Rechnung an Kanzlei Schmidt & Partner: 12 Stunden IT-Forensik à 140€ und Anfahrt Pauschal 80€, zahlbar in 14 Tagen mit 2% Skonto.",
        "type": "json_invoice",
        "expected_keys": ["client_name", "due_days", "items"],
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
        "required_keywords": ["optimierung", "webseite", "homepage", "performance", "bereinigung", "ladezeit", "effizienz"],
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


def query_model(prompt: str, model: str, base_url: str, api_key: str = "ollama", system: str = None) -> str:
    from openai import OpenAI
    client = OpenAI(base_url=base_url, api_key=api_key)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.1,
    )
    return resp.choices[0].message.content or ""


def evaluate(model: str, base_url: str):
    print(f"==================================================")
    print(f"Evaluating Model: {model}")
    print(f"Target Endpoint:  {base_url}")
    print(f"Total Tests:      {len(TEST_CASES)}")
    print(f"==================================================\n")

    passed = 0
    failed = 0

    for idx, tc in enumerate(TEST_CASES, start=1):
        print(f"[{idx}/{len(TEST_CASES)}] Testing {tc['domain']}...")
        print(f"    Prompt: \"{tc['prompt'][:60]}...\"")

        try:
            output = query_model(tc["prompt"], model, base_url)
        except Exception as e:
            print(f"    [FAIL] Connection or execution error: {e}\n")
            failed += 1
            continue

        test_passed = True
        fail_reasons = []

        if tc["type"] in ("json_invoice", "json_expense"):
            cleaned = output.strip()
            # Remove any markdown wrapping if model output it
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()

            try:
                data = json.loads(cleaned)
                for k in tc["expected_keys"]:
                    if k not in data:
                        test_passed = False
                        fail_reasons.append(f"Missing key '{k}' in JSON response")

                if tc.get("expected_vat") is not None and "items" in data:
                    for itm in data["items"]:
                        if itm.get("tax_rate_percent") != tc["expected_vat"]:
                            test_passed = False
                            fail_reasons.append(f"Expected tax {tc['expected_vat']}%, got {itm.get('tax_rate_percent')}%")

                if tc.get("expected_skr03") and str(data.get("skr03_account")) != tc["expected_skr03"]:
                    test_passed = False
                    fail_reasons.append(f"Expected SKR03 '{tc['expected_skr03']}', got '{data.get('skr03_account')}'")

            except json.JSONDecodeError as e:
                test_passed = False
                fail_reasons.append(f"Invalid JSON: {e}")

        elif tc["type"] == "text":
            out_lower = output.lower()
            if "required_keywords" in tc:
                # Require at least 2 matching keywords or key match
                matches = [kw for kw in tc["required_keywords"] if kw in out_lower]
                if len(matches) < 2:
                    test_passed = False
                    fail_reasons.append(f"Output missed required keywords. Found only: {matches}")

        if test_passed:
            print(f"    [PASS] Output satisfies criteria.")
            passed += 1
        else:
            print(f"    [FAIL] Reasons: {', '.join(fail_reasons)}")
            print(f"    Raw Response:\n{output[:160]}...\n")
            failed += 1

    print("==================================================")
    score_pct = (passed / len(TEST_CASES)) * 100
    print(f"Evaluation Results: {passed}/{len(TEST_CASES)} passed ({score_pct:.1f}%)")
    print(f"==================================================")


def main():
    parser = argparse.ArgumentParser(description="Evaluate Rechly-DE-3B model")
    parser.add_argument("--model", type=str, default="rechly-de-3b", help="Model name in Ollama")
    parser.add_argument("--base-url", type=str, default="http://localhost:11434/v1", help="API base URL")

    args = parser.parse_args()
    evaluate(args.model, args.base_url)


if __name__ == "__main__":
    main()

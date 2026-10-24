#!/usr/bin/env python3
"""
Rechly AI CLI Tool
Command-line interface for Rechly-DE-3B accounting AI.

Usage:
    python scripts/cli.py invoice "Rechnung an WebTech GmbH: 10 Std. Beratung à 100€"
    python scripts/cli.py enhance "website schneller gemacht und datenbank geputzt"
    python scripts/cli.py tax "Kleinunternehmer"
    python scripts/cli.py dunning --nr RE-2026-001 --client "Firma GmbH" --amount 1500 --days 14 --stage 1
    python scripts/cli.py expense "Geschäftsessen mit Kunde im Restaurant 120€"
    python scripts/cli.py status
"""

import sys
import json
import argparse
from pathlib import Path

# Add scripts directory to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from rechly_client import RechlyClient


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"🇩🇪 Rechly-DE-3B: {title}")
    print("=" * 60)


def cmd_invoice(args, client: RechlyClient):
    print_header("Text-zu-Rechnung (GoBD JSON)")
    print(f"Eingabe: {args.prompt}\n")
    try:
        data = client.text_to_invoice(args.prompt)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


def cmd_enhance(args, client: RechlyClient):
    print_header("B2B Positionstext-Optimierer")
    print(f"Ursprüngliche Notiz: {args.note}\n")
    try:
        enhanced = client.enhance_description(args.note)
        print("GoBD-konforme Formulierung:")
        print(f"👉 {enhanced}")
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


def cmd_tax(args, client: RechlyClient):
    print_header("Steuer- & GoBD-Pflichtklauseln")
    print(f"Sachverhalt: {args.scenario}\n")
    try:
        clause = client.get_tax_clause(args.scenario)
        print("Offizieller Rechnungsvermerk:")
        print(f"👉 {clause}")
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


def cmd_dunning(args, client: RechlyClient):
    print_header(f"Mahnwesen (Stufe {args.stage})")
    print(f"Rechnung: {args.nr} | Kunde: {args.client} | Betrag: {args.amount:.2f} € | Überfällig: {args.days} Tage\n")
    try:
        letter = client.generate_dunning_letter(
            invoice_number=args.nr,
            client_name=args.client,
            amount=args.amount,
            overdue_days=args.days,
            stage=args.stage,
        )
        print(letter)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


def cmd_expense(args, client: RechlyClient):
    print_header("DATEV SKR03 / SKR04 Kontierung")
    print(f"Beleg: {args.receipt}\n")
    try:
        data = client.categorize_expense(args.receipt)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


def cmd_status(args, client: RechlyClient):
    print_header("System & Modell Status")
    gw_ok = client.is_gateway_available()
    ollama_ok = client.is_ollama_available()

    print(f"Modell-Name:          {client.model}")
    print(f"Rechly API Gateway:   {'🟢 Online (http://localhost:8000)' if gw_ok else '⚪ Offline'}")
    print(f"Ollama Daemon:        {'🟢 Online (http://localhost:11434)' if ollama_ok else '⚪ Offline'}")
    print(f"DSGVO Konformität:    100% Lokal (Zero Data Egress)")


def main():
    parser = argparse.ArgumentParser(
        prog="rechly-cli",
        description="Rechly-DE-3B: Local German Accounting AI CLI",
    )
    parser.add_argument("--gateway-url", type=str, default="http://localhost:8000", help="Rechly API Gateway URL")
    parser.add_argument("--ollama-url", type=str, default="http://localhost:11434", help="Ollama daemon URL")
    parser.add_argument("--model", type=str, default="rechly-de-3b", help="Model name in Ollama")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # invoice
    p_inv = subparsers.add_parser("invoice", help="Convert text to GoBD invoice JSON")
    p_inv.add_argument("prompt", type=str, help="Colloquial German invoice description")

    # enhance
    p_enh = subparsers.add_parser("enhance", help="Enhance informal note into audit-proof description")
    p_enh.add_argument("note", type=str, help="Informal service or trade note")

    # tax
    p_tax = subparsers.add_parser("tax", help="Get official statutory tax clause")
    p_tax.add_argument("scenario", type=str, help="Tax scenario (e.g. Kleinunternehmer, Reverse Charge §13b)")

    # dunning
    p_dun = subparsers.add_parser("dunning", help="Generate dunning payment reminder")
    p_dun.add_argument("--nr", type=str, required=True, help="Invoice number (e.g. RE-2026-001)")
    p_dun.add_argument("--client", type=str, required=True, help="Client company name")
    p_dun.add_argument("--amount", type=float, required=True, help="Invoice total amount in EUR")
    p_dun.add_argument("--days", type=int, default=14, help="Days overdue")
    p_dun.add_argument("--stage", type=int, choices=[1, 2, 3], default=1, help="Dunning stage (1, 2, or 3)")

    # expense
    p_exp = subparsers.add_parser("expense", help="Categorize expense to SKR03/SKR04")
    p_exp.add_argument("receipt", type=str, help="Receipt or expense description")

    # status
    subparsers.add_parser("status", help="Check gateway and Ollama connection status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    client = RechlyClient(
        api_base_url=args.gateway_url,
        ollama_base_url=args.ollama_url,
        model=args.model,
    )

    cmds = {
        "invoice": cmd_invoice,
        "enhance": cmd_enhance,
        "tax": cmd_tax,
        "dunning": cmd_dunning,
        "expense": cmd_expense,
        "status": cmd_status,
    }

    cmds[args.command](args, client)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
DATEV EXTF & Buchungssatz Utilities for Rechly-DE-3B
Generates and validates DATEV-compliant ASCII / EXTF (Formatversion 700 / 510) Buchungsstapel
for automated import into DATEV Rechnungswesen, Kanzlei-Rechnungswesen, and DATEV Unternehmen online.
"""

from typing import Dict, Any, List, Optional
import csv
import io


DATEV_HEADER_EXTF_700 = (
    '"EXTF";700;21;"Buchungsstapel";13;20250101;20250101;;"";"";"";"";"";"";"";;'
    '"";"";"";"";"";"";"";"";"";"";"";"";"";"";"";""'
)

DATEV_COLUMNS = [
    "Umsatz",
    "Soll/Haben-Kennzeichen",
    "WKZ",
    "Kurs",
    "Basis-Umsatz",
    "WKZ Basis-Umsatz",
    "Konto",
    "Gegenkonto",
    "BU-Schlüssel",
    "Belegdatum",
    "Belegfeld 1",
    "Belegfeld 2",
    "Skonto",
    "Buchungstext",
]


def format_datev_buchungssatz(record: Dict[str, Any]) -> str:
    """Formats a single accounting entry into a DATEV EXTF CSV line."""
    umsatz = f"{float(record.get('umsatz', 0.0)):.2f}".replace(".", ",")
    sh = str(record.get("soll_haben", "S")).upper()
    wkz = "EUR"
    konto = str(record.get("konto", ""))
    gegenkonto = str(record.get("gegenkonto", ""))
    bu = str(record.get("bu_schluessel", ""))
    belegdatum = str(record.get("belegdatum", "")).replace("-", "")[:4]  # e.g. 1502 for 15. Feb
    belegfeld1 = str(record.get("belegfeld1", record.get("rechnungsnummer", "")))[:36]
    text = str(record.get("buchungstext", ""))[:60]

    row = [umsatz, sh, wkz, "", "", "", konto, gegenkonto, bu, belegdatum, belegfeld1, "", "", text]
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(row)
    return output.getvalue().strip()


def export_datev_csv(records: List[Dict[str, Any]]) -> str:
    """Exports a complete DATEV EXTF formatted file string with official header."""
    lines = [
        DATEV_HEADER_EXTF_700,
        ";".join([f'"{col}"' for col in DATEV_COLUMNS])
    ]
    for r in records:
        lines.append(format_datev_buchungssatz(r))
    return "\r\n".join(lines) + "\r\n"


if __name__ == "__main__":
    sample = {
        "umsatz": 142.80,
        "soll_haben": "S",
        "konto": "4964",
        "gegenkonto": "1200",
        "bu_schluessel": "9",
        "belegdatum": "1502",
        "belegfeld1": "RE-2025-081",
        "buchungstext": "Google Workspace SaaS"
    }
    print("Formatted DATEV Buchungssatz:")
    print(format_datev_buchungssatz(sample))
